"""
Тесты для WorkflowService - создание и выполнение AI workflow
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.orm import Session

from ..models.token_accounting import Workflow
from ..schemas.workflow import EventType
from ..services.workflow_service import WorkflowService


class TestWorkflowService:
    """Тесты сервиса workflow"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_ai_client(self):
        """Мок AI клиента"""
        client = MagicMock()
        client.chat_completion = AsyncMock()
        return client

    @pytest.fixture
    def mock_token_service(self):
        """Мок сервиса учета токенов"""
        service = MagicMock()
        service.check_quota_and_record_transaction = AsyncMock()
        return service

    @pytest.fixture
    def workflow_service(self, mock_db, mock_ai_client, mock_token_service):
        """Сервис workflow с моками"""
        service = WorkflowService(mock_db)
        service.ai_client = mock_ai_client
        service.token_service = mock_token_service
        return service

    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt_success(
        self, workflow_service, mock_db, mock_ai_client
    ):
        """Тест успешного создания workflow из промпта"""
        # Настройка мока AI
        mock_ai_client.chat_completion.return_value = """
        {
            "name": "Обработка срочных заказов",
            "description": "Workflow для обработки VIP заказов",
            "trigger": {"event_type": "ON_ORDER_CREATED"},
            "conditions": [
                {"field_path": "order_type", "operator": "eq", "value": "Срочный"},
                {"field_path": "total", "operator": "gt", "value": 50000}
            ],
            "actions": [
                {"name": "Отправить уведомление", "type": "send_notification", "config": {"message": "VIP заказ"}},
                {"name": "Создать задачу", "type": "create_task", "config": {"title": "Обработать VIP заказ"}}
            ]
        }
        """

        # Настройка мока БД
        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = 1
        mock_workflow.name = "Обработка срочных заказов"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = await workflow_service.create_workflow_from_prompt(
            prompt="Создать workflow для обработки VIP заказов",
            name="VIP Workflow",
            created_by=1,
        )

        # Проверки
        assert result is not None
        mock_ai_client.chat_completion.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, workflow_service, mock_db):
        """Тест успешного выполнения workflow"""
        # Создаем мок workflow
        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = 1
        mock_workflow.is_active = True
        mock_workflow.conditions = [
            {"field_path": "total", "operator": "gt", "value": 1000}
        ]
        mock_workflow.actions = [
            {
                "name": "Test action",
                "type": "send_notification",
                "config": {"message": "Test"},
            }
        ]

        # Настройка моков БД
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_workflow
        )
        mock_execution = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        # Мокаем методы
        workflow_service._check_conditions = MagicMock(return_value=True)
        workflow_service._execute_action = AsyncMock(return_value={"success": True})

        result = await workflow_service.execute_workflow(
            workflow_id=1,
            trigger_event={
                "event_type": "ON_ORDER_CREATED",
                "payload": {"total": 2000},
            },
        )

        assert result is not None
        assert result.execution_status == "completed"
        workflow_service._check_conditions.assert_called_once()
        workflow_service._execute_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_conditions_not_met(self, workflow_service, mock_db):
        """Тест выполнения workflow с невыполненными условиями"""
        # Создаем мок workflow
        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = 1
        mock_workflow.is_active = True
        mock_workflow.conditions = [
            {"field_path": "total", "operator": "gt", "value": 5000}
        ]

        # Настройка моков
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_workflow
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        # Мокаем методы
        workflow_service._check_conditions = MagicMock(return_value=False)

        result = await workflow_service.execute_workflow(
            workflow_id=1,
            trigger_event={
                "event_type": "ON_ORDER_CREATED",
                "payload": {"total": 1000},
            },
        )

        assert result.execution_status == "completed"
        assert "conditions_not_met" in result.execution_result["status"]

    def test_check_conditions_all_met(self, workflow_service):
        """Тест проверки условий - все выполнены"""
        conditions = [
            {"field_path": "total", "operator": "gt", "value": 1000},
            {"field_path": "status", "operator": "eq", "value": "new"},
        ]
        event = {"payload": {"total": 2000, "status": "new"}}

        result = workflow_service._check_conditions(conditions, event)
        assert result is True

    def test_check_conditions_some_not_met(self, workflow_service):
        """Тест проверки условий - не все выполнены"""
        conditions = [
            {"field_path": "total", "operator": "gt", "value": 1000},
            {"field_path": "status", "operator": "eq", "value": "completed"},
        ]
        event = {"payload": {"total": 2000, "status": "new"}}

        result = workflow_service._check_conditions(conditions, event)
        assert result is False

    def test_evaluate_condition_eq(self, workflow_service):
        """Тест оценки условия равенства"""
        assert workflow_service._evaluate_condition("new", "eq", "new") is True
        assert workflow_service._evaluate_condition("new", "eq", "old") is False

    def test_evaluate_condition_gt(self, workflow_service):
        """Тест оценки условия больше"""
        assert workflow_service._evaluate_condition(100, "gt", 50) is True
        assert workflow_service._evaluate_condition(30, "gt", 50) is False

    def test_evaluate_condition_contains(self, workflow_service):
        """Тест оценки условия содержит"""
        assert (
            workflow_service._evaluate_condition("hello world", "contains", "world")
            is True
        )
        assert (
            workflow_service._evaluate_condition("hello world", "contains", "test")
            is False
        )

    @pytest.mark.asyncio
    async def test_test_workflow(self, workflow_service, mock_db):
        """Тест тестирования workflow"""
        # Создаем мок workflow
        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = 1
        mock_workflow.trigger = {"event_type": "ON_ORDER_CREATED"}
        mock_workflow.conditions = [
            {"field_path": "total", "operator": "gt", "value": 1000}
        ]
        mock_workflow.actions = [
            {"name": "Test", "type": "send_notification", "config": {}}
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_workflow
        )

        # Мокаем методы
        workflow_service._check_conditions = MagicMock(return_value=True)

        result = await workflow_service.test_workflow(
            workflow_id=1,
            test_event={"event_type": "ON_ORDER_CREATED", "payload": {"total": 2000}},
        )

        assert result["workflow_id"] == 1
        assert result["triggered"] is True
        assert result["conditions_met"] is True
        assert len(result["actions_executed"]) == 1

    def test_get_workflow_executions(self, workflow_service, mock_db):
        """Тест получения истории выполнений"""
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            (
                MagicMock(
                    id=1,
                    workflow_id=1,
                    trigger_event={},
                    execution_status="completed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=None,
                ),
                "Test Workflow",
            )
        ]
        mock_db.query.return_value = mock_query

        result = workflow_service.get_workflow_executions(limit=10)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["workflow_name"] == "Test Workflow"

    def test_get_workflows(self, workflow_service, mock_db):
        """Тест получения списка workflow"""
        mock_workflows = [MagicMock(spec=Workflow), MagicMock(spec=Workflow)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            mock_workflows
        )

        result = workflow_service.get_workflows(limit=10)

        assert len(result) == 2
        mock_db.query.assert_called()


