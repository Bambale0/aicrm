"""
API роутеры для управления Telegram ботом
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...services.telegram_bot_service import TelegramBotService
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


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
    bot_service: TelegramBotService = Depends(get_telegram_bot_service)
):
    """
    Инициализация и запуск Telegram бота
    """
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=400,
            detail="Telegram bot token не настроен в конфигурации"
        )

    success = await bot_service.initialize_bot()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Не удалось инициализировать Telegram бота"
        )

    # Запуск бота в фоне
    background_tasks.add_task(bot_service.start_polling)

    return {"message": "Telegram бот успешно инициализирован и запущен"}


@router.post("/stop", summary="Остановка Telegram бота")
async def stop_bot(
    bot_service: TelegramBotService = Depends(get_telegram_bot_service)
):
    """
    Остановка Telegram бота
    """
    await bot_service.stop_bot()
    return {"message": "Telegram бот остановлен"}


@router.post("/send-message", summary="Отправка сообщения в чат")
async def send_message(
    request: SendMessageRequest,
    bot_service: TelegramBotService = Depends(get_telegram_bot_service)
):
    """
    Отправка сообщения в указанный Telegram чат
    """
    success = await bot_service.send_message_to_chat(request.chat_id, request.message)
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось отправить сообщение в чат {request.chat_id}"
        )

    return {"message": f"Сообщение отправлено в чат {request.chat_id}"}


@router.get("/stats", summary="Получение статистики бота", response_model=BotStatsResponse)
async def get_bot_stats(
    bot_service: TelegramBotService = Depends(get_telegram_bot_service)
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
    db: Session = Depends(get_db)
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
                "created_at": chat.created_at
            } for chat in chats
        ],
        "total": db.query(TelegramChat).count(),
        "limit": limit,
        "offset": offset
    }


@router.get("/chat/{chat_id}", summary="Получение информации о чате")
async def get_chat_info(
    chat_id: str,
    db: Session = Depends(get_db)
):
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
        "updated_at": chat.updated_at
    }


@router.get("/communications", summary="Получение коммуникаций через Telegram")
async def get_telegram_communications(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Получение списка коммуникаций через Telegram канал
    """
    from ...models.communication import Communication

    communications = db.query(Communication).filter(
        Communication.channel == "telegram"
    ).order_by(Communication.created_at.desc()).offset(offset).limit(limit).all()

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
                "extra_data": comm.extra_data
            } for comm in communications
        ],
        "total": db.query(Communication).filter(Communication.channel == "telegram").count(),
        "limit": limit,
        "offset": offset
    }


@router.post("/chat/{chat_id}/link-customer", summary="Связывание чата с клиентом")
async def link_chat_to_customer(
    chat_id: str,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    Связывание Telegram чата с существующим клиентом CRM
    """
    from ...models.telegram_chat import TelegramChat
    from ...models.customer import Customer

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
        "customer_id": customer_id
    }


@router.delete("/chat/{chat_id}/unlink-customer", summary="Отвязывание чата от клиента")
async def unlink_chat_from_customer(
    chat_id: str,
    db: Session = Depends(get_db)
):
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
async def telegram_webhook(
    update_data: dict,
    db: Session = Depends(get_db)
):
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
                raise HTTPException(status_code=500, detail="Не удалось инициализировать бота")

        # Инициализируем application если нужно
        if not hasattr(bot_service.application, '_initialized') or not bot_service.application._initialized:
            await bot_service.application.initialize()

        # Создаем объект Update из данных webhook
        update = Update.de_json(update_data, bot_service.bot)

        # Обрабатываем обновление
        await bot_service.application.process_update(update)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки webhook: {str(e)}")


@router.post("/set-webhook", summary="Установка webhook для бота")
async def set_webhook(
    webhook_url: str = "https://your-domain.com/telegram/webhook"
):
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
            raise HTTPException(status_code=400, detail=f"Ошибка установки webhook: {result}")
    else:
        raise HTTPException(status_code=response.status_code, detail="Ошибка HTTP запроса")


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
            raise HTTPException(status_code=400, detail=f"Ошибка удаления webhook: {result}")
    else:
        raise HTTPException(status_code=response.status_code, detail="Ошибка HTTP запроса")
