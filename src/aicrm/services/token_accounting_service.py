"""
Сервис учета токенов AI с квотами и лимитами
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..models.token_accounting import TokenQuota, TokenTransaction


class TokenAccountingService:
    """Сервис для учета токенов AI с поддержкой квот и алертов"""

    def __init__(self, db: Session):
        self.db = db

    async def create_or_update_quota(
        self,
        entity_type: str,
        entity_id: int,
        quota_type: str,
        limit_tokens: Optional[int] = None,
        alert_threshold: Optional[int] = None,
    ) -> TokenQuota:
        """
        Создание или обновление квоты токенов

        Args:
            entity_type: Тип сущности ('company' или 'user')
            entity_id: ID сущности
            quota_type: Тип квоты ('monthly', 'total', 'per_workflow')
            limit_tokens: Лимит токенов (None = безлимит)
            alert_threshold: Порог для уведомления (%)

        Returns:
            TokenQuota: Созданная или обновленная квота
        """
        # Ищем существующую квоту
        quota = (
            self.db.query(TokenQuota)
            .filter(
                and_(
                    TokenQuota.entity_type == entity_type,
                    TokenQuota.entity_id == entity_id,
                    TokenQuota.quota_type == quota_type,
                )
            )
            .first()
        )

        if quota:
            # Обновляем существующую
            if limit_tokens is not None:
                quota.limit_tokens = limit_tokens
            if alert_threshold is not None:
                quota.alert_threshold = alert_threshold
            quota.updated_at = datetime.utcnow()
        else:
            # Создаем новую
            reset_at = None
            if quota_type == "monthly":
                # Следующий месяц
                now = datetime.utcnow()
                if now.month == 12:
                    reset_at = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                else:
                    reset_at = now.replace(
                        month=now.month + 1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )

            quota = TokenQuota(
                entity_type=entity_type,
                entity_id=entity_id,
                quota_type=quota_type,
                limit_tokens=limit_tokens,
                alert_threshold=alert_threshold,
                reset_at=reset_at,
            )
            self.db.add(quota)

        self.db.commit()
        self.db.refresh(quota)
        return quota

    async def check_quota_and_record_transaction(
        self,
        entity_type: str,
        entity_id: int,
        ai_provider: str,
        ai_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        workflow_execution_id: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        request_payload: Optional[Dict[str, Any]] = None,
        response_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Проверка квоты и запись транзакции

        Args:
            entity_type: Тип сущности
            entity_id: ID сущности
            ai_provider: Провайдер AI
            ai_model: Модель AI
            prompt_tokens: Токены в запросе
            completion_tokens: Токены в ответе
            workflow_execution_id: ID выполнения workflow
            estimated_cost: Расчетная стоимость
            request_payload: Пейлоад запроса
            response_metadata: Метаданные ответа

        Returns:
            Dict: Результат с информацией о транзакции и алертах
        """
        total_tokens = prompt_tokens + completion_tokens

        # Находим активную квоту
        quota = self._get_active_quota(entity_type, entity_id, "monthly")

        quota_exceeded = False
        alert_triggered = False

        if quota and quota.limit_tokens:
            new_usage = quota.used_tokens + total_tokens
            if new_usage > quota.limit_tokens:
                quota_exceeded = True

            # Проверяем алерт
            if quota.alert_threshold:
                current_percentage = (new_usage / quota.limit_tokens) * 100
                if current_percentage >= quota.alert_threshold:
                    alert_triggered = True

        # Если квота превышена, возвращаем ошибку
        if quota_exceeded:
            return {
                "success": False,
                "error": "QUOTA_EXCEEDED",
                "quota": quota,
                "required_tokens": total_tokens,
                "available_tokens": (
                    quota.limit_tokens - quota.used_tokens if quota else 0
                ),
            }

        # Создаем транзакцию
        transaction = TokenTransaction(
            quota_id=quota.id if quota else None,
            workflow_execution_id=workflow_execution_id,
            ai_provider=ai_provider,
            ai_model=ai_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            request_payload=request_payload,
            response_metadata=response_metadata,
        )

        self.db.add(transaction)

        # Обновляем использованные токены в квоте
        if quota:
            quota.used_tokens += total_tokens
            quota.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(transaction)

        return {
            "success": True,
            "transaction": transaction,
            "quota": quota,
            "alert_triggered": alert_triggered,
        }

    def get_quota_usage_stats(
        self, entity_type: str, entity_id: int, quota_type: str = "monthly"
    ) -> Optional[Dict[str, Any]]:
        """
        Получение статистики использования квоты

        Args:
            entity_type: Тип сущности
            entity_id: ID сущности
            quota_type: Тип квоты

        Returns:
            Dict: Статистика использования
        """
        quota = self._get_active_quota(entity_type, entity_id, quota_type)
        if not quota:
            return None

        # Получаем топ workflow по токенам
        top_workflows = (
            self.db.query(
                TokenTransaction.workflow_execution_id,
                func.sum(TokenTransaction.total_tokens).label("total_tokens"),
                func.count(TokenTransaction.id).label("transaction_count"),
            )
            .filter(TokenTransaction.quota_id == quota.id)
            .filter(TokenTransaction.workflow_execution_id.isnot(None))
            .group_by(TokenTransaction.workflow_execution_id)
            .order_by(func.sum(TokenTransaction.total_tokens).desc())
            .limit(5)
            .all()
        )

        # Расчет среднего дневного использования
        days_since_creation = (datetime.utcnow() - quota.created_at).days or 1
        daily_avg_usage = quota.used_tokens / days_since_creation

        percentage_used = 0.0
        remaining_tokens = None
        if quota.limit_tokens:
            percentage_used = (quota.used_tokens / quota.limit_tokens) * 100
            remaining_tokens = quota.limit_tokens - quota.used_tokens

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "quota_type": quota_type,
            "limit_tokens": quota.limit_tokens,
            "used_tokens": quota.used_tokens,
            "remaining_tokens": remaining_tokens,
            "percentage_used": percentage_used,
            "reset_at": quota.reset_at,
            "daily_avg_usage": daily_avg_usage,
            "top_workflows_by_tokens": [
                {
                    "workflow_id": wf.workflow_execution_id,
                    "total_tokens": wf.total_tokens,
                    "transaction_count": wf.transaction_count,
                }
                for wf in top_workflows
            ],
        }

    def get_quota_alerts(self) -> List[Dict[str, Any]]:
        """
        Получение списка квот, требующих алертов

        Returns:
            List[Dict]: Список алертов
        """
        quotas = (
            self.db.query(TokenQuota)
            .filter(TokenQuota.is_active == True)
            .filter(TokenQuota.alert_threshold.isnot(None))
            .filter(TokenQuota.limit_tokens.isnot(None))
            .all()
        )

        alerts = []
        for quota in quotas:
            if quota.limit_tokens:
                percentage = (quota.used_tokens / quota.limit_tokens) * 100
                if percentage >= quota.alert_threshold:
                    alerts.append(
                        {
                            "quota_id": quota.id,
                            "entity_type": quota.entity_type,
                            "entity_id": quota.entity_id,
                            "current_usage": quota.used_tokens,
                            "limit_tokens": quota.limit_tokens,
                            "percentage_used": percentage,
                            "alert_threshold": quota.alert_threshold,
                        }
                    )

        return alerts

    def reset_monthly_quotas(self) -> int:
        """
        Сброс месячных квот (вызывается по расписанию)

        Returns:
            int: Количество сброшенных квот
        """
        now = datetime.utcnow()
        reset_count = (
            self.db.query(TokenQuota)
            .filter(TokenQuota.quota_type == "monthly")
            .filter(TokenQuota.reset_at <= now)
            .update({"used_tokens": 0, "reset_at": self._calculate_next_reset(now)})
        )
        self.db.commit()
        return reset_count

    def get_transaction_history(
        self,
        quota_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TokenTransaction]:
        """
        Получение истории транзакций

        Args:
            quota_id: ID квоты
            entity_type: Тип сущности
            entity_id: ID сущности
            limit: Максимальное количество записей
            offset: Смещение

        Returns:
            List[TokenTransaction]: Список транзакций
        """
        query = self.db.query(TokenTransaction).order_by(
            TokenTransaction.created_at.desc()
        )

        if quota_id:
            query = query.filter(TokenTransaction.quota_id == quota_id)
        elif entity_type and entity_id:
            # Находим квоту и фильтруем по ней
            quota = self._get_active_quota(entity_type, entity_id)
            if quota:
                query = query.filter(TokenTransaction.quota_id == quota.id)

        return query.offset(offset).limit(limit).all()

    def _get_active_quota(
        self, entity_type: str, entity_id: int, quota_type: str = "monthly"
    ) -> Optional[TokenQuota]:
        """Получение активной квоты для сущности"""
        return (
            self.db.query(TokenQuota)
            .filter(
                and_(
                    TokenQuota.entity_type == entity_type,
                    TokenQuota.entity_id == entity_id,
                    TokenQuota.quota_type == quota_type,
                    TokenQuota.is_active == True,
                )
            )
            .first()
        )

    def _calculate_next_reset(self, current_date: datetime) -> datetime:
        """Расчет следующей даты сброса месячной квоты"""
        if current_date.month == 12:
            return current_date.replace(
                year=current_date.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            return current_date.replace(
                month=current_date.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
