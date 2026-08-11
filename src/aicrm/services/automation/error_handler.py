"""
Обработчик ошибок автоматизации
Система уведомлений об ошибках в процессах автоматизации
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ...models.automation_log import AutomationLog
from ...models.user import User
from ..notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationService,
    NotificationType,
)
from ..system_settings_service import SystemSettingsService

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutomationErrorHandler:
    """
    Обработчик ошибок автоматизации с системой уведомлений
    """

    def __init__(self, db_session):
        self.db = db_session
        self.notification_service = NotificationService(db_session)

    async def handle_error(
        self,
        automation_execution_id: Optional[int] = None,
        robot_id: Optional[int] = None,
        trigger_id: Optional[int] = None,
        error_type: str = "automation",
        error_message: str = "",
        error_details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Универсальный обработчик ошибок автоматизации

        Args:
            automation_execution_id: ID выполнения автоматизации
            robot_id: ID робота
            trigger_id: ID триггера
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            error_details: Детали ошибки
            entity_type: Тип сущности
            entity_id: ID сущности
            action_type: Тип действия

        Returns:
            Dict с результатом обработки
        """
        try:
            # Создаем запись в логе автоматизации
            log_entry = await self._create_error_log_v2(
                automation_execution_id,
                robot_id,
                trigger_id,
                error_type,
                error_message,
                error_details,
                entity_type,
                entity_id,
                action_type,
            )

            # Определяем серьезность ошибки
            severity = self._determine_error_severity(error_type, error_message)

            # Проверяем нужно ли повторять операцию
            retry_info = await self._check_retry_needed(
                error_type, error_message, error_details
            )

            # Отправляем уведомления если нужно
            notification_result = None
            if self._should_notify(severity, error_type):
                notification_result = await self._send_error_notifications_v2(
                    error_message, error_details, severity, entity_type, entity_id
                )

            return {
                "success": True,
                "log_id": log_entry.id if log_entry else None,
                "notification_sent": notification_result is not None,
                "notification_result": notification_result,
                "severity": severity.value,
                "retry_scheduled": retry_info.get("retry_scheduled", False),
                "retry_info": retry_info,
            }

        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок автоматизации: {e}")
            return {"success": False, "error": str(e), "error_type": error_type}

    async def handle_automation_error(
        self,
        error: Exception,
        automation_type: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> Dict[str, Any]:
        """
        Обработка ошибки автоматизации

        Args:
            error: Исключение
            automation_type: Тип автоматизации (telegram, avito, email, etc.)
            context: Контекст ошибки
            user_id: ID пользователя, связанного с ошибкой
            severity: Серьезность ошибки

        Returns:
            Dict с результатом обработки
        """
        try:
            # Логируем ошибку
            error_details = self._extract_error_details(error, context)

            # Создаем запись в логе автоматизации
            log_entry = await self._create_error_log(
                automation_type, error_details, user_id, severity
            )

            # Определяем нужно ли отправлять уведомления
            should_notify = self._should_notify(severity, automation_type)

            notification_result = None
            if should_notify:
                notification_result = await self._send_error_notifications(
                    error_details, automation_type, severity, user_id
                )

            return {
                "success": True,
                "log_id": log_entry.id if log_entry else None,
                "notification_sent": notification_result is not None,
                "notification_result": notification_result,
                "severity": severity.value,
                "automation_type": automation_type,
            }

        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок автоматизации: {e}")
            return {
                "success": False,
                "error": str(e),
                "severity": severity.value,
                "automation_type": automation_type,
            }

    async def _create_error_log(
        self,
        automation_type: str,
        error_details: Dict[str, Any],
        user_id: Optional[int],
        severity: ErrorSeverity,
    ) -> Optional[AutomationLog]:
        """
        Создание записи об ошибке в логе автоматизации

        Args:
            automation_type: Тип автоматизации
            error_details: Детали ошибки
            user_id: ID пользователя
            severity: Серьезность

        Returns:
            AutomationLog или None
        """
        try:
            # Адаптируем данные под существующую модель AutomationLog
            log_data = {
                "timestamp": datetime.utcnow(),
                "level": "error",
                "message": f"Ошибка в {automation_type}: {error_details.get('message', 'Unknown error')}",
                "process_id": user_id,  # Используем user_id как process_id
                "stage_id": None,
                "details": {
                    "automation_type": automation_type,
                    "error_type": error_details.get("type", "Exception"),
                    "traceback": error_details.get("traceback", ""),
                    "context": error_details.get("context", {}),
                    "severity": severity.value,
                    "error_handler_version": "1.0",
                    "handled_at": datetime.utcnow().isoformat(),
                },
            }

            # Создаем запись в логе
            from ...services.automation.automation_log_service import (
                AutomationLogService,
            )

            log_service = AutomationLogService(self.db)

            log_entry = await log_service.create_log_entry(log_data)
            return log_entry

        except Exception as e:
            logger.error(f"Ошибка создания записи в логе ошибок: {e}")
            return None

    def _extract_error_details(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Извлечение деталей ошибки

        Args:
            error: Исключение
            context: Дополнительный контекст

        Returns:
            Dict с деталями ошибки
        """
        import traceback

        return {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "module": getattr(error, "__module__", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _should_notify(self, severity: ErrorSeverity, automation_type: str) -> bool:
        """
        Определение необходимости отправки уведомлений

        Args:
            severity: Серьезность ошибки
            automation_type: Тип автоматизации

        Returns:
            bool: Нужно ли отправлять уведомления
        """
        # Всегда уведомляем о критических ошибках
        if severity == ErrorSeverity.CRITICAL:
            return True

        # Уведомляем о высоких ошибках в важных автоматизациях
        if severity == ErrorSeverity.HIGH:
            important_automations = ["payment", "order", "security", "system"]
            return any(imp in automation_type.lower() for imp in important_automations)

        # Уведомляем о средних ошибках в ключевых автоматизациях
        if severity == ErrorSeverity.MEDIUM:
            key_automations = ["telegram", "avito", "email", "sms"]
            return automation_type.lower() in key_automations

        # Низкие ошибки не требуют уведомлений
        return False

    async def _send_error_notifications(
        self,
        error_details: Dict[str, Any],
        automation_type: str,
        severity: ErrorSeverity,
        user_id: Optional[int],
    ) -> Dict[str, Any]:
        """
        Отправка уведомлений об ошибке

        Args:
            error_details: Детали ошибки
            automation_type: Тип автоматизации
            severity: Серьезность
            user_id: ID пользователя

        Returns:
            Результат отправки уведомлений
        """
        try:
            # Формируем сообщение об ошибке
            error_message = self._format_error_message(
                error_details, automation_type, severity
            )

            # Определяем каналы и получателей
            channels, recipients = self._get_notification_targets(
                severity, automation_type
            )

            # Отправляем уведомления
            result = await self.notification_service.send_bulk_notifications(
                recipients=recipients,
                message=error_message,
                channels=channels,
                notification_type=NotificationType.ERROR,
                priority=self._map_severity_to_priority(severity),
                subject=f"Ошибка автоматизации: {automation_type} ({severity.value})",
            )

            logger.info(f"Отправлено уведомление об ошибке {automation_type}: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений об ошибке: {e}")
            return {"success": False, "error": str(e)}

    def _format_error_message(
        self,
        error_details: Dict[str, Any],
        automation_type: str,
        severity: ErrorSeverity,
    ) -> str:
        """
        Форматирование сообщения об ошибке

        Args:
            error_details: Детали ошибки
            automation_type: Тип автоматизации
            severity: Серьезность

        Returns:
            str: Отформатированное сообщение
        """
        context_info = ""
        if error_details.get("context"):
            context_items = []
            for key, value in error_details["context"].items():
                if isinstance(value, (str, int, float, bool)):
                    context_items.append(f"{key}: {value}")
            if context_items:
                context_info = "\n\nКонтекст:\n" + "\n".join(
                    f"• {item}" for item in context_items
                )

        return f"""🚨 Ошибка автоматизации

Тип автоматизации: {automation_type}
Серьезность: {severity.value.upper()}
Время: {error_details.get('timestamp', 'неизвестно')}

Ошибка: {error_details.get('message', 'Неизвестная ошибка')}
Тип: {error_details.get('type', 'Exception')}

Модуль: {error_details.get('module', 'unknown')}{context_info}

Требуется внимание разработчиков для исправления проблемы."""

    def _get_notification_targets(
        self, severity: ErrorSeverity, automation_type: str
    ) -> tuple[List[NotificationChannel], List[Dict[str, str]]]:
        """
        Получение целей для уведомлений

        Args:
            severity: Серьезность ошибки
            automation_type: Тип автоматизации

        Returns:
            Tuple[List[NotificationChannel], List[Dict[str, str]]]: Каналы и получатели
        """
        # Определяем каналы
        channels = [NotificationChannel.EMAIL]
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            channels.append(NotificationChannel.TELEGRAM)

        # Определяем получателей
        recipients = []

        # Получаем контакты администраторов из настроек
        admin_contacts = SystemSettingsService.get_admin_contacts(self.db)
        recipients.extend(admin_contacts)

        # Для критических ошибок добавляем контакты для критических ситуаций
        if severity == ErrorSeverity.CRITICAL:
            critical_contacts = SystemSettingsService.get_critical_contacts(self.db)
            recipients.extend(critical_contacts)
            channels.append(NotificationChannel.SMS)

        return channels, recipients

    def _map_severity_to_priority(
        self, severity: ErrorSeverity
    ) -> NotificationPriority:
        """
        Преобразование серьезности в приоритет уведомления

        Args:
            severity: Серьезность ошибки

        Returns:
            NotificationPriority: Приоритет уведомления
        """
        mapping = {
            ErrorSeverity.LOW: NotificationPriority.LOW,
            ErrorSeverity.MEDIUM: NotificationPriority.MEDIUM,
            ErrorSeverity.HIGH: NotificationPriority.HIGH,
            ErrorSeverity.CRITICAL: NotificationPriority.URGENT,
        }
        return mapping.get(severity, NotificationPriority.MEDIUM)

    # Методы для работы с историей ошибок

    async def get_error_history(
        self,
        automation_type: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Получение истории ошибок

        Args:
            automation_type: Фильтр по типу автоматизации
            severity: Фильтр по серьезности
            limit: Максимальное количество записей

        Returns:
            List[Dict]: История ошибок
        """
        try:
            from ...services.automation.automation_log_service import (
                AutomationLogService,
            )

            log_service = AutomationLogService(self.db)

            # Получаем логи с уровнем error
            filters = {"level": "error"}

            logs = await log_service.get_logs(filters=filters, limit=limit)

            # Фильтруем по типу автоматизации и серьезности
            filtered_logs = []
            for log in logs:
                details = log.details or {}
                if (
                    automation_type
                    and details.get("automation_type") != automation_type
                ):
                    continue
                if severity and details.get("severity") != severity.value:
                    continue
                filtered_logs.append(log)

            # Преобразуем в словари
            result = []
            for log in filtered_logs:
                log_dict = {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "level": log.level,
                    "message": log.message,
                    "process_id": log.process_id,
                    "stage_id": log.stage_id,
                    "details": log.details,
                }
                result.append(log_dict)

            return result

        except Exception as e:
            logger.error(f"Ошибка получения истории ошибок: {e}")
            return []

    async def get_error_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Получение статистики ошибок

        Args:
            days: Период в днях

        Returns:
            Dict со статистикой
        """
        try:
            from datetime import timedelta

            from ...services.automation.automation_log_service import (
                AutomationLogService,
            )

            log_service = AutomationLogService(self.db)

            # Получаем логи с уровнем error за период
            since_date = datetime.utcnow() - timedelta(days=days)
            filters = {"level": "error", "created_at_gte": since_date}

            logs = await log_service.get_logs(filters=filters)

            # Подсчитываем статистику
            stats = {
                "total_errors": len(logs),
                "by_severity": {},
                "by_automation_type": {},
                "period_days": days,
            }

            for log in logs:
                details = log.details or {}
                severity = details.get("severity", "unknown")
                automation_type = details.get("automation_type", "unknown")

                stats["by_severity"][severity] = (
                    stats["by_severity"].get(severity, 0) + 1
                )
                stats["by_automation_type"][automation_type] = (
                    stats["by_automation_type"].get(automation_type, 0) + 1
                )

            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики ошибок: {e}")
            return {"error": str(e)}

    # Метод для повторной отправки уведомлений

    async def resend_error_notification(self, log_id: int) -> Dict[str, Any]:
        """
        Повторная отправка уведомления об ошибке

        Args:
            log_id: ID записи в логе

        Returns:
            Результат повторной отправки
        """
        try:
            from ...services.automation.automation_log_service import (
                AutomationLogService,
            )

            log_service = AutomationLogService(self.db)

            # Получаем запись лога
            log_entry = await log_service.get_log_by_id(log_id)
            if not log_entry or log_entry.level != "error":
                return {
                    "success": False,
                    "error": "Запись не найдена или не является ошибкой",
                }

            # Извлекаем данные ошибки из details
            error_details = log_entry.details or {}
            automation_type = error_details.get("automation_type", "unknown")
            severity = ErrorSeverity(error_details.get("severity", "medium"))
            user_id = log_entry.process_id  # user_id хранится в process_id

            # Отправляем уведомление повторно
            result = await self._send_error_notifications(
                error_details, automation_type, severity, user_id
            )

            return {"success": True, "log_id": log_id, "notification_result": result}

        except Exception as e:
            logger.error(f"Ошибка повторной отправки уведомления: {e}")
            return {"success": False, "error": str(e)}

    # Новые методы для универсального обработчика ошибок

    async def _create_error_log_v2(
        self,
        automation_execution_id: Optional[int],
        robot_id: Optional[int],
        trigger_id: Optional[int],
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]],
        entity_type: Optional[str],
        entity_id: Optional[int],
        action_type: Optional[str],
    ) -> Optional[AutomationLog]:
        """
        Создание записи об ошибке в логе (v2)

        Args:
            automation_execution_id: ID выполнения автоматизации
            robot_id: ID робота
            trigger_id: ID триггера
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            error_details: Детали ошибки
            entity_type: Тип сущности
            entity_id: ID сущности
            action_type: Тип действия

        Returns:
            AutomationLog или None
        """
        try:
            from ...services.automation.automation_log_service import (
                AutomationLogService,
            )

            log_service = AutomationLogService(self.db)

            log_data = {
                "timestamp": datetime.utcnow(),
                "level": "error",
                "message": f"Ошибка {error_type}: {error_message}",
                "process_id": automation_execution_id or robot_id,
                "stage_id": trigger_id,
                "details": {
                    "error_type": error_type,
                    "error_message": error_message,
                    "error_details": error_details or {},
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "action_type": action_type,
                    "robot_id": robot_id,
                    "trigger_id": trigger_id,
                    "automation_execution_id": automation_execution_id,
                    "handled_at": datetime.utcnow().isoformat(),
                    "handler_version": "2.0",
                },
            }

            log_entry = await log_service.create_log_entry(log_data)
            return log_entry

        except Exception as e:
            logger.error(f"Ошибка создания записи в логе ошибок v2: {e}")
            return None

    def _determine_error_severity(
        self, error_type: str, error_message: str
    ) -> ErrorSeverity:
        """
        Определение серьезности ошибки

        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке

        Returns:
            ErrorSeverity: Уровень серьезности
        """
        # Критические ошибки
        if error_type in ["payment_error", "security_error", "database_error"]:
            return ErrorSeverity.CRITICAL

        # Высокие ошибки
        if error_type in ["api_error", "network_error", "timeout_error"]:
            return ErrorSeverity.HIGH

        # Средние ошибки
        if error_type in ["validation_error", "permission_error", "robot_action_error"]:
            return ErrorSeverity.MEDIUM

        # Низкие ошибки (по умолчанию)
        return ErrorSeverity.LOW

    async def _check_retry_needed(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Проверка необходимости повторения операции

        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            error_details: Детали ошибки

        Returns:
            Dict с информацией о retry
        """
        # Ошибки, которые можно повторять
        retryable_errors = [
            "network_error",
            "timeout_error",
            "api_rate_limit",
            "temporary_service_unavailable",
            "connection_error",
        ]

        # Ошибки, которые нельзя повторять
        non_retryable_errors = [
            "authentication_error",
            "authorization_error",
            "validation_error",
            "not_found_error",
            "permission_denied",
        ]

        if error_type in non_retryable_errors:
            return {"retry_scheduled": False, "reason": "non_retryable_error"}

        if error_type in retryable_errors:
            return {
                "retry_scheduled": True,
                "retry_after_seconds": 60,  # Повторить через 1 минуту
                "max_retries": 3,
                "reason": "retryable_error",
            }

        # По умолчанию не повторяем
        return {"retry_scheduled": False, "reason": "unknown_error_type"}

    async def _send_error_notifications_v2(
        self,
        error_message: str,
        error_details: Optional[Dict[str, Any]],
        severity: ErrorSeverity,
        entity_type: Optional[str],
        entity_id: Optional[int],
    ) -> Dict[str, Any]:
        """
        Отправка уведомлений об ошибке (v2)

        Args:
            error_message: Сообщение об ошибке
            error_details: Детали ошибки
            severity: Серьезность
            entity_type: Тип сущности
            entity_id: ID сущности

        Returns:
            Результат отправки уведомлений
        """
        try:
            # Получаем email администраторов из конфигурации
            admin_emails = await self._get_admin_emails()

            # Формируем сообщение
            message = self._format_error_message_v2(
                error_message, error_details, severity, entity_type, entity_id
            )

            # Определяем каналы
            channels = [NotificationChannel.EMAIL]
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                channels.append(NotificationChannel.TELEGRAM)

            # Готовим получателей
            recipients = [{"email": email} for email in admin_emails]

            # Отправляем уведомления
            result = await self.notification_service.send_bulk_notifications(
                recipients=recipients,
                message=message,
                channels=channels,
                notification_type=NotificationType.ERROR,
                priority=self._map_severity_to_priority(severity),
                subject=f"Ошибка автоматизации ({severity.value})",
            )

            return result

        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений v2: {e}")
            return {"success": False, "error": str(e)}

    async def _get_admin_emails(self) -> List[str]:
        """
        Получение email администраторов из конфигурации

        Returns:
            List[str]: Список email администраторов
        """
        try:
            # Получаем администраторов из базы данных
            from ...models.user import UserRole

            admins = self.db.query(User).filter(User.role == UserRole.ADMIN).all()
            admin_emails = [admin.email for admin in admins if admin.email]

            # Если нет администраторов в БД, используем значения по умолчанию
            if not admin_emails:
                admin_emails = ["admin@example.com", "dev@example.com"]

            return admin_emails

        except Exception as e:
            logger.error(f"Ошибка получения email администраторов: {e}")
            return ["admin@example.com"]

    def _format_error_message_v2(
        self,
        error_message: str,
        error_details: Optional[Dict[str, Any]],
        severity: ErrorSeverity,
        entity_type: Optional[str],
        entity_id: Optional[int],
    ) -> str:
        """
        Форматирование сообщения об ошибке (v2)

        Args:
            error_message: Сообщение об ошибке
            error_details: Детали ошибки
            severity: Серьезность
            entity_type: Тип сущности
            entity_id: ID сущности

        Returns:
            str: Отформатированное сообщение
        """
        message_parts = [
            "🚨 Ошибка автоматизации",
            f"Серьезность: {severity.value.upper()}",
            f"Время: {datetime.utcnow().isoformat()}",
            f"Сообщение: {error_message}",
        ]

        if entity_type and entity_id:
            message_parts.append(f"Сущность: {entity_type} #{entity_id}")

        if error_details:
            context_items = []
            for key, value in error_details.items():
                if isinstance(value, (str, int, float, bool)):
                    context_items.append(f"{key}: {value}")
            if context_items:
                message_parts.append("Детали:")
                message_parts.extend(f"• {item}" for item in context_items)

        message_parts.append("Требуется внимание!")

        return "\n".join(message_parts)


# Функция для создания экземпляра обработчика ошибок
def get_error_handler(db_session):
    """
    Получить экземпляр обработчика ошибок

    Args:
        db_session: Сессия базы данных

    Returns:
        AutomationErrorHandler: Экземпляр обработчика
    """
    return AutomationErrorHandler(db_session)
