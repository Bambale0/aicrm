"""
Тесты интеграции автоматизации с Avito
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from src.aicrm.services.automation.avito_integration import AvitoTaskIntegration as AvitoIntegrationService
from src.aicrm.services.automation.automation_service import AutomationService
from src.aicrm.models.automation import TriggerEvent, EntityType


class TestAvitoIntegrationService:
    """Тесты сервиса интеграции Avito с автоматизацией"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def avito_integration_service(self, mock_db):
        """Экземпляр сервиса интеграции Avito"""
        return AvitoIntegrationService(mock_db)

    @pytest.fixture
    def sample_message_data(self):
        """Пример данных сообщения Avito"""
        return {
            "id": "msg_123",
            "content": "Здравствуйте, интересует ваш товар",
            "direction": "inbound",
            "created": "2025-01-14T10:00:00Z"
        }

    @pytest.fixture
    def sample_chat_data(self):
        """Пример данных чата Avito"""
        return {
            "id": "chat_456",
            "item_id": "item_789",
            "user_id": "user_101",
            "status": "active",
            "created": "2025-01-14T09:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_handle_message_received_success(
        self,
        avito_integration_service,
        mock_db,
        sample_message_data
    ):
        """Тест успешной обработки полученного сообщения"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.save_message.return_value = MagicMock(id=1)
        avito_integration_service.avito_handler = mock_avito_handler

        # Настройка мока для automation_service
        mock_automation_service = AsyncMock()
        mock_automation_service.handle_event.return_value = {"success": True}
        avito_integration_service.automation_service = mock_automation_service

        # Выполнение теста
        result = await avito_integration_service.handle_message_received(
            chat_id="chat_456",
            message_data=sample_message_data
        )

        # Проверки
        assert result["success"] is True
        assert result["message_saved"] is True
        assert result["automation_triggered"] is True

        # Проверяем вызовы
        mock_avito_handler.save_message.assert_called_once_with(
            chat_id="chat_456",
            message=sample_message_data,
            direction="inbound"
        )

        mock_automation_service.handle_event.assert_called_once_with(
            entity_type=EntityType.COMMUNICATION,
            event_type=TriggerEvent.AVITO_MESSAGE_RECEIVED,
            entity_id=1,
            event_data={
                "chat_id": "chat_456",
                "message": sample_message_data,
                "saved_message_id": 1
            }
        )

    @pytest.mark.asyncio
    async def test_handle_message_received_save_failed(
        self,
        avito_integration_service,
        mock_db,
        sample_message_data
    ):
        """Тест обработки сообщения при неудаче сохранения"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.save_message.return_value = None
        avito_integration_service.avito_handler = mock_avito_handler

        # Выполнение теста
        result = await avito_integration_service.handle_message_received(
            chat_id="chat_456",
            message_data=sample_message_data
        )

        # Проверки
        assert result["success"] is False
        assert result["error"] == "Failed to save message"

    @pytest.mark.asyncio
    async def test_handle_chat_created_success(
        self,
        avito_integration_service,
        mock_db,
        sample_chat_data
    ):
        """Тест успешной обработки создания чата"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.save_chat_info.return_value = {"id": 1}
        avito_integration_service.avito_handler = mock_avito_handler

        # Настройка мока для automation_service
        mock_automation_service = AsyncMock()
        mock_automation_service.handle_event.return_value = {"success": True}
        avito_integration_service.automation_service = mock_automation_service

        # Выполнение теста
        result = await avito_integration_service.handle_chat_created(
            chat_id="chat_456",
            chat_data=sample_chat_data
        )

        # Проверки
        assert result["success"] is True
        assert result["chat_saved"] is True
        assert result["automation_triggered"] is True

    @pytest.mark.asyncio
    async def test_handle_chat_closed_success(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест успешной обработки закрытия чата"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        avito_integration_service.avito_handler = mock_avito_handler

        # Настройка мока для automation_service
        mock_automation_service = AsyncMock()
        mock_automation_service.handle_event.return_value = {"success": True}
        avito_integration_service.automation_service = mock_automation_service

        # Выполнение теста
        result = await avito_integration_service.handle_chat_closed(
            chat_id="chat_456",
            close_data={"reason": "completed"}
        )

        # Проверки
        assert result["success"] is True
        assert result["chat_updated"] is True
        assert result["automation_triggered"] is True

    @pytest.mark.asyncio
    async def test_generate_auto_response_success(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест успешной генерации автоматического ответа"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.get_chat_history.return_value = [
            {"content": "Привет", "direction": "inbound"},
            {"content": "Здравствуйте!", "direction": "outbound"}
        ]
        mock_avito_handler.send_message.return_value = {"success": True, "message_id": "msg_789"}
        avito_integration_service.avito_handler = mock_avito_handler

        # Настройка мока для AI клиента
        mock_ai_client = AsyncMock()
        mock_ai_client.generate_response.return_value = {
            "success": True,
            "response": "Здравствуйте! Чем могу помочь?"
        }
        avito_integration_service.ai_client = mock_ai_client

        # Выполнение теста
        result = await avito_integration_service.generate_auto_response(
            chat_id="chat_456",
            message_text="Сколько стоит товар?"
        )

        # Проверки
        assert result["success"] is True
        assert result["response_generated"] == "Здравствуйте! Чем могу помочь?"
        assert result["response_sent"] is True
        assert result["message_id"] == "msg_789"

    @pytest.mark.asyncio
    async def test_generate_auto_response_ai_failed(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест генерации ответа при неудаче AI"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        avito_integration_service.avito_handler = mock_avito_handler

        # Настройка мока для AI клиента
        mock_ai_client = AsyncMock()
        mock_ai_client.generate_response.return_value = {
            "success": False,
            "error": "AI service unavailable"
        }
        avito_integration_service.ai_client = mock_ai_client

        # Выполнение теста
        result = await avito_integration_service.generate_auto_response(
            chat_id="chat_456",
            message_text="Сколько стоит товар?"
        )

        # Проверки
        assert result["success"] is False
        assert result["error"] == "Failed to generate response"
        assert result["ai_error"] == "AI service unavailable"

    @pytest.mark.asyncio
    async def test_send_standard_response_success(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест успешной отправки стандартного ответа"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.send_message.return_value = {"success": True, "message_id": "msg_789"}
        avito_integration_service.avito_handler = mock_avito_handler

        # Выполнение теста
        result = await avito_integration_service.send_standard_response(
            chat_id="chat_456",
            response_type="greeting"
        )

        # Проверки
        assert result["success"] is True
        assert result["response_type"] == "greeting"
        assert "Здравствуйте!" in result["message_sent"]
        assert result["message_id"] == "msg_789"

    @pytest.mark.asyncio
    async def test_send_standard_response_unknown_type(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест отправки неизвестного типа стандартного ответа"""
        # Выполнение теста
        result = await avito_integration_service.send_standard_response(
            chat_id="chat_456",
            response_type="unknown_type"
        )

        # Проверки
        assert result["success"] is False
        assert result["error"] == "Unknown response type: unknown_type"

    @pytest.mark.asyncio
    async def test_escalate_complex_query_success(
        self,
        avito_integration_service,
        mock_db
    ):
        """Тест успешной эскалации сложного запроса"""
        # Настройка мока для avito_handler
        mock_avito_handler = AsyncMock()
        mock_avito_handler.send_message.return_value = {"success": True}
        avito_integration_service.avito_handler = mock_avito_handler

        # Выполнение теста
        result = await avito_integration_service.escalate_complex_query(
            chat_id="chat_456",
            message_text="Нужен срочный заказ с доставкой",
            escalation_reason="Срочный заказ"
        )

        # Проверки
        assert result["success"] is True
        assert result["escalation_message_sent"] is True
        assert result["task_created"] is True
        assert result["escalation_reason"] == "Срочный заказ"


