"""
Unit тесты для RobotService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from ..services.automation.robot_service import RobotService
from ..models.automation import EntityType, RobotAction, RobotActionConfig


class TestRobotService:
    """Тесты для сервиса роботов"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def robot_service(self, mock_db):
        """Сервис роботов с моками"""
        return RobotService(mock_db)

    @pytest.mark.asyncio
    async def test_execute_stage_robots_no_robots(self, robot_service, mock_db):
        """Тест выполнения роботов стадии - нет роботов"""
        # Мокаем пустой результат запроса
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = await robot_service.execute_stage_robots(
            EntityType.CUSTOMER, 1, 1
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_execute_stage_robots_with_robots(self, robot_service, mock_db):
        """Тест выполнения роботов стадии с роботами"""
        # Мокаем робота
        mock_robot = MagicMock()
        mock_robot.id = 1
        mock_robot.name = "Test Robot"
        mock_robot.actions = []

        # Мокаем запрос
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_robot]

        with patch.object(robot_service, "_execute_robot_sequence", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [{"action_id": 1, "success": True}]

            result = await robot_service.execute_stage_robots(
                EntityType.CUSTOMER, 1, 1
            )

        assert len(result) == 1
        assert result[0]["robot_id"] == 1
        assert result[0]["success"] is True
        assert result[0]["actions_executed"] == [{"action_id": 1, "success": True}]

    @pytest.mark.asyncio
    async def test_execute_robot_sequence_no_actions(self, robot_service, mock_db):
        """Тест выполнения последовательности робота - нет действий"""
        mock_robot = MagicMock()
        mock_robot.actions = []

        result = await robot_service._execute_robot_sequence(
            mock_robot, EntityType.CUSTOMER, 1
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_execute_robot_sequence_with_actions(self, robot_service, mock_db):
        """Тест выполнения последовательности робота с действиями"""
        # Мокаем действие
        mock_action = MagicMock()
        mock_action.id = 1
        mock_action.execution_order = 1
        mock_action.delay_seconds = 0

        mock_robot = MagicMock()
        mock_robot.id = 1
        mock_robot.name = "Test Robot"
        mock_robot.actions = [mock_action]

        with patch.object(robot_service, "_execute_robot_action", new_callable=AsyncMock) as mock_execute_action:
            mock_execute_action.return_value = {"status": "success"}

            result = await robot_service._execute_robot_sequence(
                mock_robot, EntityType.CUSTOMER, 1
            )

        assert len(result) == 1
        assert result[0]["action_id"] == 1
        assert result[0]["success"] is True
        assert result[0]["result"] == {"status": "success"}

    @pytest.mark.asyncio
    async def test_execute_robot_sequence_with_delay(self, robot_service, mock_db):
        """Тест выполнения последовательности с задержкой"""
        # Мокаем действие с задержкой
        mock_action = MagicMock()
        mock_action.id = 1
        mock_action.execution_order = 1
        mock_action.delay_seconds = 1

        mock_robot = MagicMock()
        mock_robot.actions = [mock_action]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
             patch.object(robot_service, "_execute_robot_action", new_callable=AsyncMock) as mock_execute:

            mock_execute.return_value = {"status": "success"}

            result = await robot_service._execute_robot_sequence(
                mock_robot, EntityType.CUSTOMER, 1
            )

        mock_sleep.assert_called_once_with(1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_execute_robot_action_success(self, robot_service, mock_db):
        """Тест выполнения действия робота - успех"""
        action_config = {
            "action_type": "send_email",
            "config": {"to": "test@example.com"},
            "execution_order": 1,
            "delay_seconds": 0
        }

        with patch.object(robot_service, "_execute_send_email", new_callable=AsyncMock) as mock_executor:
            mock_executor.return_value = {"status": "email_sent"}

            result = await robot_service.execute_robot_action(
                1, action_config, EntityType.CUSTOMER, 1
            )

        assert result["success"] is True
        assert result["result"]["status"] == "email_sent"

    @pytest.mark.asyncio
    async def test_execute_robot_action_unknown_type(self, robot_service, mock_db):
        """Тест выполнения действия робота - неизвестный тип"""
        action_config = {
            "action_type": "unknown_action",
            "config": {},
            "execution_order": 1,
            "delay_seconds": 0
        }

        result = await robot_service.execute_robot_action(
            1, action_config, EntityType.CUSTOMER, 1
        )

        assert result["success"] is False
        assert "No executor for action type" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_send_email(self, robot_service, mock_db):
        """Тест отправки email"""
        # Мокаем конфиг действия
        action_config = MagicMock()
        action_config.config = {
            "template": "welcome",
            "email": "test@example.com"
        }

        with patch.object(robot_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data, \
             patch.object(robot_service, "_render_email_template", new_callable=AsyncMock) as mock_render, \
             patch.object(robot_service, "_get_recipient_email", new_callable=AsyncMock) as mock_get_email:

            mock_get_data.return_value = {"name": "John"}
            mock_render.return_value = {"subject": "Welcome", "body": "Hello John"}
            mock_get_email.return_value = "test@example.com"

            result = await robot_service._execute_send_email(
                action_config, EntityType.CUSTOMER, 1
            )

        assert result["status"] == "email_queued"
        assert result["template"] == "welcome"
        assert result["recipient"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_execute_send_sms(self, robot_service, mock_db):
        """Тест отправки SMS"""
        action_config = MagicMock()
        action_config.config = {
            "message": "Hello {name}",
            "phone": "+1234567890"
        }

        with patch.object(robot_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data, \
             patch.object(robot_service, "_get_recipient_phone", new_callable=AsyncMock) as mock_get_phone, \
             patch("src.aicrm.services.automation.robot_service.sms_service") as mock_sms_service:

            mock_get_data.return_value = {"name": "John"}
            mock_get_phone.return_value = "+1234567890"
            mock_sms_service.send_sms = AsyncMock(return_value={
                "success": True, "provider": "twilio", "message_id": "msg123"
            })

            result = await robot_service._execute_send_sms(
                action_config, EntityType.CUSTOMER, 1
            )

        assert result["status"] == "sms_sent"
        assert result["phone"] == "+1234567890"
        assert result["message"] == "Hello John"
        assert result["provider"] == "twilio"

    @pytest.mark.asyncio
    async def test_execute_create_task(self, robot_service, mock_db):
        """Тест создания задачи"""
        action_config = MagicMock()
        action_config.config = {
            "title": "Test Task",
            "description": "Test Description",
            "assigned_to": 2,
            "priority": "high"
        }

        with patch("src.aicrm.services.automation.robot_service.TaskService") as mock_task_service_class:
            mock_task_service = MagicMock()
            mock_task_service_class.return_value = mock_task_service
            mock_task_service.create_task = AsyncMock()

            mock_created_task = MagicMock()
            mock_created_task.id = 1
            mock_created_task.title = "Test Task"
            mock_task_service.create_task.return_value = mock_created_task

            result = await robot_service._execute_create_task(
                action_config, EntityType.CUSTOMER, 1
            )

        assert result["status"] == "task_created"
        assert result["task_id"] == 1
        assert result["task_title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_execute_update_field_customer(self, robot_service, mock_db):
        """Тест обновления поля клиента"""
        action_config = MagicMock()
        action_config.config = {
            "field": "loyalty_level",
            "value": "gold"
        }

        # Мокаем клиента
        mock_customer = MagicMock()
        mock_customer.loyalty_level = "silver"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_customer

        result = await robot_service._execute_update_field(
            action_config, EntityType.CUSTOMER, 1
        )

        assert result["status"] == "field_updated"
        assert result["field"] == "loyalty_level"
        assert result["value"] == "gold"
        assert mock_customer.loyalty_level == "gold"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_update_field_invalid_field(self, robot_service, mock_db):
        """Тест обновления поля - недопустимое поле"""
        action_config = MagicMock()
        action_config.config = {
            "field": "",  # Пустое поле
            "value": "test"
        }

        with pytest.raises(ValueError, match="Field name not specified"):
            await robot_service._execute_update_field(
                action_config, EntityType.CUSTOMER, 1
            )

    @pytest.mark.asyncio
    async def test_execute_call_external_api(self, robot_service, mock_db):
        """Тест вызова внешнего API"""
        action_config = MagicMock()
        action_config.config = {
            "method": "POST",
            "url": "https://api.example.com/webhook",
            "json_data": {"event": "test", "user_id": "{id}"},
            "headers": {"Authorization": "Bearer token"}
        }

        with patch.object(robot_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data, \
             patch("src.aicrm.services.automation.robot_service.external_api_service") as mock_api_service:

            mock_get_data.return_value = {"id": 123, "name": "John"}
            mock_api_service.call_api = AsyncMock(return_value={
                "success": True, "status_code": 200, "json": {"result": "ok"}
            })

            result = await robot_service._execute_call_external_api(
                action_config, EntityType.CUSTOMER, 1
            )

        assert result["status"] == "api_called"
        assert result["method"] == "POST"
        assert result["success"] is True
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_execute_call_external_api_missing_url(self, robot_service, mock_db):
        """Тест вызова внешнего API - отсутствует URL"""
        action_config = MagicMock()
        action_config.config = {"method": "GET"}  # Нет URL

        with pytest.raises(ValueError, match="URL not specified"):
            await robot_service._execute_call_external_api(
                action_config, EntityType.CUSTOMER, 1
            )

    @pytest.mark.asyncio
    async def test_execute_create_calendar_event(self, robot_service, mock_db):
        """Тест создания события календаря"""
        action_config = MagicMock()
        action_config.config = {
            "title": "Meeting with {name}",
            "description": "Discuss project",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T11:00:00Z",
            "attendees": ["user1@example.com"],
            "calendar_id": "primary"
        }

        with patch.object(robot_service, "_get_entity_data", new_callable=AsyncMock) as mock_get_data, \
             patch("src.aicrm.services.automation.robot_service.calendar_service") as mock_calendar_service:

            mock_get_data.return_value = {"id": 123, "name": "John"}
            mock_calendar_service.create_event = AsyncMock(return_value={
                "success": True, "event_id": "event123", "provider": "google"
            })

            result = await robot_service._execute_create_calendar_event(
                action_config, EntityType.CUSTOMER, 1
            )

        assert result["status"] == "calendar_event_created"
        assert result["title"] == "Meeting with John"
        assert result["success"] is True
        assert result["event_id"] == "event123"

    @pytest.mark.asyncio
    async def test_get_entity_data_customer(self, robot_service, mock_db):
        """Тест получения данных клиента"""
        # Мокаем клиента
        mock_customer = MagicMock()
        mock_customer.__dict__ = {"id": 1, "name": "John", "email": "john@example.com"}

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_customer

        result = await robot_service._get_entity_data(EntityType.CUSTOMER, 1)

        assert result["id"] == 1
        assert result["name"] == "John"
        assert result["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_entity_data_unknown_type(self, robot_service, mock_db):
        """Тест получения данных - неизвестный тип сущности"""
        result = await robot_service._get_entity_data(EntityType.TASK, 1)

        assert result == {}

    def test_replace_placeholders(self, robot_service):
        """Тест замены плейсхолдеров"""
        text = "Hello {name}, your ID is {id}"
        data = {"name": "John", "id": 123}

        result = robot_service._replace_placeholders(text, data)

        assert result == "Hello John, your ID is 123"

    def test_replace_placeholders_in_dict(self, robot_service):
        """Тест замены плейсхолдеров в словаре"""
        data = {
            "message": "Hello {name}",
            "user_id": "{id}",
            "nested": {
                "text": "Welcome {name} with ID {id}"
            },
            "list": ["Item {id}", "Another {name}"]
        }
        entity_data = {"name": "John", "id": 123}

        result = robot_service._replace_placeholders_in_dict(data, entity_data)

        assert result["message"] == "Hello John"
        assert result["user_id"] == "123"
        assert result["nested"]["text"] == "Welcome John with ID 123"
        assert result["list"] == ["Item 123", "Another John"]

    @pytest.mark.asyncio
    async def test_execute_robot_sequence_error_handling(self, robot_service, mock_db):
        """Тест обработки ошибок в последовательности выполнения"""
        # Мокаем действие, которое вызовет ошибку
        mock_action = MagicMock()
        mock_action.id = 1
        mock_action.execution_order = 1
        mock_action.delay_seconds = 0

        mock_robot = MagicMock()
        mock_robot.id = 1
        mock_robot.name = "Test Robot"
        mock_robot.actions = [mock_action]

        with patch.object(robot_service, "_execute_robot_action", new_callable=AsyncMock) as mock_execute, \
             patch.object(robot_service.error_handler, "handle_error", new_callable=AsyncMock) as mock_error_handler:

            mock_execute.side_effect = Exception("Action failed")
            mock_error_handler.return_value = {"error_logged": True, "retry_scheduled": False}

            result = await robot_service._execute_robot_sequence(
                mock_robot, EntityType.CUSTOMER, 1
            )

        assert len(result) == 1
        assert result[0]["success"] is False
        assert result[0]["error"] == "Action failed"
        assert result[0]["error_handled"] is True
        mock_error_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_robot_action_error(self, robot_service, mock_db):
        """Тест ошибки выполнения действия робота"""
        action_config = {
            "action_type": "send_email",
            "config": {},
            "execution_order": 1,
            "delay_seconds": 0
        }

        with patch.object(robot_service, "_execute_send_email", new_callable=AsyncMock) as mock_executor:
            mock_executor.side_effect = Exception("Email service unavailable")

            result = await robot_service.execute_robot_action(
                1, action_config, EntityType.CUSTOMER, 1
            )

        assert result["success"] is False
        assert "Email service unavailable" in result["error"]
