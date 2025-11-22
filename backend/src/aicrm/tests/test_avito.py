"""
Тесты для интеграции с Avito
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, timedelta

from src.aicrm.services.avito_service import AvitoService, AvitoClient, AvitoAuthError
from src.aicrm.services.avito_handler import AvitoCommunicationHandler
from src.aicrm.api.schemas.avito import (
    AvitoStatsRequest,
    AvitoApplyVasRequest,
    AvitoUpdatePriceRequest,
    AvitoPromotionRequest
)


class TestAvitoClient:
    """Тесты для AvitoClient"""

    @pytest.fixture
    def mock_settings(self):
        """Мока для настроек"""
        return {
            "avito_client_id": "test_client_id",
            "avito_client_secret": "test_client_secret",
            "avito_user_id": 12345
        }

    @pytest.fixture
    def avito_client(self, mock_settings):
        """Фикстура для AvitoClient с моками"""
        with patch('src.aicrm.services.avito_service.settings') as mock_settings_obj:
            mock_settings_obj.avito_client_id = mock_settings["avito_client_id"]
            mock_settings_obj.avito_client_secret = mock_settings["avito_client_secret"]
            mock_settings_obj.avito_user_id = mock_settings["avito_user_id"]

            client = AvitoClient()
            return client

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, avito_client):
        """Тест успешного обновления токена"""
        mock_response = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        with patch.object(avito_client.http_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json = MagicMock(return_value=mock_response)

            token = await avito_client._ensure_token()

            assert token == "test_token"
            assert avito_client.access_token == "test_token"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_refresh_auth_error(self, avito_client):
        """Тест ошибки авторизации при обновлении токена"""
        with patch.object(avito_client.http_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.return_value.raise_for_status.side_effect = Exception("401")
            mock_post.return_value.status_code = 401

            with pytest.raises(AvitoAuthError):
                await avito_client._ensure_token()

    @pytest.mark.asyncio
    async def test_get_items_success(self, avito_client):
        """Тест успешного получения объявлений"""
        mock_response = {
            "resources": [
                {"id": 1, "title": "Test Item", "status": "active"}
            ]
        }

        with patch.object(avito_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            items = await avito_client.get_items(status="active")

            assert len(items) == 1
            assert items[0]["id"] == 1
            mock_request.assert_called_once_with(
                "GET",
                "/core/v1/items",
                params={"status": "active"}
            )

    @pytest.mark.asyncio
    async def test_get_item_stats_success(self, avito_client):
        """Тест успешного получения статистики"""
        item_ids = [123, 456]
        date_from = date.today() - timedelta(days=7)
        date_to = date.today()

        mock_response = {
            "result": {
                "items": [
                    {
                        "itemId": 123,
                        "stats": [
                            {"date": "2023-01-01", "uniqViews": 10, "uniqContacts": 2}
                        ]
                    }
                ]
            }
        }

        with patch.object(avito_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            stats = await avito_client.get_item_stats(item_ids, date_from, date_to)

            assert stats == mock_response
            mock_request.assert_called_once()


class TestAvitoService:
    """Тесты для AvitoService"""

    @pytest.fixture
    def avito_service(self):
        """Фикстура для AvitoService"""
        return AvitoService()

    @pytest.mark.asyncio
    async def test_get_active_items_success(self, avito_service):
        """Тест успешного получения активных объявлений"""
        mock_items = [
            {"id": 1, "title": "Item 1", "status": "active"},
            {"id": 2, "title": "Item 2", "status": "active"}
        ]

        with patch.object(avito_service.client, 'get_items', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_items

            async with avito_service:
                items = await avito_service.get_active_items()

            assert len(items) == 2
            assert items[0]["title"] == "Item 1"

    @pytest.mark.asyncio
    async def test_optimize_ad_pricing_high_conversion(self, avito_service):
        """Тест оптимизации цены при высокой конверсии"""
        mock_performance = {
            "stats": {
                "items": [{
                    "stats": [
                        {"uniqViews": 100, "uniqContacts": 10}
                    ]
                }]
            }
        }

        with patch.object(avito_service, 'get_item_performance', new_callable=AsyncMock) as mock_perf:
            mock_perf.return_value = mock_performance

            async with avito_service:
                result = await avito_service.optimize_ad_pricing(123)

            assert result["current_conversion"] == 0.1  # 10/100
            assert "оптимальном диапазоне" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_optimize_ad_pricing_low_conversion(self, avito_service):
        """Тест оптимизации цены при низкой конверсии"""
        mock_performance = {
            "stats": {
                "items": [{
                    "stats": [
                        {"uniqViews": 1000, "uniqContacts": 5}
                    ]
                }]
            }
        }

        with patch.object(avito_service, 'get_item_performance', new_callable=AsyncMock) as mock_perf:
            mock_perf.return_value = mock_performance

            async with avito_service:
                result = await avito_service.optimize_ad_pricing(123)

            assert result["current_conversion"] == 0.005  # 5/1000
            assert "Увеличить цену" in result["recommendation"]


class TestAvitoCommunicationHandler:
    """Тесты для AvitoCommunicationHandler"""

    @pytest.fixture
    def db_session(self):
        """Мок для сессии базы данных"""
        return MagicMock()

    @pytest.fixture
    def handler(self, db_session):
        """Фикстура для AvitoCommunicationHandler"""
        return AvitoCommunicationHandler(db_session)

    @pytest.mark.asyncio
    async def test_handle_incoming_message_success(self, handler):
        """Тест успешной обработки входящего сообщения"""
        message_data = {
            "chat_id": "chat123",
            "user_id": "user456",
            "message": {
                "text": "Hello, I need printing services",
                "timestamp": "2023-01-01T10:00:00Z"
            },
            "item_id": 12345
        }

        # Мокаем зависимости
        with patch.object(handler, '_find_or_create_customer', new_callable=AsyncMock) as mock_customer, \
             patch.object(handler.communication_service, 'handle_incoming_message', new_callable=AsyncMock) as mock_comm, \
             patch.object(handler, '_handle_avito_specific_logic', new_callable=AsyncMock) as mock_specific:

            mock_customer.return_value = MagicMock(id=1)
            mock_comm.return_value = {"success": True, "communication_id": 123}

            result = await handler.handle_incoming_message(message_data)

            assert result["success"] is True
            assert result["communication_id"] == 123
            mock_customer.assert_called_once_with("user456", "chat123")
            mock_comm.assert_called_once()
            mock_specific.assert_called_once()

    def test_extract_message_content_avito(self):
        """Тест извлечения содержимого сообщения из Avito"""
        from src.aicrm.services.communication_service import CommunicationService

        service = CommunicationService(MagicMock())

        # Тест с message.text
        avito_data = {
            "text": "Test message",
            "message": {"text": "Alternative text"}
        }
        content = service._extract_message_content("avito", avito_data)
        assert content == "Test message"

        # Тест с message.text (fallback)
        avito_data = {
            "message": {"text": "Alternative text"}
        }
        content = service._extract_message_content("avito", avito_data)
        assert content == "Alternative text"


class TestAvitoSchemas:
    """Тесты для Pydantic схем"""

    def test_avito_stats_request_validation(self):
        """Тест валидации AvitoStatsRequest"""
        # Корректный запрос
        request = AvitoStatsRequest(
            item_ids=[123, 456],
            date_from=date(2023, 1, 1),
            date_to=date(2023, 1, 31)
        )
        assert request.item_ids == [123, 456]

        # Проверка валидации полей статистики
        with pytest.raises(ValueError):
            AvitoStatsRequest(
                item_ids=[123],
                date_from=date(2023, 1, 1),
                date_to=date(2023, 1, 31),
                fields=["invalid_field"]
            )

    def test_avito_apply_vas_request(self):
        """Тест AvitoApplyVasRequest"""
        request = AvitoApplyVasRequest(
            slugs=["xl", "highlight"],
            stickers=[1, 2]
        )
        assert request.slugs == ["xl", "highlight"]
        assert request.stickers == [1, 2]

    def test_avito_update_price_request(self):
        """Тест AvitoUpdatePriceRequest"""
        request = AvitoUpdatePriceRequest(price=1500)
        assert request.price == 1500

        # Проверка отрицательной цены
        with pytest.raises(ValueError):
            AvitoUpdatePriceRequest(price=-100)

    def test_avito_promotion_request(self):
        """Тест AvitoPromotionRequest"""
        request = AvitoPromotionRequest(
            item_id=123,
            service_slug="xl",
            stickers=[1]
        )
        assert request.item_id == 123
        assert request.service_slug == "xl"