class TestAutomationServiceAvitoIntegration:
    """Тесты интеграции AutomationService с Avito"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def automation_service(self, mock_db):
        """Экземпляр сервиса автоматизации"""
        return AutomationService(mock_db)

    @pytest.mark.asyncio
    async def test_on_avito_message_received(
        self,
        automation_service,
        mock_db
    ):
        """Тест обработки события получения сообщения от Avito"""
        # Настройка мока для trigger_service
        mock_trigger_service = AsyncMock()
        mock_trigger_service.handle_trigger_event.return_value = [{"success": True}]
        automation_service.trigger_service = mock_trigger_service

        # Выполнение теста
        result = await automation_service.on_avito_message_received(
            chat_id="chat_456",
            message_data={"content": "Test message"}
        )

        # Проверки
        assert result["entity_type"] == "communication"
        assert result["event_type"] == "avito_message_received"
        assert result["entity_id"] == 0
        assert result["overall_success"] is True

        # Проверяем вызов trigger_service
        mock_trigger_service.handle_trigger_event.assert_called_once_with(
            EntityType.COMMUNICATION,
            TriggerEvent.AVITO_MESSAGE_RECEIVED,
            0,
            {"chat_id": "chat_456", "message_data": {"content": "Test message"}}
        )

    @pytest.mark.asyncio
    async def test_on_avito_chat_created(
        self,
        automation_service,
        mock_db
    ):
        """Тест обработки события создания чата в Avito"""
        # Настройка мока для trigger_service
        mock_trigger_service = AsyncMock()
        mock_trigger_service.handle_trigger_event.return_value = [{"success": True}]
        automation_service.trigger_service = mock_trigger_service

        # Выполнение теста
        result = await automation_service.on_avito_chat_created(
            chat_id="chat_456",
            chat_data={"user_id": "user_123"}
        )

        # Проверки
        assert result["entity_type"] == "communication"
        assert result["event_type"] == "avito_chat_created"
        assert result["entity_id"] == 0
        assert result["overall_success"] is True

    @pytest.mark.asyncio
    async def test_on_avito_chat_closed(
        self,
        automation_service,
        mock_db
    ):
        """Тест обработки события закрытия чата в Avito"""
        # Настройка мока для trigger_service
        mock_trigger_service = AsyncMock()
        mock_trigger_service.handle_trigger_event.return_value = [{"success": True}]
        automation_service.trigger_service = mock_trigger_service

        # Выполнение теста
        result = await automation_service.on_avito_chat_closed(
            chat_id="chat_456",
            close_data={"reason": "completed"}
        )

        # Проверки
        assert result["entity_type"] == "communication"
        assert result["event_type"] == "avito_chat_closed"
        assert result["entity_id"] == 0
        assert result["overall_success"] is True


class TestAvitoRobotActions:
    """Тесты действий роботов для Avito"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def avito_robot_actions(self, mock_db):
        """Экземпляр действий роботов Avito"""
        from src.aicrm.services.automation.avito_robot_actions import AvitoRobotActions
        return AvitoRobotActions(mock_db)

    @pytest.fixture
    def sample_action_config(self):
        """Пример конфигурации действия робота"""
        from src.aicrm.models.automation import RobotActionConfig, RobotAction
        config = MagicMock(spec=RobotActionConfig)
        config.action_type = RobotAction.GENERATE_AI_RESPONSE
        config.config = {
            "chat_id": "chat_456",
            "message_text": "Test message"
        }
        return config

    @pytest.mark.asyncio
    async def test_execute_generate_ai_response_success(
        self,
        avito_robot_actions,
        mock_db,
        sample_action_config
    ):
        """Тест успешного выполнения генерации AI ответа"""
        # Настройка мока для AvitoIntegrationService
        mock_integration_service = AsyncMock()
        mock_integration_service.generate_auto_response.return_value = {
            "success": True,
            "response_generated": "Test response",
            "response_sent": True,
            "message_id": "msg_123"
        }

        with patch('src.aicrm.services.automation.avito_robot_actions.AvitolntegrationService',
                   return_value=mock_integration_service):
            # Выполнение теста
            result = await avito_robot_actions._execute_generate_ai_response(
                sample_action_config,
                EntityType.COMMUNICATION,
                1
            )

            # Проверки
            assert result["status"] == "ai_response_generated"
            assert result["chat_id"] == "chat_456"
            assert result["response_generated"] == "Test response"
            assert result["response_sent"] is True
            assert result["message_id"] == "msg_123"
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_send_standard_response_success(
        self,
        avito_robot_actions,
        mock_db
    ):
        """Тест успешного выполнения отправки стандартного ответа"""
        # Создаем конфиг для действия
        from src.aicrm.models.automation import RobotActionConfig, RobotAction
        config = MagicMock(spec=RobotActionConfig)
        config.action_type = RobotAction.SEND_STANDARD_RESPONSE
        config.config = {
            "chat_id": "chat_456",
            "response_type": "greeting"
        }

        # Настройка мока для AvitoIntegrationService
        mock_integration_service = AsyncMock()
        mock_integration_service.send_standard_response.return_value = {
            "success": True,
            "response_type": "greeting",
            "message_sent": "Здравствуйте! Чем могу помочь?",
            "message_id": "msg_123"
        }

        with patch('src.aicrm.services.automation.avito_robot_actions.AvitolntegrationService',
                   return_value=mock_integration_service):
            # Выполнение теста
            result = await avito_robot_actions._execute_send_standard_response(
                config,
                EntityType.COMMUNICATION,
                1
            )

            # Проверки
            assert result["status"] == "standard_response_sent"
            assert result["chat_id"] == "chat_456"
            assert result["response_type"] == "greeting"
            assert "Здравствуйте!" in result["message_sent"]
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_escalate_complex_query_success(
        self,
        avito_robot_actions,
        mock_db
    ):
        """Тест успешного выполнения эскалации сложного запроса"""
        # Создаем конфиг для действия
        from src.aicrm.models.automation import RobotActionConfig, RobotAction
        config = MagicMock(spec=RobotActionConfig)
        config.action_type = RobotAction.ESCALATE_COMPLEX_QUERY
        config.config = {
            "chat_id": "chat_456",
            "message_text": "Нужен срочный заказ",
            "escalation_reason": "Срочный заказ"
        }

        # Настройка мока для AvitoIntegrationService
        mock_integration_service = AsyncMock()
        mock_integration_service.escalate_complex_query.return_value = {
            "success": True,
            "escalation_message_sent": True,
            "task_created": True,
            "escalation_reason": "Срочный заказ"
        }

        with patch('src.aicrm.services.automation.avito_robot_actions.AvitolntegrationService',
                   return_value=mock_integration_service):
            # Выполнение теста
            result = await avito_robot_actions._execute_escalate_complex_query(
                config,
                EntityType.COMMUNICATION,
                1
            )

            # Проверки
            assert result["status"] == "query_escalated"
            assert result["chat_id"] == "chat_456"
            assert result["escalation_reason"] == "Срочный заказ"
            assert result["escalation_message_sent"] is True
            assert result["task_created"] is True
            assert result["success"] is True
