"""
Unit тесты для AutomationAnalyticsService
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from ..services.automation.analytics_service import AutomationAnalyticsService
from ..models.automation import EntityType


class TestAutomationAnalyticsService:
    """Тесты для сервиса аналитики автоматизаций"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Сервис аналитики с моками"""
        return AutomationAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_get_execution_stats_empty(self, analytics_service, mock_db):
        """Тест получения статистики выполнений - пустой результат"""
        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_execution_stats()

        assert result["executions"]["total"] == 0
        assert result["executions"]["success_rate"] == 0
        assert result["performance"]["avg_execution_time_seconds"] == 0

    @pytest.mark.asyncio
    async def test_get_execution_stats_with_data(self, analytics_service, mock_db):
        """Тест получения статистики выполнений с данными"""
        # Создаем моковые выполнения
        mock_execution1 = MagicMock()
        mock_execution1.execution_status = "completed"
        mock_execution1.execution_time_seconds = 5.0
        mock_execution1.actions_total = 3
        mock_execution1.actions_successful = 3
        mock_execution1.actions_failed = 0

        mock_execution2 = MagicMock()
        mock_execution2.execution_status = "failed"
        mock_execution2.execution_time_seconds = 10.0
        mock_execution2.actions_total = 2
        mock_execution2.actions_successful = 1
        mock_execution2.actions_failed = 1

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_execution1, mock_execution2]

        result = await analytics_service.get_execution_stats()

        assert result["executions"]["total"] == 2
        assert result["executions"]["completed"] == 1
        assert result["executions"]["failed"] == 1
        assert result["executions"]["success_rate"] == 50.0
        assert result["performance"]["avg_execution_time_seconds"] == 7.5
        assert result["actions"]["total"] == 5
        assert result["actions"]["successful"] == 4
        assert result["actions"]["success_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_get_execution_stats_with_filters(self, analytics_service, mock_db):
        """Тест получения статистики с фильтрами по дате и типу"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_execution_stats(
            start_date=start_date,
            end_date=end_date,
            entity_type=EntityType.CUSTOMER
        )

        assert result["period"]["start_date"] == start_date.isoformat()
        assert result["period"]["end_date"] == end_date.isoformat()
        assert mock_query.filter.call_count >= 2  # Фильтры по дате и типу

    @pytest.mark.asyncio
    async def test_get_robot_performance_empty(self, analytics_service, mock_db):
        """Тест производительности роботов - пустой результат"""
        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_robot_performance()

        assert result["robots"] == []
        assert result["summary"]["total_robots"] == 0
        assert result["summary"]["total_executions"] == 0

    @pytest.mark.asyncio
    async def test_get_robot_performance_with_data(self, analytics_service, mock_db):
        """Тест производительности роботов с данными"""
        # Мокаем результат запроса
        mock_row1 = MagicMock()
        mock_row1.robot_id = 1
        mock_row1.name = "Test Robot 1"
        mock_row1.executions_count = 10
        mock_row1.avg_time = 5.5
        mock_row1.successful_actions = 25
        mock_row1.failed_actions = 5

        mock_row2 = MagicMock()
        mock_row2.robot_id = 2
        mock_row2.name = "Test Robot 2"
        mock_row2.executions_count = 5
        mock_row2.avg_time = 8.0
        mock_row2.successful_actions = 10
        mock_row2.failed_actions = 2

        # Мокаем запрос с join
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_row1, mock_row2]

        result = await analytics_service.get_robot_performance()

        assert len(result["robots"]) == 2

        # Проверяем первого робота
        robot1 = result["robots"][0]
        assert robot1["robot_id"] == 1
        assert robot1["robot_name"] == "Test Robot 1"
        assert robot1["executions_count"] == 10
        assert robot1["avg_execution_time_seconds"] == 5.5
        assert abs(robot1["actions_success_rate"] - 83.33) < 0.01  # 25/30 * 100 ≈ 83.33

        # Проверяем второго робота
        robot2 = result["robots"][1]
        assert robot2["robot_id"] == 2
        assert robot2["robot_name"] == "Test Robot 2"
        assert robot2["executions_count"] == 5
        assert robot2["avg_execution_time_seconds"] == 8.0
        assert abs(robot2["actions_success_rate"] - 83.33) < 0.01  # 10/12 * 100 ≈ 83.33

    @pytest.mark.asyncio
    async def test_get_robot_performance_with_filters(self, analytics_service, mock_db):
        """Тест производительности роботов с фильтрами"""
        robot_id = 1
        start_date = datetime(2024, 1, 1)

        # Мокаем запрос с join
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_robot_performance(
            robot_id=robot_id,
            start_date=start_date
        )

        assert mock_query.filter.call_count >= 2  # Фильтры по robot_id и дате

    @pytest.mark.asyncio
    async def test_get_action_type_stats_empty(self, analytics_service, mock_db):
        """Тест статистики типов действий - пустой результат"""
        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_action_type_stats()

        assert result["actions"] == []
        assert result["summary"]["total_action_types"] == 0

    @pytest.mark.asyncio
    async def test_get_action_type_stats_with_data(self, analytics_service, mock_db):
        """Тест статистики типов действий с данными"""
        # Мокаем выполнение с actions_executed
        mock_execution = MagicMock()
        mock_execution.actions_executed = [
            {"action_type": "send_email", "success": True},
            {"action_type": "send_email", "success": False},
            {"action_type": "update_field", "success": True}
        ]

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_execution]

        result = await analytics_service.get_action_type_stats()

        assert len(result["actions"]) == 2
        actions = {a["action_type"]: a for a in result["actions"]}

        assert actions["send_email"]["executions"] == 2
        assert actions["send_email"]["successful"] == 1
        assert actions["send_email"]["failed"] == 1
        assert actions["send_email"]["success_rate"] == 50.0

        assert actions["update_field"]["executions"] == 1
        assert actions["update_field"]["successful"] == 1
        assert actions["update_field"]["success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_error_analysis_empty(self, analytics_service, mock_db):
        """Тест анализа ошибок - пустой результат"""
        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = await analytics_service.get_error_analysis()

        assert result["errors"] == []
        assert result["error_types"] == {}
        assert result["summary"]["total_errors"] == 0

    @pytest.mark.asyncio
    async def test_get_error_analysis_with_data(self, analytics_service, mock_db):
        """Тест анализа ошибок с данными"""
        # Мокаем неудачное выполнение
        mock_execution = MagicMock()
        mock_execution.id = 1
        mock_execution.entity_type = EntityType.CUSTOMER
        mock_execution.entity_id = 123
        mock_execution.robot = MagicMock()
        mock_execution.robot.name = "Test Robot"
        mock_execution.error_message = "Connection timeout"
        mock_execution.started_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_execution.execution_time_seconds = 30.0

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_execution]

        result = await analytics_service.get_error_analysis()

        assert len(result["errors"]) == 1
        error = result["errors"][0]
        assert error["execution_id"] == 1
        assert error["entity_type"] == "CUSTOMER"
        assert error["error_message"] == "Connection timeout"

        assert result["error_types"]["timeout"] == 1
        assert result["summary"]["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_get_process_efficiency_empty(self, analytics_service, mock_db):
        """Тест эффективности процессов - пустой результат"""
        # Мокаем запросы
        mock_stages_query = MagicMock()
        mock_db.query.return_value = mock_stages_query
        mock_stages_query.filter.return_value = mock_stages_query
        mock_stages_query.all.return_value = []

        result = await analytics_service.get_process_efficiency()

        assert result["processes"] == []
        assert result["summary"]["total_processes"] == 0

    @pytest.mark.asyncio
    async def test_get_process_efficiency_with_data(self, analytics_service, mock_db):
        """Тест эффективности процессов с данными"""
        # Мокаем стадию
        mock_stage = MagicMock()
        mock_stage.id = 1
        mock_stage.process_id = 1
        mock_stage.process = MagicMock()
        mock_stage.process.name = "Test Process"
        mock_stage.name = "Test Stage"

        # Мокаем выполнение
        mock_execution = MagicMock()
        mock_execution.execution_status = "completed"
        mock_execution.execution_time_seconds = 10.0

        # Мокаем запросы
        mock_stages_query = MagicMock()
        mock_executions_query = MagicMock()

        # Правильный мок для query
        mock_db.query.return_value = mock_stages_query
        mock_stages_query.filter.return_value = mock_stages_query
        mock_stages_query.all.return_value = [mock_stage]

        # Мокаем второй вызов query для выполнений
        mock_db.query.side_effect = [mock_stages_query, mock_executions_query]
        mock_executions_query.filter.return_value = mock_executions_query
        mock_executions_query.all.return_value = [mock_execution]

        result = await analytics_service.get_process_efficiency()

        assert len(result["processes"]) == 1
        process = result["processes"][0]
        assert process["process_id"] == 1
        assert len(process["stages"]) == 1

        stage = process["stages"][0]
        assert stage["stage_name"] == "Test Stage"
        assert stage["executions"] == 1
        assert stage["successful"] == 1
        assert stage["success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_hourly_distribution(self, analytics_service, mock_db):
        """Тест почасового распределения"""
        # Мокаем результат SQL запроса
        mock_row = MagicMock()
        mock_row.hour = datetime(2024, 1, 1, 12, 0, 0)
        mock_row.executions_count = 5
        mock_row.avg_time = 8.5
        mock_row.successful_actions = 20
        mock_row.failed_actions = 5

        # Создаем список для итерации
        mock_rows = [mock_row]
        mock_result = MagicMock()
        mock_result.__iter__ = lambda: iter(mock_rows)
        mock_db.execute.return_value = mock_result

        # Мокаем text() для SQL запроса
        with patch('src.aicrm.services.automation.analytics_service.text') as mock_text:
            mock_text.return_value = "SELECT * FROM test"
            result = await analytics_service.get_hourly_distribution()

        assert "hourly_distribution" in result
        assert len(result["hourly_distribution"]) == 1
        hour_data = result["hourly_distribution"][0]
        assert hour_data["executions_count"] == 5
        assert hour_data["avg_execution_time_seconds"] == 8.5
        assert hour_data["actions_success_rate"] == 80.0  # 20/25 * 100

    def test_classify_error_timeout(self, analytics_service):
        """Тест классификации ошибок - таймаут"""
        error_msg = "Connection timeout occurred"
        result = analytics_service._classify_error(error_msg)
        assert result == "timeout"

    def test_classify_error_network(self, analytics_service):
        """Тест классификации ошибок - сеть"""
        error_msg = "Network connection failed"
        result = analytics_service._classify_error(error_msg)
        assert result == "network"

    def test_classify_error_permission(self, analytics_service):
        """Тест классификации ошибок - права доступа"""
        error_msg = "Permission denied"
        result = analytics_service._classify_error(error_msg)
        assert result == "permission"

    def test_classify_error_validation(self, analytics_service):
        """Тест классификации ошибок - валидация"""
        error_msg = "Invalid input data"
        result = analytics_service._classify_error(error_msg)
        assert result == "validation"

    def test_classify_error_other(self, analytics_service):
        """Тест классификации ошибок - другие"""
        error_msg = "Unknown error occurred"
        result = analytics_service._classify_error(error_msg)
        assert result == "other"

    @pytest.mark.asyncio
    async def test_error_handling_in_stats(self, analytics_service, mock_db):
        """Тест обработки ошибок в методах статистики"""
        # Мокаем исключение в запросе
        mock_db.query.side_effect = Exception("Database error")

        result = await analytics_service.get_execution_stats()
        assert "error" in result
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_error_handling_in_robot_performance(self, analytics_service, mock_db):
        """Тест обработки ошибок в производительности роботов"""
        mock_db.query.side_effect = Exception("Query error")

        result = await analytics_service.get_robot_performance()
        assert "error" in result
        assert "Query error" in result["error"]
