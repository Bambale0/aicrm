"""
API роутер для интеграции с Avito
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...core.config import settings
from ...core.dependencies import get_db
from ...services.avito_handler import AvitoCommunicationHandler
from ...services.avito_service import (
    AvitoAPIError,
    AvitoAuthError,
    AvitoRateLimitError,
    AvitoService,
)
from ...utils.logging import get_logger, get_messenger_logger
from ..schemas.avito import (  # Messenger schemas; Webhook schemas; Global settings schemas
    AvitoAnalyticsRequest,
    AvitoAnalyticsResponse,
    AvitoApplyVasRequest,
    AvitoApplyVasResponse,
    AvitoCallsStatsRequest,
    AvitoCallsStatsResponse,
    AvitoChatInfo,
    AvitoChatMessage,
    AvitoChatSettings,
    AvitoChatSettingsUpdate,
    AvitoErrorResponse,
    AvitoGlobalSettings,
    AvitoGlobalSettingsUpdate,
    AvitoItem,
    AvitoItemPerformance,
    AvitoMessengerStats,
    AvitoPricingRecommendation,
    AvitoPromotionRequest,
    AvitoPromotionResponse,
    AvitoSendMessageRequest,
    AvitoStatsRequest,
    AvitoStatsResponse,
    AvitoTestConnectionResponse,
    AvitoTestWebhookResponse,
    AvitoUpdatePriceRequest,
    AvitoUpdatePriceResponse,
    AvitoVasPricesResponse,
    AvitoWebhookRequest,
    AvitoWebhookResponse,
)

logger = get_logger(__name__)
messenger_logger = get_messenger_logger()


async def _get_available_ai_models():
    """Получение списка доступных AI моделей для Avito чатов"""
    try:
        # Импортируем и используем AI модели из API
        from ...config.openrouter_models import OPENROUTER_MODELS

        if OPENROUTER_MODELS and "models" in OPENROUTER_MODELS:
            # Возвращаем список моделей из OpenRouter
            model_list = []
            for model_id, model_data in OPENROUTER_MODELS["models"].items():
                model_list.append(
                    {"id": model_id, "name": model_data.get("name", model_id)}
                )
            return model_list
        else:
            # Fallback на статические модели
            return [
                {"id": "deepseek/deepseek-chat-v3.1", "name": "DeepSeek Chat v3.1"},
                {"id": "moonshotai/kimi-k2", "name": "Kimi K2"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
            ]
    except Exception as e:
        logger.error(f"Ошибка получения AI моделей: {e}")
        # Fallback на статические модели в случае ошибки
        return [
            {"id": "deepseek/deepseek-chat-v3.1", "name": "DeepSeek Chat v3.1"},
            {"id": "moonshotai/kimi-k2", "name": "Kimi K2"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
        ]


router = APIRouter(
    prefix="/avito",
    tags=["avito"],
    responses={
        401: {"model": AvitoErrorResponse, "description": "Ошибка авторизации"},
        429: {"model": AvitoErrorResponse, "description": "Превышен лимит запросов"},
        500: {"model": AvitoErrorResponse, "description": "Внутренняя ошибка сервера"},
    },
)


@router.get("/items", response_model=List[AvitoItem])
async def get_active_items(db: Session = Depends(get_db)):
    """
    Получение списка активных объявлений Avito
    """
    try:
        async with AvitoService() as service:
            items = await service.get_active_items()
            return items
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения объявлений: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/items/{item_id}/performance", response_model=AvitoItemPerformance)
async def get_item_performance(
    item_id: int, days: Optional[int] = 30, db: Session = Depends(get_db)
):
    """
    Получение производительности объявления
    """
    try:
        async with AvitoService() as service:
            performance = await service.get_item_performance(item_id, days or 30)
            return performance
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения производительности объявления {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/items/stats", response_model=AvitoStatsResponse)
async def get_items_stats(request: AvitoStatsRequest, db: Session = Depends(get_db)):
    """
    Получение статистики по списку объявлений
    """
    try:
        async with AvitoService() as service:
            stats = await service.client.get_item_stats(
                item_ids=request.item_ids,
                date_from=request.date_from,
                date_to=request.date_to,
                fields=request.fields or ["uniqViews", "uniqContacts", "uniqFavorites"],
                period_grouping=request.period_grouping or "day",
            )
            return stats
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/analytics", response_model=AvitoAnalyticsResponse)
async def get_analytics(request: AvitoAnalyticsRequest, db: Session = Depends(get_db)):
    """
    Получение аналитики по профилю
    """
    try:
        async with AvitoService() as service:
            analytics = await service.client.get_analytics(
                date_from=request.date_from,
                date_to=request.date_to,
                metrics=request.metrics,
                grouping=request.grouping or "item",
                **(request.filter or {}),
            )
            return analytics
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения аналитики: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/items/{item_id}/vas-prices", response_model=AvitoVasPricesResponse)
async def get_vas_prices(item_id: int, db: Session = Depends(get_db)):
    """
    Получение цен на услуги продвижения для объявления
    """
    try:
        async with AvitoService() as service:
            prices = await service.get_promotion_options([item_id])
            return {"prices": prices}
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения цен VAS для {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/items/{item_id}/vas", response_model=AvitoApplyVasResponse)
async def apply_vas(
    item_id: int, request: AvitoApplyVasRequest, db: Session = Depends(get_db)
):
    """
    Применение услуг продвижения к объявлению
    """
    try:
        async with AvitoService() as service:
            result = await service.client.apply_vas(
                item_id=item_id, slugs=request.slugs, stickers=request.stickers or []
            )
            return result
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка применения VAS к {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/items/{item_id}/price", response_model=AvitoUpdatePriceResponse)
async def update_item_price(
    item_id: int, request: AvitoUpdatePriceRequest, db: Session = Depends(get_db)
):
    """
    Обновление цены объявления
    """
    try:
        async with AvitoService() as service:
            result = await service.update_item_price(item_id, request.price)
            return result
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка обновления цены для {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post(
    "/items/{item_id}/optimize-price", response_model=AvitoPricingRecommendation
)
async def optimize_item_price(item_id: int, db: Session = Depends(get_db)):
    """
    Оптимизация цены объявления на основе статистики
    """
    try:
        async with AvitoService() as service:
            recommendation = await service.optimize_ad_pricing(item_id)
            return recommendation
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка оптимизации цены для {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/items/{item_id}/promote", response_model=AvitoPromotionResponse)
async def promote_item(
    item_id: int, request: AvitoPromotionRequest, db: Session = Depends(get_db)
):
    """
    Применение услуги продвижения к объявлению
    """
    try:
        async with AvitoService() as service:
            result = await service.apply_promotion_service(
                item_id=item_id,
                service_slug=request.service_slug,
                stickers=request.stickers or [],
            )
            return {
                "operation_id": result.get("operationId"),
                "service_slug": request.service_slug,
                "status": "applied",
            }
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка применения продвижения к {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/calls/stats", response_model=AvitoCallsStatsResponse)
async def get_calls_stats(
    request: AvitoCallsStatsRequest, db: Session = Depends(get_db)
):
    """
    Получение статистики звонков
    """
    try:
        async with AvitoService() as service:
            stats = await service.client.get_calls_stats(
                date_from=request.date_from,
                date_to=request.date_to,
                item_ids=request.item_ids or [],
            )
            return stats
    except AvitoAuthError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации Avito")
    except AvitoRateLimitError:
        raise HTTPException(status_code=429, detail="Превышен лимит запросов Avito")
    except AvitoAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения статистики звонков: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/webhook", response_model=AvitoWebhookResponse)
async def handle_avito_webhook(
    webhook_data: AvitoWebhookRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Webhook обработчик для уведомлений от Avito Messenger API

    Обрабатывает события:
    - message: Новые сообщения в чатах
    - status_change: Изменения статуса чатов
    - Другие события по мере необходимости
    """
    try:
        processed_events = 0
        handler = AvitoCommunicationHandler(db)

        for event in webhook_data.events:
            event_type = event.event
            payload = event.payload

            logger.info(f"Обработка webhook события: {event_type}")

            if event_type == "message":
                # Обработка нового сообщения
                chat_id = payload.get("chat_id")
                user_id = payload.get("user_id")
                message_id = payload.get("message_id")
                text = payload.get("text")
                timestamp = payload.get("timestamp")
                item_id = payload.get("item_id")

                if not chat_id or not user_id or not text:
                    logger.error(
                        f"Недостаточно данных для обработки сообщения: {payload}"
                    )
                    continue

                # Преобразуем в формат для существующего обработчика
                message_data = {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message": {"text": text, "timestamp": timestamp},
                    "item_id": item_id,
                }

                result = await handler.handle_incoming_message(message_data)
                if result.get("success", False):
                    processed_events += 1
                    logger.info(f"Сообщение {message_id} обработано успешно")
                else:
                    logger.error(
                        f"Ошибка обработки сообщения {message_id}: {result.get('error')}"
                    )

            elif event_type == "status_change":
                # Обработка изменения статуса чата
                chat_id = payload.get("chat_id")
                status = payload.get("status")
                timestamp = payload.get("timestamp")

                if not chat_id or not status:
                    logger.error(
                        f"Недостаточно данных для изменения статуса: {payload}"
                    )
                    continue

                # Обновляем статус чата в настройках
                success = await handler.update_chat_status(chat_id, status)
                if success:
                    processed_events += 1
                    logger.info(f"Статус чата {chat_id} обновлен на {status}")
                else:
                    logger.error(f"Ошибка обновления статуса чата {chat_id}")

            elif event_type == "chat_created":
                # Обработка создания нового чата
                chat_id = payload.get("chat_id")
                user_id = payload.get("user_id")
                item_id = payload.get("item_id")
                timestamp = payload.get("timestamp")

                if not chat_id:
                    logger.error(f"Недостаточно данных для создания чата: {payload}")
                    continue

                # Автоматизация для создания чата уже не нужна - просто логируем
                processed_events += 1
                logger.info(f"Чат {chat_id} создан")

            else:
                # Неизвестный тип события - логируем для отладки
                logger.warning(f"Неизвестный тип webhook события: {event_type}")
                processed_events += 1  # Считаем как обработанное

        return {"status": "ok", "processed_events": processed_events}

    except Exception as e:
        logger.error(f"Ошибка обработки webhook от Avito: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/messages/incoming")
