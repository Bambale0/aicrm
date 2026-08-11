"""
Универсальный сервис уведомлений
Интегрирует Email, SMS и Telegram для отправки уведомлений
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .email_service import EmailMessage, email_service
from .sms_service import sms_service

# Импорт WebSocket менеджеров
try:
    from ..api.routers.websocket import (
        broadcast_system_message,
        notify_chat,
        notify_user,
        ws_manager,
    )

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    ws_manager = None
    notify_chat = None
    notify_user = None
    broadcast_system_message = None

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Каналы уведомлений"""

    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBSOCKET = "websocket"


class NotificationPriority(Enum):
    """Приоритеты уведомлений"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """Типы уведомлений"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    TASK_ASSIGNED = "task_assigned"
    ORDER_UPDATE = "order_update"
    PAYMENT_REMINDER = "payment_reminder"
    SYSTEM_ALERT = "system_alert"


class NotificationService:
    """
    Универсальный сервис для отправки уведомлений через разные каналы
    """

    def __init__(self, db_session=None):
        self.email_service = email_service
        self.sms_service = sms_service
        self.db_session = db_session
        self.telegram_service = None  # Будет инициализирован при необходимости

    async def send_notification(
        self,
        recipient: Union[str, Dict[str, str]],
        message: str,
        channels: List[NotificationChannel],
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        subject: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Отправка уведомления через один или несколько каналов

        Args:
            recipient: Получатель (email, phone, telegram_id или dict с несколькими)
            message: Текст сообщения
            channels: Список каналов для отправки
            notification_type: Тип уведомления
            priority: Приоритет
            subject: Тема (для email)
            template_data: Данные для шаблона
            attachments: Вложения (для email)

        Returns:
            Dict с результатами отправки
        """
        results = {}
        errors = []

        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    result = await self._send_email_notification(
                        recipient,
                        message,
                        notification_type,
                        priority,
                        subject,
                        template_data,
                        attachments,
                    )
                    results["email"] = result

                elif channel == NotificationChannel.SMS:
                    result = await self._send_sms_notification(
                        recipient, message, notification_type, priority
                    )
                    results["sms"] = result

                elif channel == NotificationChannel.TELEGRAM:
                    result = await self._send_telegram_notification(
                        recipient, message, notification_type, priority
                    )
                    results["telegram"] = result

                elif channel == NotificationChannel.WEBSOCKET:
                    result = await self._send_websocket_notification(
                        recipient, message, notification_type, priority
                    )
                    results["websocket"] = result

            except Exception as e:
                error_msg = f"Ошибка отправки через {channel.value}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                results[channel.value] = {"success": False, "error": str(e)}

        # Определяем общий успех
        successful_channels = [k for k, v in results.items() if v.get("success", False)]
        all_success = len(successful_channels) == len(channels)

        return {
            "success": all_success,
            "successful_channels": successful_channels,
            "failed_channels": [
                k for k in results.keys() if not results[k].get("success", False)
            ],
            "results": results,
            "errors": errors,
            "notification_type": notification_type.value,
            "priority": priority.value,
            "channels_attempted": [c.value for c in channels],
        }

    async def _send_email_notification(
        self,
        recipient: Union[str, Dict[str, str]],
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
        subject: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List] = None,
    ) -> Dict[str, Any]:
        """Отправка email уведомления"""
        try:
            # Определяем email получателя
            email = self._extract_email(recipient)
            if not email:
                return {"success": False, "error": "Email не найден"}

            # Формируем тему если не указана
            if not subject:
                subject = self._generate_subject(notification_type, priority)

            # Используем шаблон если есть данные
            if template_data:
                template_name = self._get_template_for_type(notification_type)
                if template_name:
                    success = await self.email_service.send_template_email(
                        template_name=template_name,
                        to=email,
                        template_data=template_data,
                        subject=subject,
                        attachments=attachments,
                    )
                    return {
                        "success": success,
                        "recipient": email,
                        "template_used": template_name,
                    }

            # Отправка обычного email
            email_message = EmailMessage(
                to=email, subject=subject, body=message, attachments=attachments
            )

            success = await self.email_service.send_email(email_message)
            return {"success": success, "recipient": email, "subject": subject}

        except Exception as e:
            logger.error(f"Ошибка отправки email уведомления: {e}")
            return {"success": False, "error": str(e)}

    async def _send_sms_notification(
        self,
        recipient: Union[str, Dict[str, str]],
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
    ) -> Dict[str, Any]:
        """Отправка SMS уведомления"""
        try:
            # Определяем телефон получателя
            phone = self._extract_phone(recipient)
            if not phone:
                return {"success": False, "error": "Телефон не найден"}

            # Ограничиваем длину SMS (160 символов для латиницы)
            sms_message = message[:160] if len(message) > 160 else message

            result = await self.sms_service.send_sms(phone, sms_message)
            return {
                "success": result.get("success", False),
                "recipient": phone,
                "provider": result.get("provider"),
                "message_id": result.get("message_id"),
                "cost": result.get("cost"),
            }

        except Exception as e:
            logger.error(f"Ошибка отправки SMS уведомления: {e}")
            return {"success": False, "error": str(e)}

    async def _send_telegram_notification(
        self,
        recipient: Union[str, Dict[str, str]],
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
    ) -> Dict[str, Any]:
        """Отправка Telegram уведомления"""
        try:
            # Определяем Telegram chat_id
            chat_id = self._extract_telegram_id(recipient)
            if not chat_id:
                return {"success": False, "error": "Telegram chat_id не найден"}

            # Инициализируем Telegram сервис если нужно
            if not self.telegram_service:
                if self.db_session:
                    from .telegram_bot_service import TelegramBotService

                    self.telegram_service = TelegramBotService(self.db_session)
                else:
                    return {
                        "success": False,
                        "error": "Telegram сервис не инициализирован - отсутствует db_session",
                    }

            success = await self.telegram_service.send_message_to_chat(chat_id, message)
            return {
                "success": success,
                "recipient": chat_id,
                "message_length": len(message),
            }

        except Exception as e:
            logger.error(f"Ошибка отправки Telegram уведомления: {e}")
            return {"success": False, "error": str(e)}

    async def _send_websocket_notification(
        self,
        recipient: Union[str, Dict[str, str]],
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
    ) -> Dict[str, Any]:
        """Отправка WebSocket уведомления"""
        if not WEBSOCKET_AVAILABLE:
            return {"success": False, "error": "WebSocket сервис недоступен"}

        try:
            # Извлекаем user_id получателя
            user_id = self._extract_websocket_user_id(recipient)
            if not user_id:
                return {"success": False, "error": "User ID для WebSocket не найден"}

            # Формируем WebSocket сообщение
            ws_message = {
                "type": notification_type.value,
                "message": message,
                "priority": priority.value,
                "timestamp": __import__("asyncio").get_event_loop().time(),
            }

            # Определяем тип отправки: персональное уведомление или системное
            if isinstance(recipient, dict) and recipient.get("broadcast"):
                # Системное сообщение для всех
                success = await broadcast_system_message(ws_message)
                recipient_info = "all_users"
            else:
                # Персональное уведомление
                success = await notify_user(int(user_id), ws_message)
                recipient_info = user_id

            return {
                "success": success,
                "recipient": recipient_info,
                "message_length": len(message),
                "notification_type": notification_type.value,
            }

        except Exception as e:
            logger.error(f"Ошибка отправки WebSocket уведомления: {e}")
            return {"success": False, "error": str(e)}

    def _extract_email(self, recipient: Union[str, Dict[str, str]]) -> Optional[str]:
        """Извлечение email из данных получателя"""
        if isinstance(recipient, str):
            # Предполагаем что это email если содержит @
            return recipient if "@" in recipient else None
        elif isinstance(recipient, dict):
            return recipient.get("email")
        return None

    def _extract_phone(self, recipient: Union[str, Dict[str, str]]) -> Optional[str]:
        """Извлечение телефона из данных получателя"""
        if isinstance(recipient, str):
            # Простая проверка на телефон (начинается с +)
            return recipient if recipient.startswith("+") else None
        elif isinstance(recipient, dict):
            return recipient.get("phone") or recipient.get("sms")
        return None

    def _extract_telegram_id(
        self, recipient: Union[str, Dict[str, str]]
    ) -> Optional[str]:
        """Извлечение Telegram ID из данных получателя"""
        if isinstance(recipient, str):
            # Предполагаем что это chat_id если состоит из цифр
            return recipient if recipient.isdigit() else None
        elif isinstance(recipient, dict):
            return recipient.get("telegram_id") or recipient.get("chat_id")
        return None

    def _extract_websocket_user_id(
        self, recipient: Union[str, Dict[str, str]]
    ) -> Optional[str]:
        """Извлечение User ID для WebSocket из данных получателя"""
        if isinstance(recipient, str):
            # Предполагаем что это user_id если состоит из цифр
            return recipient if recipient.isdigit() else None
        elif isinstance(recipient, dict):
            return (
                recipient.get("user_id")
                or recipient.get("websocket_id")
                or recipient.get("id")
            )
        return None

    def _generate_subject(
        self, notification_type: NotificationType, priority: NotificationPriority
    ) -> str:
        """Генерация темы письма на основе типа и приоритета"""
        type_prefixes = {
            NotificationType.INFO: "Информация",
            NotificationType.WARNING: "Предупреждение",
            NotificationType.ERROR: "Ошибка",
            NotificationType.SUCCESS: "Успешно",
            NotificationType.TASK_ASSIGNED: "Новая задача",
            NotificationType.ORDER_UPDATE: "Обновление заказа",
            NotificationType.PAYMENT_REMINDER: "Напоминание об оплате",
            NotificationType.SYSTEM_ALERT: "Системное уведомление",
        }

        priority_prefixes = {
            NotificationPriority.URGENT: "СРОЧНО: ",
            NotificationPriority.HIGH: "",
            NotificationPriority.MEDIUM: "",
            NotificationPriority.LOW: "",
        }

        prefix = priority_prefixes.get(priority, "")
        type_text = type_prefixes.get(notification_type, "Уведомление")

        return f"{prefix}{type_text}"

    def _get_template_for_type(
        self, notification_type: NotificationType
    ) -> Optional[str]:
        """Получение имени шаблона для типа уведомления"""
        template_mapping = {
            NotificationType.TASK_ASSIGNED: "task_assigned",
            NotificationType.ORDER_UPDATE: "order_confirmation",
            NotificationType.PAYMENT_REMINDER: "payment_reminder",
        }

        return template_mapping.get(notification_type)

    # Методы для массовых уведомлений

    async def send_bulk_notifications(
        self,
        recipients: List[Union[str, Dict[str, str]]],
        message: str,
        channels: List[NotificationChannel],
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        subject: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Массовая отправка уведомлений

        Args:
            recipients: Список получателей
            message: Текст сообщения
            channels: Каналы отправки
            notification_type: Тип уведомления
            priority: Приоритет
            subject: Тема (для email)
            template_data: Данные для шаблона

        Returns:
            Dict с результатами массовой отправки
        """
        results = []
        total_success = 0
        total_failed = 0

        for recipient in recipients:
            result = await self.send_notification(
                recipient=recipient,
                message=message,
                channels=channels,
                notification_type=notification_type,
                priority=priority,
                subject=subject,
                template_data=template_data,
            )

            results.append(result)

            if result["success"]:
                total_success += 1
            else:
                total_failed += 1

        return {
            "total_recipients": len(recipients),
            "successful": total_success,
            "failed": total_failed,
            "success_rate": total_success / len(recipients) if recipients else 0,
            "results": results,
            "notification_type": notification_type.value,
            "channels": [c.value for c in channels],
        }

    # Методы для уведомлений по ролям пользователей

    async def notify_admins(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
        priority: NotificationPriority = NotificationPriority.HIGH,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Any]:
        """
        Отправка уведомления всем администраторам

        Args:
            message: Текст сообщения
            notification_type: Тип уведомления
            priority: Приоритет
            channels: Каналы (по умолчанию все доступные)

        Returns:
            Результат отправки
        """
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.TELEGRAM]

        # В реальном приложении здесь нужно получить список админов из БД
        # Пока что используем заглушки
        admin_contacts = [
            {"email": "admin@example.com", "telegram_id": "123456789"},
            {"email": "support@example.com", "phone": "+1234567890"},
        ]

        return await self.send_bulk_notifications(
            recipients=admin_contacts,
            message=message,
            channels=channels,
            notification_type=notification_type,
            priority=priority,
            subject=f"Системное уведомление: {notification_type.value}",
        )

    async def notify_managers(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Any]:
        """
        Отправка уведомления всем менеджерам
        """
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.TELEGRAM]

        # Заглушки для менеджеров
        manager_contacts = [
            {"email": "manager1@example.com", "telegram_id": "987654321"},
            {"email": "manager2@example.com", "phone": "+0987654321"},
        ]

        return await self.send_bulk_notifications(
            recipients=manager_contacts,
            message=message,
            channels=channels,
            notification_type=notification_type,
            priority=priority,
            subject=f"Уведомление для менеджеров: {notification_type.value}",
        )

    # Статические методы для быстрого доступа

    @staticmethod
    async def send_task_assigned_notification(
        assignee_email: str,
        assignee_name: str,
        task_title: str,
        task_description: str,
        priority: str = "medium",
    ) -> bool:
        """Быстрая отправка уведомления о назначении задачи"""
        notification_service = NotificationService()

        template_data = {
            "assignee_name": assignee_name,
            "task_title": task_title,
            "task_description": task_description,
            "priority": priority,
            "deadline": "Не указан",  # В реальности нужно передать
        }

        result = await notification_service.send_notification(
            recipient=assignee_email,
            message=f"Вам назначена задача: {task_title}",
            channels=[NotificationChannel.EMAIL],
            notification_type=NotificationType.TASK_ASSIGNED,
            priority=NotificationPriority.MEDIUM,
            template_data=template_data,
        )

        return result["success"]

    @staticmethod
    async def send_system_alert(
        message: str, priority: NotificationPriority = NotificationPriority.HIGH
    ) -> Dict[str, Any]:
        """Отправка системного оповещения администраторам"""
        notification_service = NotificationService()

        return await notification_service.notify_admins(
            message=message,
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=priority,
        )

    # Метод для получения статистики уведомлений

    def get_notification_stats(self) -> Dict[str, Any]:
        """Получение статистики по уведомлениям"""
        # В реальном приложении здесь нужно хранить статистику в БД
        return {
            "email_stats": (
                self.email_service.get_email_stats()
                if hasattr(self.email_service, "get_email_stats")
                else {}
            ),
            "sms_balance": {},  # self.sms_service.get_balance() если есть метод
            "telegram_stats": {},  # self.telegram_service.get_bot_stats() если есть метод
        }


# Глобальный экземпляр сервиса
notification_service = NotificationService()
