"""
Unit тесты для Automation API роутера
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from ..models.automation import EntityType, TriggerEvent


class TestAutomationAPIRouter:
    """Unit тесты для automation роутера"""

    def test_fire_automation_event_unit(self):
        """Unit тест запуска события автоматизации"""
        from src.aicrm.api.routers.automation import fire_automation_event

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.handle_event = AsyncMock(return_value={"success": True})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = fire_automation_event(
                EntityType.CUSTOMER,
                TriggerEvent.CUSTOMER_CREATED,
                1,
                None,
                mock_db,
                mock_current_user
            )

        assert result["message"] == "Automation event processed"
        assert result["result"] == {"success": True}

    def test_move_entity_to_stage_unit(self):
        """Unit тест перемещения сущности на стадию"""
        from src.aicrm.api.routers.automation import move_entity_to_stage

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.move_to_stage = AsyncMock(return_value={"success": True})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = move_entity_to_stage(
                EntityType.CUSTOMER,
                1,
                2,
                mock_db,
                mock_current_user
            )

        assert result["message"] == "Entity moved to stage 2"
        assert result["result"] == {"success": True}

    def test_move_entity_to_stage_failure(self):
        """Unit тест неудачного перемещения на стадию"""
        from src.aicrm.api.routers.automation import move_entity_to_stage
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.move_to_stage = AsyncMock(return_value={"success": False, "error": "Test error"})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service), \
             pytest.raises(HTTPException) as exc_info:
            move_entity_to_stage(
                EntityType.CUSTOMER,
                1,
                2,
                mock_db,
                mock_current_user
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Test error"

    def test_on_customer_created_unit(self):
        """Unit тест события создания клиента"""
        from src.aicrm.api.routers.automation import on_customer_created

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.on_customer_created = AsyncMock(return_value={"result": "ok"})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = on_customer_created(1, mock_db, mock_current_user)

        assert result == {"result": {"result": "ok"}}

    def test_on_order_created_unit(self):
        """Unit тест события создания заказа"""
        from src.aicrm.api.routers.automation import on_order_created

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.on_order_created = AsyncMock(return_value={"result": "ok"})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = on_order_created(1, mock_db, mock_current_user)

        assert result == {"result": {"result": "ok"}}

    def test_on_task_completed_unit(self):
        """Unit тест события завершения задачи"""
        from src.aicrm.api.routers.automation import on_task_completed

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.on_task_completed = AsyncMock(return_value={"result": "ok"})

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = on_task_completed(1, mock_db, mock_current_user)

        assert result == {"result": {"result": "ok"}}

    def test_get_processes_unit(self):
        """Unit тест получения списка процессов"""
        from src.aicrm.api.routers.automation import get_processes

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем процесс
        mock_process = MagicMock()
        mock_process.id = 1
        mock_process.name = "Test Process"
        mock_process.description = "Test Description"
        mock_process.entity_type = EntityType.CUSTOMER
        mock_process.is_active = True
        mock_process.stages = [MagicMock(), MagicMock()]  # 2 стадии

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_process]

        mock_db.query.return_value = mock_query

        result = get_processes(0, 100, None, mock_db, mock_current_user)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Process"
        assert result[0]["stages_count"] == 2

    def test_create_process_unit(self):
        """Unit тест создания процесса"""
        from src.aicrm.api.routers.automation import create_process
        from src.aicrm.api.schemas.automation import ProcessCreate

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем процесс
        mock_process = MagicMock()
        mock_process.id = 1
        mock_process.name = "New Process"
        mock_process.description = "New Description"
        mock_process.entity_type = EntityType.CUSTOMER
        mock_process.is_active = True
        mock_process.created_at = "2024-01-01"
        mock_process.updated_at = "2024-01-01"

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        process_data = ProcessCreate(
            name="New Process",
            description="New Description",
            entity_type=EntityType.CUSTOMER
        )

        with patch("src.aicrm.api.routers.automation.Process", return_value=mock_process):
            result = create_process(process_data, mock_db, mock_current_user)

        assert result["id"] == 1
        assert result["name"] == "New Process"
        assert result["entity_type"] == EntityType.CUSTOMER

    def test_get_process_unit(self):
        """Unit тест получения процесса по ID"""
        from src.aicrm.api.routers.automation import get_process

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем процесс
        mock_process = MagicMock()
        mock_process.id = 1
        mock_process.name = "Test Process"
        mock_process.description = "Test Description"
        mock_process.entity_type = EntityType.CUSTOMER
        mock_process.is_active = True
        mock_process.created_at = "2024-01-01"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_process

        mock_db.query.return_value = mock_query

        result = get_process(1, mock_db, mock_current_user)

        assert result["id"] == 1
        assert result["name"] == "Test Process"

    def test_get_process_not_found(self):
        """Unit тест получения несуществующего процесса"""
        from src.aicrm.api.routers.automation import get_process
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            get_process(999, mock_db, mock_current_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Process not found"

    def test_update_process_unit(self):
        """Unit тест обновления процесса"""
        from src.aicrm.api.routers.automation import update_process
        from src.aicrm.api.schemas.automation import ProcessUpdate

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем процесс
        mock_process = MagicMock()
        mock_process.id = 1
        mock_process.name = "Updated Process"
        mock_process.description = "Updated Description"
        mock_process.entity_type = EntityType.CUSTOMER
        mock_process.is_active = True
        mock_process.created_at = "2024-01-01"
        mock_process.updated_at = "2024-01-02"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_process

        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        update_data = ProcessUpdate(name="Updated Process", description="Updated Description")

        result = update_process(1, update_data, mock_db, mock_current_user)

        assert result["id"] == 1
        assert result["name"] == "Updated Process"

    def test_delete_process_unit(self):
        """Unit тест удаления процесса"""
        from src.aicrm.api.routers.automation import delete_process

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем процесс
        mock_process = MagicMock()
        mock_process.id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_process

        mock_db.query.return_value = mock_query
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = delete_process(1, mock_db, mock_current_user)

        assert result == {"message": "Process deleted"}
        mock_db.delete.assert_called_once_with(mock_process)
        mock_db.commit.assert_called_once()

    def test_get_stages_unit(self):
        """Unit тест получения списка стадий"""
        from src.aicrm.api.routers.automation import get_stages

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем стадию
        mock_stage = MagicMock()
        mock_stage.id = 1
        mock_stage.name = "Test Stage"
        mock_stage.description = "Test Description"
        mock_stage.entity_type = EntityType.CUSTOMER
        mock_stage.process_id = 1
        mock_stage.order_index = 0
        mock_stage.color = "#FF0000"
        mock_stage.is_active = True
        mock_stage.created_at = "2024-01-01"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_stage]

        mock_db.query.return_value = mock_query

        result = get_stages(None, None, 0, 100, mock_db, mock_current_user)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Stage"
        assert result[0]["color"] == "#FF0000"

    def test_create_stage_unit(self):
        """Unit тест создания стадии"""
        from src.aicrm.api.routers.automation import create_stage
        from src.aicrm.api.schemas.automation import StageCreate

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем стадию
        mock_stage = MagicMock()
        mock_stage.id = 1
        mock_stage.name = "New Stage"
        mock_stage.description = "New Description"
        mock_stage.entity_type = EntityType.CUSTOMER
        mock_stage.process_id = 1
        mock_stage.order_index = 0
        mock_stage.color = "#00FF00"
        mock_stage.is_active = True
        mock_stage.created_at = "2024-01-01"

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        stage_data = StageCreate(
            name="New Stage",
            description="New Description",
            entity_type=EntityType.CUSTOMER,
            process_id=1,
            color="#00FF00"
        )

        with patch("src.aicrm.api.routers.automation.Stage", return_value=mock_stage):
            result = create_stage(stage_data, mock_db, mock_current_user)

        assert result["id"] == 1
        assert result["name"] == "New Stage"
        assert result["color"] == "#00FF00"

    def test_get_triggers_unit(self):
        """Unit тест получения списка триггеров"""
        from src.aicrm.api.routers.automation import get_triggers

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем триггер
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "Test Trigger"
        mock_trigger.description = "Test Description"
        mock_trigger.entity_type = EntityType.CUSTOMER
        mock_trigger.event_type = TriggerEvent.CUSTOMER_CREATED
        mock_trigger.conditions = {"field": "status", "value": "new"}
        mock_trigger.target_stage_id = 1
        mock_trigger.is_active = True
        mock_trigger.created_at = "2024-01-01"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_trigger]

        mock_db.query.return_value = mock_query

        result = get_triggers(None, None, None, 0, 100, mock_db, mock_current_user)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Trigger"
        assert result[0]["event_type"] == TriggerEvent.CUSTOMER_CREATED

    def test_get_robots_unit(self):
        """Unit тест получения списка роботов"""
        from src.aicrm.api.routers.automation import get_robots

        mock_db = MagicMock()
        mock_current_user = MagicMock()

        # Мокаем робота
        mock_robot = MagicMock()
        mock_robot.id = 1
        mock_robot.name = "Test Robot"
        mock_robot.description = "Test Description"
        mock_robot.entity_type = EntityType.CUSTOMER
        mock_robot.stage_id = 1
        mock_robot.actions = [MagicMock(), MagicMock(), MagicMock()]  # 3 действия
        mock_robot.is_active = True
        mock_robot.created_at = "2024-01-01"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_robot]

        mock_db.query.return_value = mock_query

        result = get_robots(None, None, None, 0, 100, mock_db, mock_current_user)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Robot"
        assert result[0]["actions_count"] == 3

    def test_generate_automation_chain_unit(self):
        """Unit тест генерации цепочки автоматизации"""
        from src.aicrm.api.routers.automation import generate_automation_chain
        from src.aicrm.api.schemas.automation import AutomationChainRequest

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.generate_automation_chain_with_ai = AsyncMock(return_value={
            "success": True,
            "chain": {"stages": [], "robots": []}
        })

        request = AutomationChainRequest(
            description="Test automation chain",
            entity_type=EntityType.CUSTOMER,
            complexity_level="medium"
        )

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = generate_automation_chain(request, mock_db, mock_current_user)

        assert result["success"] is True
        assert "chain" in result

    def test_get_execution_stats_unit(self):
        """Unit тест получения статистики выполнений"""
        from src.aicrm.api.routers.automation import get_execution_stats

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_analytics_service = MagicMock()
        mock_analytics_service.get_execution_stats = AsyncMock(return_value={
            "total_executions": 100,
            "success_rate": 0.95
        })

        with patch("src.aicrm.api.routers.automation.AutomationAnalyticsService", return_value=mock_analytics_service):
            result = get_execution_stats(None, None, None, mock_db, mock_current_user)

        assert result["total_executions"] == 100
        assert result["success_rate"] == 0.95

    def test_get_robot_performance_unit(self):
        """Unit тест получения производительности роботов"""
        from src.aicrm.api.routers.automation import get_robot_performance

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_analytics_service = MagicMock()
        mock_analytics_service.get_robot_performance = AsyncMock(return_value={
            "robots": [{"id": 1, "executions": 50}]
        })

        with patch("src.aicrm.api.routers.automation.AutomationAnalyticsService", return_value=mock_analytics_service):
            result = get_robot_performance(None, None, None, mock_db, mock_current_user)

        assert result["robots"][0]["id"] == 1
        assert result["robots"][0]["executions"] == 50

    def test_optimize_automation_chain_unit(self):
        """Unit тест оптимизации цепочки автоматизации"""
        from src.aicrm.api.routers.automation import optimize_automation_chain

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.optimize_automation_chain_with_ai = AsyncMock(return_value={
            "success": True,
            "optimized_chain": {"stages": []}
        })

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = optimize_automation_chain(1, "performance", mock_db, mock_current_user)

        assert result["success"] is True
        assert "optimized_chain" in result

    def test_suggest_automation_improvements_unit(self):
        """Unit тест предложений по улучшению автоматизации"""
        from src.aicrm.api.routers.automation import suggest_automation_improvements

        mock_db = MagicMock()
        mock_current_user = MagicMock()
        mock_automation_service = MagicMock()
        mock_automation_service.analyze_and_suggest_improvements = AsyncMock(return_value={
            "suggestions": ["Add more robots", "Optimize triggers"]
        })

        with patch("src.aicrm.api.routers.automation.AutomationService", return_value=mock_automation_service):
            result = suggest_automation_improvements(None, 30, mock_db, mock_current_user)

        assert "suggestions" in result
        assert len(result["suggestions"]) == 2
