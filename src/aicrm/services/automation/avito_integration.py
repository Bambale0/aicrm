"""
Сервис интеграции Avito для автоматизации
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ...models.automation import TriggerEvent, EntityType
from ...services.automation.automation_service import AutomationService
from ...services.avito_handler import AvitoCommunicationHandler
from ...services.ai.client import AIClient
from ...services.task import TaskService

logger = logging.getLogger(__name__)


class AvitoIntegrationService:
    """Сервис для интеграции Avito с системой автоматизации"""

    def __init__(self, db: Session):
        self.db = db
        self.automation_service = AutomationService(db)
        self.avito_handler = AvitoCommunicationHandler(db)
        self.ai_client = AIClient()

    async def handle_message_received(
        self,
        chat_id: str,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка полученного сообщения от Avito

        Args:
            chat_id: ID чата в Avito
            message_data: Данные сообщения

        Returns:
            Dict с результатом обработки
        """
        try:
            # Сохраняем сообщение в БД
            saved_message = await self.avito_handler.save_message(
                chat_id=chat_id,
                message=message_data,
                direction="inbound"
            )

            if not saved_message:
                return {"success": False, "error": "Failed to save message"}

            # Запускаем автоматизацию для события message_received
            automation_result = await self.automation_service.handle_event(
                entity_type=EntityType.COMMUNICATION,
                event_type=TriggerEvent.AVITO_MESSAGE_RECEIVED,
                entity_id=saved_message.id,
                event_data={
                    "chat_id": chat_id,
                    "message": message_data,
                    "saved_message_id": saved_message.id
                }
            )

            return {
                "success": True,
                "message_saved": True,
                "automation_triggered": True,
                "automation_result": automation_result
            }

        except Exception as e:
            logger.error(f"Error handling Avito message: {e}")
            return {"success": False, "error": str(e)}

    async def handle_chat_created(
        self,
        chat_id: str,
        chat_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка создания нового чата в Avito

        Args:
            chat_id: ID чата
            chat_data: Данные чата

        Returns:
            Dict с результатом обработки
        """
        try:
            # Сохраняем информацию о чате
            chat_info = await self.avito_handler.save_chat_info(chat_id, chat_data)

            # Запускаем автоматизацию для события chat_created
            automation_result = await self.automation_service.handle_event(
                entity_type=EntityType.COMMUNICATION,
                event_type=TriggerEvent.AVITO_CHAT_CREATED,
                entity_id=chat_info.get("id", 0),
                event_data={
                    "chat_id": chat_id,
                    "chat_data": chat_data
                }
            )

            return {
                "success": True,
                "chat_saved": True,
                "automation_triggered": True,
                "automation_result": automation_result
            }

        except Exception as e:
            logger.error(f"Error handling Avito chat created: {e}")
            return {"success": False, "error": str(e)}

    async def handle_chat_closed(
        self,
        chat_id: str,
        close_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка закрытия чата в Avito

        Args:
            chat_id: ID чата
            close_data: Данные закрытия

        Returns:
            Dict с результатом обработки
        """
        try:
            # Обновляем статус чата
            await self.avito_handler.update_chat_status(chat_id, "closed", close_data)

            # Запускаем автоматизацию для события chat_closed
            automation_result = await self.automation_service.handle_event(
                entity_type=EntityType.COMMUNICATION,
                event_type=TriggerEvent.AVITO_CHAT_CLOSED,
                entity_id=0,  # Нет конкретной сущности
                event_data={
                    "chat_id": chat_id,
                    "close_data": close_data
                }
            )

            return {
                "success": True,
                "chat_updated": True,
                "automation_triggered": True,
                "automation_result": automation_result
            }

        except Exception as e:
            logger.error(f"Error handling Avito chat closed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_auto_response(
        self,
        chat_id: str,
        message_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерация автоматического ответа через AI

        Args:
            chat_id: ID чата
            message_text: Текст сообщения
            context: Дополнительный контекст

        Returns:
            Dict с сгенерированным ответом
        """
        try:
            # Получаем историю чата для контекста
            chat_history = await self.avito_handler.get_chat_history(chat_id, limit=10)

            # Формируем контекст для AI
            ai_context = {
                "chat_history": chat_history,
                "current_message": message_text,
                "context": context or {}
            }

            # Генерируем ответ
            response = await self.ai_client.generate_response(
                prompt=self._build_response_prompt(ai_context),
                context=ai_context
            )

            if response.get("success"):
                generated_text = response.get("response", "")

                # Отправляем ответ через Avito
                send_result = await self.avito_handler.send_message(chat_id, generated_text)

                return {
                    "success": True,
                    "response_generated": generated_text,
                    "response_sent": send_result.get("success", False),
                    "message_id": send_result.get("message_id")
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate response",
                    "ai_error": response.get("error")
                }

        except Exception as e:
            logger.error(f"Error generating auto response: {e}")
            return {"success": False, "error": str(e)}

    async def send_standard_response(
        self,
        chat_id: str,
        response_type: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Отправка стандартного ответа

        Args:
            chat_id: ID чата
            response_type: Тип стандартного ответа
            custom_data: Кастомные данные для подстановки

        Returns:
            Dict с результатом отправки
        """
        try:
            # Получаем шаблон ответа
            template = self._get_standard_response_template(response_type)

            if not template:
                return {"success": False, "error": f"Unknown response type: {response_type}"}

            # Заменяем плейсхолдеры
            message_text = self._replace_placeholders(template, custom_data or {})

            # Отправляем ответ
            send_result = await self.avito_handler.send_message(chat_id, message_text)

            return {
                "success": send_result.get("success", False),
                "response_type": response_type,
                "message_sent": message_text[:100] + "..." if len(message_text) > 100 else message_text,
                "message_id": send_result.get("message_id")
            }

        except Exception as e:
            logger.error(f"Error sending standard response: {e}")
            return {"success": False, "error": str(e)}

    async def escalate_complex_query(
        self,
        chat_id: str,
        message_text: str,
        escalation_reason: str
    ) -> Dict[str, Any]:
        """
        Эскалация сложного запроса

        Args:
            chat_id: ID чата
            message_text: Текст сообщения
            escalation_reason: Причина эскалации

        Returns:
            Dict с результатом эскалации
        """
        try:
            # Отправляем уведомление о эскалации
            escalation_message = f"Ваш запрос передан специалисту. Причина: {escalation_reason}"

            send_result = await self.avito_handler.send_message(chat_id, escalation_message)

            # Создаем задачу для специалиста через TaskService
            task_data = {
                "title": f"Avito эскалация: {chat_id}",
                "description": f"Сложный запрос от клиента в чате {chat_id}. "
                              f"Причина эскалации: {escalation_reason}. "
                              f"Сообщение: {message_text}",
                "priority": "high",
                "assigned_to": None,  # Назначить ответственному менеджеру
                "deadline": None,  # Без дедлайна, но с высоким приоритетом
                "source": "avito_integration"
            }

            # Создаем задачу через TaskService
            task_service = TaskService(self.db)
            created_task = task_service.create_task(
                self.db,
                task_data,
                created_by=1  # Системный пользователь
            )

            logger.info(f"Escalation task created for chat {chat_id}: task_id={created_task.id}")

            return {
                "success": True,
                "escalation_message_sent": send_result.get("success", False),
                "task_created": True,
                "escalation_reason": escalation_reason
            }

        except Exception as e:
            logger.error(f"Error escalating query: {e}")
            return {"success": False, "error": str(e)}

    def _build_response_prompt(self, context: Dict[str, Any]) -> str:
        """Построение промпта для генерации ответа"""
        chat_history = context.get("chat_history", [])
        current_message = context.get("current_message", "")

        history_text = ""
        if chat_history:
            history_lines = []
            for msg in chat_history[-5:]:  # Последние 5 сообщений
                direction = "Клиент" if msg.get("direction") == "inbound" else "Менеджер"
                history_lines.append(f"{direction}: {msg.get('content', '')[:100]}")
            history_text = "\n".join(history_lines)

        prompt = f"""
Ты - профессиональный менеджер по продажам печатной продукции.
Тебе пишет потенциальный клиент через Avito.

История переписки:
{history_text}

Текущее сообщение клиента: "{current_message}"

Требования:
1. Будь вежливым и профессиональным
2. Дай краткий, но информативный ответ
3. Если нужно уточнить детали - задай 1-2 вопроса
4. Не обещай невозможного
5. Ответ должен быть на русском языке

Сгенерируй ответ клиенту:
"""

        return prompt.strip()

    def _get_standard_response_template(self, response_type: str) -> Optional[str]:
        """Получение шаблона стандартного ответа"""
        templates = {
            "greeting": "Здравствуйте! Спасибо за интерес к нашей продукции. "
                       "Чем могу помочь?",
            "working_hours": "Наши рабочие часы: Пн-Пт 9:00-18:00. "
                           "Мы ответим на ваше сообщение в ближайшее время.",
            "price_request": "Для точного расчета стоимости мне нужно знать: "
                           "тираж, формат, вид печати и срочность. "
                           "Пожалуйста, уточните детали.",
            "delivery_info": "Мы доставляем заказы по Москве и МО курьером, "
                           "по России - транспортными компаниями. "
                           "Стоимость доставки рассчитывается индивидуально.",
            "contact_request": "Вы можете связаться с нами по телефону: +7-XXX-XXX-XX-XX "
                             "или написать в WhatsApp: wa.me/7XXXXXXXXXX"
        }

        return templates.get(response_type)

    def _replace_placeholders(self, template: str, data: Dict[str, Any]) -> str:
        """Замена плейсхолдеров в шаблоне"""
        result = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result


# Глобальный экземпляр сервиса
avito_integration_service = AvitoIntegrationService
