"""
Обработчик ошибок автоматизации
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...models.automation import AutomationError, AutomationExecution, RobotAction, EntityType
from ...services.email_service import EmailService

logger = logging.getLogger(__name__)


class AutomationErrorHandler:
    """Обработчик ошибок автоматизации с retry логикой и уведомлениями"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    async def handle_error(
        self,
        automation_execution_id: int,
        robot_id: Optional[int] = None,
        trigger_id: Optional[int] = None,
        error_type: str = "unknown",
        error_code: Optional[str] = None,
        error_message: str = "Unknown error",
        error_details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[int] = None,
        action_type: Optional[RobotAction] = None
    ) -> Dict[str, Any]:
        """
        Обработка ошибки автоматизации

        Args:
            automation_execution_id: ID выполнения автоматизации
            robot_id: ID робота (опционально)
            trigger_id: ID триггера (опционально)
            error_type: Тип ошибки (network, api, validation, timeout, etc.)
            error_code: Код ошибки (HTTP status, API error code)
            error_message: Сообщение об ошибке
            error_details: Дополнительные детали ошибки
            entity_type: Тип сущности
            entity_id: ID сущности
            action_type: Тип действия

        Returns:
            Dict с результатом обработки ошибки
        """
        try:
            # Создаем запись об ошибке
            error_record = AutomationError(
                automation_execution_id=automation_execution_id,
                robot_id=robot_id,
                trigger_id=trigger_id,
                error_type=error_type,
                error_code=error_code,
                error_message=error_message,
                error_details=error_details or {},
                entity_type=entity_type,
                entity_id=entity_id,
                action_type=action_type
            )

            self.db.add(error_record)
            self.db.commit()
            self.db.refresh(error_record)

            logger.error(
                f"Automation error logged: {error_type} - {error_message}",
                extra={
                    "error_id": error_record.id,
                    "automation_execution_id": automation_execution_id,
                    "robot_id": robot_id,
                    "error_type": error_type
                }
            )

            # Определяем, нужна ли retry логика
            should_retry = self._should_retry_error(error_type, error_code)

            if should_retry:
                # Планируем retry
                retry_result = await self._schedule_retry(error_record)
                if retry_result["scheduled"]:
                    return {
                        "error_logged": True,
                        "error_id": error_record.id,
                        "retry_scheduled": True,
                        "next_retry_at": retry_result["next_retry_at"]
                    }

            # Если не retry, проверяем нужно ли уведомление
            should_notify = self._should_notify_admin(error_type, error_code)

            if should_notify:
                await self._notify_administrators(error_record)

            return {
                "error_logged": True,
                "error_id": error_record.id,
                "retry_scheduled": False,
                "admin_notified": should_notify
            }

        except Exception as e:
            logger.error(f"Failed to handle automation error: {e}")
            return {"error_logged": False, "error": str(e)}

    async def process_pending_retries(self) -> Dict[str, Any]:
        """
        Обработка ожидающих retry ошибок

        Returns:
            Dict со статистикой обработки
        """
        try:
            # Находим ошибки, которые нужно retry
            now = datetime.utcnow()
            pending_errors = self.db.query(AutomationError).filter(
                and_(
                    AutomationError.resolved == False,
                    AutomationError.next_retry_at <= now,
                    AutomationError.retry_count < AutomationError.max_retries
                )
            ).all()

            processed = 0
            successful_retries = 0
            failed_retries = 0

            for error_record in pending_errors:
                retry_result = await self._execute_retry(error_record)

                if retry_result["success"]:
                    successful_retries += 1
                    error_record.resolved = True
                    error_record.resolved_at = datetime.utcnow()
                else:
                    failed_retries += 1
                    error_record.retry_count += 1

                    # Планируем следующий retry если не превысили лимит
                    if error_record.retry_count < error_record.max_retries:
                        next_retry = self._calculate_next_retry_time(error_record.retry_count)
                        error_record.next_retry_at = next_retry
                    else:
                        # Превысили лимит retry, уведомляем администратора
                        await self._notify_administrators(error_record, "max_retries_exceeded")

                processed += 1

            self.db.commit()

            return {
                "processed": processed,
                "successful_retries": successful_retries,
                "failed_retries": failed_retries,
                "remaining_pending": len(pending_errors) - processed
            }

        except Exception as e:
            logger.error(f"Failed to process pending retries: {e}")
            return {"error": str(e)}

    async def _execute_retry(self, error_record: AutomationError) -> Dict[str, Any]:
        """
        Выполнение retry для ошибки

        Args:
            error_record: Запись об ошибке

        Returns:
            Dict с результатом retry
        """
        try:
            # Получаем контекст выполнения
            execution = error_record.automation_execution
            if not execution:
                return {"success": False, "error": "No execution context found"}

            # В зависимости от типа действия выполняем retry
            if error_record.action_type:
                # Повторяем действие робота (отложенный импорт для избежания циклического импорта)
                from ...services.automation.robot_service import RobotService
                robot_service = RobotService(self.db)

                robot_result = await robot_service.execute_robot_action(
                    robot_id=error_record.robot_id,
                    action_config={
                        "action_type": error_record.action_type.value,
                        "config": error_record.error_details.get("action_config", {}),
                        "retry_attempt": error_record.retry_count + 1
                    },
                    entity_type=error_record.entity_type,
                    entity_id=error_record.entity_id
                )

                return {
                    "success": robot_result.get("success", False),
                    "result": robot_result
                }
            else:
                # Для триггеров - повторяем запуск автоматизации
                from ...services.automation.automation_service import AutomationService
                automation_service = AutomationService(self.db)

                trigger_result = await automation_service.handle_event(
                    entity_type=execution.entity_type,
                    event_type=execution.trigger.event_type if execution.trigger else None,
                    entity_id=execution.entity_id,
                    event_data={"retry_attempt": error_record.retry_count + 1}
                )

                return {
                    "success": True,  # Считаем успешным если автоматизация запущена
                    "result": trigger_result
                }

        except Exception as e:
            logger.error(f"Failed to execute retry for error {error_record.id}: {e}")
            return {"success": False, "error": str(e)}

    def _should_retry_error(self, error_type: str, error_code: Optional[str] = None) -> bool:
        """
        Определяет, нужно ли retry для данной ошибки

        Args:
            error_type: Тип ошибки
            error_code: Код ошибки

        Returns:
            True если нужно retry
        """
        # Retry для сетевых ошибок
        if error_type in ["network", "timeout", "connection"]:
            return True

        # Retry для временных ошибок API
        if error_type == "api" and error_code in ["500", "502", "503", "504"]:
            return True

        # Retry для rate limit
        if error_type == "rate_limit":
            return True

        # Не retry для ошибок валидации и авторизации
        if error_type in ["validation", "authorization", "authentication"]:
            return False

        # По умолчанию retry для неизвестных ошибок
        return True

    def _calculate_next_retry_time(self, retry_count: int) -> datetime:
        """
        Рассчитывает время следующего retry с экспоненциальной задержкой

        Args:
            retry_count: Номер попытки retry

        Returns:
            Время следующего retry
        """
        # Экспоненциальная задержка: 1 мин, 5 мин, 30 мин, 2 часа
        delays = [60, 300, 1800, 7200]  # в секундах

        if retry_count < len(delays):
            delay_seconds = delays[retry_count]
        else:
            delay_seconds = delays[-1] * (2 ** (retry_count - len(delays) + 1))

        return datetime.utcnow() + timedelta(seconds=delay_seconds)

    async def _schedule_retry(self, error_record: AutomationError) -> Dict[str, Any]:
        """
        Планирует retry для ошибки

        Args:
            error_record: Запись об ошибке

        Returns:
            Dict с результатом планирования
        """
        try:
            next_retry_time = self._calculate_next_retry_time(error_record.retry_count)
            error_record.next_retry_at = next_retry_time
            error_record.retry_count += 1

            self.db.commit()

            return {
                "scheduled": True,
                "next_retry_at": next_retry_time.isoformat(),
                "retry_count": error_record.retry_count
            }

        except Exception as e:
            logger.error(f"Failed to schedule retry: {e}")
            return {"scheduled": False, "error": str(e)}

    def _should_notify_admin(self, error_type: str, error_code: Optional[str] = None) -> bool:
        """
        Определяет, нужно ли уведомлять администратора

        Args:
            error_type: Тип ошибки
            error_code: Код ошибки

        Returns:
            True если нужно уведомить
        """
        # Всегда уведомлять о критических ошибках
        if error_type in ["security", "data_corruption", "system"]:
            return True

        # Уведомлять после нескольких неудачных retry
        # (проверка происходит в _notify_administrators)

        # Уведомлять о неизвестных ошибках
        if error_type == "unknown":
            return True

        return False

    async def _notify_administrators(
        self,
        error_record: AutomationError,
        notification_type: str = "error_occurred"
    ) -> Dict[str, Any]:
        """
        Отправляет уведомление администраторам

        Args:
            error_record: Запись об ошибке
            notification_type: Тип уведомления

        Returns:
            Dict с результатом отправки
        """
        try:
            # Получаем email администраторов из конфигурации
            admin_emails = await self.get_admin_emails()

            subject = f"Ошибка автоматизации: {error_record.error_type}"

            if notification_type == "max_retries_exceeded":
                subject = f"Превышен лимит retry: {error_record.error_type}"

            # Формируем тело письма
            body = f"""
            Произошла ошибка в системе автоматизации:

            Тип ошибки: {error_record.error_type}
            Код ошибки: {error_record.error_code or 'N/A'}
            Сообщение: {error_record.error_message}

            Контекст:
            - Сущность: {error_record.entity_type.value if error_record.entity_type else 'N/A'}
            - ID сущности: {error_record.entity_id or 'N/A'}
            - Действие: {error_record.action_type.value if error_record.action_type else 'N/A'}

            Детали ошибки: {error_record.error_details}

            Время: {error_record.created_at}
            ID ошибки: {error_record.id}
            """

            # Отправляем email
            for admin_email in admin_emails:
                await self.email_service.send_email(
                    to_email=admin_email,
                    subject=subject,
                    body=body,
                    is_html=False
                )

            # Отмечаем что уведомление отправлено
            error_record.notified_admin = True
            error_record.notification_sent_at = datetime.utcnow()
            self.db.commit()

            return {
                "notified": True,
                "recipients": admin_emails,
                "notification_type": notification_type
            }

        except Exception as e:
            logger.error(f"Failed to notify administrators: {e}")
            return {"notified": False, "error": str(e)}

    async def get_error_statistics(
        self,
        days: int = 7,
        error_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получает статистику ошибок

        Args:
            days: Период в днях
            error_type: Фильтр по типу ошибки

        Returns:
            Dict со статистикой
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(AutomationError).filter(
                AutomationError.created_at >= since_date
            )

            if error_type:
                query = query.filter(AutomationError.error_type == error_type)

            errors = query.all()

            # Группируем по типам
            error_types = {}
            for error in errors:
                error_type_key = error.error_type
                if error_type_key not in error_types:
                    error_types[error_type_key] = 0
                error_types[error_type_key] += 1

            # Считаем retry статистику
            total_retries = sum(error.retry_count for error in errors)
            resolved_errors = sum(1 for error in errors if error.resolved)

            return {
                "total_errors": len(errors),
                "resolved_errors": resolved_errors,
                "unresolved_errors": len(errors) - resolved_errors,
                "error_types": error_types,
                "total_retries": total_retries,
                "average_retries_per_error": total_retries / len(errors) if errors else 0,
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {"error": str(e)}

    async def get_admin_emails(self) -> List[str]:
        """
        Получение email адресов администраторов из конфигурации

        Returns:
            List[str]: Список email адресов администраторов
        """
        try:
            # В реальном проекте здесь должна быть загрузка из конфигурации
            # Пока возвращаем значения по умолчанию
            from ...config import settings

            # Проверяем настройки в конфигурации
            if hasattr(settings, 'ADMIN_EMAILS') and settings.ADMIN_EMAILS:
                return settings.ADMIN_EMAILS

            # Fallback на значения по умолчанию
            return ["admin@example.com", "support@example.com"]

        except Exception as e:
            logger.error(f"Failed to get admin emails from config: {e}")
            # Возвращаем значения по умолчанию в случае ошибки
            return ["admin@example.com"]


# Глобальный экземпляр обработчика
automation_error_handler = AutomationErrorHandler
