"""
Дополнительные действия роботов для Avito автоматизации
"""
import logging
from typing import Dict, Any
from ...models.automation import RobotActionConfig, EntityType

logger = logging.getLogger(__name__)


class AvitoRobotActions:
    """Класс с дополнительными действиями для Avito автоматизации"""

    def __init__(self, db):
        self.db = db

    async def _execute_generate_ai_response(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Генерация AI ответа для Avito чата"""
        config = action_config.config or {}

        # Получаем chat_id из конфига или из данных события
        chat_id = config.get("chat_id")
        message_text = config.get("message_text")
        context = config.get("context", {})

        if not chat_id:
            raise ValueError("Chat ID not specified for AI response generation")

        # Используем AvitoIntegrationService для генерации ответа
        from .avito_integration import AvitoIntegrationService
        avito_service = AvitoIntegrationService(self.db)

        result = await avito_service.generate_auto_response(
            chat_id=chat_id,
            message_text=message_text,
            context=context
        )

        return {
            "status": "ai_response_generated" if result.get("success") else "ai_response_failed",
            "chat_id": chat_id,
            "response_generated": result.get("response_generated", ""),
            "response_sent": result.get("response_sent", False),
            "message_id": result.get("message_id"),
            "success": result.get("success", False),
            "error": result.get("error")
        }

    async def _execute_send_standard_response(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка стандартного ответа в Avito чат"""
        config = action_config.config or {}

        chat_id = config.get("chat_id")
        response_type = config.get("response_type")
        custom_data = config.get("custom_data", {})

        if not chat_id:
            raise ValueError("Chat ID not specified for standard response")

        if not response_type:
            raise ValueError("Response type not specified")

        # Используем AvitoIntegrationService для отправки стандартного ответа
        from .avito_integration import AvitoIntegrationService
        avito_service = AvitoIntegrationService(self.db)

        result = await avito_service.send_standard_response(
            chat_id=chat_id,
            response_type=response_type,
            custom_data=custom_data
        )

        return {
            "status": "standard_response_sent" if result.get("success") else "standard_response_failed",
            "chat_id": chat_id,
            "response_type": response_type,
            "message_sent": result.get("message_sent", ""),
            "message_id": result.get("message_id"),
            "success": result.get("success", False),
            "error": result.get("error")
        }

    async def _execute_escalate_complex_query(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Эскалация сложного запроса"""
        config = action_config.config or {}

        chat_id = config.get("chat_id")
        message_text = config.get("message_text")
        escalation_reason = config.get("escalation_reason", "Сложный запрос")

        if not chat_id:
            raise ValueError("Chat ID not specified for escalation")

        # Используем AvitoIntegrationService для эскалации
        from .avito_integration import AvitoIntegrationService
        avito_service = AvitoIntegrationService(self.db)

        result = await avito_service.escalate_complex_query(
            chat_id=chat_id,
            message_text=message_text,
            escalation_reason=escalation_reason
        )

        return {
            "status": "query_escalated" if result.get("success") else "escalation_failed",
            "chat_id": chat_id,
            "escalation_reason": escalation_reason,
            "escalation_message_sent": result.get("escalation_message_sent", False),
            "task_created": result.get("task_created", False),
            "success": result.get("success", False),
            "error": result.get("error")
        }


# Глобальный экземпляр
avito_robot_actions = AvitoRobotActions
