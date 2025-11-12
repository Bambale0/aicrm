"""
API роутер для интеграции с Avito
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...services.avito_service import AvitoService, AvitoAPIError, AvitoRateLimitError, AvitoAuthError
from ...services.avito_handler import AvitoCommunicationHandler
from ..schemas.avito import (
    AvitoItem,
    AvitoStatsRequest,
    AvitoStatsResponse,
    AvitoAnalyticsRequest,
    AvitoAnalyticsResponse,
    AvitoVasPricesResponse,
    AvitoApplyVasRequest,
    AvitoApplyVasResponse,
    AvitoUpdatePriceRequest,
    AvitoUpdatePriceResponse,
    AvitoCallsStatsRequest,
    AvitoCallsStatsResponse,
    AvitoItemPerformance,
    AvitoPricingRecommendation,
    AvitoPromotionRequest,
    AvitoPromotionResponse,
    AvitoErrorResponse,
    # Messenger schemas
    AvitoChatSettings,
    AvitoChatSettingsCreate,
    AvitoChatSettingsUpdate,
    AvitoChatMessage,
    AvitoChatInfo,
    AvitoSendMessageRequest,
    AvitoMessengerStats
)
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/avito",
    tags=["avito"],
    responses={
        401: {"model": AvitoErrorResponse, "description": "Ошибка авторизации"},
        429: {"model": AvitoErrorResponse, "description": "Превышен лимит запросов"},
        500: {"model": AvitoErrorResponse, "description": "Внутренняя ошибка сервера"}
    }
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
async def get_item_performance(item_id: int, days: Optional[int] = 30, db: Session = Depends(get_db)):
    """
    Получение производительности объявления
    """
    try:
        async with AvitoService() as service:
            performance = await service.get_item_performance(item_id, days)
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
                fields=request.fields,
                period_grouping=request.period_grouping
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
                grouping=request.grouping,
                **(request.filter or {})
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
async def apply_vas(item_id: int, request: AvitoApplyVasRequest, db: Session = Depends(get_db)):
    """
    Применение услуг продвижения к объявлению
    """
    try:
        async with AvitoService() as service:
            result = await service.client.apply_vas(
                item_id=item_id,
                slugs=request.slugs,
                stickers=request.stickers
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
async def update_item_price(item_id: int, request: AvitoUpdatePriceRequest, db: Session = Depends(get_db)):
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


@router.post("/items/{item_id}/optimize-price", response_model=AvitoPricingRecommendation)
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
async def promote_item(item_id: int, request: AvitoPromotionRequest, db: Session = Depends(get_db)):
    """
    Применение услуги продвижения к объявлению
    """
    try:
        async with AvitoService() as service:
            result = await service.apply_promotion_service(
                item_id=item_id,
                service_slug=request.service_slug,
                stickers=request.stickers
            )
            return {
                "operation_id": result.get("operationId"),
                "service_slug": request.service_slug,
                "status": "applied"
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
async def get_calls_stats(request: AvitoCallsStatsRequest, db: Session = Depends(get_db)):
    """
    Получение статистики звонков
    """
    try:
        async with AvitoService() as service:
            stats = await service.client.get_calls_stats(
                date_from=request.date_from,
                date_to=request.date_to,
                item_ids=request.item_ids
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


@router.post("/messages/incoming")
async def handle_incoming_message(
    message_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
            raise HTTPException(status_code=400, detail=result.get("error", "Ошибка обработки сообщения"))

        return {"status": "processed", "communication_id": result.get("communication_id")}

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

@router.get("/messenger/chats", response_model=List[AvitoChatInfo])
async def get_chats(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """
    Получение списка чатов с Avito
    """
    try:
        from ...models.avito_chat import AvitoChatSettings
        from ...models.customer import Customer
        from ...models.communication import Communication

        # Получаем настройки чатов с информацией о клиентах
        chats_query = db.query(AvitoChatSettings).options(
            db.joinedload(AvitoChatSettings.customer)
        ).order_by(AvitoChatSettings.last_message_at.desc().nulls_last())

        chats = chats_query.offset(offset).limit(limit).all()

        result = []
        for chat in chats:
            # Получаем последнее сообщение
            last_comm = db.query(Communication).filter(
                Communication.extra_data.contains({"chat_id": chat.chat_id})
            ).order_by(Communication.created_at.desc()).first()

            result.append({
                "chat_id": chat.chat_id,
                "customer_name": chat.customer.name if chat.customer else None,
                "customer_email": chat.customer.email if chat.customer else None,
                "last_message": last_comm.message_content[:100] if last_comm else None,
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "message_count": chat.message_count,
                "ai_enabled": chat.ai_enabled,
                "unread_count": 0  # TODO: Реализовать подсчет непрочитанных
            })

        return result

    except Exception as e:
        logger.error(f"Ошибка получения списка чатов: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/messenger/chats/{chat_id}/settings", response_model=AvitoChatSettings)
async def get_chat_settings(chat_id: str, db: Session = Depends(get_db)):
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
            "ai_model": settings.ai_model,
            "ai_temperature": settings.ai_temperature,
            "notifications_enabled": settings.notifications_enabled,
            "message_count": settings.message_count,
            "last_message_at": settings.last_message_at.isoformat() if settings.last_message_at else None,
            "last_ai_response_at": settings.last_ai_response_at.isoformat() if settings.last_ai_response_at else None,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения настроек чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/messenger/chats/{chat_id}/settings", response_model=AvitoChatSettings)
async def update_chat_settings(chat_id: str, settings: AvitoChatSettingsUpdate, db: Session = Depends(get_db)):
    """
    Обновление настроек чата
    """
    try:
        handler = AvitoCommunicationHandler(db)
        updated_settings = await handler.update_chat_settings(chat_id, settings.dict(exclude_unset=True))

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
            "last_message_at": updated_settings.last_message_at.isoformat() if updated_settings.last_message_at else None,
            "last_ai_response_at": updated_settings.last_ai_response_at.isoformat() if updated_settings.last_ai_response_at else None,
            "created_at": updated_settings.created_at.isoformat(),
            "updated_at": updated_settings.updated_at.isoformat()
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


@router.get("/messenger/chats/{chat_id}/messages", response_model=List[AvitoChatMessage])
async def get_chat_messages(chat_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """
    Получение истории сообщений чата
    """
    try:
        from ...models.communication import Communication

        messages = db.query(Communication).filter(
            Communication.channel == "avito",
            Communication.extra_data.contains({"chat_id": chat_id})
        ).order_by(Communication.created_at.desc()).offset(offset).limit(limit).all()

        result = []
        for msg in messages:
            result.append({
                "id": msg.id,
                "chat_id": chat_id,
                "direction": msg.direction,
                "message_content": msg.message_content,
                "intent": msg.intent,
                "ai_generated": msg.extra_data.get("ai_generated", False) if msg.extra_data else False,
                "created_at": msg.created_at.isoformat()
            })

        return result

    except Exception as e:
        logger.error(f"Ошибка получения сообщений чата {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/messenger/chats/{chat_id}/messages")
async def send_message(chat_id: str, request: AvitoSendMessageRequest, db: Session = Depends(get_db)):
    """
    Отправка сообщения в чат
    """
    try:
        handler = AvitoCommunicationHandler(db)

        if request.use_ai:
            # Используем AI для генерации ответа
            # Это можно реализовать через AI сервис
            logger.info(f"Генерация AI ответа для чата {chat_id}")
            # TODO: Реализовать генерацию AI ответа
            response_text = f"AI ответ на: {request.message[:50]}..."
        else:
            response_text = request.message

        # Отправка сообщения (пока что заглушка)
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
        active_chats = db.query(AvitoChatSettings).filter(
            AvitoChatSettings.last_message_at >= yesterday
        ).count()

        # Чаты с включенным AI
        ai_enabled_chats = db.query(AvitoChatSettings).filter(
            AvitoChatSettings.ai_enabled == True
        ).count()

        # Общее количество сообщений
        total_messages = db.query(Communication).filter(
            Communication.channel == "avito"
        ).count()

        # Сообщений от AI
        ai_messages = db.query(Communication).filter(
            Communication.channel == "avito",
            Communication.extra_data.contains({"ai_generated": True})
        ).count()

        # Среднее время ответа (заглушка)
        avg_response_time = None  # TODO: Реализовать расчет среднего времени ответа

        return {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "ai_enabled_chats": ai_enabled_chats,
            "total_messages": total_messages,
            "ai_messages": ai_messages,
            "avg_response_time": avg_response_time
        }

    except Exception as e:
        logger.error(f"Ошибка получения статистики мессенджера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
