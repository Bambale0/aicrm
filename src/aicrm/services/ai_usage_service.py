"""
Сервис учета использования AI токенов
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..models.ai_usage import AIUsage


class AIUsageService:
    """Сервис для учета и анализа использования AI токенов"""

    def __init__(self, db: Session):
        self.db = db

    async def log_usage(
        self,
        model_used: str,
        endpoint: str,
        total_tokens: float,
        prompt_tokens: float = 0.0,
        completion_tokens: float = 0.0,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AIUsage:
        """
        Логирование использования токенов

        Args:
            model_used: Название использованной модели
            endpoint: Эндпоинт, который был вызван
            total_tokens: Общее количество токенов
            prompt_tokens: Токены в запросе
            completion_tokens: Токены в ответе
            user_id: ID пользователя (если аутентифицирован)
            ip_address: IP адрес клиента
            user_agent: User-Agent клиента

        Returns:
            AIUsage: Созданная запись использования
        """
        usage = AIUsage(
            model_used=model_used,
            endpoint=endpoint,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=AIUsage.generate_request_id(),
            month_year=AIUsage.get_current_month_year(),
        )

        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)

        return usage

    def get_monthly_usage(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Получение статистики использования токенов за месяц

        Args:
            year: Год (текущий, если не указан)
            month: Месяц (текущий, если не указан)
            user_id: ID пользователя для фильтрации

        Returns:
            Dict: Статистика использования
        """
        if year is None or month is None:
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month

        month_str = f"{year:04d}-{month:02d}"

        # Базовый запрос
        query = self.db.query(
            func.sum(AIUsage.total_tokens).label("total_tokens"),
            func.sum(AIUsage.prompt_tokens).label("prompt_tokens"),
            func.sum(AIUsage.completion_tokens).label("completion_tokens"),
            func.count(AIUsage.id).label("total_requests"),
            func.count(func.distinct(AIUsage.model_used)).label("unique_models"),
        ).filter(AIUsage.month_year == month_str)

        if user_id:
            query = query.filter(AIUsage.user_id == user_id)

        result = query.first()

        # Получение статистики по моделям
        model_stats_query = self.db.query(
            AIUsage.model_used,
            func.sum(AIUsage.total_tokens).label("tokens"),
            func.count(AIUsage.id).label("requests"),
        ).filter(AIUsage.month_year == month_str)

        if user_id:
            model_stats_query = model_stats_query.filter(AIUsage.user_id == user_id)

        model_stats = model_stats_query.group_by(AIUsage.model_used).all()

        return {
            "period": {"year": year, "month": month, "month_year": month_str},
            "total_tokens": float(result.total_tokens or 0),
            "prompt_tokens": float(result.prompt_tokens or 0),
            "completion_tokens": float(result.completion_tokens or 0),
            "total_requests": result.total_requests or 0,
            "unique_models": result.unique_models or 0,
            "model_breakdown": [
                {
                    "model": stat.model_used,
                    "tokens": float(stat.tokens),
                    "requests": stat.requests,
                }
                for stat in model_stats
            ],
        }

    def get_usage_history(
        self, days: int = 30, user_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получение истории использования токенов

        Args:
            days: Количество дней для просмотра истории
            user_id: ID пользователя для фильтрации
            limit: Максимальное количество записей

        Returns:
            List[Dict]: Список записей использования
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        query = (
            self.db.query(AIUsage)
            .filter(AIUsage.created_at >= since_date)
            .order_by(AIUsage.created_at.desc())
            .limit(limit)
        )

        if user_id:
            query = query.filter(AIUsage.user_id == user_id)

        usages = query.all()

        return [
            {
                "id": usage.id,
                "model_used": usage.model_used,
                "endpoint": usage.endpoint,
                "total_tokens": float(usage.total_tokens),
                "created_at": usage.created_at.isoformat(),
                "request_id": usage.request_id,
            }
            for usage in usages
        ]

    def get_current_month_usage(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение статистики использования за текущий месяц

        Args:
            user_id: ID пользователя для фильтрации

        Returns:
            Dict: Статистика за текущий месяц
        """
        return self.get_monthly_usage(user_id=user_id)
