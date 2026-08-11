"""
Интеграционные тесты для Telegram API
"""

from unittest.mock import MagicMock, patch

from httpx import AsyncClient


class TestTelegramApi:
    """Тесты для Telegram API"""

    async def test_initialize_bot_success(self, async_client: AsyncClient):
        """Тест успешной инициализации бота"""
        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.initialize_bot.return_value = True
            mock_service.get_bot_stats.return_value = {"bot_running": False}
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/initialize")

            assert response.status_code == 200
            data = response.json()
            assert "успешно инициализирован" in data["message"]

    async def test_initialize_bot_already_running(self, async_client: AsyncClient):
        """Тест инициализации уже запущенного бота"""
        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_bot_stats.return_value = {"bot_running": True}
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/initialize")

            assert response.status_code == 200
            data = response.json()
            assert "уже запущен" in data["message"]

    async def test_initialize_bot_no_token(self, async_client: AsyncClient):
        """Тест инициализации бота без токена"""
        with patch("src.aicrm.core.config.settings") as mock_settings:
            mock_settings.telegram_bot_token = None

            response = await async_client.post("/telegram/initialize")

            assert response.status_code == 400
            assert "token не настроен" in response.json()["detail"]

    async def test_initialize_bot_failure(self, async_client: AsyncClient):
        """Тест неудачной инициализации бота"""
        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.initialize_bot.return_value = False
            mock_service.get_bot_stats.return_value = {"bot_running": False}
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/initialize")

            assert response.status_code == 500
            assert "Не удалось инициализировать" in response.json()["detail"]

    async def test_stop_bot_success(self, async_client: AsyncClient):
        """Тест успешной остановки бота"""
        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/stop")

            assert response.status_code == 200
            data = response.json()
            assert "остановлен" in data["message"]

    async def test_send_message_success(self, async_client: AsyncClient):
        """Тест успешной отправки сообщения"""
        message_data = {"chat_id": "123456789", "message": "Test message"}

        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.send_message_to_chat.return_value = True
            mock_service_class.return_value = mock_service

            response = await async_client.post(
                "/telegram/send-message", json=message_data
            )

            assert response.status_code == 200
            data = response.json()
            assert "отправлено в чат" in data["message"]

    async def test_send_message_failure(self, async_client: AsyncClient):
        """Тест неудачной отправки сообщения"""
        message_data = {"chat_id": "123456789", "message": "Test message"}

        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.send_message_to_chat.return_value = False
            mock_service_class.return_value = mock_service

            response = await async_client.post(
                "/telegram/send-message", json=message_data
            )

            assert response.status_code == 500
            assert "Не удалось отправить сообщение" in response.json()["detail"]

    async def test_get_bot_stats_success(self, async_client: AsyncClient):
        """Тест успешного получения статистики бота"""
        mock_stats = {
            "total_chats": 10,
            "active_chats": 8,
            "total_messages": 150,
            "bot_running": True,
        }

        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_bot_stats.return_value = mock_stats
            mock_service_class.return_value = mock_service

            response = await async_client.get("/telegram/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_chats"] == 10
            assert data["active_chats"] == 8
            assert data["total_messages"] == 150
            assert data["bot_running"] is True

    async def test_get_chats_success(self, async_client: AsyncClient):
        """Тест успешного получения списка чатов"""
        response = await async_client.get("/telegram/chats")

        assert response.status_code == 200
        data = response.json()
        assert "chats" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    async def test_get_chats_with_params(self, async_client: AsyncClient):
        """Тест получения списка чатов с параметрами"""
        response = await async_client.get("/telegram/chats?limit=10&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    async def test_get_chat_info_success(self, async_client: AsyncClient):
        """Тест успешного получения информации о чате"""
        chat_id = "123456789"

        response = await async_client.get(f"/telegram/chat/{chat_id}")

        assert response.status_code == 200
        data = response.json()
        assert "chat_id" in data
        assert "chat_type" in data
        assert "display_name" in data

    async def test_get_chat_info_not_found(self, async_client: AsyncClient):
        """Тест получения информации о несуществующем чате"""
        chat_id = "nonexistent"

        response = await async_client.get(f"/telegram/chat/{chat_id}")

        assert response.status_code == 404
        assert "Чат не найден" in response.json()["detail"]

    async def test_get_telegram_communications_success(self, async_client: AsyncClient):
        """Тест успешного получения коммуникаций через Telegram"""
        response = await async_client.get("/telegram/communications")

        assert response.status_code == 200
        data = response.json()
        assert "communications" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    async def test_get_telegram_communications_with_params(
        self, async_client: AsyncClient
    ):
        """Тест получения коммуникаций с параметрами"""
        response = await async_client.get("/telegram/communications?limit=50&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 10

    async def test_link_chat_to_customer_success(self, async_client: AsyncClient):
        """Тест успешного связывания чата с клиентом"""
        chat_id = "123456789"
        customer_id = 1

        response = await async_client.post(
            f"/telegram/chat/{chat_id}/link-customer?customer_id={customer_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "связан с клиентом" in data["message"]
        assert data["chat_id"] == chat_id
        assert data["customer_id"] == customer_id

    async def test_link_chat_to_customer_chat_not_found(
        self, async_client: AsyncClient
    ):
        """Тест связывания несуществующего чата с клиентом"""
        chat_id = "nonexistent"
        customer_id = 1

        response = await async_client.post(
            f"/telegram/chat/{chat_id}/link-customer?customer_id={customer_id}"
        )

        assert response.status_code == 404
        assert "Чат не найден" in response.json()["detail"]

    async def test_link_chat_to_customer_customer_not_found(
        self, async_client: AsyncClient
    ):
        """Тест связывания чата с несуществующим клиентом"""
        chat_id = "123456789"
        customer_id = 999

        response = await async_client.post(
            f"/telegram/chat/{chat_id}/link-customer?customer_id={customer_id}"
        )

        assert response.status_code == 404
        assert "Клиент не найден" in response.json()["detail"]

    async def test_unlink_chat_from_customer_success(self, async_client: AsyncClient):
        """Тест успешного отвязывания чата от клиента"""
        chat_id = "123456789"

        response = await async_client.delete(
            f"/telegram/chat/{chat_id}/unlink-customer"
        )

        assert response.status_code == 200
        data = response.json()
        assert "отвязан от клиента" in data["message"]

    async def test_unlink_chat_from_customer_not_found(self, async_client: AsyncClient):
        """Тест отвязывания несуществующего чата от клиента"""
        chat_id = "nonexistent"

        response = await async_client.delete(
            f"/telegram/chat/{chat_id}/unlink-customer"
        )

        assert response.status_code == 404
        assert "Чат не найден" in response.json()["detail"]

    async def test_telegram_webhook_success(self, async_client: AsyncClient):
        """Тест успешной обработки webhook"""
        webhook_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 123456789, "type": "private"},
                "date": 1609459200,
                "text": "Hello bot",
            },
        }

        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.initialize_bot.return_value = True
            mock_service.application = MagicMock()
            mock_service.application._initialized = True
            mock_service.application.process_update = MagicMock()
            mock_service.bot = MagicMock()
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/webhook", json=webhook_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    async def test_telegram_webhook_initialization_failure(
        self, async_client: AsyncClient
    ):
        """Тест webhook с неудачной инициализацией бота"""
        webhook_data = {"update_id": 123456}

        with patch(
            "src.aicrm.services.telegram_bot_service.TelegramBotService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.initialize_bot.return_value = False
            mock_service_class.return_value = mock_service

            response = await async_client.post("/telegram/webhook", json=webhook_data)

            assert response.status_code == 500
            assert "Не удалось инициализировать бота" in response.json()["detail"]

    async def test_set_webhook_success(self, async_client: AsyncClient):
        """Тест успешной установки webhook"""
        webhook_url = "https://example.com/telegram/webhook"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": True}
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await async_client.post(
                f"/telegram/set-webhook?webhook_url={webhook_url}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "установлен успешно" in data["message"]

    async def test_set_webhook_failure(self, async_client: AsyncClient):
        """Тест неудачной установки webhook"""
        webhook_url = "https://example.com/telegram/webhook"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": False,
                "description": "Invalid URL",
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await async_client.post(
                f"/telegram/set-webhook?webhook_url={webhook_url}"
            )

            assert response.status_code == 400
            assert "Ошибка установки webhook" in response.json()["detail"]

    async def test_set_webhook_no_token(self, async_client: AsyncClient):
        """Тест установки webhook без токена"""
        webhook_url = "https://example.com/telegram/webhook"

        with patch("src.aicrm.core.config.settings") as mock_settings:
            mock_settings.telegram_bot_token = None

            response = await async_client.post(
                f"/telegram/set-webhook?webhook_url={webhook_url}"
            )

            assert response.status_code == 400
            assert "token не настроен" in response.json()["detail"]

    async def test_delete_webhook_success(self, async_client: AsyncClient):
        """Тест успешного удаления webhook"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": True}
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await async_client.post("/telegram/delete-webhook")

            assert response.status_code == 200
            data = response.json()
            assert "удален успешно" in data["message"]

    async def test_delete_webhook_failure(self, async_client: AsyncClient):
        """Тест неудачного удаления webhook"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": False,
                "description": "Webhook not found",
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await async_client.post("/telegram/delete-webhook")

            assert response.status_code == 400
            assert "Ошибка удаления webhook" in response.json()["detail"]

    async def test_delete_webhook_no_token(self, async_client: AsyncClient):
        """Тест удаления webhook без токена"""
        with patch("src.aicrm.core.config.settings") as mock_settings:
            mock_settings.telegram_bot_token = None

            response = await async_client.post("/telegram/delete-webhook")

            assert response.status_code == 400
            assert "token не настроен" in response.json()["detail"]

    # Validation tests

    async def test_send_message_validation_error_missing_fields(
        self, async_client: AsyncClient
    ):
        """Тест валидации - отсутствующие поля в сообщении"""
        invalid_data = {
            "chat_id": "123456789"
            # Отсутствует message
        }

        response = await async_client.post("/telegram/send-message", json=invalid_data)

        assert response.status_code == 422

    async def test_send_message_validation_error_empty_message(
        self, async_client: AsyncClient
    ):
        """Тест валидации - пустое сообщение"""
        invalid_data = {"chat_id": "123456789", "message": ""}  # Пустое сообщение

        response = await async_client.post("/telegram/send-message", json=invalid_data)

        assert response.status_code == 422

    async def test_link_chat_validation_error_invalid_customer_id(
        self, async_client: AsyncClient
    ):
        """Тест валидации - некорректный ID клиента"""
        chat_id = "123456789"
        customer_id = "invalid"  # Должен быть int

        response = await async_client.post(
            f"/telegram/chat/{chat_id}/link-customer?customer_id={customer_id}"
        )

        assert response.status_code == 422

    async def test_set_webhook_validation_error_invalid_url(
        self, async_client: AsyncClient
    ):
        """Тест валидации - некорректный URL webhook"""
        invalid_url = "not-a-url"

        response = await async_client.post(
            f"/telegram/set-webhook?webhook_url={invalid_url}"
        )

        assert response.status_code == 422
