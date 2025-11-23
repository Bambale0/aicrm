"""
Сервис Telegram бота с AI интеграцией
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session

from ..models.telegram_chat import TelegramChat
from ..models.customer import Customer
from ..models.order import Order
from ..models.communication import Communication
from ..core.config import settings
from .ai.intent_service import AIIntentService, IntentType
from .communication_service import CommunicationService
from .telegram_order_service import TelegramOrderService

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Сервис для управления Telegram ботом с AI консультантом
    """

    def __init__(self, db: Session):
        self.db = db
        self.bot_token = settings.telegram_bot_token
        self.application = None
        self.bot = None

        # Инициализация зависимостей
        self.ai_service = AIIntentService()
        self.communication_service = CommunicationService(db)
        self.order_service = TelegramOrderService(db)

        # Кеш чатов для быстрого доступа
        self.chat_cache: Dict[str, TelegramChat] = {}

    async def initialize_bot(self) -> bool:
        """Инициализация Telegram бота"""
        if not self.bot_token:
            logger.error("Telegram bot token не настроен")
            return False

        # Проверяем, не инициализирован ли уже бот
        if self.application is not None:
            logger.info("Telegram бот уже инициализирован")
            return True

        try:
            # Создание приложения с явным HTTP клиентом
            from telegram.request import HTTPXRequest

            # Создаем HTTPX клиент с таймаутами
            request = HTTPXRequest(
                connection_pool_size=20,
                read_timeout=30.0,
                write_timeout=30.0,
                connect_timeout=10.0,
                pool_timeout=10.0
            )

            # Создание приложения с кастомным HTTP клиентом
            self.application = Application.builder().token(self.bot_token).request(request).build()

            # Регистрация обработчиков
            self._register_handlers()

            # Инициализация бота
            self.bot = self.application.bot

            logger.info("Telegram бот успешно инициализирован")
            return True

        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
            # Очищаем состояние при ошибке
            self.application = None
            self.bot = None
            return False

    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("orders", self._handle_orders))
        self.application.add_handler(CommandHandler("support", self._handle_support))

        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

        # Обработчик ошибок
        self.application.add_error_handler(self._handle_error)

    async def start_polling(self):
        """Запуск бота в режиме polling"""
        if not self.application:
            logger.error("Бот не инициализирован")
            return

        logger.info("Запуск Telegram бота...")

        try:
            # Проверяем и инициализируем приложение если нужно
            if not hasattr(self.application, '_initialized') or not self.application._initialized:
                await self.application.initialize()

            # Запускаем приложение
            await self.application.start()

            # Проверяем что updater существует и инициализирован
            if not self.application.updater:
                logger.error("Updater не инициализирован")
                return

            # Запускаем polling в фоне с обработкой ошибок
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Игнорируем pending updates при старте
            )
            logger.info("Telegram бот успешно запущен в режиме polling")

        except Exception as e:
            logger.error(f"Ошибка запуска polling: {e}")
            # Пытаемся корректно остановить приложение
            try:
                await self.stop_bot()
            except Exception as stop_error:
                logger.error(f"Ошибка остановки после неудачного запуска: {stop_error}")
            raise

    async def stop_bot(self):
        """Остановка бота"""
        if self.application:
            logger.info("Остановка Telegram бота...")
            try:
                # Сначала останавливаем updater (polling)
                if hasattr(self.application, 'updater') and self.application.updater:
                    await self.application.updater.stop()
            except Exception as e:
                logger.warning(f"Ошибка остановки updater: {e}")

            try:
                # Останавливаем приложение
                await self.application.stop()
            except Exception as e:
                logger.warning(f"Ошибка остановки приложения: {e}")

            try:
                # Завершаем работу приложения
                await self.application.shutdown()
            except Exception as e:
                logger.warning(f"Ошибка завершения работы приложения: {e}")

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        chat_id = str(update.effective_chat.id)
        user = update.effective_user

        # Создание или обновление чата в БД
        telegram_chat = await self._get_or_create_chat(update.effective_chat, user)

        welcome_message = (
            f"👋 Привет, {user.first_name or 'друг'}!\n\n"
            "Я AI-консультант компании по печати. Я могу:\n"
            "• Помочь оформить заказ\n"
            "• Ответить на вопросы о наших услугах\n"
            "• Предоставить информацию о ценах и сроках\n\n"
            "Просто напишите мне, что вас интересует! 🚀"
        )

        await update.message.reply_text(welcome_message)

        # Логирование коммуникации
        await self._log_communication(
            chat_id=chat_id,
            message_content="/start",
            direction="inbound",
            customer_id=telegram_chat.customer_id
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_message = (
            "🆘 Помощь\n\n"
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/orders - Посмотреть ваши заказы\n"
            "/support - Связаться с поддержкой\n\n"
            "Просто напишите сообщение с вашим вопросом или запросом на заказ!"
        )

        await update.message.reply_text(help_message)

    async def _handle_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /orders"""
        chat_id = str(update.effective_chat.id)
        telegram_chat = await self._get_chat_by_id(chat_id)

        orders_summary = await self.order_service.get_customer_orders_summary(telegram_chat)
        await update.message.reply_text(orders_summary)

    async def _handle_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /support"""
        support_message = (
            "🛠 Техническая поддержка\n\n"
            "Если у вас возникли проблемы или вопросы:\n"
            "• Напишите нам в чат\n"
            "• Позвоните: +7 (999) 123-45-67\n"
            "• Email: support@printcompany.ru\n\n"
            "Мы ответим в ближайшее время! ⏰"
        )

        await update.message.reply_text(support_message)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        chat_id = str(update.effective_chat.id)
        message_text = update.message.text

        # Получение или создание чата
        telegram_chat = await self._get_or_create_chat(update.effective_chat, update.effective_user)

        # Логирование входящего сообщения
        await self._log_communication(
            chat_id=chat_id,
            message_content=message_text,
            direction="inbound",
            customer_id=telegram_chat.customer_id
        )

        try:
            # Обработка через AI
            ai_result = await self._process_with_ai(message_text, telegram_chat.customer_id)

            # Отправка ответа
            await update.message.reply_text(ai_result["response"])

            # Логирование исходящего ответа
            await self._log_communication(
                chat_id=chat_id,
                message_content=ai_result["response"],
                direction="outbound",
                customer_id=telegram_chat.customer_id,
                intent=ai_result.get("intent"),
                ai_response=True
            )

            # Обработка специальных действий (например, создание заказа)
            await self._handle_ai_actions(ai_result, telegram_chat, update)

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            error_message = "❌ Произошла ошибка. Попробуйте позже или свяжитесь с поддержкой."
            await update.message.reply_text(error_message)

    async def _process_with_ai(self, message: str, customer_id: int = None) -> Dict[str, Any]:
        """Обработка сообщения через AI"""
        # Получение контекста клиента
        customer_context = {}
        if customer_id:
            customer_context = await self._get_customer_context(customer_id)

        # AI анализ и генерация ответа
        result = await self.ai_service.process_customer_message(message, customer_context)

        return result

    async def _handle_ai_actions(self, ai_result: Dict[str, Any], telegram_chat: TelegramChat, update: Update):
        """Обработка специальных действий на основе AI анализа"""
        intent = ai_result.get("intent")

        if intent == IntentType.ORDER:
            # Попытка создать заказ через AI
            await self._process_order_creation(telegram_chat, update.message.text, update)
        elif intent == IntentType.COMPLAINT:
            # Эскалация к поддержке
            await self._escalate_to_support(telegram_chat, ai_result)

    async def _process_order_creation(self, telegram_chat: TelegramChat, message: str, update: Update):
        """Обработка создания заказа через AI"""
        try:
            # Использование сервиса заказов для обработки
            result = await self.order_service.process_order_request(
                message=message,
                telegram_chat=telegram_chat,
                conversation_history=None  # Пока без истории разговора
            )

            # Отправка результата пользователю
            await update.message.reply_text(result["message"])

            # Логирование результата
            if result["success"]:
                await self._log_communication(
                    chat_id=str(update.effective_chat.id),
                    message_content=f"Заказ #{result['order_id']} создан через Telegram",
                    direction="outbound",
                    customer_id=telegram_chat.customer_id,
                    intent="order_created",
                    ai_response=True
                )

        except Exception as e:
            logger.error(f"Ошибка создания заказа: {e}")
            await update.message.reply_text("❌ Произошла ошибка при создании заказа. Попробуйте позже.")

    async def _suggest_order_creation(self, telegram_chat: TelegramChat, update: Update):
        """Предложение создать заказ"""
        if not telegram_chat.customer_id:
            # Клиент не зарегистрирован
            await update.message.reply_text(
                "📝 Для оформления заказа нужно зарегистрироваться.\n"
                "Пожалуйста, предоставьте ваши контактные данные или свяжитесь с менеджером."
            )
            return

        # Создание черновика заказа или предложение заполнить форму
        order_suggestion = (
            "🛒 Готов помочь оформить заказ!\n\n"
            "Расскажите подробнее:\n"
            "• Что хотите напечатать?\n"
            "• Какое количество?\n"
            "• Есть ли дизайн или файл?\n"
            "• Когда нужен заказ?\n\n"
            "Или я могу создать заказ на основе нашей беседы."
        )

        await update.message.reply_text(order_suggestion)

    async def _escalate_to_support(self, telegram_chat: TelegramChat, ai_result: Dict[str, Any]):
        """Эскалация проблемы к поддержке"""
        # Здесь можно отправить уведомление менеджерам
        logger.info(f"Эскалация проблемы от клиента {telegram_chat.customer_id}: {ai_result}")

    async def _get_or_create_chat(self, chat, user) -> TelegramChat:
        """Получение или создание Telegram чата в БД"""
        chat_id = str(chat.id)

        # Проверка кеша
        if chat_id in self.chat_cache:
            return self.chat_cache[chat_id]

        # Поиск в БД
        telegram_chat = self.db.query(TelegramChat).filter(TelegramChat.chat_id == chat_id).first()

        if not telegram_chat:
            # Создание нового чата
            telegram_chat = TelegramChat(
                chat_id=chat_id,
                chat_type=chat.type,
                title=getattr(chat, 'title', None),
                username=getattr(user, 'username', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None)
            )

            # Попытка найти существующего клиента по username или имени
            customer = await self._find_customer_by_telegram_data(user)
            if customer:
                telegram_chat.customer_id = customer.id

            self.db.add(telegram_chat)
            self.db.commit()
            self.db.refresh(telegram_chat)

        # Добавление в кеш
        self.chat_cache[chat_id] = telegram_chat

        return telegram_chat

    async def _get_chat_by_id(self, chat_id: str) -> Optional[TelegramChat]:
        """Получение чата по ID"""
        if chat_id in self.chat_cache:
            return self.chat_cache[chat_id]

        telegram_chat = self.db.query(TelegramChat).filter(TelegramChat.chat_id == chat_id).first()
        if telegram_chat:
            self.chat_cache[chat_id] = telegram_chat

        return telegram_chat

    async def _find_customer_by_telegram_data(self, user) -> Optional[Customer]:
        """Поиск клиента по данным Telegram"""
        # Поиск по username в contact_info
        if user.username:
            customers = self.db.query(Customer).filter(
                Customer.contact_info.contains({"telegram": f"@{user.username}"})
            ).all()
            if customers:
                return customers[0]

        # Поиск по имени и фамилии
        if user.first_name and user.last_name:
            full_name = f"{user.first_name} {user.last_name}"
            customer = self.db.query(Customer).filter(Customer.name == full_name).first()
            if customer:
                return customer

        return None

    async def _get_customer_context(self, customer_id: int) -> Dict[str, Any]:
        """Получение контекста клиента для AI"""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {}

        recent_orders = self.db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(Order.created_at.desc()).limit(3).all()

        return {
            "customer_name": customer.name,
            "total_orders": customer.total_orders,
            "loyalty_level": customer.loyalty_level,
            "recent_orders": [
                {
                    "id": order.id,
                    "status": order.status,
                    "amount": float(order.total_amount) if order.total_amount else 0
                } for order in recent_orders
            ]
        }

    async def _log_communication(
        self,
        chat_id: str,
        message_content: str,
        direction: str,
        customer_id: int = None,
        intent: str = None,
        ai_response: bool = False
    ):
        """Логирование коммуникации"""
        communication = Communication(
            channel="telegram",
            direction=direction,
            message_content=message_content,
            customer_id=customer_id,
            intent=intent,
            extra_data={
                "chat_id": chat_id,
                "ai_generated": ai_response
            }
        )

        self.db.add(communication)
        self.db.commit()

        # Обновление статистики чата
        telegram_chat = await self._get_chat_by_id(chat_id)
        if telegram_chat:
            telegram_chat.increment_message_count()
            self.db.commit()

    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Ошибка в Telegram боте: {context.error}")

        # Специальная обработка сетевых ошибок
        from telegram.error import NetworkError
        if isinstance(context.error, NetworkError):
            logger.warning("Сетевая ошибка Telegram бота - возможно проблемы с подключением к API Telegram")
            # Не отправляем сообщение пользователю при сетевых ошибках,
            # так как это может вызвать дополнительные ошибки
            return

        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Произошла ошибка. Попробуйте позже."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    # API методы для управления ботом

    async def send_message_to_chat(self, chat_id: str, message: str) -> bool:
        """Отправка сообщения в чат"""
        try:
            if not self.bot:
                return False

            await self.bot.send_message(chat_id=chat_id, text=message)

            # Логирование
            telegram_chat = await self._get_chat_by_id(chat_id)
            await self._log_communication(
                chat_id=chat_id,
                message_content=message,
                direction="outbound",
                customer_id=telegram_chat.customer_id if telegram_chat else None,
                ai_response=False
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
            return False

    def get_bot_stats(self) -> Dict[str, Any]:
        """Получение статистики бота"""
        total_chats = self.db.query(TelegramChat).count()
        active_chats = self.db.query(TelegramChat).filter(TelegramChat.is_active == True).count()
        total_messages = self.db.query(Communication).filter(Communication.channel == "telegram").count()

        return {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "total_messages": total_messages,
            "bot_running": self.application is not None
        }


# Глобальный экземпляр сервиса для использования в роботах автоматизации
# В продакшене рекомендуется использовать dependency injection вместо глобальной переменной
telegram_bot_service = None


def get_telegram_bot_service(db_session=None) -> TelegramBotService:
    """
    Получение глобального экземпляра сервиса Telegram бота

    Args:
        db_session: Сессия базы данных (SqlAlchemy Session)

    Returns:
        TelegramBotService: Экземпляр сервиса
    """
    global telegram_bot_service
    if telegram_bot_service is None:
        if db_session is None:
            # Используем паттерн singleton с lazy инициализацией
            # Для реального использования нужно передать db_session
            telegram_bot_service = TelegramBotService(None)
        else:
            telegram_bot_service = TelegramBotService(db_session)
    return telegram_bot_service
