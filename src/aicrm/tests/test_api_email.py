"""
Интеграционные тесты для Email API
"""

from unittest.mock import MagicMock, patch

from httpx import AsyncClient


class TestEmailApi:
    """Тесты для Email API"""

    async def test_send_email_success(self, async_client: AsyncClient):
        """Тест успешной отправки email"""
        # Сначала регистрируем и логинимся пользователя
        register_data = {
            "email": "test_email@example.com",
            "password": "testpass123",
            "full_name": "Test Email User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_email@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем email
        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
        }

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_email = MagicMock()

            response = await async_client.post(
                "/email/send",
                json=email_data,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "принят в очередь" in data["message"]
            assert data["email_id"] is not None

    async def test_send_email_with_html_and_cc(self, async_client: AsyncClient):
        """Тест отправки email с HTML и CC"""
        # Регистрация и логин
        register_data = {
            "email": "test_email2@example.com",
            "password": "testpass123",
            "full_name": "Test Email User 2",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_email2@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем email с дополнительными полями
        email_data = {
            "to": ["recipient1@example.com", "recipient2@example.com"],
            "subject": "HTML Test Subject",
            "body": "Plain text body",
            "html_body": "<h1>HTML Body</h1><p>This is HTML content</p>",
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "reply_to": "reply@example.com",
        }

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_email = MagicMock()

            response = await async_client.post(
                "/email/send",
                json=email_data,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    async def test_send_email_unauthorized(self, async_client: AsyncClient):
        """Тест отправки email без авторизации"""
        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
        }

        response = await async_client.post("/email/send", json=email_data)

        assert response.status_code == 401

    async def test_send_email_service_error(self, async_client: AsyncClient):
        """Тест ошибки сервиса при отправке email"""
        # Регистрация и логин
        register_data = {
            "email": "test_email3@example.com",
            "password": "testpass123",
            "full_name": "Test Email User 3",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_email3@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
        }

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_email = MagicMock(side_effect=Exception("SMTP Error"))

            response = await async_client.post(
                "/email/send",
                json=email_data,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 500
            assert "Ошибка при отправке email" in response.json()["detail"]

    async def test_send_template_email_success(self, async_client: AsyncClient):
        """Тест успешной отправки шаблонного email"""
        # Регистрация и логин
        register_data = {
            "email": "test_template@example.com",
            "password": "testpass123",
            "full_name": "Test Template User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_template@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        template_data = {
            "template_name": "order_confirmation",
            "to": "customer@example.com",
            "template_data": {
                "order_id": "12345",
                "customer_name": "Иван Иванов",
                "total_amount": "1500.00",
                "deadline": "2024-12-31",
            },
            "subject": "Подтверждение заказа #12345",
        }

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_template_email = MagicMock()

            response = await async_client.post(
                "/email/send-template",
                json=template_data,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Шаблонный email принят" in data["message"]

    async def test_send_template_email_unauthorized(self, async_client: AsyncClient):
        """Тест отправки шаблонного email без авторизации"""
        template_data = {
            "template_name": "order_confirmation",
            "to": "customer@example.com",
            "template_data": {"order_id": "12345"},
            "subject": "Test Subject",
        }

        response = await async_client.post("/email/send-template", json=template_data)

        assert response.status_code == 401

    async def test_send_template_email_service_error(self, async_client: AsyncClient):
        """Тест ошибки сервиса при отправке шаблонного email"""
        # Регистрация и логин
        register_data = {
            "email": "test_template_error@example.com",
            "password": "testpass123",
            "full_name": "Test Template Error User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {
            "email": "test_template_error@example.com",
            "password": "testpass123",
        }

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        template_data = {
            "template_name": "order_confirmation",
            "to": "customer@example.com",
            "template_data": {"order_id": "12345"},
            "subject": "Test Subject",
        }

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_template_email = MagicMock(
                side_effect=Exception("Template Error")
            )

            response = await async_client.post(
                "/email/send-template",
                json=template_data,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 500
            assert "Ошибка при отправке шаблонного email" in response.json()["detail"]

    async def test_test_email_config_success(self, async_client: AsyncClient):
        """Тест успешной тестовой отправки email"""
        # Регистрация и логин
        register_data = {
            "email": "test_config@example.com",
            "password": "testpass123",
            "full_name": "Test Config User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_config@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_email = MagicMock()

            response = await async_client.post(
                "/email/test",
                params={"test_email": "test@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Тестовое email отправлено" in data["message"]

    async def test_test_email_config_unauthorized(self, async_client: AsyncClient):
        """Тест тестовой отправки email без авторизации"""
        response = await async_client.post(
            "/email/test", params={"test_email": "test@example.com"}
        )

        assert response.status_code == 401

    async def test_test_email_config_service_error(self, async_client: AsyncClient):
        """Тест ошибки сервиса при тестовой отправке"""
        # Регистрация и логин
        register_data = {
            "email": "test_config_error@example.com",
            "password": "testpass123",
            "full_name": "Test Config Error User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {
            "email": "test_config_error@example.com",
            "password": "testpass123",
        }

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        with patch("src.aicrm.services.email_service.email_service") as mock_service:
            mock_service.send_email = MagicMock(
                side_effect=Exception("SMTP Config Error")
            )

            response = await async_client.post(
                "/email/test",
                params={"test_email": "test@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 500
            assert "Ошибка при отправке тестового email" in response.json()["detail"]

    async def test_get_available_templates_success(self, async_client: AsyncClient):
        """Тест успешного получения списка шаблонов"""
        # Регистрация и логин
        register_data = {
            "email": "test_templates@example.com",
            "password": "testpass123",
            "full_name": "Test Templates User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_templates@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/email/templates", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert data["total"] == 2  # order_confirmation и task_assigned
        assert "order_confirmation" in data["templates"]
        assert "task_assigned" in data["templates"]

    async def test_get_available_templates_unauthorized(
        self, async_client: AsyncClient
    ):
        """Тест получения шаблонов без авторизации"""
        response = await async_client.get("/email/templates")

        assert response.status_code == 401

    async def test_get_email_service_status_success(self, async_client: AsyncClient):
        """Тест успешного получения статуса email сервиса"""
        # Регистрация и логин
        register_data = {
            "email": "test_status@example.com",
            "password": "testpass123",
            "full_name": "Test Status User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_status@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/email/status", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "email"
        assert "status" in data
        assert "config" in data
        assert "smtp_server" in data["config"]
        assert "smtp_port" in data["config"]
        assert "from_email" in data["config"]

    async def test_get_email_service_status_unauthorized(
        self, async_client: AsyncClient
    ):
        """Тест получения статуса без авторизации"""
        response = await async_client.get("/email/status")

        assert response.status_code == 401

    # Validation tests

    async def test_send_email_validation_error_missing_fields(
        self, async_client: AsyncClient
    ):
        """Тест валидации - отсутствующие обязательные поля"""
        # Регистрация и логин
        register_data = {
            "email": "test_validation@example.com",
            "password": "testpass123",
            "full_name": "Test Validation User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_validation@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем неполные данные
        invalid_data = {
            "to": "recipient@example.com"
            # Отсутствуют subject и body
        }

        response = await async_client.post(
            "/email/send",
            json=invalid_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_send_email_validation_error_invalid_email(
        self, async_client: AsyncClient
    ):
        """Тест валидации - некорректный email"""
        # Регистрация и логин
        register_data = {
            "email": "test_invalid@example.com",
            "password": "testpass123",
            "full_name": "Test Invalid User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {"email": "test_invalid@example.com", "password": "testpass123"}

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем данные с некорректным email
        invalid_data = {
            "to": "invalid-email",  # Некорректный email
            "subject": "Test Subject",
            "body": "Test body",
        }

        response = await async_client.post(
            "/email/send",
            json=invalid_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_send_template_email_validation_error(
        self, async_client: AsyncClient
    ):
        """Тест валидации шаблонного email"""
        # Регистрация и логин
        register_data = {
            "email": "test_template_validation@example.com",
            "password": "testpass123",
            "full_name": "Test Template Validation User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {
            "email": "test_template_validation@example.com",
            "password": "testpass123",
        }

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем неполные данные шаблона
        invalid_data = {
            "template_name": "order_confirmation",
            "to": "customer@example.com",
            # Отсутствуют template_data и subject
        }

        response = await async_client.post(
            "/email/send-template",
            json=invalid_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_test_email_config_validation_error(self, async_client: AsyncClient):
        """Тест валидации тестовой отправки"""
        # Регистрация и логин
        register_data = {
            "email": "test_config_validation@example.com",
            "password": "testpass123",
            "full_name": "Test Config Validation User",
        }

        register_response = await async_client.post(
            "/auth/register", json=register_data
        )
        assert register_response.status_code == 200

        login_data = {
            "email": "test_config_validation@example.com",
            "password": "testpass123",
        }

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Отправляем запрос без параметра test_email
        response = await async_client.post(
            "/email/test", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422
