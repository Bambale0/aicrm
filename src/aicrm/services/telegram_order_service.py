"""
Сервис для создания заказов через Telegram бот
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.order import Order, OrderStatus
from ..models.telegram_chat import TelegramChat
from .ai.intent_service import AIIntentService

logger = logging.getLogger(__name__)


class TelegramOrderService:
    """
    Сервис для обработки заказов через Telegram с AI помощью
    """

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIIntentService()

    async def process_order_request(
        self,
        message: str,
        telegram_chat: TelegramChat,
        conversation_history: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Обработка запроса на заказ через AI

        Args:
            message: Сообщение пользователя
            telegram_chat: Объект Telegram чата
            conversation_history: История разговора

        Returns:
            Dict с результатом обработки
        """
        try:
            # Проверка, зарегистрирован ли клиент
            if not telegram_chat.customer_id:
                return {
                    "success": False,
                    "message": "Для оформления заказа необходимо зарегистрироваться в системе.",
                    "action": "registration_required",
                }

            customer = (
                self.db.query(Customer)
                .filter(Customer.id == telegram_chat.customer_id)
                .first()
            )
            if not customer:
                return {
                    "success": False,
                    "message": "Клиент не найден в системе.",
                    "action": "customer_not_found",
                }

            # Анализ сообщения через AI для извлечения данных заказа
            order_data = await self._extract_order_data(message, conversation_history)

            if not order_data.get("has_order_intent"):
                return {
                    "success": False,
                    "message": "Не удалось распознать запрос на заказ. Попробуйте перефразировать.",
                    "action": "clarification_needed",
                }

            # Создание заказа
            order = await self._create_order_from_data(order_data, customer)

            return {
                "success": True,
                "message": self._generate_order_confirmation_message(order),
                "order_id": order.id,
                "action": "order_created",
            }

        except Exception as e:
            logger.error(f"Ошибка обработки заказа: {e}")
            return {
                "success": False,
                "message": "Произошла ошибка при обработке заказа. Попробуйте позже.",
                "action": "error",
            }

    async def _extract_order_data(
        self, message: str, conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Извлечение данных заказа из сообщения с помощью AI
        """
        # Context prepared inline below when needed (removed unused `context` variable)

        # Промпт для извлечения данных заказа
        extraction_prompt = f"""
        Проанализируй сообщение пользователя и извлеки информацию о заказе на печать.

        Сообщение: "{message}"

        История разговора:
        {json.dumps(conversation_history, ensure_ascii=False, indent=2) if conversation_history else "Нет истории"}

        Извлеки следующие данные (если они есть):
        - product_type: тип продукта (футболки, худи, кружки, сумки, etc.)
        - quantity: количество
        - size: размер (S, M, L, XL, etc.)
        - color: цвет
        - design_description: описание дизайна
        - has_design_file: есть ли файл с дизайном (true/false)
        - deadline: желаемый срок (в формате YYYY-MM-DD или относительная дата)
        - special_requirements: особые требования
        - budget: бюджет в рублях

        Верни результат в формате JSON с полями:
        - has_order_intent: true/false
        - order_data: объект с извлеченными данными
        - confidence: уверенность в извлечении (0-1)
        - missing_info: массив недостающих полей
        """

        messages = [
            {
                "role": "system",
                "content": "Ты эксперт по извлечению данных заказов из текстов. Отвечай только в формате JSON.",
            },
            {"role": "user", "content": extraction_prompt},
        ]

        try:
            response = await self.ai_service.ai_client.chat_completion(
                messages=messages,
                temperature=0.1,  # Низкая температура для точного извлечения
            )

            # Парсинг JSON ответа
            result = json.loads(response)

            # Валидация структуры
            if not isinstance(result, dict):
                raise ValueError("Ответ не является объектом")

            return {
                "has_order_intent": result.get("has_order_intent", False),
                "order_data": result.get("order_data", {}),
                "confidence": result.get("confidence", 0),
                "missing_info": result.get("missing_info", []),
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка парсинга AI ответа: {e}")
            return {
                "has_order_intent": False,
                "order_data": {},
                "confidence": 0,
                "missing_info": [],
            }

    async def _create_order_from_data(
        self, order_data: Dict[str, Any], customer: Customer
    ) -> Order:
        """
        Создание заказа из извлеченных данных
        """
        order_info = order_data.get("order_data", {})

        # Подготовка данных заказа
        items = []

        # Основной товар
        item = {
            "product_type": order_info.get("product_type", "не указано"),
            "quantity": order_info.get("quantity", 1),
            "size": order_info.get("size"),
            "color": order_info.get("color"),
            "design_description": order_info.get("design_description"),
            "has_design_file": order_info.get("has_design_file", False),
        }
        items.append(item)

        # Расчет примерной стоимости (упрощенная логика)
        base_price = self._calculate_base_price(item)
        total_amount = base_price * item["quantity"]

        # Создание заказа
        order = Order(
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            items=json.dumps(items, ensure_ascii=False),
            notes=order_info.get("special_requirements"),
            requirements=order_info.get("design_description"),
            deadline=self._parse_deadline(order_info.get("deadline")),
            source="telegram",
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Обновление статистики клиента
        customer.update_stats()
        self.db.commit()

        logger.info(f"Создан заказ {order.id} для клиента {customer.id} через Telegram")

        return order

    def _calculate_base_price(self, item: Dict[str, Any]) -> float:
        """
        Расчет базовой цены товара (упрощенная логика)
        """
        product_type = item.get("product_type", "").lower()

        # Базовые цены за единицу
        base_prices = {
            "футболка": 500,
            "худи": 1200,
            "кружка": 300,
            "сумка": 400,
            "кепка": 350,
            "подушка": 600,
            "постер": 200,
            "наклейка": 50,
        }

        # Поиск по ключевым словам
        for key, price in base_prices.items():
            if key in product_type:
                return price

        # Цена по умолчанию
        return 500

    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        """
        Парсинг срока выполнения
        """
        if not deadline_str:
            return None

        try:
            # Простой парсинг - можно расширить
            if "завтра" in deadline_str.lower():
                return datetime.utcnow().replace(hour=23, minute=59, second=59)
            elif "послезавтра" in deadline_str.lower():
                return datetime.utcnow().replace(
                    day=datetime.utcnow().day + 2, hour=23, minute=59, second=59
                )
            elif "неделя" in deadline_str.lower():
                return datetime.utcnow().replace(day=datetime.utcnow().day + 7)
            else:
                # Попытка парсинга даты
                return datetime.fromisoformat(deadline_str)
        except:
            return None

    def _generate_order_confirmation_message(self, order: Order) -> str:
        """
        Генерация сообщения подтверждения заказа
        """
        items = json.loads(order.items) if isinstance(order.items, str) else order.items

        message = f"✅ Заказ №{order.id} успешно создан!\n\n"

        if items:
            item = items[0]  # Пока поддерживаем один товар
            message += f"📦 Товар: {item.get('product_type', 'Не указано')}\n"
            message += f"🔢 Количество: {item.get('quantity', 1)}\n"
            if item.get("size"):
                message += f"📏 Размер: {item['size']}\n"
            if item.get("color"):
                message += f"🎨 Цвет: {item['color']}\n"

        message += f"💰 Сумма: {order.total_amount} ₽\n"
        message += f"📊 Статус: {order.status_display}\n"

        if order.deadline:
            message += f"⏰ Срок: {order.deadline.strftime('%d.%m.%Y')}\n"

        message += (
            "\n📞 Мы свяжемся с вами для уточнения деталей и подтверждения заказа."
        )

        return message

    async def get_customer_orders_summary(self, telegram_chat: TelegramChat) -> str:
        """
        Получение сводки заказов клиента
        """
        if not telegram_chat.customer_id:
            return "❌ Вы не зарегистрированы в системе."

        customer = (
            self.db.query(Customer)
            .filter(Customer.id == telegram_chat.customer_id)
            .first()
        )
        if not customer:
            return "❌ Клиент не найден."

        orders = (
            self.db.query(Order)
            .filter(Order.customer_id == customer.id)
            .order_by(Order.created_at.desc())
            .limit(5)
            .all()
        )

        if not orders:
            return "📭 У вас пока нет заказов."

        summary = f"📋 Ваши заказы ({len(orders)}):\n\n"

        for order in orders:
            summary += f"🆔 #{order.id} - {order.status_display}\n"
            summary += f"💰 {order.total_amount} ₽ - {order.created_at.strftime('%d.%m.%Y')}\n\n"

        return summary

    async def update_order_from_message(
        self, order_id: int, message: str, telegram_chat: TelegramChat
    ) -> Dict[str, Any]:
        """
        Обновление существующего заказа на основе сообщения
        """
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return {"success": False, "message": "Заказ не найден."}

            # Проверка прав доступа
            if order.customer_id != telegram_chat.customer_id:
                return {"success": False, "message": "Нет доступа к этому заказу."}

            # Извлечение обновлений через AI
            update_data = await self._extract_order_updates(message, order)

            if update_data.get("has_updates"):
                # Применение обновлений
                await self._apply_order_updates(order, update_data["updates"])

                return {
                    "success": True,
                    "message": f"Заказ #{order.id} обновлен.",
                    "updates": update_data["updates"],
                }
            else:
                return {
                    "success": False,
                    "message": "Не удалось распознать обновления для заказа.",
                }

        except Exception as e:
            logger.error(f"Ошибка обновления заказа: {e}")
            return {"success": False, "message": "Ошибка обновления заказа."}

    async def _extract_order_updates(
        self, message: str, order: Order
    ) -> Dict[str, Any]:
        """
        Извлечение обновлений заказа из сообщения
        """
        current_items = (
            json.loads(order.items) if isinstance(order.items, str) else order.items
        )

        prompt = f"""
        Проанализируй сообщение пользователя и определи, какие обновления нужно внести в заказ.

        Текущий заказ:
        - ID: {order.id}
        - Товары: {json.dumps(current_items, ensure_ascii=False)}
        - Сумма: {order.total_amount}
        - Статус: {order.status}
        - Заметки: {order.notes}

        Сообщение пользователя: "{message}"

        Определи:
        - has_updates: true/false - есть ли запросы на изменения
        - updates: объект с обновлениями (items, notes, deadline и т.д.)
        - clarification_needed: массив вопросов для уточнения

        Верни в формате JSON.
        """

        messages = [
            {
                "role": "system",
                "content": "Анализируй запросы на обновление заказов. Отвечай в JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.ai_service.ai_client.chat_completion(
                messages=messages, temperature=0.1
            )

            result = json.loads(response)
            return result

        except Exception as e:
            logger.error(f"Ошибка извлечения обновлений: {e}")
            return {"has_updates": False, "updates": {}, "clarification_needed": []}

    async def _apply_order_updates(self, order: Order, updates: Dict[str, Any]):
        """
        Применение обновлений к заказу
        """
        # Обновление товаров
        if "items" in updates:
            order.items = json.dumps(updates["items"], ensure_ascii=False)

        # Обновление заметок
        if "notes" in updates:
            order.notes = updates["notes"]

        # Обновление требований
        if "requirements" in updates:
            order.requirements = updates["requirements"]

        # Обновление срока
        if "deadline" in updates:
            order.deadline = self._parse_deadline(updates["deadline"])

        # Пересчет суммы если изменились товары
        if "items" in updates:
            items = updates["items"]
            if items:
                item = items[0]
                base_price = self._calculate_base_price(item)
                order.total_amount = base_price * item.get("quantity", 1)

        order.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Заказ {order.id} обновлен через Telegram")
