"""
API роутер для интеграции с Avito
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload

from ...core.database import get_db
from ...services.avito_service import AvitoService, AvitoAPIError, AvitoRateLimitError, AvitoAuthError
from ...services.avito_handler import AvitoCommunicationHandler
from ...services.avito_background_tasks import avito_background_tasks
from ...services.automation.avito_integration import AvitoIntegrationService
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
    AvitoMessengerStats,
    # Webhook schemas
    AvitoWebhookRequest,
    AvitoWebhookResponse,
    AvitoWebhookMessagePayload,
    AvitoWebhookStatusPayload,
    # Global settings schemas
    AvitoGlobalSettings,
    AvitoGlobalSettingsCreate,
    AvitoGlobalSettingsUpdate,
    AvitoTestConnectionResponse,
    AvitoTestWebhookResponse
)
from ...utils.logging import get_logger, get_messenger_logger

logger = get_logger(__name__)
messenger_logger = get_messenger_logger()

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


@router.post("/webhook", response_model=AvitoWebhookResponse)
async def handle_avito_webhook(
    webhook_data: AvitoWebhookRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
        integration_service = AvitoIntegrationService(db)

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
                author_role = payload.get("author_role")

                if not chat_id or not user_id or not text:
                    logger.error(f"Недостаточно данных для обработки сообщения: {payload}")
                    continue

                # Преобразуем в формат для существующего обработчика
                message_data = {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message": {
                        "text": text,
                        "timestamp": timestamp
                    },
                    "item_id": item_id
                }

                result = await handler.handle_incoming_message(message_data)
                if result.get("success", False):
                    processed_events += 1
                    logger.info(f"Сообщение {message_id} обработано успешно")

                    # Запускаем автоматизацию для нового сообщения
                    automation_result = await integration_service.handle_message_received(
                        chat_id=chat_id,
                        message_data={
                            "message_id": message_id,
                            "text": text,
                            "timestamp": timestamp,
                            "user_id": user_id,
                            "item_id": item_id,
                            "author_role": author_role
                        }
                    )
                    logger.info(f"Автоматизация для сообщения {message_id}: {automation_result}")
                else:
                    logger.error(f"Ошибка обработки сообщения {message_id}: {result.get('error')}")

            elif event_type == "status_change":
                # Обработка изменения статуса чата
                chat_id = payload.get("chat_id")
                status = payload.get("status")
                timestamp = payload.get("timestamp")

                if not chat_id or not status:
                    logger.error(f"Недостаточно данных для изменения статуса: {payload}")
                    continue

                # Обновляем статус чата в настройках
                success = await handler.update_chat_status(chat_id, status)
                if success:
                    processed_events += 1
                    logger.info(f"Статус чата {chat_id} обновлен на {status}")

                    # Запускаем автоматизацию для изменения статуса чата
                    if status == "closed":
                        automation_result = await integration_service.handle_chat_closed(
                            chat_id=chat_id,
                            close_data={
                                "status": status,
                                "timestamp": timestamp
                            }
                        )
                        logger.info(f"Автоматизация для закрытия чата {chat_id}: {automation_result}")
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

                # Запускаем автоматизацию для создания чата
                automation_result = await integration_service.handle_chat_created(
                    chat_id=chat_id,
                    chat_data={
                        "user_id": user_id,
                        "item_id": item_id,
                        "timestamp": timestamp
                    }
                )
                processed_events += 1
                logger.info(f"Автоматизация для создания чата {chat_id}: {automation_result}")

            else:
                # Неизвестный тип события - логируем для отладки
                logger.warning(f"Неизвестный тип webhook события: {event_type}")
                processed_events += 1  # Считаем как обработанное

        return {
            "status": "ok",
            "processed_events": processed_events
        }

    except Exception as e:
        logger.error(f"Ошибка обработки webhook от Avito: {e}")
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





async def _count_unread_messages(chat_id: str, db: Session) -> int:
    """Подсчет количества непрочитанных сообщений в чате"""
    try:
        from ...models.communication import Communication

        # Считаем входящие сообщения, которые не отмечены как прочитанные
        unread_count = db.query(Communication).filter(
            Communication.channel == "avito",
            Communication.extra_data.contains({"chat_id": chat_id}),
            Communication.direction == "inbound",
            ~Communication.extra_data.contains({"read": True})  # Не отмечены как прочитанные
        ).count()

        return unread_count

    except Exception as e:
        logger.error(f"Ошибка подсчета непрочитанных сообщений для чата {chat_id}: {e}")
        return 0


async def _calculate_average_response_time(db: Session) -> Optional[float]:
    """Расчет среднего времени ответа на сообщения (оптимизированная версия)"""
    try:
        from ...models.communication import Communication
        from sqlalchemy import func, text
        from sqlalchemy.orm import aliased

        # Оптимизированный SQL запрос для расчета среднего времени ответа
        # Используем оконные функции для поиска пар входящее->исходящее сообщение

        # Создаем подзапрос для получения всех avito сообщений с chat_id
        avito_messages = db.query(
            Communication.id,
            Communication.created_at,
            Communication.direction,
            func.json_extract_path_text(Communication.extra_data, 'chat_id').label('chat_id')
        ).filter(
            Communication.channel == "avito",
            Communication.extra_data.isnot(None),
            text("extra_data::jsonb ? 'chat_id'")
        ).subquery()

        # Алиасы для удобства
        msg1 = aliased(avito_messages)
        msg2 = aliased(avito_messages)

        # Находим пары: входящее сообщение и следующее исходящее в том же чате
        response_times_query = db.query(
            func.avg(
                func.extract('epoch', msg2.c.created_at - msg1.c.created_at)
            ).label('avg_response_seconds')
        ).select_from(
            msg1.join(
                msg2,
                (msg1.c.chat_id == msg2.c.chat_id) &
                (msg1.c.direction == "inbound") &
                (msg2.c.direction == "outbound") &
                (msg1.c.created_at < msg2.c.created_at)
            )
        ).filter(
            # Исключаем пары, где между входящим и исходящим есть другое входящее
            ~db.query(msg1).filter(
                msg1.c.chat_id == msg1.c.chat_id,
                msg1.c.direction == "inbound",
                msg1.c.created_at > msg1.c.created_at,
                msg1.c.created_at < msg2.c.created_at
            ).exists()
        ).filter(
            # Ограничиваем время ответа 24 часами
            func.extract('epoch', msg2.c.created_at - msg1.c.created_at) < 86400,
            func.extract('epoch', msg2.c.created_at - msg1.c.created_at) > 0
        )

        result = response_times_query.scalar()

        if result:
            # Возвращаем среднее время в минутах
            return result / 60

        return None

    except Exception as e:
        logger.error(f"Ошибка расчета среднего времени ответа: {e}")
        # Fallback на старую версию при ошибке SQL
        try:
            # Получаем все сообщения, отсортированные по времени
            messages = db.query(Communication).filter(
                Communication.channel == "avito"
            ).order_by(Communication.created_at).all()

            response_times = []

            # Группируем сообщения по чату
            chat_messages = {}
            for msg in messages:
                chat_id = msg.extra_data.get("chat_id") if msg.extra_data else None
                if chat_id:
                    if chat_id not in chat_messages:
                        chat_messages[chat_id] = []
                    chat_messages[chat_id].append(msg)

            # Для каждого чата рассчитываем время ответа
            for chat_id, msgs in chat_messages.items():
                # Сортируем сообщения чата по времени
                msgs.sort(key=lambda x: x.created_at)

                # Ищем пары: входящее -> исходящее
                i = 0
                while i < len(msgs) - 1:
                    if msgs[i].direction == "inbound":
                        # Ищем следующее исходящее сообщение
                        for j in range(i + 1, len(msgs)):
                            if msgs[j].direction == "outbound":
                                # Рассчитываем время ответа в секундах
                                response_time = (msgs[j].created_at - msgs[i].created_at).total_seconds()
                                if response_time > 0 and response_time < 86400:  # Менее 24 часов
                                    response_times.append(response_time)
                                break
                        i = j  # Пропускаем до следующего входящего
                    else:
                        i += 1

            if response_times:
                # Возвращаем среднее время в минутах
                return sum(response_times) / len(response_times) / 60

            return None
        except Exception as fallback_error:
            logger.error(f"Ошибка fallback расчета среднего времени ответа: {fallback_error}")
            return None


# Messenger endpoints

@router.get("/messenger/v1/accounts/{user_id}/chats", response_model=List[AvitoChatInfo])
async def get_chats(user_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """
    Получение списка чатов с Avito
    """
    try:
        messenger_logger.info(
            "Получение списка чатов",
            user_id=user_id,
            limit=limit,
            offset=offset,
            operation="get_chats"
        )

        from ...models.avito_chat import AvitoChatSettings
        from ...models.customer import Customer
        from ...models.communication import Communication

        # Оптимизированный запрос: получаем чаты с последними сообщениями
        # Используем простой и надежный подход - кэшируем последние сообщения в настройках чата
        chats = db.query(AvitoChatSettings).options(
            joinedload(AvitoChatSettings.customer)
        ).order_by(AvitoChatSettings.last_message_at.desc().nulls_last()).offset(offset).limit(limit).all()

        # Создаем словарь последних сообщений из кэшированных данных в настройках чата
        # Это самый эффективный подход - данные уже кэшированы при получении сообщений
        last_messages_dict = {}
        for chat in chats:
            # Используем кэшированное последнее сообщение из extra_data чата
            if chat.extra_data and 'last_message_preview' in chat.extra_data:
                last_messages_dict[chat.chat_id] = chat.extra_data['last_message_preview'][:100]
            else:
                # Fallback: если нет кэшированного сообщения, оставляем пустым
                last_messages_dict[chat.chat_id] = None

        messenger_logger.info(
            "Список чатов получен (оптимизированный запрос)",
            user_id=user_id,
            chats_count=len(chats),
            operation="get_chats"
        )

        result = []
        for chat in chats:
            result.append({
                "chat_id": chat.chat_id,
                "customer_name": chat.customer.name if chat.customer else None,
                "customer_email": chat.customer.email if chat.customer else None,
                "last_message": last_messages_dict.get(chat.chat_id),
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "message_count": chat.message_count,
                "ai_enabled": chat.ai_enabled,
                "unread_count": chat.unread_count
            })

        return result

    except Exception as e:
        logger.error(f"Ошибка получения списка чатов: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/messenger/v1/accounts/{user_id}/chats/{chat_id}", response_model=AvitoChatSettings)
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


@router.put("/messenger/v1/accounts/{user_id}/chats/{chat_id}", response_model=AvitoChatSettings)
async def update_chat_settings(user_id: int, chat_id: str, settings: AvitoChatSettingsUpdate, db: Session = Depends(get_db)):
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


@router.get("/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages", response_model=List[AvitoChatMessage])
async def get_chat_messages(user_id: int, chat_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
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


@router.post("/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages")
async def send_message(user_id: int, chat_id: str, request: AvitoSendMessageRequest, db: Session = Depends(get_db)):
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
            operation="send_message"
        )

        handler = AvitoCommunicationHandler(db)

        if request.use_ai:
            # Используем AI для генерации ответа
            messenger_logger.info(
                "Генерация AI ответа для чата",
                chat_id=chat_id,
                operation="send_message"
            )

            # Получаем историю чата для контекста
            chat_history = await handler.get_chat_history(chat_id, limit=10)

            # Получаем настройки чата для параметров AI
            chat_settings = await handler.get_chat_settings(chat_id)
            ai_model = chat_settings.ai_model if chat_settings else None
            ai_temperature = chat_settings.ai_temperature if chat_settings else 0.7

            # Генерируем AI ответ
            from ...services.ai.intent_service import AIIntentService
            ai_service = AIIntentService()

            # Получаем контекст клиента
            customer_context = {}
            if chat_settings and chat_settings.customer_id:
                from ...models.customer import Customer
                customer = db.query(Customer).filter(Customer.id == chat_settings.customer_id).first()
                if customer:
                    customer_context = {
                        "customer_name": customer.name,
                        "order_count": customer.total_orders,
                        "preferences": customer.preferences or {}
                    }

            # Генерируем ответ на основе истории и контекста
            ai_result = await ai_service.process_customer_message(
                request.message,
                customer_context
            )
            response_text = ai_result["response"]

            # Помечаем как AI-generated
            ai_generated = True
        else:
            response_text = request.message
            ai_generated = False

        # Отправка сообщения через Avito Messenger API (реализовано)
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

        # Расчет среднего времени ответа
        avg_response_time = await _calculate_average_response_time(db)

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


# Background Tasks endpoints

@router.post("/background/sync-chats")
async def start_sync_chats_background(
    chat_ids: List[str],
    background_tasks: BackgroundTasks,
    limit_per_chat: int = 100
):
    """
    Запуск background синхронизации истории чатов

    Args:
        chat_ids: Список ID чатов для синхронизации
        limit_per_chat: Максимальное количество сообщений на чат
    """
    try:
        # Запускаем задачу в фоне
        background_tasks.add_task(
            avito_background_tasks.sync_chats_history_background,
            chat_ids=chat_ids,
            limit_per_chat=limit_per_chat
        )

        return {
            "message": f"Запущена синхронизация {len(chat_ids)} чатов",
            "chat_ids": chat_ids,
            "status": "started"
        }

    except Exception as e:
        logger.error(f"Ошибка запуска background синхронизации чатов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска задачи")


@router.post("/background/bulk-send")
async def start_bulk_send_background(
    messages: List[dict],
    background_tasks: BackgroundTasks,
    delay_between_messages: float = 1.0
):
    """
    Запуск background массовой отправки сообщений

    Args:
        messages: Список сообщений [{"chat_id": str, "message": str, "use_ai": bool}]
        delay_between_messages: Задержка между сообщениями в секундах
    """
    try:
        # Валидация входных данных
        for i, msg in enumerate(messages):
            if not msg.get("chat_id") or not msg.get("message"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный формат сообщения {i}: требуется chat_id и message"
                )

        # Запускаем задачу в фоне
        background_tasks.add_task(
            avito_background_tasks.bulk_send_messages_background,
            messages=messages,
            delay_between_messages=delay_between_messages
        )

        return {
            "message": f"Запущена отправка {len(messages)} сообщений",
            "total_messages": len(messages),
            "status": "started"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка запуска background отправки сообщений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска задачи")


@router.post("/background/update-performance")
async def start_update_performance_background(
    item_ids: List[int],
    background_tasks: BackgroundTasks,
    days: int = 30
):
    """
    Запуск background обновления производительности объявлений

    Args:
        item_ids: Список ID объявлений
        days: Период анализа в днях
    """
    try:
        # Запускаем задачу в фоне
        background_tasks.add_task(
            avito_background_tasks.update_items_performance_background,
            item_ids=item_ids,
            days=days
        )

        return {
            "message": f"Запущено обновление производительности {len(item_ids)} объявлений",
            "item_ids": item_ids,
            "days": days,
            "status": "started"
        }

    except Exception as e:
        logger.error(f"Ошибка запуска background обновления производительности: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска задачи")


@router.post("/background/cleanup")
async def start_cleanup_background(
    background_tasks: BackgroundTasks,
    days_to_keep: int = 90
):
    """
    Запуск background очистки старых данных

    Args:
        days_to_keep: Количество дней для хранения данных
    """
    try:
        # Запускаем задачу в фоне
        background_tasks.add_task(
            avito_background_tasks.cleanup_old_data_background,
            days_to_keep=days_to_keep
        )

        return {
            "message": f"Запущена очистка данных старше {days_to_keep} дней",
            "days_to_keep": days_to_keep,
            "status": "started"
        }

    except Exception as e:
        logger.error(f"Ошибка запуска background очистки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска задачи")


@router.post("/background/health-check")
async def start_health_check_background(background_tasks: BackgroundTasks):
    """
    Запуск background проверки здоровья Avito интеграции
    """
    try:
        # Запускаем задачу в фоне
        background_tasks.add_task(avito_background_tasks.health_check_background)

        return {
            "message": "Запущена проверка здоровья Avito интеграции",
            "status": "started"
        }

    except Exception as e:
        logger.error(f"Ошибка запуска background проверки здоровья: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска задачи")


@router.get("/background/tasks")
async def get_running_tasks():
    """
    Получение списка выполняющихся background задач
    """
    try:
        running_tasks = avito_background_tasks.get_running_tasks()
        return {
            "running_tasks": running_tasks,
            "count": len(running_tasks)
        }

    except Exception as e:
        logger.error(f"Ошибка получения списка задач: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@router.get("/background/tasks/{task_id}")
async def check_task_status(task_id: str):
    """
    Проверка статуса background задачи
    """
    try:
        is_running = avito_background_tasks.is_task_running(task_id)
        return {
            "task_id": task_id,
            "is_running": is_running,
            "status": "running" if is_running else "completed_or_not_found"
        }

    except Exception as e:
        logger.error(f"Ошибка проверки статуса задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка проверки статуса")


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
            "token_expires_at": settings.token_expires_at.isoformat() if settings.token_expires_at else None,
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
            "last_sync_at": settings.last_sync_at.isoformat() if settings.last_sync_at else None,
            "last_error": settings.last_error,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Ошибка получения глобальных настроек Avito: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/settings", response_model=AvitoGlobalSettings)
async def update_global_settings(settings: AvitoGlobalSettingsUpdate, db: Session = Depends(get_db)):
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
            "token_expires_at": existing_settings.token_expires_at.isoformat() if existing_settings.token_expires_at else None,
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
            "last_sync_at": existing_settings.last_sync_at.isoformat() if existing_settings.last_sync_at else None,
            "last_error": existing_settings.last_error,
            "created_at": existing_settings.created_at.isoformat(),
            "updated_at": existing_settings.updated_at.isoformat()
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
        from ...models.avito_chat import AvitoGlobalSettings

        settings = db.query(AvitoGlobalSettings).first()
        if not settings or not settings.client_id or not settings.client_secret:
            return {
                "success": False,
                "message": "Не настроены учетные данные Avito (Client ID и Client Secret)"
            }

        # Здесь должна быть логика тестирования подключения
        # Avito API интеграция не реализована
        return {
            "success": False,
            "message": "Интеграция с Avito API временно недоступна. Функциональность будет добавлена в следующих обновлениях."
        }

    except Exception as e:
        logger.error(f"Ошибка тестирования подключения к Avito: {e}")
        return {
            "success": False,
            "message": f"Ошибка при тестировании подключения: {str(e)}"
        }


@router.post("/settings/test-webhook", response_model=AvitoTestWebhookResponse)
async def test_webhook(db: Session = Depends(get_db)):
    """
    Тестирование webhook
    """
    try:
        from ...models.avito_chat import AvitoGlobalSettings

        settings = db.query(AvitoGlobalSettings).first()
        if not settings or not settings.webhook_url:
            return {
                "success": False,
                "message": "Не настроен URL webhook"
            }

        # Здесь должна быть логика тестирования webhook
        # Webhook интеграция не реализована
        return {
            "success": False,
            "message": "Webhook интеграция временно недоступна. Функциональность будет добавлена в следующих обновлениях."
        }

    except Exception as e:
        logger.error(f"Ошибка тестирования webhook: {e}")
        return {
            "success": False,
            "message": f"Ошибка при тестировании webhook: {str(e)}"
        }
