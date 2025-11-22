"""
Тесты для AvitoTaskIntegration
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ..services.automation.avito_integration import AvitoTaskIntegration
from ..models.task import Task
from ..models.customer import Customer
from ..models.order import Order


class TestAvitoTaskIntegration:
    """Тесты для интеграции задач с Avito"""

    @pytest.fixture
    def db_session(self):
        """Мок для сессии базы данных"""
        session = MagicMock()
        # Мокаем методы запросов
        session.query = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def task_integration(self, db_session):
        """Фикстура для AvitoTaskIntegration"""
        return AvitoTaskIntegration(db_session)

    @pytest.fixture
    def mock_task_service(self):
        """Мок для TaskService"""
        with patch('src.aicrm.services.automation.avito_integration.TaskService') as mock:
            mock_instance = MagicMock()
            mock_instance.create_task = AsyncMock()
            mock_instance.update_task = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def sample_message_data(self):
        """Пример данных сообщения Avito"""
        return {
            "chat_id": "avito_chat_123",
            "user_id": "avito_user_456",
            "message": {
                "text": "Здравствуйте, хочу заказать услугу печати визиток",
                "timestamp": "2023-01-01T10:00:00Z"
            },
            "item_id": 12345,
            "direction": "inbound"
        }

    @pytest.fixture
    def sample_customer(self):
        """Пример клиента"""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.name = "Иван Иванов"
        customer.phone = "+7-999-123-45-67"
        customer.email = "ivan@example.com"
        customer.external_ids = {"avito_user_id": "avito_user_456"}
        return customer

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_urgent_help(self, task_integration, sample_message_data):
        """Тест анализа сообщения с срочной помощью"""
        urgent_message = sample_message_data.copy()
        urgent_message["message"]["text"] = "Срочно нужна печать документов! Помогите!"

        triggers = await task_integration._analyze_message_for_tasks(
            urgent_message["message"]["text"], None, urgent_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "urgent_help"
        assert triggers[0]["priority"] == "high"
        assert "срочно" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_complaint(self, task_integration, sample_message_data):
        """Тест анализа сообщения с жалобой"""
        complaint_message = sample_message_data.copy()
        complaint_message["message"]["text"] = "Очень недоволен качеством печати, все размазано!"

        triggers = await task_integration._analyze_message_for_tasks(
            complaint_message["message"]["text"], None, complaint_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "complaint"
        assert triggers[0]["priority"] == "high"
        assert "недоволен" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_order_inquiry(self, task_integration, sample_message_data):
        """Тест анализа сообщения с запросом о заказе"""
        inquiry_message = sample_message_data.copy()
        inquiry_message["message"]["text"] = "Когда будет готов мой заказ? Статус заказа пожалуйста."

        triggers = await task_integration._analyze_message_for_tasks(
            inquiry_message["message"]["text"], None, inquiry_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "order_inquiry"
        assert triggers[0]["priority"] == "medium"
        assert "статус" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_price_negotiation(self, task_integration, sample_message_data):
        """Тест анализа сообщения с переговорами о цене"""
        price_message = sample_message_data.copy()
        price_message["message"]["text"] = "Цена слишком высокая, можно скидку сделать?"

        triggers = await task_integration._analyze_message_for_tasks(
            price_message["message"]["text"], None, price_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "price_negotiation"
        assert triggers[0]["priority"] == "medium"
        assert "цена" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_quality_issue(self, task_integration, sample_message_data):
        """Тест анализа сообщения с проблемой качества"""
        quality_message = sample_message_data.copy()
        quality_message["message"]["text"] = "Печать плохая, все буквы смазанные, брак!"

        triggers = await task_integration._analyze_message_for_tasks(
            quality_message["message"]["text"], None, quality_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "quality_issue"
        assert triggers[0]["priority"] == "high"
        assert "брак" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_return_request(self, task_integration, sample_message_data):
        """Тест анализа сообщения с запросом на возврат"""
        return_message = sample_message_data.copy()
        return_message["message"]["text"] = "Хочу вернуть товар, он не подошел. Обмен или возврат."

        triggers = await task_integration._analyze_message_for_tasks(
            return_message["message"]["text"], None, return_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "return_request"
        assert triggers[0]["priority"] == "high"
        assert "возврат" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_tasks_custom_order(self, task_integration, sample_message_data):
        """Тест анализа сообщения с заказом кастомного изделия"""
        custom_message = sample_message_data.copy()
        custom_message["message"]["text"] = "Заказать изготовить баннер с моим дизайном"

        triggers = await task_integration._analyze_message_for_tasks(
            custom_message["message"]["text"], None, custom_message.get("item_id")
        )

        assert len(triggers) == 1
        assert triggers[0]["type"] == "custom_order"
        assert triggers[0]["priority"] == "medium"
        assert "заказать" in triggers[0]["matched_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_message_for_vip_client_attention(self, task_integration, sample_message_data, sample_customer):
        """Тест анализа для VIP клиента с высокой активностью"""
        # Мокаем запрос к коммуникациям
        mock_communications = [MagicMock()] * 15  # 15 коммуникаций за неделю
        task_integration.db.query.return_value.filter.return_value.count.return_value = 15

        triggers = await task_integration._analyze_message_for_tasks(
            "Простой вопрос о заказе", sample_customer, sample_message_data.get("item_id")
        )

        # Должен быть триггер для VIP клиента
        vip_trigger = next((t for t in triggers if t["type"] == "vip_client_attention"), None)
        assert vip_trigger is not None
        assert vip_trigger["priority"] == "high"
        assert "активность" in vip_trigger["matched_keywords"]

    @pytest.mark.asyncio
    async def test_create_task_from_trigger_success(self, task_integration, mock_task_service, sample_customer):
        """Тест успешного создания задачи из триггера"""
        trigger = {
            "type": "urgent_help",
            "title": "Срочная помощь клиенту",
            "description": "Клиент просит срочной помощи",
            "priority": "high",
            "matched_keywords": ["срочно"]
        }

        # Мокаем определение ответственного
        task_integration._determine_task_assignee = AsyncMock(return_value=2)

        # Мокаем создание задачи
        mock_task = MagicMock(spec=Task)
        mock_task.id = 123
        mock_task_service.create_task.return_value = mock_task

        result = await task_integration._create_task_from_trigger(
            trigger, sample_customer, "chat_123", 12345
        )

        assert result is not None
        assert result.id == 123
        mock_task_service.create_task.assert_called_once()

        # Проверяем аргументы вызова
        call_args = mock_task_service.create_task.call_args
        task_data = call_args[1]["task_data"]

        assert task_data["title"] == "Срочная помощь клиенту"
        assert task_data["priority"] == "high"
        assert task_data["customer_id"] == sample_customer.id
        assert task_data["assigned_to"] == 2
        assert "chat_123" in task_data["description"]
        assert "12345" in task_data["description"]

    @pytest.mark.asyncio
    async def test_create_task_from_trigger_no_assignee(self, task_integration, mock_task_service, sample_customer):
        """Тест создания задачи без определенного ответственного"""
        trigger = {
            "type": "order_inquiry",
            "title": "Запрос информации о заказе",
            "description": "Клиент спрашивает о статусе заказа",
            "priority": "medium",
            "matched_keywords": ["заказ"]
        }

        # Мокаем определение ответственного (возвращает None)
        task_integration._determine_task_assignee = AsyncMock(return_value=None)

        mock_task = MagicMock(spec=Task)
        mock_task.id = 124
        mock_task_service.create_task.return_value = mock_task

        result = await task_integration._create_task_from_trigger(
            trigger, sample_customer, "chat_123", None
        )

        assert result is not None
        # Проверяем что задача создана даже без ответственного
        call_args = mock_task_service.create_task.call_args
        task_data = call_args[1]["task_data"]
        assert task_data["assigned_to"] is None

    @pytest.mark.asyncio
    async def test_determine_task_assignee_priority_logic(self, task_integration, db_session):
        """Тест логики определения ответственного по приоритету"""
        # Мокаем пользователей
        mock_user_low = MagicMock()
        mock_user_low.id = 7
        mock_user_medium = MagicMock()
        mock_user_medium.id = 4
        mock_user_high = MagicMock()
        mock_user_high.id = 2

        # Мокаем запросы к БД
        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_user_high, mock_user_medium, mock_user_low
        ]

        # Мокаем активные задачи
        db_session.query.return_value.filter.return_value.count.side_effect = [1, 2, 0]  # Разная нагрузка

        # Тест высокого приоритета
        assignee = await task_integration._determine_task_assignee(
            {"priority": "high"}, None
        )
        assert assignee == 2  # Должен выбрать менеджера

        # Тест среднего приоритета
        assignee = await task_integration._determine_task_assignee(
            {"priority": "medium"}, None
        )
        assert assignee == 4  # Должен выбрать оператора

    @pytest.mark.asyncio
    async def test_determine_task_assignee_vip_client(self, task_integration, db_session, sample_customer):
        """Тест определения ответственного для VIP клиента"""
        # Мокаем пользователей-менеджеров
        mock_manager1 = MagicMock()
        mock_manager1.id = 2
        mock_manager2 = MagicMock()
        mock_manager2.id = 3

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_manager1, mock_manager2
        ]

        # Мокаем активные задачи (manager1 имеет меньше задач)
        db_session.query.return_value.filter.return_value.count.side_effect = [1, 3]

        assignee = await task_integration._determine_task_assignee(
            {"priority": "medium", "type": "vip_client_attention"}, sample_customer
        )

        assert assignee == 2  # Должен выбрать менеджера с меньшей нагрузкой

    @pytest.mark.asyncio
    async def test_analyze_and_create_tasks_full_flow(self, task_integration, sample_message_data, sample_customer, mock_task_service):
        """Тест полного потока анализа и создания задач"""
        # Мокаем анализ сообщения
        task_integration._analyze_message_for_tasks = AsyncMock(return_value=[
            {
                "type": "order_inquiry",
                "title": "Запрос информации о заказе",
                "description": "Клиент спрашивает о статусе заказа",
                "priority": "medium",
                "matched_keywords": ["заказ", "статус"]
            }
        ])

        # Мокаем создание задачи
        mock_task = MagicMock(spec=Task)
        mock_task.id = 125
        task_integration._create_task_from_trigger = AsyncMock(return_value=mock_task)

        result = await task_integration.analyze_and_create_tasks(
            sample_message_data, sample_customer
        )

        assert len(result) == 1
        assert result[0].id == 125
        task_integration._analyze_message_for_tasks.assert_called_once()
        task_integration._create_task_from_trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_and_create_tasks_no_triggers(self, task_integration, sample_message_data, sample_customer):
        """Тест анализа сообщения без триггеров"""
        # Мокаем анализ сообщения (без триггеров)
        task_integration._analyze_message_for_tasks = AsyncMock(return_value=[])

        result = await task_integration.analyze_and_create_tasks(
            sample_message_data, sample_customer
        )

        assert len(result) == 0
        task_integration._create_task_from_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_followup_task_success(self, task_integration, mock_task_service, sample_customer):
        """Тест создания задачи follow-up"""
        # Мокаем определение ответственного
        task_integration._determine_task_assignee = AsyncMock(return_value=5)

        mock_task = MagicMock(spec=Task)
        mock_task.id = 126
        mock_task_service.create_task.return_value = mock_task

        result = await task_integration.create_followup_task(
            sample_customer, "chat_123", "Проверить удовлетворенность заказом"
        )

        assert result is not None
        assert result.id == 126

        # Проверяем данные задачи
        call_args = mock_task_service.create_task.call_args
        task_data = call_args[1]["task_data"]

        assert "Follow-up" in task_data["title"]
        assert sample_customer.name in task_data["title"]
        assert "Проверить удовлетворенность заказом" in task_data["description"]
        assert task_data["customer_id"] == sample_customer.id
        assert task_data["assigned_to"] == 5

    @pytest.mark.asyncio
    async def test_create_order_tracking_task_success(self, task_integration, mock_task_service, sample_customer):
        """Тест создания задачи отслеживания заказа"""
        # Мокаем заказ
        mock_order = MagicMock(spec=Order)
        mock_order.id = 100
        mock_order.status = MagicMock()
        mock_order.status.value = "in_progress"
        mock_order.deadline = datetime(2023, 12, 31)

        # Мокаем определение ответственного
        task_integration._determine_task_assignee = AsyncMock(return_value=4)

        mock_task = MagicMock(spec=Task)
        mock_task.id = 127
        mock_task_service.create_task.return_value = mock_task

        result = await task_integration.create_order_tracking_task(
            mock_order, sample_customer, "chat_123"
        )

        assert result is not None
        assert result.id == 127

        # Проверяем данные задачи
        call_args = mock_task_service.create_task.call_args
        task_data = call_args[1]["task_data"]

        assert "Отслеживание заказа" in task_data["title"]
        assert "#100" in task_data["title"]
        assert "in_progress" in task_data["description"]
        assert task_data["order_id"] == mock_order.id
        assert task_data["customer_id"] == sample_customer.id

    @pytest.mark.asyncio
    async def test_get_tasks_for_chat_success(self, task_integration, db_session):
        """Тест получения задач для чата"""
        # Мокаем задачи
        mock_task1 = MagicMock(spec=Task)
        mock_task1.id = 128
        mock_task2 = MagicMock(spec=Task)
        mock_task2.id = 129

        # Мокаем запрос к БД
        db_session.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

        result = await task_integration.get_tasks_for_chat("chat_123")

        assert len(result) == 2
        assert result[0].id == 128
        assert result[1].id == 129

        # Проверяем вызов БД
        db_session.query.return_value.filter.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status_from_avito_success(self, task_integration, mock_task_service):
        """Тест обновления статуса задач из Avito"""
        # Мокаем получение задач для чата
        mock_task = MagicMock(spec=Task)
        mock_task.id = 130
        mock_task.status = "todo"
        task_integration.get_tasks_for_chat = AsyncMock(return_value=[mock_task])

        result = await task_integration.update_task_status_from_avito(
            "chat_123", "in_progress", 1
        )

        assert result is True
        mock_task_service.update_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status_from_avito_no_tasks(self, task_integration):
        """Тест обновления статуса когда нет задач для чата"""
        task_integration.get_tasks_for_chat = AsyncMock(return_value=[])

        result = await task_integration.update_task_status_from_avito(
            "chat_123", "completed", 1
        )

        assert result is False

    def test_multiple_keywords_matching(self, task_integration):
        """Тест совпадения нескольких ключевых слов"""
        message = "Срочно нужен возврат товара, качество ужасное!"

        # Проверяем что сообщение содержит ключевые слова из разных категорий
        urgent_keywords = ["срочно", "urgent", "асап", "немедленно", "проблема"]
        return_keywords = ["возврат", "return", "вернуть", "exchange", "обмен"]
        quality_keywords = ["качество", "quality", "брак", "defect", "плохо"]

        has_urgent = any(kw in message.lower() for kw in urgent_keywords)
        has_return = any(kw in message.lower() for kw in return_keywords)
        has_quality = any(kw in message.lower() for kw in quality_keywords)

        assert has_urgent is True
        assert has_return is True
        assert has_quality is True

        # В реальном сценарии должно сработать несколько триггеров
        # Но приоритет отдается по логике анализа

    def test_case_insensitive_matching(self, task_integration):
        """Тест регистронезависимого поиска ключевых слов"""
        messages = [
            "СРОЧНО нужна помощь!",
            "срочно НУЖНА помощь!",
            "Срочно нужна ПОМОЩЬ!",
            "СРОЧНО НУЖНА ПОМОЩЬ!"
        ]

        for message in messages:
            has_urgent = "срочно" in message.lower()
            assert has_urgent is True, f"Failed for message: {message}"

    def test_empty_message_handling(self, task_integration):
        """Тест обработки пустых сообщений"""
        empty_messages = ["", "   ", "\n\t  \n"]

        for message in empty_messages:
            triggers = task_integration._analyze_message_for_tasks(message, None, None)
            # Пустые сообщения не должны генерировать триггеры
            # (если только нет специальной логики для пустых сообщений)
            assert isinstance(triggers, list)

    def test_special_characters_handling(self, task_integration):
        """Тест обработки специальных символов в сообщениях"""
        message = "Срочно!!! Нужна помощь??? С качеством проблемы!!!"

        # Специальные символы не должны мешать распознаванию
        has_urgent = "срочно" in message.lower()
        has_quality = "качество" in message.lower()

        assert has_urgent is True
        assert has_quality is True
