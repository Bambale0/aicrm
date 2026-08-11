"""
API роутеры для управления Telegram ботом
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.dependencies import get_current_user, get_db
from ...services.telegram_bot_service import TelegramBotService
from ..schemas.auth import User as UserSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/ping")
async def ping():
    return "pong"


class SendMessageRequest(BaseModel):
    """Запрос на отправку сообщения"""

    chat_id: str
    message: str


class BotStatsResponse(BaseModel):
    """Ответ со статистикой бота"""

    total_chats: int
    active_chats: int
    total_messages: int
    bot_running: bool


# Глобальный экземпляр бота (в продакшене лучше использовать dependency injection)
bot_service = None


def get_telegram_bot_service(db: Session = Depends(get_db)) -> TelegramBotService:
    """Получение сервиса Telegram бота"""
    global bot_service
    if bot_service is None:
        bot_service = TelegramBotService(db)
    return bot_service


@router.post("/initialize", summary="Инициализация Telegram бота")
async def initialize_bot(
    background_tasks: BackgroundTasks,
    bot_service: TelegramBotService = Depends(get_telegram_bot_service),
):
    """
    Инициализация и запуск Telegram бота
    """
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=400, detail="Telegram bot token не настроен в конфигурации"
        )

    # Проверяем, не запущен ли уже бот
    stats = bot_service.get_bot_stats()
    if stats.get("bot_running"):
        return {"message": "Telegram бот уже запущен"}

    success = await bot_service.initialize_bot()
    if not success:
        raise HTTPException(
            status_code=500, detail="Не удалось инициализировать Telegram бота"
        )

    # Запуск бота в фоне
    background_tasks.add_task(bot_service.start_polling)

    return {"message": "Telegram бот успешно инициализирован и запущен"}


@router.post("/stop", summary="Остановка Telegram бота")
async def stop_bot(bot_service: TelegramBotService = Depends(get_telegram_bot_service)):
    """
    Остановка Telegram бота
    """
    await bot_service.stop_bot()
    return {"message": "Telegram бот остановлен"}


@router.post("/send-message", summary="Отправка сообщения в чат")
async def send_message(
    request: SendMessageRequest,
    bot_service: TelegramBotService = Depends(get_telegram_bot_service),
):
    """
    Отправка сообщения в указанный Telegram чат
    """
    success = await bot_service.send_message_to_chat(request.chat_id, request.message)
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось отправить сообщение в чат {request.chat_id}",
        )

    return {"message": f"Сообщение отправлено в чат {request.chat_id}"}


@router.get(
    "/stats", summary="Получение статистики бота", response_model=BotStatsResponse
)
async def get_bot_stats(
    bot_service: TelegramBotService = Depends(get_telegram_bot_service),
):
    """
    Получение статистики работы Telegram бота
    """
    stats = bot_service.get_bot_stats()
    return BotStatsResponse(**stats)


@router.get("/chats", summary="Получение списка чатов")
async def get_chats(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """
    Получение списка Telegram чатов
    """
    from ...models.telegram_chat import TelegramChat

    chats = db.query(TelegramChat).offset(offset).limit(limit).all()

    return {
        "chats": [
            {
                "id": chat.id,
                "chat_id": chat.chat_id,
                "chat_type": chat.chat_type,
                "display_name": chat.display_name,
                "customer_id": chat.customer_id,
                "is_active": chat.is_active,
                "message_count": chat.message_count,
                "last_message_at": chat.last_message_at,
                "created_at": chat.created_at,
            }
            for chat in chats
        ],
        "total": db.query(TelegramChat).count(),
        "limit": limit,
        "offset": offset,
    }


@router.get("/chat/{chat_id}", summary="Получение информации о чате")
async def get_chat_info(chat_id: str, db: Session = Depends(get_db)):
    """
    Получение детальной информации о Telegram чате
    """
    from ...models.telegram_chat import TelegramChat

    chat = db.query(TelegramChat).filter(TelegramChat.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    return {
        "id": chat.id,
        "chat_id": chat.chat_id,
        "chat_type": chat.chat_type,
        "title": chat.title,
        "username": chat.username,
        "first_name": chat.first_name,
        "last_name": chat.last_name,
        "display_name": chat.display_name,
        "customer_id": chat.customer_id,
        "is_active": chat.is_active,
        "is_blocked": chat.is_blocked,
        "language": chat.language,
        "notifications_enabled": chat.notifications_enabled,
        "message_count": chat.message_count,
        "last_message_at": chat.last_message_at,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
    }


@router.get("/communications", summary="Получение коммуникаций через Telegram")
async def get_telegram_communications(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
):
    """
    Получение списка коммуникаций через Telegram канал
    """
    from ...models.communication import Communication

    communications = (
        db.query(Communication)
        .filter(Communication.channel == "telegram")
        .order_by(Communication.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "communications": [
            {
                "id": comm.id,
                "channel": comm.channel,
                "direction": comm.direction,
                "direction_display": comm.direction_display,
                "message_content": comm.message_content,
                "message_type": comm.message_type,
                "customer_id": comm.customer_id,
                "order_id": comm.order_id,
                "intent": comm.intent,
                "sentiment": comm.sentiment,
                "created_at": comm.created_at,
                "extra_data": comm.extra_data,
            }
            for comm in communications
        ],
        "total": db.query(Communication)
        .filter(Communication.channel == "telegram")
        .count(),
        "limit": limit,
        "offset": offset,
    }


@router.post("/chat/{chat_id}/link-customer", summary="Связывание чата с клиентом")
async def link_chat_to_customer(
    chat_id: str, customer_id: int, db: Session = Depends(get_db)
):
    """
    Связывание Telegram чата с существующим клиентом CRM
    """
    from ...models.customer import Customer
    from ...models.telegram_chat import TelegramChat

    # Проверка существования чата
    chat = db.query(TelegramChat).filter(TelegramChat.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    # Проверка существования клиента
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Связывание
    chat.customer_id = customer_id
    db.commit()

    return {
        "message": f"Чат {chat.display_name} связан с клиентом {customer.name}",
        "chat_id": chat_id,
        "customer_id": customer_id,
    }


@router.delete("/chat/{chat_id}/unlink-customer", summary="Отвязывание чата от клиента")
async def unlink_chat_from_customer(chat_id: str, db: Session = Depends(get_db)):
    """
    Отвязывание Telegram чата от клиента
    """
    from ...models.telegram_chat import TelegramChat

    chat = db.query(TelegramChat).filter(TelegramChat.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    chat.customer_id = None
    db.commit()

    return {"message": f"Чат {chat.display_name} отвязан от клиента"}


@router.post("/webhook", summary="Webhook для обработки сообщений Telegram")
async def telegram_webhook(update_data: dict, db: Session = Depends(get_db)):
    """
    Обработка webhook обновлений от Telegram
    """
    global bot_service

    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from telegram import Update

        # Инициализируем бота если нужно
        if bot_service is None or bot_service.application is None:
            bot_service = TelegramBotService(db)
            success = await bot_service.initialize_bot()
            if not success:
                raise HTTPException(
                    status_code=500, detail="Не удалось инициализировать бота"
                )

        # Инициализируем application если нужно
        if (
            not hasattr(bot_service.application, "_initialized")
            or not bot_service.application._initialized
        ):
            await bot_service.application.initialize()

        # Создаем объект Update из данных webhook
        update = Update.de_json(update_data, bot_service.bot)

        # Обрабатываем обновление
        await bot_service.application.process_update(update)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка обработки webhook: {str(e)}"
        )


@router.post("/set-webhook", summary="Установка webhook для бота")
async def set_webhook(webhook_url: str = "https://your-domain.com/telegram/webhook"):
    """
    Установка webhook URL для Telegram бота
    """
    import httpx

    token = settings.telegram_bot_token
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token не настроен")

    url = f"https://api.telegram.org/bot{token}/setWebhook"
    data = {"url": webhook_url}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            return {"message": "Webhook установлен успешно", "result": result}
        else:
            raise HTTPException(
                status_code=400, detail=f"Ошибка установки webhook: {result}"
            )
    else:
        raise HTTPException(
            status_code=response.status_code, detail="Ошибка HTTP запроса"
        )


# Настройки Telegram
@router.get("/settings", summary="Получение настроек Telegram")
async def get_telegram_settings(
    db: Session = Depends(get_db), current_user: UserSchema = Depends(get_current_user)
):
    """
    Получение текущих настроек Telegram бота
    """
    from ...models.telegram_settings import TelegramSettings

    settings = db.query(TelegramSettings).first()

    if not settings:
        # Возвращаем настройки по умолчанию
        return {
            "bot_token": "",
            "webhook_url": "",
            "webhook_secret": "",
            "auto_reply_enabled": False,
            "auto_reply_message": "",
            "ai_enabled": True,
            "ai_model": "gpt-4",
            "ai_temperature": 0.7,
            "ai_max_tokens": 1000,
            "notification_email": "",
            "sync_interval": 300,
            "max_concurrent_chats": 10,
        }

    return {
        "id": settings.id,
        "bot_token": settings.bot_token or "",
        "webhook_url": settings.webhook_url or "",
        "webhook_secret": settings.webhook_secret or "",
        "auto_reply_enabled": settings.auto_reply_enabled,
        "auto_reply_message": settings.auto_reply_message or "",
        "ai_enabled": settings.ai_enabled,
        "ai_model": settings.ai_model,
        "ai_temperature": settings.ai_temperature,
        "ai_max_tokens": settings.ai_max_tokens,
        "notification_email": settings.notification_email or "",
        "sync_interval": settings.sync_interval,
        "max_concurrent_chats": settings.max_concurrent_chats,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }


@router.put("/settings", summary="Сохранение настроек Telegram")
async def save_telegram_settings(
    settings_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """
    Сохранение настроек Telegram бота
    """
    from ...models.telegram_settings import TelegramSettings

    # Получаем или создаем настройки
    settings = db.query(TelegramSettings).first()
    if not settings:
        settings = TelegramSettings()
        db.add(settings)

    # Обновляем поля
    allowed_fields = {
        "bot_token",
        "webhook_url",
        "webhook_secret",
        "auto_reply_enabled",
        "auto_reply_message",
        "ai_enabled",
        "ai_model",
        "ai_temperature",
        "ai_max_tokens",
        "notification_email",
        "sync_interval",
        "max_concurrent_chats",
    }

    for field, value in settings_data.items():
        if field in allowed_fields and hasattr(settings, field):
            setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return {
        "message": "Настройки Telegram сохранены успешно",
        "settings": {
            "id": settings.id,
            "bot_token": settings.bot_token or "",
            "webhook_url": settings.webhook_url or "",
            "webhook_secret": settings.webhook_secret or "",
            "auto_reply_enabled": settings.auto_reply_enabled,
            "auto_reply_message": settings.auto_reply_message or "",
            "ai_enabled": settings.ai_enabled,
            "ai_model": settings.ai_model,
            "ai_temperature": settings.ai_temperature,
            "ai_max_tokens": settings.ai_max_tokens,
            "notification_email": settings.notification_email or "",
            "sync_interval": settings.sync_interval,
            "max_concurrent_chats": settings.max_concurrent_chats,
        },
    }


@router.post("/test-connection", summary="Тест подключения к Telegram боту")
async def test_telegram_connection(
    db: Session = Depends(get_db), current_user: UserSchema = Depends(get_current_user)
):
    """
    Тестирование подключения к Telegram боту
    """
    import httpx

    from ...models.telegram_settings import TelegramSettings

    settings = db.query(TelegramSettings).first()
    if not settings or not settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token не настроен")

    try:
        # Тестируем подключение через getMe
        url = f"https://api.telegram.org/bot{settings.bot_token}/getMe"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                return {
                    "success": True,
                    "message": "Подключение к Telegram боту успешно",
                    "bot_info": {
                        "id": bot_info.get("id"),
                        "username": bot_info.get("username"),
                        "first_name": bot_info.get("first_name"),
                        "can_join_groups": bot_info.get("can_join_groups"),
                        "can_read_all_group_messages": bot_info.get(
                            "can_read_all_group_messages"
                        ),
                        "supports_inline_queries": bot_info.get(
                            "supports_inline_queries"
                        ),
                    },
                }
            else:
                return {
                    "success": False,
                    "message": f"Ошибка API Telegram: {result.get('description', 'Unknown error')}",
                    "error_code": result.get("error_code"),
                }
        else:
            return {
                "success": False,
                "message": f"HTTP ошибка: {response.status_code}",
                "response": response.text,
            }

    except httpx.TimeoutException:
        return {"success": False, "message": "Таймаут подключения к Telegram API"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при тестировании подключения: {str(e)}",
        }


@router.post("/test-webhook", summary="Тест webhook Telegram")
async def test_telegram_webhook(
    db: Session = Depends(get_db), current_user: UserSchema = Depends(get_current_user)
):
    """
    Тестирование webhook для Telegram бота
    """
    import httpx

    from ...models.telegram_settings import TelegramSettings

    settings = db.query(TelegramSettings).first()
    if not settings or not settings.webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL не настроен")

    try:
        # Создаем тестовый update
        test_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1609459200,
                "text": "Тестовое сообщение для проверки webhook",
            },
        }

        # Отправляем тестовый запрос на webhook
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.webhook_url,
                json=test_update,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "ok":
                    return {
                        "success": True,
                        "message": "Webhook успешно обработал тестовый запрос",
                        "response": result,
                    }
                else:
                    return {
                        "success": False,
                        "message": "Webhook вернул ошибку",
                        "response": result,
                    }
            except ValueError:
                return {
                    "success": True,
                    "message": "Webhook ответил успешно (статус 200)",
                    "response_text": response.text[:200],
                }
        else:
            return {
                "success": False,
                "message": f"Webhook вернул ошибку HTTP {response.status_code}",
                "response": response.text[:200],
            }

    except httpx.TimeoutException:
        return {"success": False, "message": "Таймаут ожидания ответа от webhook"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при тестировании webhook: {str(e)}",
        }


@router.post("/delete-webhook", summary="Удаление webhook")
async def delete_webhook():
    """
    Удаление webhook для бота
    """
    import httpx

    token = settings.telegram_bot_token
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token не настроен")

    url = f"https://api.telegram.org/bot{token}/deleteWebhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(url)

    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            return {"message": "Webhook удален успешно", "result": result}
        else:
            raise HTTPException(
                status_code=400, detail=f"Ошибка удаления webhook: {result}"
            )
    else:
        raise HTTPException(
            status_code=response.status_code, detail="Ошибка HTTP запроса"
        )