async def handle_incoming_message(
    message_data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Обработка входящего сообщения из Avito

    Ожидаемый формат message_data:
    {
        "chat_id": "string",
        "user_id": "string",
        "message": {
            "text": "string",
            "timestamp": "2023-01-01T10:00:00Z"
        },
        "item_id": 12345
    }
    """
    try:
        handler = AvitoCommunicationHandler(db)
        result = await handler.handle_incoming_message(message_data)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Ошибка обработки сообщения"),
            )

        return {
            "status": "processed",
            "communication_id": result.get("communication_id"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обработки входящего сообщения Avito: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/health")
async def health_check():
    """
    Проверка работоспособности интеграции с Avito
    """
    return {"status": "ok", "service": "avito_integration"}


# Messenger endpoints


@router.get(
    "/messenger/v1/accounts/{user_id}/chats", response_model=List[AvitoChatInfo]
)
async def get_chats(
    user_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    """
    Получение списка чатов с Avito
    """
    try:
        messenger_logger.info(
            "Получение списка чатов",
            user_id=user_id,
            limit=limit,
            offset=offset,
            operation="get_chats",
        )

        from ...models.avito_chat import AvitoChatSettings

        # Оптимизированный запрос
        query = db.query(AvitoChatSettings)
        if hasattr(AvitoChatSettings, "customer"):
            query = query.options(joinedload(AvitoChatSettings.customer))

        chats = (
            query.order_by(AvitoChatSettings.last_message_at.desc().nulls_last())
            .offset(offset)
            .limit(limit)
            .all()
        )

        messenger_logger.info(
            "Список чатов получен",
            user_id=user_id,
            chats_count=len(chats),
            operation="get_chats",
        )

        result = []
        for chat in chats:
            customer_name = (
                chat.customer.name
                if hasattr(chat, "customer") and chat.customer
                else None
            )
            customer_email = (
                chat.customer.email
                if hasattr(chat, "customer") and chat.customer
                else None
            )

            result.append(
                {
                    "chat_id": chat.chat_id,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "last_message": getattr(chat, "last_message_preview", None),
                    "last_message_at": (
                        chat.last_message_at.isoformat()
                        if chat.last_message_at
                        else None
                    ),
                    "message_count": chat.message_count,
                    "ai_enabled": chat.ai_enabled,
                    "unread_count": getattr(chat, "unread_count", 0),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Ошибка получения списка чатов: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get(
    "/messenger/v1/accounts/{user_id}/chats/{chat_id}", response_model=AvitoChatSettings
)
async def get_chat_settings(user_id: int, chat_id: str, db: Session = Depends(get_db)):
    """
    Получение настроек чата
    """
    try:
        handler = AvitoCommunicationHandler(db)
        settings = await handler.get_chat_settings(chat_id)

        if not settings:
            raise HTTPException(status_code=404, detail="Настройки чата не найдены")

        return {
            "id": settings.id,
            "chat_id": settings.chat_id,
            "customer_id": settings.customer_id,
            "ai_enabled": settings.ai_enabled,
            "ai_model": await _get_available_ai_models(),
            "ai_temperature": settings.ai_temperature,
            "notifications_enabled": settings.notifications_enabled,
            "message_count": settings.message_count,
            "last_message_at": (
                settings.last_message_at.isoformat()
                if settings.last_message_at
                else None
            ),
            "last_ai_response_at": (
                settings.last_ai_response_at.isoformat()
                if settings.last_ai_response_at
                else None
            ),
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения настроек чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put(
    "/messenger/v1/accounts/{user_id}/chats/{chat_id}", response_model=AvitoChatSettings
)
async def update_chat_settings(
    user_id: int,
    chat_id: str,
    settings: AvitoChatSettingsUpdate,
    db: Session = Depends(get_db),
):
    """
    Обновление настроек чата
    """
    try:
        handler = AvitoCommunicationHandler(db)
        updated_settings = await handler.update_chat_settings(
            chat_id, settings.dict(exclude_unset=True)
        )

        if not updated_settings:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return {
            "id": updated_settings.id,
            "chat_id": updated_settings.chat_id,
            "customer_id": updated_settings.customer_id,
            "ai_enabled": updated_settings.ai_enabled,
            "ai_model": updated_settings.ai_model,
            "ai_temperature": updated_settings.ai_temperature,
            "notifications_enabled": updated_settings.notifications_enabled,
            "message_count": updated_settings.message_count,
            "last_message_at": (
                updated_settings.last_message_at.isoformat()
                if updated_settings.last_message_at
                else None
            ),
            "last_ai_response_at": (
                updated_settings.last_ai_response_at.isoformat()
                if updated_settings.last_ai_response_at
                else None
            ),
            "created_at": updated_settings.created_at.isoformat(),
            "updated_at": updated_settings.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления настроек чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/messenger/chats/{chat_id}/toggle-ai")
async def toggle_chat_ai(chat_id: str, enabled: bool, db: Session = Depends(get_db)):
    """
    Включение/выключение AI для чата
    """
    try:
        handler = AvitoCommunicationHandler(db)
        success = await handler.toggle_ai_for_chat(chat_id, enabled)

        if not success:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return {"success": True, "ai_enabled": enabled}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка переключения AI для чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get(
    "/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages",
    response_model=List[AvitoChatMessage],
)
async def get_chat_messages(
    user_id: int,
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Получение истории сообщений чата
    """
    try:
        from ...models.communication import Communication

        messages = (
            db.query(Communication)
            .filter(
                Communication.channel == "avito",
                Communication.extra_data.contains({"chat_id": chat_id}),
            )
            .order_by(Communication.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for msg in messages:
            result.append(
                {
                    "id": msg.id,
                    "chat_id": chat_id,
                    "direction": msg.direction,
                    "message_content": msg.message_content,
                    "intent": msg.intent,
                    "ai_generated": (
                        msg.extra_data.get("ai_generated", False)
                        if msg.extra_data
                        else False
                    ),
                    "created_at": msg.created_at.isoformat(),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Ошибка получения сообщений чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages")
async def send_message(
    user_id: int,
    chat_id: str,
    request: AvitoSendMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Отправка сообщения в чат
    """
    try:
        messenger_logger.info(
            "Отправка сообщения в чат",
            user_id=user_id,
            chat_id=chat_id,
            use_ai=request.use_ai,
            message_length=len(request.message),
            operation="send_message",
        )

        handler = AvitoCommunicationHandler(db)

        response_text = request.message

        # Отправка сообщения через Avito Messenger API
        success = await handler.send_message(chat_id, response_text)

        if not success:
            raise HTTPException(status_code=500, detail="Ошибка отправки сообщения")

        return {"success": True, "message": "Сообщение отправлено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/messenger/stats", response_model=AvitoMessengerStats)
async def get_messenger_stats(db: Session = Depends(get_db)):
    """
    Получение статистики мессенджера
    """
    try:
        from ...models.avito_chat import AvitoChatSettings
        from ...models.communication import Communication

        # Общее количество чатов
        total_chats = db.query(AvitoChatSettings).count()

        # Активные чаты (с сообщениями за последние 24 часа)
        from datetime import datetime, timedelta

        yesterday = datetime.utcnow() - timedelta(days=1)
        active_chats = (
            db.query(AvitoChatSettings)
            .filter(
                AvitoChatSettings.last_message_at is not None,
                AvitoChatSettings.last_message_at >= yesterday,
            )
            .count()
        )

        # Чаты с включенным AI
        ai_enabled_chats = (
            db.query(AvitoChatSettings)
            .filter(AvitoChatSettings.ai_enabled.is_(True))
            .count()
        )

        # Общее количество сообщений
        total_messages = (
            db.query(Communication).filter(Communication.channel == "avito").count()
        )

        # Сообщений от AI
        ai_messages = (
            db.query(Communication)
            .filter(
                Communication.channel == "avito",
                Communication.extra_data.contains({"ai_generated": True}),
            )
            .count()
        )

        # Простой расчет времени ответа (может быть None)
        avg_response_time = None

        return {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "ai_enabled_chats": ai_enabled_chats,
            "total_messages": total_messages,
            "ai_messages": ai_messages,
            "avg_response_time": avg_response_time,
        }

    except Exception as e:
        logger.error(f"Ошибка получения статистики мессенджера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# Global Settings endpoints


@router.get("/settings", response_model=AvitoGlobalSettings)
async def get_global_settings(db: Session = Depends(get_db)):
    """
    Получение глобальных настроек Avito
    """
    try:
        from ...models.avito_chat import AvitoGlobalSettings

        settings = db.query(AvitoGlobalSettings).first()
        if not settings:
            # Создаем настройки по умолчанию
            settings = AvitoGlobalSettings()
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return {
            "id": settings.id,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "access_token": settings.access_token,
            "refresh_token": settings.refresh_token,
            "token_expires_at": (
                settings.token_expires_at.isoformat()
                if settings.token_expires_at
                else None
            ),
            "webhook_url": settings.webhook_url,
            "webhook_secret": settings.webhook_secret,
            "auto_reply_enabled": settings.auto_reply_enabled,
            "auto_reply_message": settings.auto_reply_message,
            "ai_enabled": settings.ai_enabled,
            "ai_model": settings.ai_model,
            "ai_temperature": settings.ai_temperature,
            "ai_max_tokens": settings.ai_max_tokens,
            "notification_email": settings.notification_email,
            "sync_interval": settings.sync_interval,
            "max_concurrent_chats": settings.max_concurrent_chats,
            "is_active": settings.is_active,
            "last_sync_at": (
                settings.last_sync_at.isoformat() if settings.last_sync_at else None
            ),
            "last_error": settings.last_error,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Ошибка получения глобальных настроек Avito: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/settings", response_model=AvitoGlobalSettings)
async def update_global_settings(
    settings: AvitoGlobalSettingsUpdate, db: Session = Depends(get_db)
):
    """
    Обновление глобальных настроек Avito
    """
    try:
        from ...models.avito_chat import AvitoGlobalSettings

        existing_settings = db.query(AvitoGlobalSettings).first()
        if not existing_settings:
            existing_settings = AvitoGlobalSettings()
            db.add(existing_settings)

        # Обновляем только переданные поля
        update_data = settings.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_settings, field, value)

        db.commit()
        db.refresh(existing_settings)

        return {
            "id": existing_settings.id,
            "client_id": existing_settings.client_id,
            "client_secret": existing_settings.client_secret,
            "access_token": existing_settings.access_token,
            "refresh_token": existing_settings.refresh_token,
            "token_expires_at": (
                existing_settings.token_expires_at.isoformat()
                if existing_settings.token_expires_at
                else None
            ),
            "webhook_url": existing_settings.webhook_url,
            "webhook_secret": existing_settings.webhook_secret,
            "auto_reply_enabled": existing_settings.auto_reply_enabled,
            "auto_reply_message": existing_settings.auto_reply_message,
            "ai_enabled": existing_settings.ai_enabled,
            "ai_model": existing_settings.ai_model,
            "ai_temperature": existing_settings.ai_temperature,
            "ai_max_tokens": existing_settings.ai_max_tokens,
            "notification_email": existing_settings.notification_email,
            "sync_interval": existing_settings.sync_interval,
            "max_concurrent_chats": existing_settings.max_concurrent_chats,
            "is_active": existing_settings.is_active,
            "last_sync_at": (
                existing_settings.last_sync_at.isoformat()
                if existing_settings.last_sync_at
                else None
            ),
            "last_error": existing_settings.last_error,
            "created_at": existing_settings.created_at.isoformat(),
            "updated_at": existing_settings.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Ошибка обновления глобальных настроек Avito: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/settings/test-connection", response_model=AvitoTestConnectionResponse)
async def test_connection(db: Session = Depends(get_db)):
    """
    Тестирование подключения к Avito API
    """
    try:
        # Используем настройки из config.py (settings)
        if (
            not settings.avito_client_id
            or not settings.avito_client_secret
            or not settings.avito_user_id
        ):
            return {
                "success": False,
                "message": "Не настроены учетные данные Avito (AVITO_CLIENT_ID, AVITO_CLIENT_SECRET, AVITO_USER_ID в .env файле)",
            }

        # Тестируем получение токена и простой API вызов
        async with AvitoService() as avito_service:
            try:
                # Получаем список объявлений для тестирования аутентификации
                items = await avito_service.get_active_items()
                logger.info(
                    f"Успешное тестирование Avito API: получено {len(items)} объявлений"
                )

                return {
                    "success": True,
                    "message": f"Подключение успешно. Получено {len(items)} активных объявлений.",
                }

            except AvitoAuthError as e:
                return {
                    "success": False,
                    "message": f"Ошибка авторизации Avito: проверьте корректность Client ID и Client Secret. {str(e.details) if hasattr(e, 'details') and e.details else ''}",
                }
            except AvitoAPIError as e:
                return {"success": False, "message": f"Ошибка API Avito: {str(e)}"}
            except Exception as api_error:
                logger.error(
                    f"Неожиданная ошибка при тестировании Avito API: {api_error}"
                )
                return {
                    "success": False,
                    "message": f"Неожиданная ошибка при тестировании API: {str(api_error)}",
                }

    except Exception as e:
        logger.error(f"Ошибка тестирования подключения к Avito: {e}")
        return {
            "success": False,
            "message": f"Ошибка при тестировании подключения: {str(e)}",
        }


@router.post("/settings/test-webhook", response_model=AvitoTestWebhookResponse)
async def test_webhook(db: Session = Depends(get_db)):
    """
    Тестирование webhook
    """
    try:
        import httpx

        from ...models.avito_chat import AvitoGlobalSettings

        global_settings = db.query(AvitoGlobalSettings).first()
        if not global_settings or not global_settings.webhook_url:
            return {
                "success": False,
                "message": "Не настроен URL webhook в глобальных настройках Avito",
            }

        webhook_url = global_settings.webhook_url.strip()

        # Проверяем формат URL
        if not webhook_url.startswith(("http://", "https://")):
            return {
                "success": False,
                "message": "Неверный формат URL webhook: должен начинаться с http:// или https://",
            }

        # Проверяем доступность endpoint'а через HEAD запрос
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(webhook_url)

                if response.status_code not in [200, 201, 202, 204, 301, 302, 307, 308]:
                    return {
                        "success": False,
                        "message": f"Webhook URL недоступен: HTTP {response.status_code}",
                    }

                # Отправляем тестовый POST запрос с тестовым webhook событием
                test_payload = {
                    "events": [
                        {
                            "event": "message",
                            "payload": {
                                "chat_id": "test_chat_123",
                                "user_id": "test_user",
                                "message_id": "test_message_456",
                                "text": "Тестовое сообщение от Avito webhook",
                                "timestamp": "2023-01-01T12:00:00Z",
                                "item_id": 12345,
                                "author_role": "buyer",
                            },
                        }
                    ]
                }

                response = await client.post(
                    webhook_url,
                    json=test_payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in [200, 201, 202]:
                    try:
                        response_data = response.json()
                        if response_data.get("status") == "ok":
                            processed_events = response_data.get("processed_events", 0)
                            return {
                                "success": True,
                                "message": f"Webhook успешно протестирован. Обработано событий: {processed_events}",
                                "status_code": response.status_code,
                            }
                        else:
                            return {
                                "success": False,
                                "message": f"Webhook вернул неуспешный статус: {response_data}",
                            }
                    except ValueError:
                        return {
                            "success": True,
                            "message": f"Webhook ответил HTTP {response.status_code}, но формат ответа не распознан",
                        }
                else:
                    return {
                        "success": False,
                        "message": f"Webhook вернул ошибку: HTTP {response.status_code} - {response.text[:200]}",
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при обращении к webhook URL: {webhook_url} - {str(e)}",
            }

    except Exception as e:
        logger.error(f"Ошибка тестирования webhook: {e}")
        return {
            "success": False,
            "message": f"Ошибка при тестировании webhook: {str(e)}",
        }


# Chat linking/unlinking endpoints


@router.post("/messenger/chats/{chat_id}/link-customer")
async def link_avito_chat_to_customer(
    chat_id: str, customer_id: int, db: Session = Depends(get_db)
):
    """
    Связывание Avito чата с существующим клиентом CRM
    """
    try:
        from ...models.avito_chat import AvitoChatSettings

        # Проверка существования чата
        chat = (
            db.query(AvitoChatSettings)
            .filter(AvitoChatSettings.chat_id == chat_id)
            .first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        # Проверка существования клиента
        from ...models.customer import Customer

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Клиент не найден")

        # Связывание
        if hasattr(chat, "customer_id"):
            setattr(chat, "customer_id", customer_id)
        db.commit()

        return {
            "message": f"Чат {chat_id} связан с клиентом {customer.name}",
            "chat_id": chat_id,
            "customer_id": customer_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка связывания чата {chat_id} с клиентом {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/messenger/chats/{chat_id}/unlink-customer")
async def unlink_avito_chat_from_customer(chat_id: str, db: Session = Depends(get_db)):
    """
    Отвязывание Avito чата от клиента
    """
    try:
        from ...models.avito_chat import AvitoChatSettings

        chat = (
            db.query(AvitoChatSettings)
            .filter(AvitoChatSettings.chat_id == chat_id)
            .first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        # Отвязывание
        if hasattr(chat, "customer_id"):
            setattr(chat, "customer_id", None)
        db.commit()

        return {"message": f"Чат {chat_id} отвязан от клиента"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отвязывания чата {chat_id} от клиента: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
