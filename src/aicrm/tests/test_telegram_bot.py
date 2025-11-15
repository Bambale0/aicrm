"""
Тесты для Telegram бота
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from ..models.telegram_chat import TelegramChat
from ..models.customer import Customer
from ..models.order import Order
from ..services.telegram_bot_service import TelegramBotService
from ..services.telegram_order_service import TelegramOrderService
from ..core.config import settings


class TestTelegramBotService:
    """Тесты сервиса Telegram бота"""

    @pytest.fixture
    def db_session(self):
        """Фикстура для сессии БД"""
        return Mock(spec=Session)

    @pytest.fixture
    def bot_service(self, db_session):
        """Фикстура для сервиса бота"""
        return TelegramBotService(db_session)

    @pytest.fixture
    def sample_chat(self):
        """Фикстура для тестового чата"""
        return TelegramChat(
            id=1,
            chat_id="123456789",
            chat_type="private",
            username="testuser",
            first_name="Test",
            last_name="User",
            customer_id=1
        )

    @pytest.fixture
    def sample_customer(self):
        """Фикстура для тестового клиента"""
        return Customer(
            id=1,
            name="Test Customer",
            email="test@example.com",
            total_orders=5
        )

    def test_initialization_without_token(self, db_session):
        """Тест инициализации без токена"""
        with patch.object(settings, 'telegram_bot_token', None):
            service = TelegramBotService(db_session)
            success = service.initialize_bot()
            assert not success

    @pytest.mark.asyncio
    async def test_get_or_create_chat_new(self, bot_service, db_session, sample_chat):
        """Тест создания нового чата"""
        # Мокаем запросы к БД
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Мокаем Telegram объекты
        mock_chat = Mock()
        mock_chat.id = 123456789
        mock_chat.type = "private"

        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"

        # Вызываем метод
        result = await bot_service._get_or_create_chat(mock_chat, mock_user)

        # Проверяем результат
        assert result.chat_id == "123456789"
        assert result.chat_type == "private"
        assert result.username == "testuser"
        assert result.first_name == "Test"
        assert result.last_name == "User"

        # Проверяем, что чат был добавлен в БД
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_chat_existing(self, bot_service, db_session, sample_chat):
        """Тест получения существующего чата"""
        # Мокаем запрос к БД - чат найден
        db_session.query.return_value.filter.return_value.first.return_value = sample_chat

        mock_chat = Mock()
        mock_chat.id = 123456789

        mock_user = Mock()

        # Вызываем метод
        result = await bot_service._get_or_create_chat(mock_chat, mock_user)

        # Проверяем результат
        assert result == sample_chat
        assert result.chat_id == "123456789"

        # Проверяем, что новый чат не был добавлен
        db_session.add.assert_not_called()

    def test_get_bot_stats(self, bot_service, db_session):
        """Тест получения статистики бота"""
        # Мокаем запросы к БД
        db_session.query.return_value.count.side_effect = [10, 7, 150]  # chats, active, messages

        with patch.object(bot_service, 'application', Mock()):
            stats = bot_service.get_bot_stats()

        assert stats["total_chats"] == 10
        assert stats["active_chats"] == 7
        assert stats["total_messages"] == 150
        assert stats["bot_running"] is True

    @pytest.mark.asyncio
    async def test_send_message_success(self, bot_service):
        """Тест успешной отправки сообщения"""
        # Мокаем бота
        mock_bot = AsyncMock()
        bot_service.bot = mock_bot

        # Мокаем чат
        mock_chat = Mock()
        mock_chat.customer_id = 1
        bot_service._get_chat_by_id = AsyncMock(return_value=mock_chat)
        bot_service._log_communication = AsyncMock()

        success = await bot_service.send_message_to_chat("123456789", "Test message")

        assert success
        mock_bot.send_message.assert_called_once_with(chat_id="123456789", text="Test message")
        bot_service._log_communication.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self, bot_service):
        """Тест неудачной отправки сообщения"""
        # Бот не инициализирован
        bot_service.bot = None

        success = await bot_service.send_message_to_chat("123456789", "Test message")

        assert not success


class TestTelegramOrderService:
    """Тесты сервиса заказов Telegram"""

    @pytest.fixture
    def db_session(self):
        """Фикстура для сессии БД"""
        return Mock(spec=Session)

    @pytest.fixture
    def order_service(self, db_session):
        """Фикстура для сервиса заказов"""
        return TelegramOrderService(db_session)

    @pytest.fixture
    def sample_customer(self):
        """Фикстура для тестового клиента"""
        return Customer(
            id=1,
            name="Test Customer",
            email="test@example.com"
        )

    @pytest.fixture
    def sample_chat(self, sample_customer):
        """Фикстура для тестового чата"""
        return TelegramChat(
            id=1,
            chat_id="123456789",
            customer_id=sample_customer.id
        )

    @pytest.mark.asyncio
    async def test_process_order_request_success(self, order_service, db_session, sample_chat, sample_customer):
        """Тест успешной обработки запроса на заказ"""
        # Мокаем БД запросы
        db_session.query.return_value.filter.return_value.first.side_effect = [sample_customer, sample_customer]

        # Мокаем AI сервис
        order_service.ai_service.ai_client.chat_completion = AsyncMock(return_value='{"has_order_intent": true, "order_data": {"product_type": "футболка", "quantity": 5, "size": "M", "color": "черный"}, "confidence": 0.9, "missing_info": []}')

        # Мокаем создание заказа
        mock_order = Mock()
        mock_order.id = 123
        order_service._create_order_from_data = AsyncMock(return_value=mock_order)
        order_service._generate_order_confirmation_message = Mock(return_value="Заказ создан!")

        message = "Хочу заказать 5 черных футболок размера M"

        result = await order_service.process_order_request(message, sample_chat)

        assert result["success"] is True
        assert result["order_id"] == 123
        assert result["action"] == "order_created"

    @pytest.mark.asyncio
    async def test_process_order_request_no_customer(self, order_service, sample_chat):
        """Тест обработки заказа без зарегистрированного клиента"""
        sample_chat.customer_id = None

        message = "Хочу заказать футболку"

        result = await order_service.process_order_request(message, sample_chat)

        assert result["success"] is False
        assert result["action"] == "registration_required"

    @pytest.mark.asyncio
    async def test_process_order_request_no_order_intent(self, order_service, db_session, sample_chat, sample_customer):
        """Тест обработки сообщения без намерения заказа"""
        # Мокаем БД запросы
        db_session.query.return_value.filter.return_value.first.side_effect = [sample_customer, sample_customer]

        # Мокаем AI сервис - нет намерения заказа
        order_service.ai_service.ai_client.chat_completion = AsyncMock(return_value='{"has_order_intent": false, "order_data": {}, "confidence": 0, "missing_info": []}')

        message = "Привет, как дела?"

        result = await order_service.process_order_request(message, sample_chat)

        assert result["success"] is False
        assert result["action"] == "clarification_needed"

    def test_calculate_base_price(self, order_service):
        """Тест расчета базовой цены"""
        # Футболка
        item = {"product_type": "футболка"}
        price = order_service._calculate_base_price(item)
        assert price == 500

        # Худи
        item = {"product_type": "худи"}
        price = order_service._calculate_base_price(item)
        assert price == 1200

        # Неизвестный товар
        item = {"product_type": "неизвестный"}
        price = order_service._calculate_base_price(item)
        assert price == 500  # цена по умолчанию

    def test_generate_order_confirmation_message(self, order_service):
        """Тест генерации сообщения подтверждения заказа"""
        mock_order = Mock()
        mock_order.id = 123
        mock_order.items = '[{"product_type": "футболка", "quantity": 2, "size": "L", "color": "синий"}]'
        mock_order.total_amount = 1000
        mock_order.status_display = "Ожидает обработки"
        mock_order.deadline = None

        message = order_service._generate_order_confirmation_message(mock_order)

        assert "✅ Заказ №123 успешно создан!" in message
        assert "футболка" in message
        assert "2" in message
        assert "L" in message
        assert "синий" in message
        assert "1000 ₽" in message

    @pytest.mark.asyncio
    async def test_get_customer_orders_summary(self, order_service, db_session, sample_chat, sample_customer):
        """Тест получения сводки заказов клиента"""
        # Мокаем БД запросы
        db_session.query.return_value.filter.return_value.first.side_effect = [sample_customer, sample_customer]

        mock_orders = [
            Mock(id=1, status=Mock(display="Ожидает обработки"), total_amount=500, created_at=Mock(strftime=Mock(return_value="01.01.2024"))),
            Mock(id=2, status=Mock(display="Готов"), total_amount=1200, created_at=Mock(strftime=Mock(return_value="02.01.2024")))
        ]
        db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_orders

        summary = await order_service.get_customer_orders_summary(sample_chat)

        assert "📋 Ваши заказы (2):" in summary
        assert "#1" in summary
        assert "#2" in summary
        assert "500 ₽" in summary
        assert "1200 ₽" in summary

    @pytest.mark.asyncio
    async def test_get_customer_orders_summary_no_customer(self, order_service, sample_chat):
        """Тест получения сводки заказов для незарегистрированного клиента"""
        sample_chat.customer_id = None

        summary = await order_service.get_customer_orders_summary(sample_chat)

        assert "не зарегистрированы" in summary
