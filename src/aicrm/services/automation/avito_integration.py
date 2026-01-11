"""
Интеграция TaskService с Avito обработчиком
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...models.communication import Communication
from ...models.customer import Customer
from ...models.order import Order
from ...models.task import Task
from ...services.task import TaskService
from ..communication_service import CommunicationService

logger = logging.getLogger(__name__)


class AvitoTaskIntegration:
    """
    Интеграция создания задач на основе анализа сообщений Avito
    """

    def __init__(self, db_session):
        self.db = db_session
        self.task_service = TaskService
        self.communication_service = CommunicationService(db_session)

    async def analyze_and_create_tasks(
        self, message_data: Dict[str, Any], customer: Optional[Customer] = None
    ) -> List[Task]:
        """
        Анализ сообщения и создание задач на основе содержания

        Args:
            message_data: Данные сообщения из Avito
            customer: Клиент (опционально)

        Returns:
            List[Task]: Созданные задачи
        """
        try:
            message_text = message_data.get("message", {}).get("text", "").lower()
            chat_id = str(message_data.get("chat_id", ""))
            item_id = message_data.get("item_id")

            if not chat_id:
                logger.warning("Chat ID не найден в данных сообщения Avito")
                return []

            created_tasks = []

            # Анализ ключевых слов и создание соответствующих задач
            task_triggers = await self._analyze_message_for_tasks(
                message_text, customer, item_id
            )

            for trigger in task_triggers:
                task = await self._create_task_from_trigger(
                    trigger, customer, chat_id, item_id
                )
                if task:
                    created_tasks.append(task)
                    logger.info(
                        f"Создана задача {task.id} на основе сообщения Avito: {trigger['type']}"
                    )

            return created_tasks

        except Exception as e:
            logger.error(f"Ошибка анализа сообщения Avito для создания задач: {e}")
            return []

    async def _analyze_message_for_tasks(
        self, message_text: str, customer: Optional[Customer], item_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Анализ текста сообщения на предмет создания задач

        Returns:
            List[Dict]: Список триггеров для создания задач
        """
        triggers = []

        # Анализ ключевых слов для разных типов задач
        task_patterns = {
            "urgent_help": {
                "keywords": ["срочно", "urgent", "асап", "немедленно", "проблема"],
                "title": "Срочная помощь клиенту",
                "description": "Клиент просит срочной помощи",
                "priority": "high",
            },
            "complaint": {
                "keywords": ["жалоба", "complaint", "претензия", "недоволен", "плохо"],
                "title": "Жалоба от клиента",
                "description": "Клиент выразил недовольство или подал жалобу",
                "priority": "high",
            },
            "order_inquiry": {
                "keywords": ["заказ", "order", "статус", "status", "когда", "готов"],
                "title": "Запрос информации о заказе",
                "description": "Клиент спрашивает о статусе заказа",
                "priority": "medium",
            },
            "price_negotiation": {
                "keywords": ["цена", "price", "скидка", "discount", "дорого"],
                "title": "Переговоры о цене",
                "description": "Клиент обсуждает цену или просит скидку",
                "priority": "medium",
            },
            "delivery_issue": {
                "keywords": ["доставка", "delivery", "адрес", "address", "курьер"],
                "title": "Вопрос по доставке",
                "description": "Клиент спрашивает о доставке",
                "priority": "medium",
            },
            "quality_issue": {
                "keywords": ["качество", "quality", "брак", "defect", "плохо"],
                "title": "Проблема с качеством",
                "description": "Клиент сообщает о проблеме с качеством товара",
                "priority": "high",
            },
            "return_request": {
                "keywords": ["возврат", "return", "вернуть", "exchange", "обмен"],
                "title": "Запрос на возврат/обмен",
                "description": "Клиент хочет вернуть или обменять товар",
                "priority": "high",
            },
            "custom_order": {
                "keywords": ["заказать", "order", "сделать", "изготовить", "custom"],
                "title": "Заказ кастомного изделия",
                "description": "Клиент хочет заказать кастомное изделие",
                "priority": "medium",
            },
        }

        for task_type, config in task_patterns.items():
            if any(keyword in message_text for keyword in config["keywords"]):
                triggers.append(
                    {
                        "type": task_type,
                        "title": config["title"],
                        "description": config["description"],
                        "priority": config["priority"],
                        "matched_keywords": [
                            kw for kw in config["keywords"] if kw in message_text
                        ],
                    }
                )

        # Дополнительный анализ контекста
        if customer:
            # Проверяем историю клиента
            recent_communications = (
                self.db.query(Communication)
                .filter(
                    Communication.customer_id == customer.id,
                    Communication.created_at >= datetime.utcnow() - timedelta(days=7),
                )
                .count()
            )

            if recent_communications > 10:
                # Клиент очень активен - возможно нужно создать задачу для менеджера
                triggers.append(
                    {
                        "type": "vip_client_attention",
                        "title": "Внимание к VIP клиенту",
                        "description": f"Активный клиент {customer.name} требует повышенного внимания",
                        "priority": "high",
                        "matched_keywords": ["активность"],
                    }
                )

        return triggers

    async def _create_task_from_trigger(
        self,
        trigger: Dict[str, Any],
        customer: Optional[Customer],
        chat_id: str,
        item_id: Optional[int],
    ) -> Optional[Task]:
        """
        Создание задачи на основе триггера

        Args:
            trigger: Данные триггера
            customer: Клиент
            chat_id: ID чата Avito
            item_id: ID объявления

        Returns:
            Task: Созданная задача или None
        """
        try:
            # Определяем ответственного за задачу
            assigned_user_id = await self._determine_task_assignee(trigger, customer)

            # Формируем описание задачи
            description = trigger["description"]
            if customer:
                description += f"\nКлиент: {customer.name}"
                phone = getattr(customer, "phone", None)
                if phone:
                    description += f"\nТелефон: {phone}"
                email = getattr(customer, "email", None)
                if email:
                    description += f"\nEmail: {email}"

            description += f"\nЧат Avito: {chat_id}"
            if item_id:
                description += f"\nОбъявление: {item_id}"

            # Добавляем найденные ключевые слова
            if trigger.get("matched_keywords"):
                description += (
                    f"\nКлючевые слова: {', '.join(trigger['matched_keywords'])}"
                )

            # Создаем задачу
            task_data = {
                "title": trigger["title"],
                "description": description,
                "assigned_to": assigned_user_id,
                "priority": trigger["priority"],
                "related_order_id": None,  # Можно определить по item_id если нужно
                "extra_data": {
                    "source": "avito_integration",
                    "chat_id": chat_id,
                    "item_id": item_id,
                    "trigger_type": trigger["type"],
                    "matched_keywords": trigger.get("matched_keywords", []),
                },
            }

            task = self.task_service.create_task(
                db=self.db, task_data=task_data, created_by=1  # Системный пользователь
            )

            logger.info(
                f"Создана задача {task.id} типа '{trigger['type']}' для пользователя {assigned_user_id}"
            )
            return task

        except Exception as e:
            logger.error(f"Ошибка создания задачи из триггера {trigger['type']}: {e}")
            return None

    async def _determine_task_assignee(
        self, trigger: Dict[str, Any], customer: Optional[Customer]
    ) -> Optional[int]:
        """
        Определение ответственного за задачу

        Args:
            trigger: Данные триггера
            customer: Клиент

        Returns:
            int: ID пользователя или None
        """
        try:
            # Логика назначения задач по типам
            priority_assignments = {
                "high": [2, 3],  # Менеджеры и супервайзеры для срочных задач
                "medium": [4, 5, 6],  # Операторы для обычных задач
                "low": [7, 8],  # Стажировщики для простых задач
            }

            priority = trigger.get("priority", "medium")
            possible_assignees = priority_assignments.get(priority, [4, 5, 6])

            # Для VIP клиентов - только опытные менеджеры
            if customer and trigger.get("type") == "vip_client_attention":
                possible_assignees = [2, 3]  # Только менеджеры

            # Простая логика балансировки нагрузки
            # Находим пользователя с наименьшим количеством активных задач
            from ...models.user import User

            min_tasks = float("inf")
            selected_user = None

            for user_id in possible_assignees:
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue

                active_tasks = (
                    self.db.query(Task)
                    .filter(
                        Task.assigned_to == user_id,
                        Task.status.in_(["todo", "in_progress"]),
                    )
                    .count()
                )

                if active_tasks < min_tasks:
                    min_tasks = active_tasks
                    selected_user = user

            return selected_user.id if selected_user else None

        except Exception as e:
            logger.error(f"Ошибка определения ответственного за задачу: {e}")
            return None  # Система назначит задачу позже

    async def create_followup_task(
        self, customer: Customer, chat_id: str, reason: str
    ) -> Optional[Task]:
        """
        Создание задачи для последующего контакта с клиентом

        Args:
            customer: Клиент
            chat_id: ID чата
            reason: Причина для follow-up

        Returns:
            Task: Созданная задача или None
        """
        try:
            task_data = {
                "title": f"Follow-up с клиентом {customer.name}",
                "description": f"Необходимо связаться с клиентом по причине: {reason}\n\n"
                f"Клиент: {customer.name}\n"
                f"Чат Avito: {chat_id}\n"
                f"Телефон: {customer.phone or 'Не указан'}\n"
                f"Email: {customer.email or 'Не указан'}",
                "assigned_to": await self._determine_task_assignee(
                    {"priority": "medium"}, customer
                ),
                "priority": "medium",
                "customer_id": customer.id,
                "extra_data": {
                    "source": "avito_followup",
                    "chat_id": chat_id,
                    "reason": reason,
                    "followup_type": "customer_contact",
                },
            }

            task = self.task_service.create_task(
                db=self.db, task_data=task_data, created_by=1
            )

            logger.info(
                f"Создана задача follow-up {task.id} для клиента {customer.name}"
            )
            return task

        except Exception as e:
            logger.error(
                f"Ошибка создания задачи follow-up для клиента {customer.id}: {e}"
            )
            return None

    async def create_order_tracking_task(
        self, order: Order, customer: Customer, chat_id: str
    ) -> Optional[Task]:
        """
        Создание задачи для отслеживания заказа

        Args:
            order: Заказ
            customer: Клиент
            chat_id: ID чата

        Returns:
            Task: Созданная задача или None
        """
        try:
            # Получаем данные заказа безопасно
            order_status = getattr(order, "status", None)
            status_value = order_status.value if order_status else "Неизвестен"
            deadline = getattr(order, "deadline", None)
            deadline_str = deadline.strftime("%d.%m.%Y") if deadline else "Не указан"

            task_data = {
                "title": f"Отслеживание заказа #{order.id}",
                "description": f"Отслеживать статус заказа #{order.id} для клиента {customer.name}\n\n"
                f"Текущий статус: {status_value}\n"
                f"Клиент: {customer.name}\n"
                f"Чат Avito: {chat_id}\n"
                f"Дедлайн: {deadline_str}",
                "assigned_to": await self._determine_task_assignee(
                    {"priority": "medium"}, customer
                ),
                "priority": "medium",
                "customer_id": customer.id,
                "order_id": order.id,
                "extra_data": {
                    "source": "avito_order_tracking",
                    "chat_id": chat_id,
                    "order_status": order_status.value if order_status else None,
                    "tracking_type": "order_status",
                },
            }

            task = self.task_service.create_task(
                db=self.db, task_data=task_data, created_by=1
            )

            logger.info(
                f"Создана задача отслеживания заказа {task.id} для заказа #{order.id}"
            )
            return task

        except Exception as e:
            logger.error(
                f"Ошибка создания задачи отслеживания для заказа {order.id}: {e}"
            )
            return None

    async def get_tasks_for_chat(self, chat_id: str) -> List[Task]:
        """
        Получение всех задач связанных с чатом Avito

        Args:
            chat_id: ID чата Avito

        Returns:
            List[Task]: Список задач
        """
        try:
            tasks = (
                self.db.query(Task)
                .filter(Task.extra_data.contains({"chat_id": chat_id}))
                .all()
            )

            return tasks

        except Exception as e:
            logger.error(f"Ошибка получения задач для чата {chat_id}: {e}")
            return []

    async def update_task_status_from_avito(
        self, chat_id: str, new_status: str, updated_by: int = 1
    ) -> bool:
        """
        Обновление статуса задач при получении ответа от клиента в Avito

        Args:
            chat_id: ID чата
            new_status: Новый статус задач
            updated_by: Кто обновляет

        Returns:
            bool: Успешно ли обновлено
        """
        try:
            tasks = await self.get_tasks_for_chat(chat_id)

            updated_count = 0
            for task in tasks:
                if task.status in ["todo", "in_progress"]:
                    self.task_service.update_task(
                        db=self.db,
                        task_id=task.id,
                        update_data={"status": new_status, "updated_by": updated_by},
                    )
                    updated_count += 1

            if updated_count > 0:
                logger.info(
                    f"Обновлено {updated_count} задач для чата {chat_id} на статус '{new_status}'"
                )

            return updated_count > 0

        except Exception as e:
            logger.error(f"Ошибка обновления статуса задач для чата {chat_id}: {e}")
            return False

    async def notify_new_lead(
        self, customer: Customer, chat_id: str, item_id: Optional[int] = None
    ) -> bool:
        """
        Уведомление о новом лиде из Avito

        Args:
            customer: Новый клиент/лид
            chat_id: ID чата Avito
            item_id: ID объявления (опционально)

        Returns:
            bool: Успешно ли отправлены уведомления
        """
        try:
            # Создаем задачу для обработки нового лида
            task_data = {
                "title": f"Новый лид из Avito: {customer.name}",
                "description": f"Получен новый лид из Avito\n\n"
                f"Клиент: {customer.name}\n"
                f"Телефон: {customer.phone or 'Не указан'}\n"
                f"Email: {customer.email or 'Не указан'}\n"
                f"Чат Avito: {chat_id}\n"
                f"Объявление: {item_id or 'Не указано'}\n\n"
                f"Необходимо:\n"
                f"1. Провести первичную консультацию\n"
                f"2. Определить потребности клиента\n"
                f"3. Предложить подходящие услуги\n"
                f"4. Зафиксировать результат разговора",
                "assigned_to": await self._determine_task_assignee(
                    {"priority": "high"}, customer
                ),
                "priority": "high",
                "customer_id": customer.id,
                "extra_data": {
                    "source": "avito_new_lead",
                    "chat_id": chat_id,
                    "item_id": item_id,
                    "lead_type": "avito_inquiry",
                    "notification_sent": True,
                },
            }

            # Создаем задачу
            lead_task = self.task_service.create_task(
                db=self.db, task_data=task_data, created_by=1
            )

            # Отправляем уведомления ответственным пользователям
            await self._notify_managers_about_new_lead(
                customer, chat_id, item_id, lead_task
            )

            logger.info(
                f"Создано уведомление о новом лиде {customer.name}, задача #{lead_task.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Ошибка создания уведомления о новом лиде {customer.id}: {e}")
            return False

    async def _notify_managers_about_new_lead(
        self, customer: Customer, chat_id: str, item_id: Optional[int], lead_task: Task
    ) -> None:
        """
        Отправка уведомлений менеджерам о новом лиде

        Args:
            customer: Новый клиент
            chat_id: ID чата
            item_id: ID объявления
            lead_task: Созданная задача
        """
        try:
            # Получаем менеджеров для уведомления
            from ...models.user import User

            managers = (
                self.db.query(User).filter(User.role.in_(["manager", "admin"])).all()
            )

            notification_message = (
                f"🚨 Новый лид из Avito!\n\n"
                f"👤 Клиент: {customer.name}\n"
                f"📞 Телефон: {customer.phone or 'Не указан'}\n"
                f"📧 Email: {customer.email or 'Не указан'}\n"
                f"💬 Чат: {chat_id}\n"
                f"📋 Задача: #{lead_task.id}\n\n"
                f"Пожалуйста, обработайте лид в ближайшее время!"
            )

            # Отправляем уведомления всем менеджерам
            for manager in managers:
                try:
                    # Используем robot_service для отправки уведомлений
                    from .robot_service import RobotService

                    robot_service = RobotService(self.db)

                    await robot_service.notify_user(
                        user_id=manager.id,
                        message=notification_message,
                        type="lead",
                        channel="email",
                    )

                    # Также пытаемся отправить в Telegram если есть ID
                    if hasattr(manager, "telegram_id") and manager.telegram_id:
                        await robot_service.send_telegram_message(
                            telegram_id=str(manager.telegram_id),
                            message=notification_message,
                        )

                except Exception as e:
                    logger.error(
                        f"Не удалось уведомить менеджера {manager.id} о новом лиде: {e}"
                    )

            logger.info(
                f"Отправлены уведомления {len(managers)} менеджерам о новом лиде {customer.name}"
            )

        except Exception as e:
            logger.error(
                f"Ошибка отправки уведомлений менеджерам о лиде {customer.id}: {e}"
            )

    async def create_lead_followup_reminder(
        self, customer: Customer, chat_id: str, hours_delay: int = 24
    ) -> Optional[Task]:
        """
        Создание напоминания для follow-up с лидом

        Args:
            customer: Клиент
            chat_id: ID чата
            hours_delay: Задержка в часах

        Returns:
            Task: Созданная задача напоминания или None
        """
        try:
            from datetime import datetime, timedelta

            followup_time = datetime.utcnow() + timedelta(hours=hours_delay)

            task_data = {
                "title": f"Follow-up с лидом {customer.name} через {hours_delay}ч",
                "description": f"Напоминание для повторного контакта с лидом из Avito\n\n"
                f"Клиент: {customer.name}\n"
                f"Чат Avito: {chat_id}\n"
                f"Время follow-up: {followup_time.strftime('%d.%m.%Y %H:%M UTC')}\n\n"
                f"Если лид не ответил в течение {hours_delay} часов, "
                f"необходимо связаться самостоятельно.",
                "assigned_to": await self._determine_task_assignee(
                    {"priority": "medium"}, customer
                ),
                "priority": "medium",
                "customer_id": customer.id,
                "deadline": followup_time,
                "extra_data": {
                    "source": "avito_lead_followup",
                    "chat_id": chat_id,
                    "followup_type": "lead_reminder",
                    "hours_delay": hours_delay,
                    "scheduled_time": followup_time.isoformat(),
                },
            }

            task = self.task_service.create_task(
                db=self.db, task_data=task_data, created_by=1
            )

            logger.info(
                f"Создано напоминание follow-up #{task.id} для лида {customer.name}"
            )
            return task

        except Exception as e:
            logger.error(
                f"Ошибка создания напоминания follow-up для лида {customer.id}: {e}"
            )
            return None


# Функция для создания экземпляра с сессией базы данных
def get_avito_task_integration(db_session):
    """
    Получить экземпляр AvitoTaskIntegration с сессией БД

    Args:
        db_session: Сессия базы данных

    Returns:
        AvitoTaskIntegration: Экземпляр интеграции
    """
    return AvitoTaskIntegration(db_session)