class TestWorkflowIntegration:
    """Интеграционные тесты workflow"""

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(
        self, workflow_service, mock_db, mock_ai_client
    ):
        """Тест полного жизненного цикла workflow"""
        # Настройка AI ответа
        mock_ai_client.chat_completion.return_value = """
        {
            "name": "Test Workflow",
            "description": "Integration test workflow",
            "trigger": {"event_type": "ON_ORDER_CREATED"},
            "conditions": [{"field_path": "total", "operator": "gt", "value": 100}],
            "actions": [{"name": "Log", "type": "send_notification", "config": {"message": "Order created"}}]
        }
        """

        # 1. Создание workflow
        workflow = await workflow_service.create_workflow_from_prompt(
            prompt="Test workflow", name="Integration Test"
        )

        # 2. Выполнение workflow
        workflow_service._check_conditions = MagicMock(return_value=True)
        workflow_service._execute_action = AsyncMock(return_value={"success": True})

        execution = await workflow_service.execute_workflow(
            workflow_id=1,
            trigger_event={"event_type": "ON_ORDER_CREATED", "payload": {"total": 200}},
        )

        assert execution.execution_status == "completed"

        # 3. Тестирование workflow
        test_result = await workflow_service.test_workflow(
            workflow_id=1,
            test_event={"event_type": "ON_ORDER_CREATED", "payload": {"total": 200}},
        )

        assert test_result["triggered"] is True
        assert test_result["conditions_met"] is True
