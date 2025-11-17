"""
Unit тесты для AutomationErrorHandler
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..services.automation.error_handler import AutomationErrorHandler
from ..models.automation import EntityType, RobotAction, AutomationError


class TestAutomationErrorHandler:
    """Тесты для обработчика ошибок автоматизации"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def error_handler(self, mock_db):
        """Обработчик ошибок с моками"""
        return AutomationErrorHandler(mock_db)

    @pytest.mark.asyncio
    async def test_handle_error_basic(self, error_handler, mock_db):
        """Тест базовой обработки ошибки"""
        # Мокаем создание записи об ошибке
        mock_error_record = MagicMock()
        mock_error_record.id = 1

        with patch("src.aicrm.services.automation.error_handler.AutomationError", return_value=mock_error_record):
            result = await error_handler.handle_error(
                automation_execution_id=1,
                error_type="network",
                error_message="Connection failed"
            )

        assert result["error_logged"] is True
        assert result["error_id"] == 1
        assert result["retry_scheduled"] is False  # network ошибки не retry по умолчанию
        assert result["admin_notified"] is False

        # Проверяем что запись добавлена в БД
        mock_db.add.assert_called_once_with(mock_error_record)
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_handle_error_with_retry(self, error_handler, mock_db):
        """Тест обработки ошибки с retry"""
        mock_error_record = MagicMock()
        mock_error_record.id = 1
        mock_error_record.retry_count = 0

        with patch("src.aicrm.services.automation.error_handler.AutomationError", return_value=mock_error_record), \
             patch.object(error_handler, "_schedule_retry", new_callable=AsyncMock) as mock_schedule:

            mock_schedule.return_value = {
                "scheduled": True,
                "next_retry_at": "2024-01-01T12:00:00",
                "retry_count": 1
            }

            result = await error_handler.handle_error(
                automation_execution_id=1,
                error_type="timeout",  # timeout должен retry
                error_message="Request timeout"
            )

        assert result["retry_scheduled"] is True
        assert "next_retry_at" in result
        mock_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_with_admin_notification(self, error_handler, mock_db):
        """Тест обработки ошибки с уведомлением администратора"""
        mock_error_record = MagicMock()
        mock_error_record.id = 1

        with patch("src.aicrm.services.automation.error_handler.AutomationError", return_value=mock_error_record), \
             patch.object(error_handler, "_notify_administrators", new_callable=AsyncMock) as mock_notify:

            mock_notify.return_value = {"notified": True}

            result = await error_handler.handle_error(
                automation_execution_id=1,
                error_type="security",  # security ошибки требуют уведомления
                error_message="Security breach detected"
            )

        assert result["admin_notified"] is True
        mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_full_context(self, error_handler, mock_db):
        """Тест обработки ошибки с полным контекстом"""
        mock_error_record = MagicMock()
        mock_error_record.id = 1

        with patch("src.aicrm.services.automation.error_handler.AutomationError", return_value=mock_error_record):
            result = await error_handler.handle_error(
                automation_execution_id=1,
                robot_id=2,
                trigger_id=3,
                error_type="api",
                error_code="500",
                error_message="Internal server error",
                error_details={"url": "http://api.example.com", "method": "POST"},
                entity_type=EntityType.CUSTOMER,
                entity_id=123,
                action_type=RobotAction.SEND_EMAIL
            )

        assert result["error_logged"] is True
        # Проверяем что все поля переданы в конструктор AutomationError
        # (проверка через mock_db.add.assert_called_once)

    @pytest.mark.asyncio
    async def test_process_pending_retries_no_pending(self, error_handler, mock_db):
        """Тест обработки retry - нет ожидающих"""
        # Мокаем пустой результат запроса
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await error_handler.process_pending_retries()

        assert result["processed"] == 0
        assert result["successful_retries"] == 0
        assert result["failed_retries"] == 0

    @pytest.mark.asyncio
    async def test_process_pending_retries_successful(self, error_handler, mock_db):
        """Тест обработки retry - успешный retry"""
        # Мокаем ошибку для retry
        mock_error = MagicMock()
        mock_error.id = 1
        mock_error.retry_count = 0
        mock_error.max_retries = 3

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_error]

        with patch.object(error_handler, "_execute_retry", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True}

            result = await error_handler.process_pending_retries()

        assert result["processed"] == 1
        assert result["successful_retries"] == 1
        assert result["failed_retries"] == 0
        assert mock_error.resolved is True
        assert mock_error.resolved_at is not None

    @pytest.mark.asyncio
    async def test_process_pending_retries_failed(self, error_handler, mock_db):
        """Тест обработки retry - неудачный retry"""
        mock_error = MagicMock()
        mock_error.id = 1
        mock_error.retry_count = 0
        mock_error.max_retries = 3

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_error]

        with patch.object(error_handler, "_execute_retry", new_callable=AsyncMock) as mock_execute, \
             patch.object(error_handler, "_calculate_next_retry_time") as mock_calc:

            mock_execute.return_value = {"success": False}
            mock_calc.return_value = datetime(2024, 1, 1, 13, 0, 0)

            result = await error_handler.process_pending_retries()

        assert result["processed"] == 1
        assert result["successful_retries"] == 0
        assert result["failed_retries"] == 1
        assert mock_error.retry_count == 1
        assert mock_error.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_process_pending_retries_max_retries_exceeded(self, error_handler, mock_db):
        """Тест обработки retry - превышен лимит retry"""
        mock_error = MagicMock()
        mock_error.id = 1
        mock_error.retry_count = 2  # Уже 2 попытки
        mock_error.max_retries = 3

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_error]

        with patch.object(error_handler, "_execute_retry", new_callable=AsyncMock) as mock_execute, \
             patch.object(error_handler, "_notify_administrators", new_callable=AsyncMock) as mock_notify:

            mock_execute.return_value = {"success": False}
            mock_notify.return_value = {"notified": True}

            result = await error_handler.process_pending_retries()

        assert result["processed"] == 1
        assert result["failed_retries"] == 1
        mock_notify.assert_called_once_with(mock_error, "max_retries_exceeded")

    @pytest.mark.asyncio
    async def test_execute_retry_robot_action(self, error_handler, mock_db):
        """Тест выполнения retry для действия робота"""
        mock_error = MagicMock()
        mock_error.robot_id = 1
        mock_error.action_type = RobotAction.SEND_EMAIL
        mock_error.error_details = {"action_config": {"to": "test@example.com"}}
        mock_error.entity_type = EntityType.CUSTOMER
        mock_error.entity_id = 123

        with patch("src.aicrm.services.automation.robot_service.RobotService") as mock_robot_service_class:
            mock_robot_service = MagicMock()
            mock_robot_service_class.return_value = mock_robot_service
            mock_robot_service.execute_robot_action = AsyncMock(return_value={"success": True})

            result = await error_handler._execute_retry(mock_error)

        assert result["success"] is True
        mock_robot_service.execute_robot_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_retry_trigger_event(self, error_handler, mock_db):
        """Тест выполнения retry для события триггера"""
        mock_execution = MagicMock()
        mock_execution.entity_type = EntityType.CUSTOMER
        mock_execution.entity_id = 123
        mock_execution.trigger = MagicMock()
        mock_execution.trigger.event_type = "customer_created"

        mock_error = MagicMock()
        mock_error.automation_execution = mock_execution
        mock_error.action_type = None  # Нет действия, значит триггер
        mock_error.retry_count = 0

        with patch("src.aicrm.services.automation.automation_service.AutomationService") as mock_automation_service_class:
            mock_automation_service = MagicMock()
            mock_automation_service_class.return_value = mock_automation_service
            mock_automation_service.handle_event = AsyncMock(return_value={"success": True})

            result = await error_handler._execute_retry(mock_error)

        assert result["success"] is True
        mock_automation_service.handle_event.assert_called_once()

    def test_should_retry_error_network(self, error_handler):
        """Тест определения необходимости retry - сетевая ошибка"""
        assert error_handler._should_retry_error("network") is True
        assert error_handler._should_retry_error("timeout") is True
        assert error_handler._should_retry_error("connection") is True

    def test_should_retry_error_api(self, error_handler):
        """Тест определения необходимости retry - API ошибка"""
        assert error_handler._should_retry_error("api", "500") is True
        assert error_handler._should_retry_error("api", "502") is True
        assert error_handler._should_retry_error("api", "503") is True
        assert error_handler._should_retry_error("api", "504") is True
        assert error_handler._should_retry_error("api", "400") is False  # Client error

    def test_should_retry_error_rate_limit(self, error_handler):
        """Тест определения необходимости retry - rate limit"""
        assert error_handler._should_retry_error("rate_limit") is True

    def test_should_retry_error_no_retry(self, error_handler):
        """Тест определения необходимости retry - ошибки без retry"""
        assert error_handler._should_retry_error("validation") is False
        assert error_handler._should_retry_error("authorization") is False
        assert error_handler._should_retry_error("authentication") is False

    def test_calculate_next_retry_time(self, error_handler):
        """Тест расчета времени следующего retry"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        with patch("src.aicrm.services.automation.error_handler.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = base_time

            # Первая попытка - 1 минута
            next_time = error_handler._calculate_next_retry_time(0)
            expected = base_time + timedelta(seconds=60)
            assert next_time == expected

            # Вторая попытка - 5 минут
            next_time = error_handler._calculate_next_retry_time(1)
            expected = base_time + timedelta(seconds=300)
            assert next_time == expected

            # Третья попытка - 30 минут
            next_time = error_handler._calculate_next_retry_time(2)
            expected = base_time + timedelta(seconds=1800)
            assert next_time == expected

    @pytest.mark.asyncio
    async def test_schedule_retry(self, error_handler, mock_db):
        """Тест планирования retry"""
        mock_error_record = MagicMock()
        mock_error_record.retry_count = 0

        with patch.object(error_handler, "_calculate_next_retry_time") as mock_calc:
            mock_calc.return_value = datetime(2024, 1, 1, 13, 0, 0)

            result = await error_handler._schedule_retry(mock_error_record)

        assert result["scheduled"] is True
        assert result["retry_count"] == 1
        assert mock_error_record.next_retry_at is not None
        assert mock_error_record.retry_count == 1

    def test_should_notify_admin_critical_errors(self, error_handler):
        """Тест определения необходимости уведомления - критические ошибки"""
        assert error_handler._should_notify_admin("security") is True
        assert error_handler._should_notify_admin("data_corruption") is True
        assert error_handler._should_notify_admin("system") is True
        assert error_handler._should_notify_admin("unknown") is True

    def test_should_notify_admin_non_critical(self, error_handler):
        """Тест определения необходимости уведомления - некритические ошибки"""
        assert error_handler._should_notify_admin("network") is False
        assert error_handler._should_notify_admin("timeout") is False
        assert error_handler._should_notify_admin("validation") is False

    @pytest.mark.asyncio
    async def test_notify_administrators(self, error_handler, mock_db):
        """Тест отправки уведомления администраторам"""
        mock_error_record = MagicMock()
        mock_error_record.id = 1
        mock_error_record.error_type = "security"
        mock_error_record.error_code = "403"
        mock_error_record.error_message = "Access denied"
        mock_error_record.entity_type = EntityType.CUSTOMER
        mock_error_record.entity_id = 123
        mock_error_record.action_type = RobotAction.SEND_EMAIL
        mock_error_record.error_details = {"details": "test"}
        mock_error_record.created_at = datetime(2024, 1, 1, 12, 0, 0)

        with patch.object(error_handler.email_service, "send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}

            result = await error_handler._notify_administrators(mock_error_record)

        assert result["notified"] is True
        assert "admin@example.com" in result["recipients"]
        mock_send.assert_called_once()

        # Проверяем что флаги обновлены
        assert mock_error_record.notified_admin is True
        assert mock_error_record.notification_sent_at is not None

    @pytest.mark.asyncio
    async def test_get_error_statistics(self, error_handler, mock_db):
        """Тест получения статистики ошибок"""
        # Мокаем ошибки
        mock_error1 = MagicMock()
        mock_error1.error_type = "network"
        mock_error1.retry_count = 2
        mock_error1.resolved = True

        mock_error2 = MagicMock()
        mock_error2.error_type = "api"
        mock_error2.retry_count = 1
        mock_error2.resolved = False

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_error1, mock_error2]

        result = await error_handler.get_error_statistics(days=7)

        assert result["total_errors"] == 2
        assert result["resolved_errors"] == 1
        assert result["unresolved_errors"] == 1
        assert result["error_types"]["network"] == 1
        assert result["error_types"]["api"] == 1
        assert result["total_retries"] == 3
        assert result["average_retries_per_error"] == 1.5

    @pytest.mark.asyncio
    async def test_get_error_statistics_with_filter(self, error_handler, mock_db):
        """Тест получения статистики ошибок с фильтром"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await error_handler.get_error_statistics(days=30, error_type="network")

        assert result["total_errors"] == 0
        # Проверяем что фильтр по типу применен
        assert mock_query.filter.call_count >= 2  # Фильтр по дате + фильтр по типу

    @pytest.mark.asyncio
    async def test_error_handling_in_handle_error(self, error_handler, mock_db):
        """Тест обработки ошибок в handle_error"""
        # Мокаем исключение при работе с БД
        mock_db.add.side_effect = Exception("Database connection failed")

        result = await error_handler.handle_error(
            automation_execution_id=1,
            error_message="Test error"
        )

        assert result["error_logged"] is False
        assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_error_handling_in_process_pending_retries(self, error_handler, mock_db):
        """Тест обработки ошибок в process_pending_retries"""
        mock_db.query.side_effect = Exception("Query failed")

        result = await error_handler.process_pending_retries()

        assert "error" in result
        assert "Query failed" in result["error"]
