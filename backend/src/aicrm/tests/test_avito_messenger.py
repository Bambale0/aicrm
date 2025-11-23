"""
Юнит-тесты для Avito Messenger функциональности
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

# from src.aicrm.api.routers.avito import _count_unread_messages, _calculate_average_response_time  # Functions not implemented yet


# Temporarily disabled - functions not implemented yet
# class TestAvitoMessengerUtils:
#     """Тесты для вспомогательных функций Avito Messenger"""


class TestAvitoCommunicationHandlerMessenger:
    """Тесты для методов AvitoCommunicationHandler связанных с мессенджером"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_db):
        """Фикстура для AvitoCommunicationHandler"""
        from src.aicrm.services.avito_handler import AvitoCommunicationHandler
        return AvitoCommunicationHandler(mock_db)

    @pytest.mark.asyncio
    async def test_get_chat_history_from_db(self, handler, mock_db):
        """Тест получения истории чата из базы данных"""
        chat_id = "chat_123"

        # Мокаем сообщения в БД
        mock_messages = []
        for i in range(3):
            mock_msg = MagicMock()
            mock_msg.id = i + 1
            mock_msg.direction = "inbound" if i % 2 == 0 else "outbound"
            mock_msg.message_content = f"Message {i + 1}"
            mock_msg.created_at = datetime.utcnow() - timedelta(minutes=i * 10)
            mock_msg.intent = "question" if i % 2 == 0 else None
            mock_messages.append(mock_msg)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_messages

        result = await handler.get_chat_history(chat_id, limit=10, use_api=False)

        assert len(result) == 3
        assert result[0]["direction"] == "inbound"
        assert result[0]["message"] == "Message 1"
        assert result[0]["from_api"] is False

    @pytest.mark.asyncio
    async def test_get_chat_history_from_api(self, handler, mock_db):
        """Тест получения истории чата из Avito API"""
        chat_id = "chat_123"

        # Мокаем API ответ
        api_messages = {
            "messages": [
                {
                    "id": "msg_1",
                    "direction": "inbound",
                    "content": {"text": "Hello from API"},
                    "created": "2024-01-15T10:00:00Z"
                }
            ]
        }

        with patch.object(handler.avito_service, 'get_avito_messages', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = api_messages

            result = await handler.get_chat_history(chat_id, limit=10, use_api=True)

            assert len(result) == 1
            assert result[0]["id"] == "msg_1"
            assert result[0]["direction"] == "outbound"  # inbound -> outbound mapping
            assert result[0]["message"] == "Hello from API"
            assert result[0]["from_api"] is True

    @pytest.mark.asyncio
    async def test_get_chat_history_api_error(self, handler, mock_db):
        """Тест получения истории чата - ошибка API"""
        chat_id = "chat_123"

        with patch.object(handler.avito_service, 'get_avito_messages', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")

            result = await handler.get_chat_history(chat_id, limit=10, use_api=True)

            assert result == []  # Возвращает пустой список при ошибке

    @pytest.mark.asyncio
    async def test_sync_messages_from_api(self, handler, mock_db):
        """Тест синхронизации сообщений из API с БД"""
        chat_id = "chat_123"

        # Мокаем API сообщения
        api_messages = {
            "messages": [
                {
                    "id": "msg_1",
                    "direction": "inbound",
                    "content": {"text": "New message"},
                    "created": "2024-01-15T10:00:00Z"
                }
            ]
        }

        # Мокаем, что сообщение не существует в БД
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Мокаем настройки чата
        mock_chat_settings = MagicMock()
        mock_chat_settings.customer = MagicMock()
        mock_chat_settings.customer.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_chat_settings

        await handler._sync_messages_from_api(chat_id, api_messages)

        # Проверяем, что add был вызван
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_messages_from_api_existing_message(self, handler, mock_db):
        """Тест синхронизации сообщений - сообщение уже существует"""
        chat_id = "chat_123"

        api_messages = {
            "messages": [
                {
                    "id": "msg_1",
                    "direction": "inbound",
                    "content": {"text": "Existing message"},
                    "created": "2024-01-15T10:00:00Z"
                }
            ]
        }

        # Мокаем, что сообщение уже существует
        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        await handler._sync_messages_from_api(chat_id, api_messages)

        # Проверяем, что add НЕ был вызван
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_mark_messages_read_success(self, handler, mock_db):
        """Тест отметки сообщений как прочитанные - успех"""
        chat_id = "chat_123"

        # Мокаем успешный ответ API
        with patch.object(handler.avito_service, 'mark_avito_chat_read', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"success": True}

            # Мокаем сообщения в БД
            mock_messages = [MagicMock() for _ in range(2)]
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = mock_messages

            result = await handler.mark_messages_read(chat_id, [])

            assert result is True

            # Проверяем, что сообщения обновлены
            for msg in mock_messages:
                assert msg.extra_data["read"] is True

            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_messages_read_api_error(self, handler, mock_db):
        """Тест отметки сообщений как прочитанные - ошибка API"""
        chat_id = "chat_123"

        with patch.object(handler.avito_service, 'mark_avito_chat_read', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")

            result = await handler.mark_messages_read(chat_id, [])

            assert result is False
