"""
Unit тесты для TriggerService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from ..services.automation.trigger_service import TriggerService
from ..models.automation import EntityType, TriggerEvent


class TestTriggerService:
    """Тесты для сервиса триггеров"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def trigger_service(self, mock_db):
        """Сервис триггеров с моками"""
        return TriggerService(mock_db)

    @pytest.mark.asyncio
    async def test_handle_trigger_event_no_triggers(self, trigger_service, mock_db):
        """Тест обработки события - нет триггеров"""
        # Мокаем пустой результат запроса
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await trigger_service.handle_trigger_event(
            EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED, 1
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_handle_trigger_event_with_triggers(self, trigger_service, mock_db):
        """Тест обработки события с триггерами"""
        # Мокаем триггер
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "Test Trigger"
        mock_trigger.entity_type = EntityType.CUSTOMER
        mock_trigger.event_type = TriggerEvent.CUSTOMER_CREATED
        mock_trigger.target_stage_id = 2
        mock_trigger.conditions = None

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_trigger]

        with patch.object(trigger_service, "_check_trigger_conditions", new_callable=AsyncMock) as mock_check, \
             patch.object(trigger_service, "_move_to_target_stage", new_callable=AsyncMock) as mock_move:

            mock_check.return_value = True
            mock_move.return_value = {"success": True, "stage_name": "New Stage"}

            result = await trigger_service.handle_trigger_event(
                EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED, 1
            )

        assert len(result) == 1
        assert result[0]["trigger_id"] == 1
        assert result[0]["success"] is True
        assert result[0]["target_stage_id"] == 2

    @pytest.mark.asyncio
    async def test_handle_trigger_event_conditions_not_met(self, trigger_service, mock_db):
        """Тест обработки события - условия не выполнены"""
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "Test Trigger"
        mock_trigger.conditions = {"status": "active"}

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_trigger]

        with patch.object(trigger_service, "_check_trigger_conditions", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = False

            result = await trigger_service.handle_trigger_event(
                EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED, 1
            )

        assert result == []  # Триггер не сработал

    @pytest.mark.asyncio
    async def test_check_trigger_conditions_no_conditions(self, trigger_service, mock_db):
        """Тест проверки условий - нет условий"""
        mock_trigger = MagicMock()
        mock_trigger.conditions = None

        result = await trigger_service._check_trigger_conditions(mock_trigger, 1, {})

        assert result is True

    @pytest.mark.asyncio
    async def test_check_trigger_conditions_with_conditions(self, trigger_service, mock_db):
        """Тест проверки условий с условиями"""
        mock_trigger = MagicMock()
        mock_trigger.conditions = {"status": "active"}
        mock_trigger.entity_type = EntityType.CUSTOMER

        with patch.object(trigger_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {"status": "active"}

            result = await trigger_service._check_trigger_conditions(mock_trigger, 1, {})

        assert result is True

    @pytest.mark.asyncio
    async def test_check_trigger_conditions_entity_not_found(self, trigger_service, mock_db):
        """Тест проверки условий - сущность не найдена"""
        mock_trigger = MagicMock()
        mock_trigger.conditions = {"status": "active"}
        mock_trigger.entity_type = EntityType.CUSTOMER

        with patch.object(trigger_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = None

            result = await trigger_service._check_trigger_conditions(mock_trigger, 1, {})

        assert result is False

    def test_evaluate_conditions_simple(self, trigger_service):
        """Тест оценки простых условий"""
        conditions = {"status": "active"}
        entity_data = {"status": "active"}
        event_data = {}

        result = trigger_service._evaluate_conditions(conditions, entity_data, event_data)

        assert result is True

    def test_evaluate_conditions_complex(self, trigger_service):
        """Тест оценки сложных условий"""
        conditions = {
            "status": {"operator": "equals", "value": "active"},
            "priority": {"operator": "greater", "value": 1}
        }
        entity_data = {"status": "active", "priority": 3}
        event_data = {}

        result = trigger_service._evaluate_conditions(conditions, entity_data, event_data)

        assert result is True

    def test_evaluate_conditions_failed(self, trigger_service):
        """Тест оценки условий - условие не выполнено"""
        conditions = {"status": "inactive"}
        entity_data = {"status": "active"}
        event_data = {}

        result = trigger_service._evaluate_conditions(conditions, entity_data, event_data)

        assert result is False

    def test_get_nested_value(self, trigger_service):
        """Тест получения вложенного значения"""
        data = {"user": {"profile": {"name": "John"}}}

        result = trigger_service._get_nested_value(data, "user.profile.name")
        assert result == "John"

        result = trigger_service._get_nested_value(data, "user.email")
        assert result is None

    def test_check_condition_equals(self, trigger_service):
        """Тест проверки условия - equals"""
        assert trigger_service._check_condition("active", "equals", "active") is True
        assert trigger_service._check_condition("active", "equals", "inactive") is False

    def test_check_condition_not_equals(self, trigger_service):
        """Тест проверки условия - not_equals"""
        assert trigger_service._check_condition("active", "not_equals", "inactive") is True
        assert trigger_service._check_condition("active", "not_equals", "active") is False

    def test_check_condition_greater(self, trigger_service):
        """Тест проверки условия - greater"""
        assert trigger_service._check_condition(5, "greater", 3) is True
        assert trigger_service._check_condition(2, "greater", 3) is False

    def test_check_condition_contains(self, trigger_service):
        """Тест проверки условия - contains"""
        assert trigger_service._check_condition("hello world", "contains", "world") is True
        assert trigger_service._check_condition("hello world", "contains", "foo") is False
        assert trigger_service._check_condition([1, 2, 3], "contains", 2) is True

    @pytest.mark.asyncio
    async def test_move_to_target_stage_customer(self, trigger_service, mock_db):
        """Тест перемещения клиента на стадию"""
        # Мокаем стадию
        mock_stage = MagicMock()
        mock_stage.id = 1
        mock_stage.name = "Active"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stage

        with patch.object(trigger_service, "_move_customer_to_stage", new_callable=AsyncMock) as mock_move:
            mock_move.return_value = {"success": True, "stage_name": "Active"}

            result = await trigger_service._move_to_target_stage(
                EntityType.CUSTOMER, 1, 1
            )

        assert result["success"] is True
        assert result["stage_name"] == "Active"

    @pytest.mark.asyncio
    async def test_move_to_target_stage_stage_not_found(self, trigger_service, mock_db):
        """Тест перемещения на стадию - стадия не найдена"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="Target stage 1 not found"):
            await trigger_service._move_to_target_stage(EntityType.CUSTOMER, 1, 1)

    @pytest.mark.asyncio
    async def test_move_to_target_stage_unsupported_entity(self, trigger_service, mock_db):
        """Тест перемещения - неподдерживаемый тип сущности"""
        mock_stage = MagicMock()
        mock_stage.id = 1

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stage

        with pytest.raises(ValueError, match="Unsupported entity type"):
            await trigger_service._move_to_target_stage(EntityType.TASK, 1, 1)

    @pytest.mark.asyncio
    async def test_get_entity_data_customer(self, trigger_service, mock_db):
        """Тест получения данных клиента"""
        # Мокаем клиента
        mock_customer = MagicMock()
        mock_customer.__dict__ = {"id": 1, "name": "John", "status": "active"}

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_customer

        result = await trigger_service._get_entity_data(EntityType.CUSTOMER, 1)

        assert result["id"] == 1
        assert result["name"] == "John"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_entity_data_not_found(self, trigger_service, mock_db):
        """Тест получения данных - сущность не найдена"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = await trigger_service._get_entity_data(EntityType.CUSTOMER, 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_move_customer_to_stage(self, trigger_service, mock_db):
        """Тест перемещения клиента на стадию"""
        mock_customer = MagicMock()
        mock_customer.id = 1

        mock_stage = MagicMock()
        mock_stage.name = "VIP"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_customer

        result = await trigger_service._move_customer_to_stage(1, mock_stage)

        assert result["success"] is True
        assert result["entity_type"] == "customer"
        assert result["stage_name"] == "VIP"

    @pytest.mark.asyncio
    async def test_move_customer_to_stage_not_found(self, trigger_service, mock_db):
        """Тест перемещения клиента - клиент не найден"""
        mock_stage = MagicMock()
        mock_stage.name = "VIP"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="Customer 1 not found"):
            await trigger_service._move_customer_to_stage(1, mock_stage)

    @pytest.mark.asyncio
    async def test_move_order_to_stage(self, trigger_service, mock_db):
        """Тест перемещения заказа на стадию"""
        from ..models.order import OrderStatus

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = OrderStatus.PENDING

        mock_stage = MagicMock()
        mock_stage.name = "В работе"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_order

        result = await trigger_service._move_order_to_stage(1, mock_stage)

        assert result["success"] is True
        assert result["new_status"] == OrderStatus.IN_PRODUCTION.value
        assert mock_order.status == OrderStatus.IN_PRODUCTION

    @pytest.mark.asyncio
    async def test_move_task_to_stage(self, trigger_service, mock_db):
        """Тест перемещения задачи на стадию"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "todo"

        mock_stage = MagicMock()
        mock_stage.name = "В работе"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_task

        result = await trigger_service._move_task_to_stage(1, mock_stage)

        assert result["success"] is True
        assert result["new_status"] == "in_progress"
        assert mock_task.status == "in_progress"

    @pytest.mark.asyncio
    async def test_move_production_step_to_stage(self, trigger_service, mock_db):
        """Тест перемещения этапа производства на стадию"""
        from ..models.production_step import StepStatus

        mock_step = MagicMock()
        mock_step.id = 1
        mock_step.status = StepStatus.PENDING
        mock_step.started_at = None
        mock_step.completed_at = None

        mock_stage = MagicMock()
        mock_stage.name = "В работе"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_step

        result = await trigger_service._move_production_step_to_stage(1, mock_stage)

        assert result["success"] is True
        assert result["new_status"] == StepStatus.IN_PROGRESS.value
        assert mock_step.status == StepStatus.IN_PROGRESS
        assert mock_step.started_at is not None

    @pytest.mark.asyncio
    async def test_move_production_step_to_completed(self, trigger_service, mock_db):
        """Тест перемещения этапа производства в завершенный статус"""
        from ..models.production_step import StepStatus

        mock_step = MagicMock()
        mock_step.id = 1
        mock_step.status = StepStatus.IN_PROGRESS
        mock_step.started_at = "2024-01-01"
        mock_step.completed_at = None

        mock_stage = MagicMock()
        mock_stage.name = "Завершен"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_step

        result = await trigger_service._move_production_step_to_stage(1, mock_stage)

        assert result["success"] is True
        assert result["new_status"] == StepStatus.COMPLETED.value
        assert mock_step.status == StepStatus.COMPLETED
        assert mock_step.completed_at is not None

    @pytest.mark.asyncio
    async def test_handle_trigger_event_error(self, trigger_service, mock_db):
        """Тест обработки ошибки в триггере"""
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "Test Trigger"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_trigger]

        with patch.object(trigger_service, "_check_trigger_conditions", new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = Exception("Condition check failed")

            result = await trigger_service.handle_trigger_event(
                EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED, 1
            )

        assert len(result) == 1
        assert result[0]["success"] is False
        assert "Condition check failed" in result[0]["error"]
