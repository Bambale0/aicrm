"""
Сервис анализа намерений с AI
"""
from typing import Dict, Any, List
from enum import Enum
import json
import logging

from .client import UnifiedAIClient

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    ORDER = "order"
    QUESTION = "question"
    COMPLAINT = "complaint"
    SUPPORT = "support"
    OTHER = "other"


class AIIntentService:
    """
    AI сервис для анализа намерений и генерации ответов
    """

    def __init__(self):
        self.ai_client = UnifiedAIClient()
        self.intent_prompts = self._load_intent_prompts()

    def _load_intent_prompts(self) -> Dict[str, str]:
        """Загрузка промптов для разных намерений"""
        return {
            "intent_analysis": """
            Проанализируйте сообщение пользователя и определите его основное намерение.
            Возможные намерения:
            - order: Пользователь хочет разместить заказ на услуги печати
            - question: Пользователь спрашивает о услугах, ценах или процессе
            - complaint: Пользователь сообщает о проблеме или неудовлетворенности
            - support: Пользователь нуждается в технической или клиентской поддержке
            - other: Не подходит под другие категории

            Верните ТОЛЬКО намерение как одно слово: order, question, complaint, support, или other.

            Сообщение пользователя: "{message}"
            """,

            "order_creation": """
            Вы полезный помощник компании по печати.
            Пользователь хочет разместить заказ. Помогите ему предоставить необходимую информацию.

            Необходимая информация для заказов на печать:
            - Тип продукта (футболки, худи и т.д.)
            - Количество
            - Детали дизайна или наличие файла
            - Требования к размеру
            - Сроки, если есть

            Текущий контекст разговора:
            {context}

            Последнее сообщение пользователя: {message}

            Предоставьте полезный, профессиональный ответ, который продвигает процесс заказа вперед.
            """,

            "question_answer": """
            Вы знающий помощник компании по печати.
            Ответьте на вопрос пользователя на основе общего знания об услугах печати.

            Общие темы:
            - Цены на разные продукты
            - Временные рамки производства
            - Требования к дизайну
            - Варианты материалов
            - Доставка и shipping

            Вопрос: {message}

            Предоставьте точную, полезную информацию. Если не уверены, предложите обратиться в поддержку.
            """
        }

    async def analyze_intent(self, message: str, context: Dict[str, Any] = None, model: str = None) -> IntentType:
        """Анализ намерения сообщения пользователя с помощью AI"""
        prompt = self.intent_prompts["intent_analysis"].format(message=message)

        messages = [
            {"role": "system", "content": "Вы помощник по классификации намерений. Верните только метку намерения."},
            {"role": "user", "content": prompt}
        ]

        response = await self.ai_client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.1  # Низкая температура для последовательной классификации
        )

        # Очистка и парсинг ответа
        intent_str = response.strip().lower()
        try:
            return IntentType(intent_str)
        except ValueError:
            logger.warning(f"Получено неизвестное намерение: {intent_str}")
            return IntentType.OTHER

    async def generate_response(
        self,
        intent: IntentType,
        message: str,
        context: Dict[str, Any] = None,
        model: str = None
    ) -> str:
        """Генерация контекстно-зависимого ответа на основе намерения"""
        context = context or {}

        if intent == IntentType.ORDER:
            prompt_template = "order_creation"
        elif intent == IntentType.QUESTION:
            prompt_template = "question_answer"
        else:
            # Общий ответ для других намерений
            prompt_template = "question_answer"

        prompt = self.intent_prompts[prompt_template].format(
            message=message,
            context=json.dumps(context, indent=2, ensure_ascii=False)
        )

        messages = [
            {"role": "system", "content": "Вы полезный помощник компании по печати."},
            {"role": "user", "content": prompt}
        ]

        return await self.ai_client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.7
        )

    async def process_customer_message(
        self,
        message: str,
        customer_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Полный пайплайн обработки сообщения:
        1. Анализ намерения
        2. Генерация ответа
        3. Возврат структурированного результата
        """
        intent = await self.analyze_intent(message, customer_context)
        response = await self.generate_response(intent, message, customer_context)

        return {
            "intent": intent,
            "response": response,
            "needs_human_intervention": intent in [IntentType.COMPLAINT, IntentType.SUPPORT],
            "suggested_actions": self._get_suggested_actions(intent)
        }

    def _get_suggested_actions(self, intent: IntentType) -> List[str]:
        """Получение предлагаемых бизнес-действий на основе намерения"""
        actions = {
            IntentType.ORDER: ["create_order_draft", "assign_sales_agent"],
            IntentType.QUESTION: ["log_question", "update_knowledge_base"],
            IntentType.COMPLAINT: ["escalate_to_manager", "create_support_ticket"],
            IntentType.SUPPORT: ["assign_support_agent", "create_help_ticket"],
            IntentType.OTHER: ["log_interaction"]
        }
        return actions.get(intent, [])
