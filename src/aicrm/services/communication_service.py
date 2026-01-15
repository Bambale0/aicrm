"""
Сервис коммуникаций с AI интеграцией
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..models.communication import Communication
from .ai.intent_service import AIIntentService, IntentType

logger = logging.getLogger(__name__)


class CommunicationService:
    """
    Многоканальный сервис коммуникаций с AI интеграцией
    """

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIIntentService()
        # Заглушки для обработчиков каналов - будут реализованы отдельно
        self.channel_handlers = {
            "telegram": None,  # TelegramHandler(),
            "email": None,  # EmailHandler(),
            "website": None,  # WebsiteHandler(),
            "avito": None,  # AvitoHandler() - будет инициализирован при первом использовании
        }

    async def handle_incoming_message(
        self, channel: str, message_data: Dict[str, Any], customer_id: int = None
    ) -> Dict[str, Any]:
        """
        Обработка входящего сообщения из любого канала с AI обработкой
        """
        try:
            # Извлечение содержимого сообщения в зависимости от канала
            message_content = self._extract_message_content(channel, message_data)

            # Получение контекста клиента
            customer_context = await self._get_customer_context(customer_id)

            # Обработка с помощью AI
            ai_result = await self.ai_service.process_customer_message(
                message_content, customer_context
            )

            # Сохранение коммуникации в базу данных
            communication = await self._save_communication(
                channel=channel,
                direction="inbound",
                content=message_content,
                customer_id=customer_id,
                ai_analysis=ai_result,
            )

            # Отправка AI ответа, если не требуется вмешательство человека
            if not ai_result["needs_human_intervention"]:
                await self._send_ai_response(
                    channel=channel,
                    recipient=message_data.get("from"),
                    response=ai_result["response"],
                    customer_id=customer_id,
                )
            else:
                await self._escalate_to_human(communication, ai_result)

            return {
                "success": True,
                "communication_id": communication.id,
                "ai_analysis": ai_result,
                "handled_by_ai": not ai_result["needs_human_intervention"],
            }

        except Exception as e:
            logger.error(f"Ошибка обработки входящего сообщения: {e}")
            return {"success": False, "error": str(e)}

    def _extract_message_content(
        self, channel: str, message_data: Dict[str, Any]
    ) -> str:
        """Извлечение текстового содержимого из разных форматов каналов"""
        if channel == "telegram":
            return message_data.get("text", "") or message_data.get("caption", "")
        elif channel == "email":
            return message_data.get("body", "") or message_data.get("subject", "")
        elif channel == "website":
            return message_data.get("message", "") or message_data.get("question", "")
        elif channel == "avito":
            return message_data.get("text", "") or message_data.get("message", {}).get(
                "text", ""
            )
        else:
            return str(message_data)

    async def _get_customer_context(self, customer_id: int) -> Dict[str, Any]:
        """Получение контекста клиента для AI обработки"""
        if not customer_id:
            return {}

        # Получение данных клиента, истории заказов, предпочтений
        from ..models.customer import Customer
        from ..models.order import Order

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {}

        recent_orders = (
            self.db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "customer_name": customer.name,
            "order_count": customer.total_orders,
            "recent_orders": [
                {"id": order.id, "status": order.status, "product": order.product_type}
                for order in recent_orders
            ],
            "preferences": customer.preferences or {},
        }

    async def _save_communication(
        self,
        channel: str,
        direction: str,
        content: str,
        customer_id: int = None,
        ai_analysis: Dict[str, Any] = None,
    ) -> Communication:
        """Сохранение коммуникации в базу данных"""
        communication = Communication(
            channel=channel,
            direction=direction,
            message_content=content,
            customer_id=customer_id,
            intent=ai_analysis.get("intent") if ai_analysis else None,
            extra_data=ai_analysis,
        )

        self.db.add(communication)
        self.db.commit()
        self.db.refresh(communication)

        return communication

    async def _send_ai_response(
        self, channel: str, recipient: str, response: str, customer_id: int = None
    ):
        """Отправка AI-сгенерированного ответа через соответствующий канал"""
        handler = self.channel_handlers.get(channel)
        if handler:
            await handler.send_message(recipient, response)

            # Логирование исходящего ответа
            await self._save_communication(
                channel=channel,
                direction="outbound",
                content=response,
                customer_id=customer_id,
                ai_analysis={"ai_generated": True},
            )

    async def _escalate_to_human(
        self, communication: Communication, ai_result: Dict[str, Any]
    ):
        """Эскалация к человеку для обработки"""
        # Здесь можно добавить логику уведомления менеджеров/поддержки
        # Например, отправка уведомления в Telegram бота менеджеров
        logger.info(
            f"Эскалация коммуникации {communication.id} к человеку. Намерение: {ai_result['intent']}"
        )

        # Можно добавить запись в очередь задач для обработки человеком
        # await self._create_human_task(communication, ai_result)
