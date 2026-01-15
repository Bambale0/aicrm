"""
Юнит-тесты для Avito Messenger функциональности
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aicrm.api.routers.avito import (
    _calculate_average_response_time,
    _count_unread_messages,
)


class TestAvitoMessengerUtils:
    """Тесты для вспомогательных функций Avito Messenger"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_count_unread_messages_no_unread(self, mock_db):
        """Тест подсчета непрочитанных сообщений - нет непрочитанных"""
        # Мокаем цепочку вызовов БД так, чтобы count() возвращал 0
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = (
            0
        )

        result = await _count_unread_messages("chat_123", mock_db)

        assert result == 0

    @pytest.mark.asyncio
    async def test_count_unread_messages_with_unread(self, mock_db):
        """Тест подсчета непрочитанных сообщений - есть непрочитанные"""
        # Мокаем цепочку вызовов БД
        mock_count = MagicMock(return_value=3)
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.count = (
            mock_count
        )

        result = await _count_unread_messages("chat_123", mock_db)

        assert result == 3
        mock_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_unread_messages_error(self, mock_db):
        """Тест подсчета непрочитанных сообщений - ошибка БД"""
        # Мокаем ошибку БД
        mock_db.query.side_effect = Exception("Database error")

        result = await _count_unread_messages("chat_123", mock_db)

        assert result == 0  # Возвращает 0 при ошибке

    @pytest.mark.asyncio
    async def test_calculate_average_response_time_no_data(self, mock_db):
        """Тест расчета среднего времени ответа - нет данных"""
        # Мокаем пустой результат запроса
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = await _calculate_average_response_time(mock_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_average_response_time_with_data(self, mock_db):
        """Тест расчета среднего времени ответа - есть данные"""
        # Создаем мок сообщения
        base_time = datetime.utcnow()

        # Мокаем сообщения в одном чате
        mock_messages = []
        for i in range(4):
            mock_msg = MagicMock()
            mock_msg.extra_data = {"chat_id": "chat_123"}
            mock_msg.direction = "inbound" if i % 2 == 0 else "outbound"
            mock_msg.created_at = base_time + timedelta(
                minutes=i * 10
            )  # 0, 10, 20, 30 мин
            mock_messages.append(mock_msg)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_messages
        )

        result = await _calculate_average_response_time(mock_db)

        # Ожидаемое среднее время: (10 + 10) / 2 / 60 = 10/60 ≈ 0.167 мин
        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculate_average_response_time_multiple_chats(self, mock_db):
        """Тест расчета среднего времени ответа - несколько чатов"""
        base_time = datetime.utcnow()

        # Мокаем сообщения в двух чатах
        mock_messages = []

        # Чат 1: 2 пары сообщений
        for i in range(4):
            mock_msg = MagicMock()
            mock_msg.extra_data = {
                "chat_id": f"chat_{i//4 + 1}"
            }  # chat_1 для первых 4, chat_2 для следующих
            mock_msg.direction = "inbound" if i % 2 == 0 else "outbound"
            mock_msg.created_at = base_time + timedelta(minutes=i * 5)
            mock_messages.append(mock_msg)

        # Чат 2: 2 пары сообщений
        for i in range(4, 8):
            mock_msg = MagicMock()
            mock_msg.extra_data = {"chat_id": "chat_2"}
            mock_msg.direction = "inbound" if (i - 4) % 2 == 0 else "outbound"
            mock_msg.created_at = base_time + timedelta(minutes=i * 5)
            mock_messages.append(mock_msg)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_messages
        )

        result = await _calculate_average_response_time(mock_db)

        assert result is not None
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_average_response_time_long_responses_filtered(
        self, mock_db
    ):
        """Тест расчета среднего времени ответа - фильтрация слишком длинных ответов"""
        base_time = datetime.utcnow()

        # Создаем сообщения с очень длинным временем ответа (>24 часов)
        mock_messages = []
        for i in range(2):
            mock_msg = MagicMock()
            mock_msg.extra_data = {"chat_id": "chat_123"}
            mock_msg.direction = "inbound" if i % 2 == 0 else "outbound"
            if i == 0:
                mock_msg.created_at = base_time
            else:
                mock_msg.created_at = base_time + timedelta(hours=25)  # Слишком долго
            mock_messages.append(mock_msg)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_messages
        )

        result = await _calculate_average_response_time(mock_db)

        # Должен вернуть None, так как единственный ответ слишком длинный
        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_average_response_time_error(self, mock_db):
        """Тест расчета среднего времени ответа - ошибка БД"""
        # Мокаем ошибку БД
        mock_db.query.side_effect = Exception("Database error")

        result = await _calculate_average_response_time(mock_db)

        assert result is None


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

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_messages
        )

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
                    "created": "2024-01-15T10:00:00Z",
                }
            ]
        }

        with patch.object(
            handler.avito_service, "get_avito_messages", new_callable=AsyncMock
        ) as mock_api:
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

        with patch.object(
            handler.avito_service, "get_avito_messages", new_callable=AsyncMock
        ) as mock_api:
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
                    "created": "2024-01-15T10:00:00Z",
                }
            ]
        }

        # Мокаем, что сообщение не существует в БД
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Мокаем настройки чата
        mock_chat_settings = MagicMock()
        mock_chat_settings.customer = MagicMock()
        mock_chat_settings.customer.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_chat_settings
        )

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
                    "created": "2024-01-15T10:00:00Z",
                }
            ]
        }

        # Мокаем, что сообщение уже существует
        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing
        )

        await handler._sync_messages_from_api(chat_id, api_messages)

        # Проверяем, что add НЕ был вызван
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_mark_messages_read_success(self, handler, mock_db):
        """Тест отметки сообщений как прочитанные - успех"""
        chat_id = "chat_123"

        # Мокаем успешный ответ API
        with patch.object(
            handler.avito_service, "mark_avito_chat_read", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = {"success": True}

            # Мокаем сообщения в БД
            mock_messages = [MagicMock() for _ in range(2)]
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
                mock_messages
            )

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

        with patch.object(
            handler.avito_service, "mark_avito_chat_read", new_callable=AsyncMock
        ) as mock_api:
            mock_api.side_effect = Exception("API Error")

            result = await handler.mark_messages_read(chat_id, [])

            assert result is False
