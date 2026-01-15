"""
Сервис для автоматической отправки уведомлений о событиях системы
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..utils.logging import get_logger
from .notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationService,
    NotificationType,
)
from .system_settings_service import SystemSettingsService

logger = get_logger(__name__)


class EventNotificationService:
    """
    Сервис для автоматической обработки событий и отправки уведомлений
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.notification_service = NotificationService(db_session)
        self.system_settings_service = SystemSettingsService()
        self._event_handlers = {}
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Настройка обработчиков событий"""
        self._event_handlers = {
            "user_registered": self._handle_user_registered,
            "user_login_failed": self._handle_user_login_failed,
            "user_password_changed": self._handle_user_password_changed,
            "organization_created": self._handle_organization_created,
            "organization_activated": self._handle_organization_activated,
            "organization_deactivated": self._handle_organization_deactivated,
            "order_created": self._handle_order_created,
            "order_status_changed": self._handle_order_status_changed,
            "order_completed": self._handle_order_completed,
            "payment_received": self._handle_payment_received,
            "task_assigned": self._handle_task_assigned,
            "task_overdue": self._handle_task_overdue,
            "system_error": self._handle_system_error,
            "system_backup_completed": self._handle_system_backup_completed,
            "system_resource_high": self._handle_system_resource_high,
            "security_alert": self._handle_security_alert,
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка события и отправка соответствующих уведомлений

        Args:
            event_type: Тип события
            event_data: Данные события

        Returns:
            Dict с результатами обработки
        """
        if event_type not in self._event_handlers:
            logger.warning(f"Unknown event type: {event_type}")
            return {"success": False, "error": f"Unknown event type: {event_type}"}

        try:
            logger.info(f"Processing event: {event_type}", extra=event_data)
            result = await self._event_handlers[event_type](event_data)
            return {"success": True, "event_type": event_type, "result": result}

        except Exception as e:
            logger.error(f"Failed to process event {event_type}: {e}", extra=event_data)
            return {"success": False, "error": str(e), "event_type": event_type}

    # Обработчики событий пользователей

    async def _handle_user_registered(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события регистрации пользователя"""
        user_email = event_data.get("user_email")
        user_name = event_data.get("user_name", "Новый пользователь")

        # Получаем настройки уведомлений
        notification_config = self.system_settings_service.get_notification_config(
            self.db_session
        )

        if notification_config.get("enabled") and notification_config.get(
            "email_enabled"
        ):
            message = f"Новый пользователь зарегистрирован: {user_name} ({user_email})"

            result = await self.notification_service.notify_admins(
                message=message,
                notification_type=NotificationType.INFO,
                priority=NotificationPriority.LOW,
                channels=[NotificationChannel.EMAIL],
            )

            return {"notification_sent": result}
        return {"notification_sent": False}

    async def _handle_user_login_failed(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события неудачной попытки входа"""
        email = event_data.get("email")
        attempts = event_data.get("failed_attempts", 1)

        # Проверяем порог для уведомлений (каждые 5 неудачных попыток)
        if attempts % 5 == 0:
            message = f"Множественные неудачные попытки входа для пользователя: {email} (попыток: {attempts})"

            # Получаем настройки безопасности
            security_config = self.system_settings_service.get_security_config(
                self.db_session
            )
            max_attempts = security_config.get("max_login_attempts", 5)

            priority = (
                NotificationPriority.HIGH
                if attempts >= max_attempts
                else NotificationPriority.MEDIUM
            )

            result = await self.notification_service.notify_admins(
                message=message,
                notification_type=NotificationType.SECURITY_ALERT,
                priority=priority,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
            )

            return {"notification_sent": result, "priority": priority.value}

        return {"notification_sent": False}

    async def _handle_user_password_changed(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события изменения пароля"""
        user_email = event_data.get("user_email")
        user_name = event_data.get("user_name")

        message = f"Пароль был изменен для пользователя: {user_name} ({user_email})"

        # Отправляем только email уведомление пользователю
        result = await self.notification_service.send_notification(
            recipient=user_email,
            message=message,
            channels=[NotificationChannel.EMAIL],
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
            subject="Пароль успешно изменен",
        )

        return {"notification_sent": result}

    # Обработчики событий организаций

    async def _handle_organization_created(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события создания организации"""
        org_name = event_data.get("organization_name")
        org_email = event_data.get("organization_email")
        admin_email = event_data.get("admin_email")

        message = f"Новая организация создана: {org_name} ({org_email})"
        admin_message = (
            f"Ваша организация '{org_name}' успешно создана и находится на проверке."
        )

        results = {}

        # Уведомление администраторов системы
        admin_result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )
        results["admins_notified"] = admin_result

        # Уведомление администратора организации
        if admin_email:
            org_result = await self.notification_service.send_notification(
                recipient=admin_email,
                message=admin_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.HIGH,
                subject="Организация создана",
            )
            results["org_admin_notified"] = org_result

        return results

    async def _handle_organization_activated(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события активации организации"""
        org_name = event_data.get("organization_name")
        org_email = event_data.get("organization_email")

        message = f"Организация активирована: {org_name} ({org_email})"
        org_message = (
            f"Ваша организация '{org_name}' успешно активирована и готова к работе."
        )

        results = {}

        # Уведомление администраторов системы
        admin_result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )
        results["admins_notified"] = admin_result

        # Уведомление организации
        if org_email:
            org_result = await self.notification_service.send_notification(
                recipient=org_email,
                message=org_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.HIGH,
                subject="Организация активирована",
            )
            results["org_notified"] = org_result

        return results

    async def _handle_organization_deactivated(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события деактивации организации"""
        org_name = event_data.get("organization_name")
        reason = event_data.get("reason", "Не указана")

        message = f"Организация деактивирована: {org_name}. Причина: {reason}"

        result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )

        return {"notification_sent": result}

    # Обработчики событий заказов

    async def _handle_order_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка события создания заказа"""
        order_id = event_data.get("order_id")
        customer_email = event_data.get("customer_email")
        total_amount = event_data.get("total_amount")

        message = f"Новый заказ #{order_id} на сумму {total_amount}"
        customer_message = (
            f"Ваш заказ #{order_id} успешно создан. Сумма: {total_amount}"
        )

        results = {}

        # Уведомление менеджеров
        manager_result = await self.notification_service.notify_managers(
            message=message,
            notification_type=NotificationType.ORDER_UPDATE,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.WEBSOCKET],
        )
        results["managers_notified"] = manager_result

        # Уведомление клиента
        if customer_email:
            customer_result = await self.notification_service.send_notification(
                recipient=customer_email,
                message=customer_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.ORDER_UPDATE,
                priority=NotificationPriority.HIGH,
                subject=f"Заказ #{order_id} создан",
            )
            results["customer_notified"] = customer_result

        return results

    async def _handle_order_status_changed(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события изменения статуса заказа"""
        order_id = event_data.get("order_id")
        old_status = event_data.get("old_status")
        new_status = event_data.get("new_status")
        customer_email = event_data.get("customer_email")

        message = (
            f"Заказ #{order_id}: статус изменен с '{old_status}' на '{new_status}'"
        )
        customer_message = f"Статус вашего заказа #{order_id} изменен на: {new_status}"

        results = {}

        # Уведомление клиента
        if customer_email:
            customer_result = await self.notification_service.send_notification(
                recipient=customer_email,
                message=customer_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.ORDER_UPDATE,
                priority=NotificationPriority.MEDIUM,
                subject=f"Заказ #{order_id} - статус изменен",
            )
            results["customer_notified"] = customer_result

        # Важные статусы также уведомляем менеджеров
        important_statuses = ["completed", "cancelled", "refunded"]
        if new_status.lower() in important_statuses:
            manager_result = await self.notification_service.notify_managers(
                message=message,
                notification_type=NotificationType.ORDER_UPDATE,
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.WEBSOCKET],
            )
            results["managers_notified"] = manager_result

        return results

    async def _handle_order_completed(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события завершения заказа"""
        order_id = event_data.get("order_id")
        customer_email = event_data.get("customer_email")
        completion_time = event_data.get("completion_time", "Н/Д")

        message = f"Заказ #{order_id} завершен за {completion_time}"
        customer_message = f"Ваш заказ #{order_id} успешно выполнен!"

        results = {}

        # Уведомление клиента
        if customer_email:
            customer_result = await self.notification_service.send_notification(
                recipient=customer_email,
                message=customer_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.HIGH,
                subject=f"Заказ #{order_id} выполнен",
            )
            results["customer_notified"] = customer_result

        # Уведомление менеджеров
        manager_result = await self.notification_service.notify_managers(
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.WEBSOCKET],
        )
        results["managers_notified"] = manager_result

        return results

    async def _handle_payment_received(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события получения платежа"""
        order_id = event_data.get("order_id")
        amount = event_data.get("amount")
        customer_email = event_data.get("customer_email")

        message = f"Платеж получен: {amount} за заказ #{order_id}"
        customer_message = (
            f"Платеж на сумму {amount} за заказ #{order_id} успешно получен."
        )

        results = {}

        # Уведомление клиента
        if customer_email:
            customer_result = await self.notification_service.send_notification(
                recipient=customer_email,
                message=customer_message,
                channels=[NotificationChannel.EMAIL],
                notification_type=NotificationType.PAYMENT_SUCCESS,
                priority=NotificationPriority.HIGH,
                subject="Платеж получен",
            )
            results["customer_notified"] = customer_result

        # Уведомление менеджеров
        manager_result = await self.notification_service.notify_managers(
            message=message,
            notification_type=NotificationType.PAYMENT_SUCCESS,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.WEBSOCKET],
        )
        results["managers_notified"] = manager_result

        return results

    # Обработчики событий задач

    async def _handle_task_assigned(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка события назначения задачи"""
        task_title = event_data.get("task_title")
        assignee_email = event_data.get("assignee_email")
        assignee_name = event_data.get("assignee_name")
        # assigner_name intentionally unused
        # compose message for assignee
        assignee_message = f"Вам назначена задача: {task_title}"

        results = {}

        # Уведомление исполнителя
        if assignee_email:
            assignee_result = await self.notification_service.send_notification(
                recipient=assignee_email,
                message=assignee_message,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
                notification_type=NotificationType.TASK_ASSIGNED,
                priority=NotificationPriority.MEDIUM,
                subject="Новая задача",
            )
            results["assignee_notified"] = assignee_result

        return results

    async def _handle_task_overdue(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка события просроченной задачи"""
        task_title = event_data.get("task_title")
        assignee_email = event_data.get("assignee_email")
        days_overdue = event_data.get("days_overdue", 1)

        message = f"Задача просрочена: '{task_title}' ({days_overdue} дней просрочки)"
        assignee_message = f"Крайний срок выполнения задачи '{task_title}' истек {days_overdue} дней назад!"

        results = {}

        # Уведомление исполнителя
        if assignee_email:
            assignee_result = await self.notification_service.send_notification(
                recipient=assignee_email,
                message=assignee_message,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
                notification_type=NotificationType.WARNING,
                priority=NotificationPriority.HIGH,
                subject="Задача просрочена",
            )
            results["assignee_notified"] = assignee_result

        # Уведомление менеджеров
        manager_result = await self.notification_service.notify_managers(
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.WEBSOCKET],
        )
        results["managers_notified"] = manager_result

        return results

    # Обработчики системных событий

    async def _handle_system_error(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка системной ошибки"""
        error_message = event_data.get("error_message", "Неизвестная ошибка")
        error_location = event_data.get("error_location", "Не указано")
        severity = event_data.get("severity", "error")

        priority_map = {
            "critical": NotificationPriority.URGENT,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
        }

        priority = priority_map.get(severity.lower(), NotificationPriority.HIGH)

        message = (
            f"Системная ошибка: {error_message} (местоположение: {error_location})"
        )

        result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.ERROR,
            priority=priority,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )

        return {"notification_sent": result, "priority": priority.value}

    async def _handle_system_backup_completed(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события завершения резервного копирования"""
        backup_size = event_data.get("backup_size", "Неизвестно")
        backup_duration = event_data.get("backup_duration", "Неизвестно")

        message = f"Резервное копирование завершено. Размер: {backup_size}, время: {backup_duration}"

        result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.LOW,
            channels=[NotificationChannel.EMAIL],
        )

        return {"notification_sent": result}

    async def _handle_system_resource_high(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события высокой загрузки ресурсов"""
        resource_type = event_data.get("resource_type", "Неизвестно")
        current_usage = event_data.get("current_usage", 0)
        threshold = event_data.get("threshold", 80)

        message = f"Высокая загрузка ресурса {resource_type}: {current_usage}% (порог: {threshold}%)"

        result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )

        return {"notification_sent": result}

    async def _handle_security_alert(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка события безопасности"""
        alert_type = event_data.get("alert_type", "Неизвестно")
        description = event_data.get("description", "Без описания")
        ip_address = event_data.get("ip_address", "Неизвестно")

        message = f"Предупреждение безопасности: {alert_type} - {description} (IP: {ip_address})"

        result = await self.notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.SECURITY_ALERT,
            priority=NotificationPriority.URGENT,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )

        return {"notification_sent": result}

    # Вспомогательные методы

    async def schedule_reminders(self) -> Dict[str, Any]:
        """Планировщик напоминаний о событиях"""
        # Этот метод должен вызываться периодически (например, каждые 5 минут)
        # для проверки предстоящих событий и отправки напоминаний

        # Пример: напоминания о просроченных задачах
        overdue_tasks = await self._get_overdue_tasks()
        for task in overdue_tasks:
            await self.process_event("task_overdue", task)

        # Пример: напоминания о платежах
        pending_payments = await self._get_pending_payments()
        for payment in pending_payments:
            await self.process_event("payment_reminder", payment)

        return {
            "overdue_tasks_checked": len(overdue_tasks),
            "pending_payments_checked": len(pending_payments),
        }

    async def _get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Получение просроченных задач (заглушка)"""
        # В реальном приложении здесь запрос к БД
        return []

    async def _get_pending_payments(self) -> List[Dict[str, Any]]:
        """Получение ожидающих платежей (заглушка)"""
        # В реальном приложении здесь запрос к БД
        return []


# Функция для быстрого создания экземпляра сервиса
def create_event_notification_service(db_session: Session) -> EventNotificationService:
    """Создание экземпляра сервиса уведомлений о событиях"""
    return EventNotificationService(db_session)


# Глобальный экземпляр (нужен db_session для инициализации)
def get_event_notification_service(db_session: Session) -> EventNotificationService:
    """Получение экземпляра сервиса уведомлений о событиях"""
    return EventNotificationService(db_session)
