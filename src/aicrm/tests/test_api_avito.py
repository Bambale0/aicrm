"""
Интеграционные тесты для Avito API
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestAvitoAPI:
    """Тесты для Avito API"""

    async def test_get_active_items_success(self, async_client: AsyncClient):
        """Тест успешного получения активных объявлений"""
        mock_items = [
            {
                "id": 12345,
                "title": "Футболка с принтом",
                "price": 1500,
                "status": "active",
                "url": "https://avito.ru/item/12345"
            },
            {
                "id": 67890,
                "title": "Худи с логотипом",
                "price": 2500,
                "status": "active",
                "url": "https://avito.ru/item/67890"
            }
        ]

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_active_items.return_value = mock_items
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get("/avito/items")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["id"] == 12345
            assert data[0]["status"] == "active"

    async def test_get_active_items_auth_error(self, async_client: AsyncClient):
        """Тест ошибки авторизации Avito"""
        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_active_items.side_effect = Exception("Auth error")
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            # Мокаем исключение AvitoAuthError
            from src.aicrm.services.avito_service import AvitoAuthError
            mock_service.get_active_items.side_effect = AvitoAuthError("Invalid token")

            response = await async_client.get("/avito/items")

            assert response.status_code == 401
            assert "авторизации" in response.json()["detail"].lower()

    async def test_get_item_performance_success(self, async_client: AsyncClient):
        """Тест успешного получения производительности объявления"""
        item_id = 12345
        mock_performance = {
            "item_id": item_id,
            "views": 150,
            "contacts": 12,
            "favorites": 8,
            "conversion_rate": 8.0,
            "avg_position": 5.2,
            "period_days": 30
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_item_performance.return_value = mock_performance
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get(f"/avito/items/{item_id}/performance")

            assert response.status_code == 200
            data = response.json()
            assert data["item_id"] == item_id
            assert data["views"] == 150
            assert data["contacts"] == 12
            assert "conversion_rate" in data

    async def test_get_item_performance_with_days_param(self, async_client: AsyncClient):
        """Тест получения производительности с параметром дней"""
        item_id = 12345
        days = 7

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_item_performance.return_value = {"item_id": item_id, "period_days": days}
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get(f"/avito/items/{item_id}/performance?days={days}")

            assert response.status_code == 200
            data = response.json()
            assert data["period_days"] == days

    async def test_get_items_stats_success(self, async_client: AsyncClient):
        """Тест успешного получения статистики по объявлениям"""
        request_data = {
            "item_ids": [12345, 67890],
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
            "fields": ["views", "contacts"],
            "period_grouping": "day"
        }

        mock_stats = {
            "items": [
                {"item_id": 12345, "stats": {"views": 100, "contacts": 5}},
                {"item_id": 67890, "stats": {"views": 80, "contacts": 3}}
            ],
            "period_grouping": "day"
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.client.get_item_stats.return_value = mock_stats
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post("/avito/items/stats", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2

    async def test_get_analytics_success(self, async_client: AsyncClient):
        """Тест успешного получения аналитики"""
        request_data = {
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
            "metrics": ["views", "contacts", "favorites"],
            "grouping": "day"
        }

        mock_analytics = {
            "metrics": {
                "views": {"total": 1250, "avg": 40.3},
                "contacts": {"total": 45, "avg": 1.5},
                "favorites": {"total": 23, "avg": 0.7}
            },
            "grouping": "day",
            "period": {"from": "2024-01-01", "to": "2024-01-31"}
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.client.get_analytics.return_value = mock_analytics
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post("/avito/analytics", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data
            assert "views" in data["metrics"]
            assert "contacts" in data["metrics"]

    async def test_get_vas_prices_success(self, async_client: AsyncClient):
        """Тест успешного получения цен на услуги продвижения"""
        item_id = 12345
        mock_prices = {
            "vas_services": [
                {"slug": "premium", "name": "Премиум", "price": 150, "currency": "RUB"},
                {"slug": "highlight", "name": "Выделение", "price": 50, "currency": "RUB"}
            ]
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_promotion_options.return_value = mock_prices["vas_services"]
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get(f"/avito/items/{item_id}/vas-prices")

            assert response.status_code == 200
            data = response.json()
            assert "prices" in data
            assert isinstance(data["prices"], list)

    async def test_apply_vas_success(self, async_client: AsyncClient):
        """Тест успешного применения услуг продвижения"""
        item_id = 12345
        request_data = {
            "slugs": ["premium", "highlight"],
            "stickers": ["new", "discount"]
        }

        mock_result = {
            "operation_id": "op_123456",
            "status": "applied",
            "services": request_data["slugs"],
            "stickers": request_data["stickers"]
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.client.apply_vas.return_value = mock_result
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post(f"/avito/items/{item_id}/vas", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["operation_id"] == "op_123456"
            assert data["status"] == "applied"

    async def test_update_item_price_success(self, async_client: AsyncClient):
        """Тест успешного обновления цены объявления"""
        item_id = 12345
        new_price = 2000

        mock_result = {
            "item_id": item_id,
            "new_price": new_price,
            "old_price": 1500,
            "updated_at": "2024-01-15T10:00:00Z"
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_item_price.return_value = mock_result
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.put(
                f"/avito/items/{item_id}/price",
                json={"price": new_price}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["new_price"] == new_price
            assert data["item_id"] == item_id

    async def test_optimize_item_price_success(self, async_client: AsyncClient):
        """Тест успешной оптимизации цены"""
        item_id = 12345

        mock_recommendation = {
            "item_id": item_id,
            "current_price": 1500,
            "recommended_price": 1800,
            "confidence": 0.85,
            "reasoning": "На основе анализа конкурентов и просмотров",
            "expected_improvement": {
                "contacts_increase": 25,
                "conversion_improvement": 15
            }
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.optimize_ad_pricing.return_value = mock_recommendation
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post(f"/avito/items/{item_id}/optimize-price")

            assert response.status_code == 200
            data = response.json()
            assert data["recommended_price"] == 1800
            assert data["confidence"] == 0.85
            assert "expected_improvement" in data

    async def test_promote_item_success(self, async_client: AsyncClient):
        """Тест успешного применения продвижения"""
        item_id = 12345
        request_data = {
            "service_slug": "premium",
            "stickers": ["new"]
        }

        mock_result = {
            "operation_id": "promo_123456",
            "service_slug": "premium",
            "status": "applied",
            "stickers": ["new"]
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.apply_promotion_service.return_value = mock_result
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post(f"/avito/items/{item_id}/promote", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["operation_id"] == "promo_123456"
            assert data["service_slug"] == "premium"
            assert data["status"] == "applied"

    async def test_get_calls_stats_success(self, async_client: AsyncClient):
        """Тест успешного получения статистики звонков"""
        request_data = {
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
            "item_ids": [12345, 67890]
        }

        mock_stats = {
            "calls": {
                "total": 25,
                "answered": 18,
                "missed": 7,
                "avg_duration": 180
            },
            "items": [
                {"item_id": 12345, "calls": 15, "answered": 12},
                {"item_id": 67890, "calls": 10, "answered": 6}
            ],
            "period": {"from": "2024-01-01", "to": "2024-01-31"}
        }

        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.client.get_calls_stats.return_value = mock_stats
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.post("/avito/calls/stats", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "calls" in data
            assert data["calls"]["total"] == 25
            assert "items" in data

    async def test_handle_incoming_message_success(self, async_client: AsyncClient):
        """Тест успешной обработки входящего сообщения"""
        message_data = {
            "chat_id": "chat_123",
            "user_id": "user_456",
            "message": {
                "text": "Здравствуйте, футболка еще в наличии?",
                "timestamp": "2024-01-15T10:00:00Z"
            },
            "item_id": 12345
        }

        mock_result = {
            "success": True,
            "communication_id": 789,
            "intent": "question",
            "ai_response": "Да, футболка в наличии. Могу оформить заказ."
        }

        with patch("src.aicrm.api.routers.avito.AvitoCommunicationHandler") as mock_handler_class:
            mock_handler = MagicMock()
            mock_handler.handle_incoming_message.return_value = mock_result
            mock_handler_class.return_value = mock_handler

            response = await async_client.post("/avito/messages/incoming", json=message_data)

            assert response.status_code == 200
            data = response.json()
            assert data["communication_id"] == 789

    async def test_health_check(self, async_client: AsyncClient):
        """Тест проверки работоспособности"""
        response = await async_client.get("/avito/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "avito_integration"

    async def test_rate_limit_error(self, async_client: AsyncClient):
        """Тест ошибки превышения лимита запросов"""
        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            from src.aicrm.services.avito_service import AvitoRateLimitError
            mock_service = MagicMock()
            mock_service.get_active_items.side_effect = AvitoRateLimitError("Rate limit exceeded")
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get("/avito/items")

            assert response.status_code == 429
            assert "лимит" in response.json()["detail"].lower()

    async def test_api_error(self, async_client: AsyncClient):
        """Тест общей ошибки API"""
        with patch("src.aicrm.api.routers.avito.AvitoService") as mock_service_class:
            from src.aicrm.services.avito_service import AvitoAPIError
            mock_service = MagicMock()
            mock_service.get_active_items.side_effect = AvitoAPIError("API temporarily unavailable")
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None

            response = await async_client.get("/avito/items")

            assert response.status_code == 500
            assert "API temporarily unavailable" in response.json()["detail"]

    async def test_validation_error(self, async_client: AsyncClient):
        """Тест ошибки валидации данных"""
        # Неправильные данные для статистики
        request_data = {
            "item_ids": [],  # Пустой список
            "date_from": "invalid-date",
            "date_to": "2024-01-31"
        }

        response = await async_client.post("/avito/items/stats", json=request_data)

        assert response.status_code == 422  # Validation error

    async def test_get_chats_success(self, async_client: AsyncClient):
        """Тест успешного получения списка чатов"""
        mock_chats = [
            {
                "chat_id": "chat_1",
                "customer_name": "Иван Иванов",
                "last_message": "Когда будет готов заказ?",
                "last_message_at": "2024-01-15T10:00:00Z",
                "message_count": 5,
                "ai_enabled": True,
                "unread_count": 0
            },
            {
                "chat_id": "chat_2",
                "customer_name": "Петр Петров",
                "last_message": "Спасибо за информацию",
                "last_message_at": "2024-01-14T15:30:00Z",
                "message_count": 3,
                "ai_enabled": False,
                "unread_count": 1
            }
        ]

        with patch("src.aicrm.api.routers.avito.db") as mock_db:
            mock_db.query.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

            # Мокаем чаты с настройками
            mock_chat_settings = []
            for chat in mock_chats:
                mock_setting = MagicMock()
                mock_setting.chat_id = chat["chat_id"]
                mock_setting.customer.name = chat["customer_name"]
                mock_setting.last_message_at = None
                mock_setting.message_count = chat["message_count"]
                mock_setting.ai_enabled = chat["ai_enabled"]
                mock_chat_settings.append(mock_setting)

            mock_db.query.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_chat_settings

            response = await async_client.get("/avito/messenger/chats")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_get_messenger_stats_success(self, async_client: AsyncClient):
        """Тест успешного получения статистики мессенджера"""
        mock_stats = {
            "total_chats": 25,
            "active_chats": 18,
            "ai_enabled_chats": 12,
            "total_messages": 450,
            "ai_messages": 180,
            "avg_response_time": 300
        }

        with patch("src.aicrm.api.routers.avito.db") as mock_db:
            # Мокаем запросы к БД
            mock_db.query.return_value.count.return_value = 25  # total_chats
            mock_db.query.return_value.filter.return_value.count.side_effect = [18, 12]  # active_chats, ai_enabled_chats
            mock_db.query.return_value.filter.return_value.all.return_value = []  # messages

            response = await async_client.get("/avito/messenger/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_chats" in data
            assert "active_chats" in data
            assert "ai_enabled_chats" in data
            assert "total_messages" in data
            assert "ai_messages" in data
