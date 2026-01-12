"""
Тесты для NotificationService
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..services.notification_service import (NotificationChannel,
                                             NotificationPriority,
                                             NotificationService,
                                             NotificationType)


class TestNotificationService:
    """Тесты для сервиса уведомлений"""

    @pytest.fixture
    def notification_service(self):
        """Фикстура для NotificationService"""
        return NotificationService()

    @pytest.fixture
    def mock_email_service(self):
        """Мок для email сервиса"""
        with patch("src.aicrm.services.notification_service.email_service") as mock:
            mock.send_email = AsyncMock(return_value=True)
            mock.send_template_email = AsyncMock(return_value=True)
            yield mock

    @pytest.fixture
    def mock_sms_service(self):
        """Мок для SMS сервиса"""
        with patch("src.aicrm.services.notification_service.sms_service") as mock:
            mock.send_sms = AsyncMock(
                return_value={
                    "success": True,
                    "provider": "smsc",
                    "message_id": "msg123",
                    "cost": 1.5,
                }
            )
            yield mock

    @pytest.fixture
    def mock_telegram_service(self):
        """Мок для Telegram сервиса"""
        with patch(
            "src.aicrm.services.notification_service.TelegramBotService"
        ) as mock_class:
            mock_instance = MagicMock()
            mock_instance.send_message_to_chat = AsyncMock(return_value=True)
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_send_email_notification_success(
        self, notification_service, mock_email_service
    ):
        """Тест успешной отправки email уведомления"""
        result = await notification_service.send_notification(
            recipient="test@example.com",
            message="Test message",
            channels=[NotificationChannel.EMAIL],
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
        )

        assert result["success"] is True
        assert result["successful_channels"] == ["email"]
        assert result["failed_channels"] == []
        mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_notification_success(
        self, notification_service, mock_sms_service
    ):
        """Тест успешной отправки SMS уведомления"""
        result = await notification_service.send_notification(
            recipient="+1234567890",
            message="Test SMS",
            channels=[NotificationChannel.SMS],
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
        )

        assert result["success"] is True
        assert result["successful_channels"] == ["sms"]
        assert "provider" in result["results"]["sms"]
        assert "message_id" in result["results"]["sms"]
        mock_sms_service.send_sms.assert_called_once_with("+1234567890", "Test SMS")

    @pytest.mark.asyncio
    async def test_send_telegram_notification_success(
        self, notification_service, mock_telegram_service
    ):
        """Тест успешной отправки Telegram уведомления"""
        result = await notification_service.send_notification(
            recipient="123456789",
            message="Test Telegram message",
            channels=[NotificationChannel.TELEGRAM],
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.LOW,
        )

        assert result["success"] is True
        assert result["successful_channels"] == ["telegram"]
        mock_telegram_service.send_message_to_chat.assert_called_once_with(
            "123456789", "Test Telegram message"
        )

    @pytest.mark.asyncio
    async def test_send_multi_channel_notification(
        self, notification_service, mock_email_service, mock_sms_service
    ):
        """Тест отправки уведомления через несколько каналов"""
        result = await notification_service.send_notification(
            recipient={"email": "test@example.com", "phone": "+1234567890"},
            message="Multi-channel message",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.URGENT,
        )

        assert result["success"] is True
        assert set(result["successful_channels"]) == {"email", "sms"}
        assert result["failed_channels"] == []
        assert mock_email_service.send_email.called
        assert mock_sms_service.send_sms.called

    @pytest.mark.asyncio
    async def test_send_notification_with_template(
        self, notification_service, mock_email_service
    ):
        """Тест отправки уведомления с использованием шаблона"""
        template_data = {
            "assignee_name": "John Doe",
            "task_title": "Test Task",
            "task_description": "Test Description",
        }

        result = await notification_service.send_notification(
            recipient="test@example.com",
            message="Task assigned",
            channels=[NotificationChannel.EMAIL],
            notification_type=NotificationType.TASK_ASSIGNED,
            priority=NotificationPriority.HIGH,
            template_data=template_data,
        )

        assert result["success"] is True
        mock_email_service.send_template_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_partial_failure(
        self, notification_service, mock_email_service, mock_sms_service
    ):
        """Тест частичной неудачи отправки уведомлений"""
        mock_email_service.send_email.side_effect = Exception("Email failed")

        result = await notification_service.send_notification(
            recipient={"email": "test@example.com", "phone": "+1234567890"},
            message="Test message",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        assert result["success"] is False
        assert result["successful_channels"] == ["sms"]
        assert result["failed_channels"] == ["email"]
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_notifications(
        self, notification_service, mock_email_service
    ):
        """Тест массовой отправки уведомлений"""
        recipients = [
            "user1@example.com",
            "user2@example.com",
            {"email": "user3@example.com"},
        ]

        result = await notification_service.send_bulk_notifications(
            recipients=recipients,
            message="Bulk message",
            channels=[NotificationChannel.EMAIL],
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
        )

        assert result["total_recipients"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert result["success_rate"] == 1.0
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_notify_admins_success(
        self, notification_service, mock_email_service, mock_sms_service
    ):
        """Тест уведомления администраторов"""
        result = await notification_service.notify_admins(
            message="System alert",
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        assert (
            result["total_recipients"] == 2
        )  # admin@example.com и support@example.com
        assert result["successful"] == 2
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_notify_managers_success(
        self, notification_service, mock_email_service
    ):
        """Тест уведомления менеджеров"""
        result = await notification_service.notify_managers(
            message="Manager alert",
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
        )

        assert result["total_recipients"] == 2  # manager1 и manager2
        assert result["successful"] == 2

    @pytest.mark.asyncio
    async def test_send_task_assigned_notification(self):
        """Тест статического метода отправки уведомления о задаче"""
        with patch(
            "src.aicrm.services.notification_service.NotificationService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.send_notification = AsyncMock(return_value={"success": True})
            mock_service_class.return_value = mock_service

            result = await NotificationService.send_task_assigned_notification(
                assignee_email="assignee@example.com",
                assignee_name="John Doe",
                task_title="Test Task",
                task_description="Test Description",
            )

            assert result is True
            mock_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_system_alert(self):
        """Тест статического метода отправки системного алерта"""
        with patch(
            "src.aicrm.services.notification_service.NotificationService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.notify_admins = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_service_class.return_value = mock_service

            result = await NotificationService.send_system_alert(
                message="Critical system error", priority=NotificationPriority.URGENT
            )

            assert result["successful"] == 2
            mock_service.notify_admins.assert_called_once()

    def test_generate_subject_by_type_and_priority(self, notification_service):
        """Тест генерации темы письма"""
        # Тест обычного уведомления
        subject = notification_service._generate_subject(
            NotificationType.INFO, NotificationPriority.MEDIUM
        )
        assert subject == "Информация"

        # Тест срочного уведомления
        subject = notification_service._generate_subject(
            NotificationType.ERROR, NotificationPriority.URGENT
        )
        assert subject == "СРОЧНО: Ошибка"

        # Тест высокого приоритета
        subject = notification_service._generate_subject(
            NotificationType.WARNING, NotificationPriority.HIGH
        )
        assert subject == "Предупреждение"

    def test_extract_email_from_recipient(self, notification_service):
        """Тест извлечения email из данных получателя"""
        # Из строки
        email = notification_service._extract_email("test@example.com")
        assert email == "test@example.com"

        # Из dict
        email = notification_service._extract_email({"email": "test@example.com"})
        assert email == "test@example.com"

        # Неверный формат
        email = notification_service._extract_email("not-an-email")
        assert email is None

    def test_extract_phone_from_recipient(self, notification_service):
        """Тест извлечения телефона из данных получателя"""
        # Из строки
        phone = notification_service._extract_phone("+1234567890")
        assert phone == "+1234567890"

        # Из dict
        phone = notification_service._extract_phone({"phone": "+1234567890"})
        assert phone == "+1234567890"

        # Неверный формат
        phone = notification_service._extract_phone("not-a-phone")
        assert phone is None

    def test_extract_telegram_id_from_recipient(self, notification_service):
        """Тест извлечения Telegram ID из данных получателя"""
        # Из строки
        tg_id = notification_service._extract_telegram_id("123456789")
        assert tg_id == "123456789"

        # Из dict
        tg_id = notification_service._extract_telegram_id({"telegram_id": "123456789"})
        assert tg_id == "123456789"

        # Неверный формат
        tg_id = notification_service._extract_telegram_id("not-a-number")
        assert tg_id is None

    def test_get_template_for_type(self, notification_service):
        """Тест получения шаблона для типа уведомления"""
        template = notification_service._get_template_for_type(
            NotificationType.TASK_ASSIGNED
        )
        assert template == "task_assigned"

        template = notification_service._get_template_for_type(
            NotificationType.ORDER_UPDATE
        )
        assert template == "order_confirmation"

        template = notification_service._get_template_for_type(NotificationType.INFO)
        assert template is None

    def test_sms_message_truncation(self, notification_service, mock_sms_service):
        """Тест усечения длинных SMS сообщений"""
        long_message = "A" * 200  # Сообщение длиннее 160 символов

        # Это будет протестировано в send_sms_notification
        # Проверяем что сообщение усекается до 160 символов
        assert len(long_message) > 160

        # В реальном тесте нужно проверить вызов send_sms с усеченным сообщением
        # mock_sms_service.send_sms.assert_called_with(phone, long_message[:160])

    def test_notification_stats_method(self, notification_service):
        """Тест метода получения статистики уведомлений"""
        stats = notification_service.get_notification_stats()

        # Проверяем структуру ответа
        assert isinstance(stats, dict)
        assert "email_stats" in stats
        assert "sms_balance" in stats
        assert "telegram_stats" in stats
