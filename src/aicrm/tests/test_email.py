"""
Тесты для email сервиса
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ..models.user import User
from ..services.email_service import EmailMessage, EmailService


class TestEmailService:
    """Тесты для EmailService"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.service = EmailService()

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class):
        """Тест успешной отправки email"""
        # Настройка мока
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        # Создание тестового сообщения
        message = EmailMessage(
            to="test@example.com", subject="Test Subject", body="Test body"
        )

        # Выполнение асинхронной отправки
        import asyncio

        result = asyncio.run(self.service.send_email(message))

        # Проверки
        assert result is True
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp_class):
        """Тест неудачной отправки email"""
        # Настройка мока для ошибки
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception("SMTP Error")
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        message = EmailMessage(
            to="test@example.com", subject="Test Subject", body="Test body"
        )

        import asyncio

        result = asyncio.run(self.service.send_email(message))

        assert result is False

    def test_render_template_order_confirmation(self):
        """Тест рендеринга шаблона подтверждения заказа"""
        template_data = {
            "order_id": 123,
            "customer_name": "Иван Иванов",
            "total_amount": "5000 руб.",
            "deadline": "2025-12-01",
        }

        html_body, text_body = self.service._render_template(
            "order_confirmation", template_data
        )

        assert "Заказ №123 подтвержден!" in html_body
        assert "Уважаемый Иван Иванов," in html_body
        assert "5000 руб." in html_body

        assert "Заказ №123 подтвержден!" in text_body
        assert "Уважаемый Иван Иванов," in text_body

    def test_render_template_task_assigned(self):
        """Тест рендеринга шаблона назначения задачи"""
        template_data = {
            "task_id": 456,
            "assignee_name": "Мария Петрова",
            "task_title": "Дизайн логотипа",
            "task_description": "Создать логотип для компании",
            "priority": "Высокий",
            "deadline": "2025-11-20",
        }

        html_body, text_body = self.service._render_template(
            "task_assigned", template_data
        )

        assert "Вам назначена новая задача" in html_body
        assert "Мария Петрова" in html_body
        assert "Дизайн логотипа" in html_body

        assert "Вам назначена новая задача" in text_body
        assert "Мария Петрова" in text_body


class TestEmailAPI:
    """Тесты для email API"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        from ..main import app

        self.client = TestClient(app)

        # Создание тестового пользователя
        self.test_user = {
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
        }

    @patch("src.aicrm.services.email_service.email_service.send_email")
    def test_send_email_endpoint(self, mock_send_email, auth_headers):
        """Тест эндпоинта отправки email"""
        mock_send_email.return_value = True

        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email",
        }

        response = self.client.post(
            "/email/send", json=email_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "принят в очередь" in data["message"]

    @patch("src.aicrm.services.email_service.email_service.send_template_email")
    def test_send_template_email_endpoint(self, mock_send_template, auth_headers):
        """Тест эндпоинта отправки шаблонного email"""
        mock_send_template.return_value = True

        template_data = {
            "template_name": "order_confirmation",
            "to": "customer@example.com",
            "template_data": {"order_id": 123, "customer_name": "Иван Иванов"},
            "subject": "Заказ подтвержден",
        }

        response = self.client.post(
            "/email/send-template", json=template_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_templates_endpoint(self, auth_headers):
        """Тест получения списка шаблонов"""
        response = self.client.get("/email/templates", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert data["total"] >= 2  # Минимум 2 шаблона

        # Проверка наличия шаблонов
        templates = data["templates"]
        assert "order_confirmation" in templates
        assert "task_assigned" in templates

    def test_get_email_status_endpoint(self, auth_headers):
        """Тест получения статуса email сервиса"""
        response = self.client.get("/email/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "email"
        assert "status" in data
        assert "config" in data

    @patch("src.aicrm.services.email_service.email_service.send_email")
    def test_test_email_endpoint(self, mock_send_email, auth_headers):
        """Тест эндпоинта тестовой отправки email"""
        mock_send_email.return_value = True

        test_data = {"test_email": "test@example.com"}

        response = self.client.post(
            "/email/test", params=test_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "тестовое email отправлено" in data["message"]

    def test_send_email_unauthorized(self):
        """Тест отправки email без авторизации"""
        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email",
        }

        response = self.client.post("/email/send", json=email_data)

        assert response.status_code == 401


# Фикстура для авторизационных заголовков
@pytest.fixture
def auth_headers():
    """Фикстура для заголовков авторизации"""
    # В реальном тесте здесь нужно получить JWT токен
    return {"Authorization": "Bearer test-token"}


# Фикстура для мока пользователя
@pytest.fixture
def mock_current_user():
    """Фикстура для мока текущего пользователя"""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    return user
