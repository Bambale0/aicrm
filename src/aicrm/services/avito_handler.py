"""
Обработчик коммуникаций из Avito
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .avito_service import AvitoService, AvitoAPIError, AvitoRateLimitError
from .communication_service import CommunicationService
from ..models.communication import Communication
from ..models.customer import Customer
from ..models.order import Order
from ..models.avito_chat import AvitoChatSettings
from ..utils.logging import get_logger, get_messenger_logger

logger = get_logger(__name__)
messenger_logger = get_messenger_logger()


class AvitoCommunicationHandler:
    """
    Обработчик входящих сообщений из Avito
    """

    def __init__(self, db_session):
        self.db = db_session
        self.avito_service = AvitoService()
        self.communication_service = CommunicationService(db_session)

    async def handle_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка входящего сообщения из Avito

        Ожидаемый формат message_data:
        {
            "chat_id": "string",  # ID чата в Avito
            "user_id": "string",  # ID пользователя в Avito
            "message": {
                "text": "string",
                "timestamp": "2023-01-01T10:00:00Z"
            },
            "item_id": 12345,  # ID объявления (опционально)
            "direction": "inbound"  # inbound/outbound
        }
        """
        try:
            # Извлечение данных сообщения
            chat_id = message_data.get("chat_id")
            user_id = message_data.get("user_id")
            message_text = message_data.get("message", {}).get("text", "")
            item_id = message_data.get("item_id")
            timestamp = message_data.get("message", {}).get("timestamp")

            messenger_logger.info(
                "Начало обработки входящего сообщения Avito",
                chat_id=chat_id,
                user_id=user_id,
                message_length=len(message_text),
                item_id=item_id,
                operation="handle_incoming_message"
            )

            if not chat_id or not user_id:
                messenger_logger.error(
                    "Отсутствуют обязательные поля в сообщении Avito",
                    chat_id=chat_id,
                    user_id=user_id,
                    operation="handle_incoming_message"
                )
                raise ValueError("Отсутствуют обязательные поля: chat_id или user_id")

            # Поиск или создание клиента
            customer = await self._find_or_create_customer(user_id, chat_id)

            # Получение настроек чата
            chat_settings = await self._get_or_create_chat_settings(chat_id, customer)

            # Обновление статистики чата
            chat_settings.update_last_message()

            # Увеличиваем счетчик непрочитанных для входящих сообщений
            if message_data.get("direction") == "inbound":
                chat_settings.unread_count += 1

                # Кэшируем превью последнего сообщения для оптимизации запросов
                if not chat_settings.extra_data:
                    chat_settings.extra_data = {}
                chat_settings.extra_data['last_message_preview'] = message_text[:100]  # Первые 100 символов

            # Определение контекста (связь с заказом через объявление)
            order_context = None
            if item_id:
                order_context = await self._find_order_by_item_id(item_id)

            # Проверка, нужно ли использовать AI
            should_use_ai = chat_settings.ai_enabled

            # Подготовка данных для обработки коммуникации
            communication_data = {
                "channel": "avito",
                "message_data": {
                    "text": message_text,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "item_id": item_id,
                    "timestamp": timestamp
                }
            }

            # Обработка через общий сервис коммуникаций только если AI включен
            if should_use_ai:
                result = await self.communication_service.handle_incoming_message(
                    channel="avito",
                    message_data=communication_data,
                    customer_id=customer.id if customer else None
                )

                # Обновление времени последнего AI ответа
                if result.get("ai_analysis"):
                    chat_settings.update_last_ai_response()
            else:
                # Сохраняем сообщение без AI обработки
                from ..models.communication import Communication
                communication = Communication(
                    channel="avito",
                    direction="inbound",
                    message_content=message_text,
                    customer_id=customer.id if customer else None,
                    extra_data={
                        "chat_id": chat_id,
                        "user_id": user_id,
                        "item_id": item_id,
                        "ai_disabled": True
                    }
                )
                self.db.add(communication)
                self.db.commit()
                self.db.refresh(communication)

                result = {
                    "success": True,
                    "communication_id": communication.id,
                    "ai_analysis": None,
                    "handled_by_ai": False,
                    "message": "AI отключен для этого чата"
                }

            # Дополнительная обработка специфичная для Avito
            await self._handle_avito_specific_logic(
                customer=customer,
                message_text=message_text,
                item_id=item_id,
                order_context=order_context,
                chat_settings=chat_settings
            )

            # Сохранение изменений в настройках чата
            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения Avito: {e}")
            return {"success": False, "error": str(e)}

    async def send_message(self, chat_id: str, message: str) -> bool:
        """
        Отправка сообщения через Avito API
        """
        start_time = datetime.utcnow()
        try:
            messenger_logger.info(
                "Начало отправки сообщения через Avito API",
                chat_id=chat_id,
                message_length=len(message),
                message_preview=message[:50],
                operation="send_message"
            )

            async with AvitoService() as avito_service:
                messenger_logger.debug(
                    "Вызов Avito API для отправки сообщения",
                    chat_id=chat_id,
                    operation="send_message"
                )

                result = await avito_service.send_avito_message(chat_id, message)

                # Извлекаем ID отправленного сообщения из ответа Avito API
                avito_message_id = result.get("message", {}).get("id") or result.get("id")

                messenger_logger.debug(
                    "Получен ответ от Avito API",
                    chat_id=chat_id,
                    avito_message_id=avito_message_id,
                    operation="send_message"
                )

                # Сохраняем исходящее сообщение в базу
                communication = Communication(
                    channel="avito",
                    direction="outbound",
                    message_content=message,
                    customer_id=None,  # Будет установлено позже через связь с чатом
                    extra_data={
                        "chat_id": chat_id,
                        "ai_generated": False,
                        "avito_message_id": avito_message_id
                    }
                )
                self.db.add(communication)
                self.db.commit()
                self.db.refresh(communication)

                messenger_logger.debug(
                    "Сообщение сохранено в базу данных",
                    chat_id=chat_id,
                    communication_id=communication.id,
                    operation="send_message"
                )

                # Обновляем статистику чата и кэшируем последнее сообщение
                chat_settings = self.db.query(AvitoChatSettings).filter(
                    AvitoChatSettings.chat_id == chat_id
                ).first()
                if chat_settings:
                    old_message_count = chat_settings.message_count
                    chat_settings.message_count += 1
                    chat_settings.last_message_at = datetime.utcnow()
                    # Сбрасываем счетчик непрочитанных при отправке ответа
                    old_unread_count = chat_settings.unread_count
                    chat_settings.unread_count = 0

                    # Кэшируем превью последнего сообщения для оптимизации запросов
                    if not chat_settings.extra_data:
                        chat_settings.extra_data = {}
                    chat_settings.extra_data['last_message_preview'] = message[:100]  # Первые 100 символов

                    self.db.commit()

                    messenger_logger.info(
                        "Обновлена статистика чата",
                        chat_id=chat_id,
                        old_message_count=old_message_count,
                        new_message_count=chat_settings.message_count,
                        old_unread_count=old_unread_count,
                        new_unread_count=chat_settings.unread_count,
                        operation="send_message"
                    )
                else:
                    messenger_logger.warning(
                        "Настройки чата не найдены для обновления статистики",
                        chat_id=chat_id,
                        operation="send_message"
                    )

                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                messenger_logger.info(
                    "Сообщение успешно отправлено",
                    chat_id=chat_id,
                    avito_message_id=avito_message_id,
                    communication_id=communication.id,
                    duration_seconds=duration,
                    operation="send_message"
                )
                return True

        except AvitoAPIError as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            messenger_logger.error(
                "Ошибка Avito API при отправке сообщения",
                chat_id=chat_id,
                error=str(e),
                duration_seconds=duration,
                operation="send_message"
            )
            return False
        except AvitoRateLimitError as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            messenger_logger.warning(
                "Превышен лимит запросов Avito при отправке сообщения",
                chat_id=chat_id,
                error=str(e),
                duration_seconds=duration,
                operation="send_message"
            )
            return False
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            messenger_logger.error(
                "Неожиданная ошибка при отправке сообщения",
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=duration,
                operation="send_message"
            )
            return False

    async def _find_or_create_customer(self, avito_user_id: str, chat_id: str) -> Optional[Customer]:
        """Поиск существующего клиента или создание нового"""
        try:
            # Поиск по Avito user_id
            customer = self.db.query(Customer).filter(
                Customer.external_ids.contains({"avito_user_id": avito_user_id})
            ).first()

            if customer:
                # Обновляем chat_id если изменился
                if customer.external_ids.get("avito_chat_id") != chat_id:
                    customer.external_ids["avito_chat_id"] = chat_id
                    self.db.commit()
                return customer

            # Создание нового клиента
            customer = Customer(
                name=f"Avito User {avito_user_id[:8]}",
                phone=None,  # Avito не предоставляет телефон напрямую
                email=None,
                external_ids={
                    "avito_user_id": avito_user_id,
                    "avito_chat_id": chat_id
                },
                preferences={
                    "communication_channels": ["avito"],
                    "source": "avito"
                }
            )

            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)

            logger.info(f"Создан новый клиент из Avito: {customer.id}")
            return customer

        except Exception as e:
            logger.error(f"Ошибка создания/поиска клиента Avito: {e}")
            return None

    async def _find_order_by_item_id(self, item_id: int) -> Optional[Order]:
        """Поиск заказа по ID объявления Avito"""
        try:
            # Поиск в поле items заказа (где могут храниться external_ids)
            orders = self.db.query(Order).filter(
                Order.items.contains({"avito_item_id": item_id})
            ).all()

            if orders:
                # Возвращаем самый свежий заказ
                return max(orders, key=lambda o: o.created_at)

            return None

        except Exception as e:
            logger.error(f"Ошибка поиска заказа по item_id {item_id}: {e}")
            return None

    async def _get_or_create_chat_settings(self, chat_id: str, customer: Optional[Customer]) -> AvitoChatSettings:
        """Получение или создание настроек чата"""
        try:
            # Поиск существующих настроек
            settings = self.db.query(AvitoChatSettings).filter(
                AvitoChatSettings.chat_id == chat_id
            ).first()

            if settings:
                # Связываем с клиентом если не связано
                if not settings.customer_id and customer:
                    settings.customer_id = customer.id
                    self.db.commit()
                return settings

            # Создание новых настроек
            settings = AvitoChatSettings(
                chat_id=chat_id,
                customer_id=customer.id if customer else None
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

            logger.info(f"Созданы настройки чата для {chat_id}")
            return settings

        except Exception as e:
            logger.error(f"Ошибка создания настроек чата {chat_id}: {e}")
            # Возвращаем дефолтные настройки
            return AvitoChatSettings(chat_id=chat_id, customer_id=customer.id if customer else None)

    async def update_chat_settings(self, chat_id: str, settings_update: Dict[str, Any]) -> Optional[AvitoChatSettings]:
        """Обновление настроек чата"""
        try:
            settings = self.db.query(AvitoChatSettings).filter(
                AvitoChatSettings.chat_id == chat_id
            ).first()

            if not settings:
                return None

            # Обновление полей
            for key, value in settings_update.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            self.db.commit()
            self.db.refresh(settings)

            logger.info(f"Обновлены настройки чата {chat_id}")
            return settings

        except Exception as e:
            logger.error(f"Ошибка обновления настроек чата {chat_id}: {e}")
            return None

    async def get_chat_settings(self, chat_id: str) -> Optional[AvitoChatSettings]:
        """Получение настроек чата"""
        try:
            return self.db.query(AvitoChatSettings).filter(
                AvitoChatSettings.chat_id == chat_id
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения настроек чата {chat_id}: {e}")
            return None

    async def toggle_ai_for_chat(self, chat_id: str, enabled: bool) -> bool:
        """Включение/выключение AI для чата"""
        try:
            result = await self.update_chat_settings(chat_id, {"ai_enabled": enabled})
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка переключения AI для чата {chat_id}: {e}")
            return False

    async def update_chat_status(self, chat_id: str, status: str) -> bool:
        """Обновление статуса чата"""
        try:
            # Обновляем статус в настройках чата
            settings = self.db.query(AvitoChatSettings).filter(
                AvitoChatSettings.chat_id == chat_id
            ).first()

            if not settings:
                logger.warning(f"Настройки чата {chat_id} не найдены для обновления статуса")
                return False

            # Сохраняем статус в extra_data или добавляем специальное поле
            if not settings.extra_data:
                settings.extra_data = {}
            settings.extra_data["status"] = status
            settings.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Обновлен статус чата {chat_id} на {status}")
            return True

        except Exception as e:
            logger.error(f"Ошибка обновления статуса чата {chat_id}: {e}")
            return False

    async def _handle_avito_specific_logic(
        self,
        customer: Optional[Customer],
        message_text: str,
        item_id: Optional[int],
        order_context: Optional[Order],
        chat_settings: AvitoChatSettings
    ):
        """Обработка логики специфичной для Avito"""
        try:
            # Если есть контекст заказа, проверяем статус
            if order_context:
                await self._check_order_status_context(order_context, message_text)

            # Если есть ID объявления, можем получить дополнительную информацию
            if item_id and customer:
                await self._enrich_customer_with_item_info(customer, item_id)

            # Специфическая обработка ключевых слов
            await self._handle_keyword_triggers(message_text, customer, item_id)

        except Exception as e:
            logger.error(f"Ошибка обработки Avito-специфичной логики: {e}")

    async def _check_order_status_context(self, order: Order, message_text: str):
        """Проверка контекста статуса заказа"""
        # Если клиент спрашивает о статусе заказа
        status_keywords = ["статус", "status", "готов", "ready", "когда"]
        if any(keyword in message_text.lower() for keyword in status_keywords):
            logger.info(f"Клиент спрашивает о статусе заказа {order.id}")

            # Можно добавить автоматический ответ со статусом
            # await self._send_order_status_update(order)

    async def _enrich_customer_with_item_info(self, customer: Customer, item_id: int):
        """Обогащение профиля клиента информацией об объявлении"""
        try:
            # Получаем информацию об объявлении
            async with AvitoService() as avito:
                item_info = await avito.client.get_item_info(item_id)

            if item_info:
                # Обновляем предпочтения клиента
                if not customer.preferences:
                    customer.preferences = {}

                customer.preferences["last_avito_item"] = {
                    "item_id": item_id,
                    "title": item_info.get("title"),
                    "url": item_info.get("url"),
                    "last_interaction": datetime.utcnow().isoformat()
                }

                self.db.commit()
                logger.info(f"Обновлен профиль клиента {customer.id} информацией об объявлении {item_id}")

        except Exception as e:
            logger.error(f"Ошибка обогащения профиля клиента: {e}")

    async def _handle_keyword_triggers(self, message_text: str, customer: Optional[Customer], item_id: Optional[int]):
        """Обработка триггеров по ключевым словам"""
        text_lower = message_text.lower()

        # Триггеры для разных типов запросов
        triggers = {
            "цена": "price_inquiry",
            "доставка": "delivery_inquiry",
            "оплата": "payment_inquiry",
            "размер": "size_inquiry",
            "цвет": "color_inquiry"
        }

        for keyword, trigger_type in triggers.items():
            if keyword in text_lower:
                logger.info(f"Сработал триггер '{trigger_type}' для клиента {customer.id if customer else 'unknown'}")
                # Можно добавить специальную обработку для каждого типа триггера
                break

    async def get_chat_history(self, chat_id: str, limit: int = 50, use_api: bool = False) -> List[Dict[str, Any]]:
        """Получение истории чата из Avito API или базы данных"""
        try:
            if use_api:
                # Получаем историю из Avito API
                async with AvitoService() as avito_service:
                    api_messages = await avito_service.get_avito_messages(chat_id, limit=limit)

                    # Синхронизируем с базой данных
                    await self._sync_messages_from_api(chat_id, api_messages)

                    # Возвращаем данные из API
                    return [
                        {
                            "id": msg.get("id"),
                            "direction": "inbound" if msg.get("direction") == "inbound" else "outbound",
                            "message": msg.get("content", {}).get("text", ""),
                            "timestamp": msg.get("created"),
                            "intent": None,  # API не предоставляет intent
                            "from_api": True
                        }
                        for msg in api_messages.get("messages", [])
                    ]
            else:
                # Получаем из базы данных
                communications = self.db.query(Communication).filter(
                    Communication.channel == "avito",
                    Communication.extra_data.contains({"chat_id": chat_id})
                ).order_by(Communication.created_at.desc()).limit(limit).all()

                return [
                    {
                        "id": comm.id,
                        "direction": comm.direction,
                        "message": comm.message_content,
                        "timestamp": comm.created_at.isoformat(),
                        "intent": comm.intent,
                        "from_api": False
                    }
                    for comm in communications
                ]

        except Exception as e:
            logger.error(f"Ошибка получения истории чата {chat_id}: {e}")
            return []

    async def sync_chat_history_from_avito(self, chat_id: str, limit: int = 100) -> Dict[str, Any]:
        """Синхронизация истории чата с Avito API"""
        try:
            async with AvitoService() as avito_service:
                # Получаем сообщения из Avito API
                api_messages = await avito_service.get_avito_messages(chat_id, limit=limit)

                # Синхронизируем с базой данных
                synced_count = await self._sync_messages_from_api(chat_id, api_messages)

                # Обновляем статистику чата
                chat_settings = self.db.query(AvitoChatSettings).filter(
                    AvitoChatSettings.chat_id == chat_id
                ).first()

                if chat_settings:
                    # Обновляем количество сообщений
                    total_messages = self.db.query(Communication).filter(
                        Communication.channel == "avito",
                        Communication.extra_data.contains({"chat_id": chat_id})
                    ).count()

                    chat_settings.message_count = total_messages
                    chat_settings.last_message_at = datetime.utcnow()
                    self.db.commit()

                logger.info(f"Синхронизирована история чата {chat_id}: {synced_count} новых сообщений")
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "synced_messages": synced_count,
                    "total_messages": len(api_messages.get("messages", []))
                }

        except Exception as e:
            logger.error(f"Ошибка синхронизации истории чата {chat_id}: {e}")
            return {
                "success": False,
                "chat_id": chat_id,
                "error": str(e)
            }

    async def mark_messages_read(self, chat_id: str, message_ids: List[str]) -> bool:
        """Отметка сообщений как прочитанные через Avito API"""
        try:
            async with AvitoService() as avito_service:
                # Для Avito используется отметка всего чата как прочитанного
                result = await avito_service.mark_avito_chat_read(chat_id)
                
                # Обновляем статус сообщений в базе
                if result.get("success", False):
                    # Помечаем сообщения как прочитанные в нашей базе
                    communications = self.db.query(Communication).filter(
                        Communication.channel == "avito",
                        Communication.extra_data.contains({"chat_id": chat_id}),
                        Communication.direction == "inbound"
                    ).all()

                    for comm in communications:
                        if not comm.extra_data:
                            comm.extra_data = {}
                        comm.extra_data["read"] = True

                    # Сбрасываем счетчик непрочитанных сообщений
                    chat_settings = self.db.query(AvitoChatSettings).filter(
                        AvitoChatSettings.chat_id == chat_id
                    ).first()
                    if chat_settings:
                        chat_settings.unread_count = 0

                    self.db.commit()
                    logger.info(f"Чат {chat_id} отмечен как прочитанный в Avito")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Ошибка отметки чата {chat_id} как прочитанного: {e}")
            return False

    async def _sync_messages_from_api(self, chat_id: str, api_messages: Dict[str, Any]) -> int:
        """Синхронизация сообщений из Avito API с базой данных"""
        try:
            messages = api_messages.get("messages", [])
            synced_count = 0

            for msg_data in messages:
                message_id = msg_data.get("id")
                if not message_id:
                    continue

                # Проверяем, существует ли уже сообщение в базе
                existing = self.db.query(Communication).filter(
                    Communication.extra_data.contains({"avito_message_id": message_id})
                ).first()

                if existing:
                    continue  # Сообщение уже есть

                # Создаем новое сообщение
                direction = "inbound" if msg_data.get("direction") == "inbound" else "outbound"
                content = msg_data.get("content", {}).get("text", "")
                created_at = msg_data.get("created")

                # Находим клиента по chat_id
                customer = None
                chat_settings = self.db.query(AvitoChatSettings).filter(
                    AvitoChatSettings.chat_id == chat_id
                ).first()
                if chat_settings:
                    customer = chat_settings.customer

                communication = Communication(
                    channel="avito",
                    direction=direction,
                    message_content=content,
                    customer_id=customer.id if customer else None,
                    extra_data={
                        "chat_id": chat_id,
                        "avito_message_id": message_id,
                        "from_api_sync": True
                    }
                )

                # Устанавливаем время создания если есть
                if created_at:
                    from datetime import datetime
                    try:
                        communication.created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        pass  # Оставляем дефолтное время

                self.db.add(communication)
                synced_count += 1

            self.db.commit()
            logger.info(f"Синхронизировано {synced_count} новых сообщений для чата {chat_id}")
            return synced_count

        except Exception as e:
            logger.error(f"Ошибка синхронизации сообщений из API для чата {chat_id}: {e}")
            self.db.rollback()
            return 0
