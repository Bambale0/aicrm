"""
Тесты для автоматизации бизнес-процессов
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from ..models.automation import EntityType, TriggerEvent, RobotAction
from ..services.automation.automation_service import AutomationService
from ..services.automation.trigger_service import TriggerService
from ..services.automation.robot_service import RobotService


class TestAutomationService:
    """Тесты основного сервиса автоматизации"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def automation_service(self, mock_db):
        """Сервис автоматизации с моками"""
        return AutomationService(mock_db)

    @pytest.mark.asyncio
    async def test_on_customer_created(self, automation_service, mock_db):
        """Тест события создания клиента"""
        # Мокаем методы
        automation_service.trigger_service.handle_trigger_event = AsyncMock(return_value=[])

        result = await automation_service.on_customer_created(1)

        assert result["entity_type"] == EntityType.CUSTOMER.value
        assert result["entity_id"] == 1
        assert result["event_type"] == TriggerEvent.CUSTOMER_CREATED.value
        assert "triggers_executed" in result
        assert "robots_executed" in result

    @pytest.mark.asyncio
    async def test_handle_event(self, automation_service, mock_db):
        """Тест обработки события"""
        automation_service.trigger_service.handle_trigger_event = AsyncMock(return_value=[])

        result = await automation_service.handle_event(
            EntityType.CUSTOMER,
            TriggerEvent.CUSTOMER_CREATED,
            1
        )

        assert result["entity_type"] == EntityType.CUSTOMER.value
        assert result["entity_id"] == 1
        assert result["event_type"] == TriggerEvent.CUSTOMER_CREATED.value


class TestTriggerService:
    """Тесты сервиса триггеров"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def trigger_service(self, mock_db):
        """Сервис триггеров с моками"""
        return TriggerService(mock_db)

    def test_find_matching_triggers(self, trigger_service, mock_db):
        """Тест поиска подходящих триггеров"""
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = trigger_service.find_matching_triggers(
            EntityType.CUSTOMER,
            TriggerEvent.CUSTOMER_CREATED,
            1
        )

        assert isinstance(result, list)
        mock_db.query.assert_called()


class TestRobotService:
    """Тесты сервиса роботов"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def robot_service(self, mock_db):
        """Сервис роботов с моками"""
        return RobotService(mock_db)

    @pytest.mark.asyncio
    async def test_execute_robot(self, robot_service, mock_db):
        """Тест выполнения робота"""
        # Мокаем робота
        mock_robot = MagicMock()
        mock_robot.actions = []

        robot_service._execute_action = AsyncMock(return_value={"success": True})

        result = await robot_service.execute_robot(mock_robot, 1, {})

        assert "robot_id" in result
        assert "actions_executed" in result
        assert "success" in result

    @pytest.mark.asyncio
    async def test_execute_send_email_action(self, robot_service, mock_db):
        """Тест действия отправки email"""
        action_config = {
            "action_type": RobotAction.SEND_EMAIL,
            "config": {
                "to": "test@example.com",
                "subject": "Test",
                "body": "Test message"
            }
        }

        # Мокаем email сервис
        robot_service.email_service = AsyncMock()
        robot_service.email_service.send_email.return_value = {"success": True}

        result = await robot_service._execute_action(action_config, 1, {})

        assert result["success"] is True
        robot_service.email_service.send_email.assert_called_once()


class TestAutomationIntegration:
    """Интеграционные тесты автоматизации"""

    @pytest.mark.asyncio
    async def test_customer_creation_workflow(self):
        """Тест полного workflow создания клиента"""
        # Этот тест требует реальной БД и сервисов
        # В реальном проекте здесь будут интеграционные тесты
        # с тестовой базой данных
        pass

    @pytest.mark.asyncio
    async def test_order_status_change_workflow(self):
        """Тест workflow изменения статуса заказа"""
        # Аналогично предыдущему тесту
        pass


# Параметризованные тесты для разных типов событий
@pytest.mark.parametrize("entity_type,event_type", [
    (EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED),
    (EntityType.ORDER, TriggerEvent.ORDER_CREATED),
    (EntityType.TASK, TriggerEvent.TASK_COMPLETED),
    (EntityType.PRODUCTION_STEP, TriggerEvent.PRODUCTION_STEP_COMPLETED),
])
def test_supported_events(entity_type, event_type):
    """Тест поддерживаемых типов событий"""
    assert isinstance(entity_type, EntityType)
    assert isinstance(event_type, TriggerEvent)


# Тесты для валидации конфигураций действий
@pytest.mark.parametrize("action_type,config", [
    (RobotAction.SEND_EMAIL, {
        "to": "test@example.com",
        "subject": "Test",
        "body": "Test message"
    }),
    (RobotAction.UPDATE_FIELD, {
        "field": "status",
        "value": "completed"
    }),
    (RobotAction.CREATE_TASK, {
        "title": "New task",
        "description": "Task description",
        "assignee_id": 1
    }),
])
def test_robot_action_configs(action_type, config):
    """Тест конфигураций действий роботов"""
    assert isinstance(action_type, RobotAction)
    assert isinstance(config, dict)
    assert len(config) > 0
