"""
Unit тесты для TelegramBotService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from ..services.telegram_bot_service import TelegramBotService


class TestTelegramBotService:
    """Тесты для сервиса Telegram бота"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def bot_service(self, mock_db):
        """Сервис Telegram бота с моками"""
        return TelegramBotService(mock_db)

    @pytest.mark.asyncio
    async def test_initialize_bot_success(self, bot_service, mock_db):
        """Тест успешной инициализации бота"""
        with patch("src.aicrm.services.telegram_bot_service.settings") as mock_settings, \
             patch("telegram.Application.builder") as mock_builder:

            mock_settings.telegram_bot_token = "test_token"
            mock_app = MagicMock()
            mock_builder.return_value.token.return_value.request.return_value.build.return_value = mock_app

            result = await bot_service.initialize_bot()

        assert result is True
        assert bot_service.application == mock_app

    @pytest.mark.asyncio
    async def test_initialize_bot_no_token(self, bot_service, mock_db):
        """Тест инициализации бота без токена"""
        with patch("src.aicrm.services.telegram_bot_service.settings") as mock_settings:
            mock_settings.telegram_bot_token = None

            result = await bot_service.initialize_bot()

        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_bot_already_initialized(self, bot_service, mock_db):
        """Тест инициализации уже инициализированного бота"""
        bot_service.application = MagicMock()

        result = await bot_service.initialize_bot()

        assert result is True

    @pytest.mark.asyncio
    async def test_start_polling_success(self, bot_service, mock_db):
        """Тест успешного запуска polling"""
        mock_app = MagicMock()
        mock_updater = MagicMock()
        mock_app.updater = mock_updater
        bot_service.application = mock_app

        with patch.object(mock_app, "initialize", new_callable=AsyncMock), \
             patch.object(mock_app, "start", new_callable=AsyncMock), \
             patch.object(mock_updater, "start_polling", new_callable=AsyncMock):

            await bot_service.start_polling()

        mock_app.initialize.assert_called_once()
        mock_app.start.assert_called_once()
        mock_updater.start_polling.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_polling_no_application(self, bot_service, mock_db):
        """Тест запуска polling без инициализированного приложения"""
        bot_service.application = None

        with pytest.raises(AttributeError):
            await bot_service.start_polling()

    @pytest.mark.asyncio
    async def test_stop_bot(self, bot_service, mock_db):
        """Тест остановки бота"""
        mock_app = MagicMock()
        mock_updater = MagicMock()
        mock_app.updater = mock_updater
        bot_service.application = mock_app

        with patch.object(mock_app, "stop", new_callable=AsyncMock), \
             patch.object(mock_app, "shutdown", new_callable=AsyncMock), \
             patch.object(mock_updater, "stop", new_callable=AsyncMock):

            await bot_service.stop_bot()

        mock_updater.stop.assert_called_once()
        mock_app.stop.assert_called_once()
        mock_app.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_start_command(self, bot_service, mock_db):
        """Тест обработки команды /start"""
        # Мокаем объекты Telegram
        mock_update = MagicMock()
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_user = MagicMock()
        mock_user.first_name = "John"
        mock_message = MagicMock()

        mock_update.effective_chat = mock_chat
        mock_update.effective_user = mock_user
        mock_update.message = mock_message

        # Мокаем создание чата
        mock_telegram_chat = MagicMock()
        mock_telegram_chat.customer_id = 1

        with patch.object(bot_service, "_get_or_create_chat", new_callable=AsyncMock) as mock_get_chat, \
             patch.object(bot_service, "_log_communication", new_callable=AsyncMock) as mock_log:

            mock_get_chat.return_value = mock_telegram_chat

            await bot_service._handle_start(mock_update, None)

        mock_message.reply_text.assert_called_once()
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message(self, bot_service, mock_db):
        """Тест обработки текстового сообщения"""
        # Мокаем объекты
        mock_update = MagicMock()
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_user = MagicMock()
        mock_message = MagicMock()
        mock_message.text = "Hello bot"

        mock_update.effective_chat = mock_chat
        mock_update.effective_user = mock_user
        mock_update.message = mock_message

        # Мокаем AI результат
        ai_result = {
            "intent": "greeting",
            "response": "Hello human!",
            "needs_human_intervention": False
        }

        mock_telegram_chat = MagicMock()
        mock_telegram_chat.customer_id = 1

        with patch.object(bot_service, "_get_or_create_chat", new_callable=AsyncMock) as mock_get_chat, \
             patch.object(bot_service, "_process_with_ai", new_callable=AsyncMock) as mock_process_ai, \
             patch.object(bot_service, "_log_communication", new_callable=AsyncMock) as mock_log, \
             patch.object(bot_service, "_handle_ai_actions", new_callable=AsyncMock) as mock_handle_actions:

            mock_get_chat.return_value = mock_telegram_chat
            mock_process_ai.return_value = ai_result

            await bot_service._handle_message(mock_update, None)

        mock_message.reply_text.assert_called_once_with("Hello human!")
        assert mock_log.call_count == 2  # Входящее и исходящее сообщения

    @pytest.mark.asyncio
    async def test_handle_message_ai_error(self, bot_service, mock_db):
        """Тест обработки сообщения с ошибкой AI"""
        mock_update = MagicMock()
        mock_chat = MagicMock()
        mock_message = MagicMock()
        mock_message.text = "Test"

        mock_update.effective_chat = mock_chat
        mock_update.message = mock_message

        mock_telegram_chat = MagicMock()

        with patch.object(bot_service, "_get_or_create_chat", new_callable=AsyncMock) as mock_get_chat, \
             patch.object(bot_service, "_process_with_ai", new_callable=AsyncMock) as mock_process_ai:

            mock_get_chat.return_value = mock_telegram_chat
            mock_process_ai.side_effect = Exception("AI failed")

            await bot_service._handle_message(mock_update, None)

        # Должно отправить сообщение об ошибке
        mock_message.reply_text.assert_called_once()
        error_text = mock_message.reply_text.call_args[0][0]
        assert "ошибка" in error_text.lower()

    @pytest.mark.asyncio
    async def test_process_with_ai(self, bot_service, mock_db):
        """Тест обработки сообщения через AI"""
        message = "Hello"
        customer_id = 1

        expected_result = {
            "intent": "greeting",
            "response": "Hi there!",
            "confidence": 0.9
        }

        with patch.object(bot_service.ai_service, "process_customer_message", new_callable=AsyncMock) as mock_ai, \
             patch.object(bot_service, "_get_customer_context", new_callable=AsyncMock) as mock_context:

            mock_ai.return_value = expected_result
            mock_context.return_value = {"customer_name": "John"}

            result = await bot_service._process_with_ai(message, customer_id)

        assert result == expected_result
        mock_ai.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_chat_new(self, bot_service, mock_db):
        """Тест создания нового чата"""
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_chat.type = "private"
        mock_chat.title = None

        mock_user = MagicMock()
        mock_user.username = "john_doe"
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"

        # Мокаем поиск существующего чата
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Чат не найден

        # Мокаем создание нового чата
        mock_telegram_chat = MagicMock()
        mock_telegram_chat.id = 1
        mock_telegram_chat.customer_id = None

        with patch("src.aicrm.services.telegram_bot_service.TelegramChat", return_value=mock_telegram_chat), \
             patch.object(bot_service, "_find_customer_by_telegram_data", new_callable=AsyncMock) as mock_find_customer:

            mock_find_customer.return_value = None

            result = await bot_service._get_or_create_chat(mock_chat, mock_user)

        assert result == mock_telegram_chat
        mock_db.add.assert_called_once_with(mock_telegram_chat)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_chat_existing(self, bot_service, mock_db):
        """Тест получения существующего чата"""
        mock_chat = MagicMock()
        mock_chat.id = 123

        mock_user = MagicMock()

        # Мокаем найденный чат
        mock_existing_chat = MagicMock()
        mock_existing_chat.id = 1

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing_chat

        result = await bot_service._get_or_create_chat(mock_chat, mock_user)

        assert result == mock_existing_chat
        # Не должно создавать новый чат
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_customer_by_username(self, bot_service, mock_db):
        """Тест поиска клиента по username"""
        mock_user = MagicMock()
        mock_user.username = "john_doe"

        mock_customer = MagicMock()
        mock_customer.id = 1

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_customer]

        result = await bot_service._find_customer_by_telegram_data(mock_user)

        assert result == mock_customer

    @pytest.mark.asyncio
    async def test_find_customer_by_name(self, bot_service, mock_db):
        """Тест поиска клиента по имени"""
        mock_user = MagicMock()
        mock_user.username = None
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"

        mock_customer = MagicMock()
        mock_customer.id = 1

        # Мокаем запросы
        mock_query1 = MagicMock()
        mock_query1.filter.return_value = mock_query1
        mock_query1.all.return_value = []  # Не найден по username

        mock_query2 = MagicMock()
        mock_query2.filter.return_value = mock_query2
        mock_query2.first.return_value = mock_customer  # Найден по имени

        mock_db.query.side_effect = [mock_query1, mock_query2]

        result = await bot_service._find_customer_by_telegram_data(mock_user)

        assert result == mock_customer

    @pytest.mark.asyncio
    async def test_get_customer_context(self, bot_service, mock_db):
        """Тест получения контекста клиента"""
        customer_id = 1

        # Мокаем клиента и заказы
        mock_customer = MagicMock()
        mock_customer.name = "John Doe"
        mock_customer.total_orders = 5
        mock_customer.loyalty_level = "gold"

        mock_order = MagicMock()
        mock_order.id = 100
        mock_order.status = "completed"
        mock_order.total_amount = 1500.00

        mock_query_customer = MagicMock()
        mock_query_customer.filter.return_value = mock_query_customer
        mock_query_customer.first.return_value = mock_customer

        mock_query_orders = MagicMock()
        mock_query_orders.filter.return_value = mock_query_orders
        mock_query_orders.order_by.return_value = mock_query_orders
        mock_query_orders.limit.return_value = mock_query_orders
        mock_query_orders.all.return_value = [mock_order]

        mock_db.query.side_effect = [mock_query_customer, mock_query_orders]

        result = await bot_service._get_customer_context(customer_id)

        assert result["customer_name"] == "John Doe"
        assert result["total_orders"] == 5
        assert result["loyalty_level"] == "gold"
        assert len(result["recent_orders"]) == 1

    @pytest.mark.asyncio
    async def test_log_communication(self, bot_service, mock_db):
        """Тест логирования коммуникации"""
        chat_id = "123"
        message_content = "Test message"
        direction = "inbound"
        customer_id = 1

        # Мокаем чат
        mock_chat = MagicMock()
        mock_chat.message_count = 5

        with patch.object(bot_service, "_get_chat_by_id", new_callable=AsyncMock) as mock_get_chat, \
             patch("src.aicrm.services.telegram_bot_service.Communication") as mock_communication_class:

            mock_get_chat.return_value = mock_chat

            await bot_service._log_communication(
                chat_id, message_content, direction, customer_id
            )

        # Проверяем создание записи коммуникации
        mock_communication_class.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Проверяем обновление счетчика сообщений
        mock_chat.increment_message_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_to_chat_success(self, bot_service, mock_db):
        """Тест успешной отправки сообщения в чат"""
        chat_id = "123"
        message = "Test message"

        bot_service.bot = MagicMock()

        with patch.object(bot_service, "_get_chat_by_id", new_callable=AsyncMock) as mock_get_chat, \
             patch.object(bot_service, "_log_communication", new_callable=AsyncMock) as mock_log:

            mock_get_chat.return_value = None

            result = await bot_service.send_message_to_chat(chat_id, message)

        assert result is True
        bot_service.bot.send_message.assert_called_once_with(chat_id=chat_id, text=message)

    @pytest.mark.asyncio
    async def test_send_message_to_chat_no_bot(self, bot_service, mock_db):
        """Тест отправки сообщения без инициализированного бота"""
        bot_service.bot = None

        result = await bot_service.send_message_to_chat("123", "message")

        assert result is False

    def test_get_bot_stats(self, bot_service, mock_db):
        """Тест получения статистики бота"""
        # Мокаем запросы
        mock_query_chats = MagicMock()
        mock_query_chats.count.return_value = 10

        mock_query_active = MagicMock()
        mock_query_active.filter.return_value = mock_query_active
        mock_query_active.count.return_value = 8

        mock_query_messages = MagicMock()
        mock_query_messages.filter.return_value = mock_query_messages
        mock_query_messages.count.return_value = 150

        mock_db.query.side_effect = [mock_query_chats, mock_query_active, mock_query_messages]

        bot_service.application = MagicMock()

        result = bot_service.get_bot_stats()

        assert result["total_chats"] == 10
        assert result["active_chats"] == 8
        assert result["total_messages"] == 150
        assert result["bot_running"] is True

    @pytest.mark.asyncio
    async def test_handle_help_command(self, bot_service, mock_db):
        """Тест обработки команды /help"""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message

        await bot_service._handle_help(mock_update, None)

        mock_message.reply_text.assert_called_once()
        help_text = mock_message.reply_text.call_args[0][0]
        assert "/start" in help_text
        assert "/help" in help_text

    @pytest.mark.asyncio
    async def test_handle_orders_command(self, bot_service, mock_db):
        """Тест обработки команды /orders"""
        mock_update = MagicMock()
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_message = MagicMock()

        mock_update.effective_chat = mock_chat
        mock_update.message = mock_message

        mock_telegram_chat = MagicMock()

        with patch.object(bot_service, "_get_chat_by_id", new_callable=AsyncMock) as mock_get_chat, \
             patch.object(bot_service.order_service, "get_customer_orders_summary", new_callable=AsyncMock) as mock_orders:

            mock_get_chat.return_value = mock_telegram_chat
            mock_orders.return_value = "Your orders: Order #1 - Completed"

            await bot_service._handle_orders(mock_update, None)

        mock_orders.assert_called_once_with(mock_telegram_chat)
        mock_message.reply_text.assert_called_once_with("Your orders: Order #1 - Completed")

    @pytest.mark.asyncio
    async def test_handle_ai_actions_order_creation(self, bot_service, mock_db):
        """Тест обработки AI действий - создание заказа"""
        ai_result = {"intent": "order"}
        mock_telegram_chat = MagicMock()
        mock_update = MagicMock()

        with patch.object(bot_service, "_process_order_creation", new_callable=AsyncMock) as mock_process_order:
            mock_process_order.return_value = None

            await bot_service._handle_ai_actions(ai_result, mock_telegram_chat, mock_update)

        mock_process_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ai_actions_complaint(self, bot_service, mock_db):
        """Тест обработки AI действий - жалоба"""
        ai_result = {"intent": "complaint"}
        mock_telegram_chat = MagicMock()
        mock_update = MagicMock()

        with patch.object(bot_service, "_escalate_to_support", new_callable=AsyncMock) as mock_escalate:
            mock_escalate.return_value = None

            await bot_service._handle_ai_actions(ai_result, mock_telegram_chat, mock_update)

        mock_escalate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_order_creation_success(self, bot_service, mock_db):
        """Тест успешного создания заказа"""
        mock_telegram_chat = MagicMock()
        mock_update = MagicMock()
        message_text = "I want to order a t-shirt"

        with patch.object(bot_service.order_service, "process_order_request", new_callable=AsyncMock) as mock_process, \
             patch.object(bot_service, "_log_communication", new_callable=AsyncMock) as mock_log:

            mock_process.return_value = {
                "success": True,
                "message": "Order created successfully",
                "order_id": 123
            }

            await bot_service._process_order_creation(mock_telegram_chat, message_text, mock_update)

        mock_update.message.reply_text.assert_called_once_with("Order created successfully")
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_order_creation_failure(self, bot_service, mock_db):
        """Тест неудачного создания заказа"""
        mock_telegram_chat = MagicMock()
        mock_update = MagicMock()
        message_text = "Order something"

        with patch.object(bot_service.order_service, "process_order_request", new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Order creation failed")

            await bot_service._process_order_creation(mock_telegram_chat, message_text, mock_update)

        mock_update.message.reply_text.assert_called_once()
        error_text = mock_update.message.reply_text.call_args[0][0]
        assert "ошибка" in error_text.lower()

    @pytest.mark.asyncio
    async def test_suggest_order_creation_no_customer(self, bot_service, mock_db):
        """Тест предложения создания заказа - клиент не зарегистрирован"""
        mock_telegram_chat = MagicMock()
        mock_telegram_chat.customer_id = None
        mock_update = MagicMock()

        await bot_service._suggest_order_creation(mock_telegram_chat, mock_update)

        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "зарегистрироваться" in message.lower()

    @pytest.mark.asyncio
    async def test_suggest_order_creation_with_customer(self, bot_service, mock_db):
        """Тест предложения создания заказа - клиент зарегистрирован"""
        mock_telegram_chat = MagicMock()
        mock_telegram_chat.customer_id = 1
        mock_update = MagicMock()

        await bot_service._suggest_order_creation(mock_telegram_chat, mock_update)

        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "готов помочь" in message.lower()

    @pytest.mark.asyncio
    async def test_handle_error_network_error(self, bot_service, mock_db):
        """Тест обработки сетевой ошибки"""
        from telegram.error import NetworkError

        mock_update = MagicMock()
        mock_context = MagicMock()
        mock_context.error = NetworkError("Connection failed")

        await bot_service._handle_error(mock_update, mock_context)

        # Для сетевых ошибок не должно отправлять сообщение пользователю
        # (проверка через отсутствие вызова bot.send_message)

    @pytest.mark.asyncio
    async def test_handle_error_other_error(self, bot_service, mock_db):
        """Тест обработки других ошибок"""
        mock_update = MagicMock()
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_update.effective_chat = mock_chat

        mock_context = MagicMock()
        mock_context.error = Exception("Some error")
        mock_context.bot = MagicMock()

        with patch.object(mock_context.bot, "send_message", new_callable=AsyncMock):
            await bot_service._handle_error(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]["chat_id"] == 123
        assert "ошибка" in call_args[1]["text"].lower()
