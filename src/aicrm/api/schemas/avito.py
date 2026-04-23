"""
Pydantic схемы для Avito API
"""
from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, validator
from enum import Enum


class AvitoItemStatus(str, Enum):
    """Статус объявления Avito"""
    ACTIVE = "active"
    REMOVED = "removed"
    OLD = "old"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"
    ANOTHER_USER = "another_user"


class AvitoVasInfo(BaseModel):
    """Информация о примененной услуге VAS"""
    vas_id: str = Field(..., description="Идентификатор услуги")
    finish_time: Optional[str] = Field(None, description="Дата завершения услуги")
    schedule: Optional[List[str]] = Field(None, description="Информация о следующих применениях")


class AvitoItemInfo(BaseModel):
    """Информация об объявлении Avito"""
    autoload_item_id: Optional[str] = Field(None, description="ID из файла автозагрузки")
    finish_time: Optional[str] = Field(None, description="Дата завершения объявления")
    start_time: Optional[str] = Field(None, description="Дата создания объявления")
    status: AvitoItemStatus = Field(..., description="Статус объявления")
    url: Optional[str] = Field(None, description="URL объявления")
    vas: Optional[List[AvitoVasInfo]] = Field(None, description="Примененные услуги")


class AvitoItem(BaseModel):
    """Объявление Avito"""
    id: int = Field(..., description="Идентификатор объявления")
    title: str = Field(..., description="Наименование объявления")
    address: Optional[str] = Field(None, description="Адрес объявления")
    category: Dict[str, Any] = Field(..., description="Категория объявления")
    price: Optional[int] = Field(None, description="Цена объявления")
    status: AvitoItemStatus = Field(..., description="Статус объявления")
    url: Optional[str] = Field(None, description="URL объявления")


class AvitoStatsRequest(BaseModel):
    """Запрос статистики объявлений"""
    item_ids: List[int] = Field(..., description="Идентификаторы объявлений")
    date_from: date = Field(..., description="Дата начала периода")
    date_to: date = Field(..., description="Дата окончания периода")
    fields: Optional[List[str]] = Field(
        ["uniqViews", "uniqContacts", "uniqFavorites"],
        description="Поля статистики"
    )
    period_grouping: Optional[str] = Field("day", description="Группировка по периодам")

    @validator('fields')
    def validate_fields(cls, v):
        allowed_fields = ["views", "uniqViews", "contacts", "uniqContacts", "favorites", "uniqFavorites"]
        if not all(field in allowed_fields for field in v):
            raise ValueError(f"Поля должны быть из списка: {allowed_fields}")
        return v

    @validator('period_grouping')
    def validate_period_grouping(cls, v):
        allowed_groupings = ["day", "week", "month"]
        if v not in allowed_groupings:
            raise ValueError(f"Группировка должна быть из списка: {allowed_groupings}")
        return v


class AvitoStatsDay(BaseModel):
    """Статистика за день"""
    date: str = Field(..., description="Дата (YYYY-MM-DD)")
    uniqViews: Optional[int] = Field(None, description="Уникальные просмотры")
    uniqContacts: Optional[int] = Field(None, description="Уникальные контакты")
    uniqFavorites: Optional[int] = Field(None, description="Уникальные добавления в избранное")
    views: Optional[int] = Field(None, description="Все просмотры (deprecated)")
    contacts: Optional[int] = Field(None, description="Все контакты (deprecated)")
    favorites: Optional[int] = Field(None, description="Все добавления в избранное (deprecated)")


class AvitoItemStats(BaseModel):
    """Статистика объявления"""
    itemId: int = Field(..., description="Идентификатор объявления")
    stats: List[AvitoStatsDay] = Field(..., description="Статистика по дням")


class AvitoStatsResponse(BaseModel):
    """Ответ со статистикой"""
    result: Dict[str, Any] = Field(..., description="Результаты статистики")


class AvitoAnalyticsRequest(BaseModel):
    """Запрос аналитики"""
    date_from: date = Field(..., description="Дата начала периода")
    date_to: date = Field(..., description="Дата окончания периода")
    metrics: List[str] = Field(..., description="Метрики для анализа")
    grouping: Optional[str] = Field("item", description="Группировка данных")
    limit: Optional[int] = Field(1000, description="Лимит результатов")
    offset: Optional[int] = Field(0, description="Смещение")
    filter: Optional[Dict[str, Any]] = Field(None, description="Фильтры")

    @validator('grouping')
    def validate_grouping(cls, v):
        allowed_groupings = ["totals", "item", "day", "week", "month"]
        if v not in allowed_groupings:
            raise ValueError(f"Группировка должна быть из списка: {allowed_groupings}")
        return v


class AvitoAnalyticsResponse(BaseModel):
    """Ответ аналитики"""
    result: Dict[str, Any] = Field(..., description="Результаты аналитики")


class AvitoVasPrice(BaseModel):
    """Цена услуги VAS"""
    slug: str = Field(..., description="Идентификатор услуги")
    price: int = Field(..., description="Цена со скидкой")
    priceOld: Optional[int] = Field(None, description="Цена без скидки")


class AvitoSticker(BaseModel):
    """Информация о стикере"""
    id: int = Field(..., description="Идентификатор стикера")
    title: str = Field(..., description="Название стикера")
    description: str = Field(..., description="Описание стикера")


class AvitoItemVasPrices(BaseModel):
    """Цены VAS для объявления"""
    itemId: int = Field(..., description="Идентификатор объявления")
    vas: List[AvitoVasPrice] = Field(..., description="Услуги VAS")
    stickers: Optional[List[AvitoSticker]] = Field(None, description="Доступные стикеры")


class AvitoVasPricesResponse(BaseModel):
    """Ответ с ценами VAS"""
    prices: List[AvitoItemVasPrices] = Field(..., description="Цены для объявлений")


class AvitoApplyVasRequest(BaseModel):
    """Запрос на применение VAS"""
    slugs: List[str] = Field(..., description="Идентификаторы услуг")
    stickers: Optional[List[int]] = Field(None, description="Идентификаторы стикеров")


class AvitoApplyVasResponse(BaseModel):
    """Ответ на применение VAS"""
    operationId: int = Field(..., description="Идентификатор операции")


class AvitoUpdatePriceRequest(BaseModel):
    """Запрос на обновление цены"""
    price: int = Field(..., gt=0, description="Новая цена в рублях")


class AvitoUpdatePriceResponse(BaseModel):
    """Ответ на обновление цены"""
    result: Dict[str, bool] = Field(..., description="Результат операции")


class AvitoCallsStatsRequest(BaseModel):
    """Запрос статистики звонков"""
    date_from: date = Field(..., description="Дата начала периода")
    date_to: date = Field(..., description="Дата окончания периода")
    item_ids: Optional[List[int]] = Field(None, description="Идентификаторы объявлений")


class AvitoCallsStatsDay(BaseModel):
    """Статистика звонков за день"""
    date: str = Field(..., description="Дата (YYYY-MM-DD)")
    answered: int = Field(..., description="Отвеченные звонки")
    calls: int = Field(..., description="Все звонки")
    new: int = Field(..., description="Новые звонки")
    newAnswered: int = Field(..., description="Новые отвеченные звонки")


class AvitoCallsStatsItem(BaseModel):
    """Статистика звонков по объявлению"""
    employeeId: int = Field(..., description="ID сотрудника")
    itemId: int = Field(..., description="ID объявления")
    days: List[AvitoCallsStatsDay] = Field(..., description="Статистика по дням")


class AvitoCallsStatsResponse(BaseModel):
    """Ответ со статистикой звонков"""
    result: Dict[str, List[AvitoCallsStatsItem]] = Field(..., description="Результаты статистики")


# Схемы для бизнес-логики

class AvitoItemPerformance(BaseModel):
    """Производительность объявления"""
    item_id: int = Field(..., description="Идентификатор объявления")
    title: Optional[str] = Field(None, description="Название объявления")
    status: AvitoItemStatus = Field(..., description="Статус объявления")
    url: Optional[str] = Field(None, description="URL объявления")
    stats: Dict[str, Any] = Field(..., description="Статистика просмотров")
    calls: Dict[str, Any] = Field(..., description="Статистика звонков")
    vas_active: List[AvitoVasInfo] = Field(default_factory=list, description="Активные VAS")


class AvitoPricingRecommendation(BaseModel):
    """Рекомендация по ценообразованию"""
    item_id: int = Field(..., description="Идентификатор объявления")
    current_conversion: float = Field(..., description="Текущая конверсия")
    total_views: int = Field(..., description="Общее количество просмотров")
    total_contacts: int = Field(..., description="Общее количество контактов")
    recommendation: str = Field(..., description="Рекомендация")


class AvitoPromotionRequest(BaseModel):
    """Запрос на применение продвижения"""
    item_id: int = Field(..., description="Идентификатор объявления")
    service_slug: str = Field(..., description="Идентификатор услуги")
    stickers: Optional[List[int]] = Field(None, description="Идентификаторы стикеров")


class AvitoPromotionResponse(BaseModel):
    """Ответ на применение продвижения"""
    operation_id: int = Field(..., description="Идентификатор операции")
    service_slug: str = Field(..., description="Идентификатор услуги")
    status: str = Field(..., description="Статус операции")


# Схемы ошибок

class AvitoErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: Dict[str, Any] = Field(..., description="Информация об ошибке")


class AvitoValidationError(BaseModel):
    """Ошибка валидации"""
    code: int = Field(..., description="Код ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    fields: Optional[Dict[str, Any]] = Field(None, description="Ошибки полей")


# Схемы для мессенджера

class AvitoChatSettingsBase(BaseModel):
    """Базовая схема настроек чата"""
    ai_enabled: bool = Field(True, description="Включены ли AI ответы")
    ai_model: str = Field("deepseek/deepseek-coder:33b-instruct", description="Модель AI")
    ai_temperature: int = Field(70, ge=0, le=100, description="Температура AI (0-100)")
    notifications_enabled: bool = Field(True, description="Включены ли уведомления")


class AvitoChatSettingsCreate(AvitoChatSettingsBase):
    """Создание настроек чата"""
    chat_id: str = Field(..., description="ID чата в Avito")


class AvitoChatSettingsUpdate(BaseModel):
    """Обновление настроек чата"""
    ai_enabled: Optional[bool] = Field(None, description="Включены ли AI ответы")
    ai_model: Optional[str] = Field(None, description="Модель AI")
    ai_temperature: Optional[int] = Field(None, ge=0, le=100, description="Температура AI (0-100)")
    notifications_enabled: Optional[bool] = Field(None, description="Включены ли уведомления")


class AvitoChatSettings(AvitoChatSettingsBase):
    """Настройки чата с метаданными"""
    id: int = Field(..., description="ID настройки")
    chat_id: str = Field(..., description="ID чата в Avito")
    customer_id: Optional[int] = Field(None, description="ID клиента")
    message_count: int = Field(..., description="Количество сообщений")
    last_message_at: Optional[str] = Field(None, description="Время последнего сообщения")
    last_ai_response_at: Optional[str] = Field(None, description="Время последнего AI ответа")
    created_at: str = Field(..., description="Время создания")
    updated_at: str = Field(..., description="Время обновления")


class AvitoChatMessage(BaseModel):
    """Сообщение в чате"""
    id: int = Field(..., description="ID сообщения")
    chat_id: str = Field(..., description="ID чата")
    direction: str = Field(..., description="Направление (inbound/outbound)")
    message_content: str = Field(..., description="Текст сообщения")
    intent: Optional[str] = Field(None, description="Определенный намерение")
    ai_generated: bool = Field(False, description="Сгенерировано ли AI")
    created_at: str = Field(..., description="Время создания")


class AvitoChatInfo(BaseModel):
    """Информация о чате"""
    chat_id: str = Field(..., description="ID чата")
    customer_name: Optional[str] = Field(None, description="Имя клиента")
    customer_email: Optional[str] = Field(None, description="Email клиента")
    last_message: Optional[str] = Field(None, description="Последнее сообщение")
    last_message_at: Optional[str] = Field(None, description="Время последнего сообщения")
    message_count: int = Field(..., description="Количество сообщений")
    ai_enabled: bool = Field(True, description="AI включен")
    unread_count: int = Field(0, description="Количество непрочитанных")


class AvitoSendMessageRequest(BaseModel):
    """Запрос на отправку сообщения"""
    message: str = Field(..., min_length=1, max_length=1000, description="Текст сообщения")
    use_ai: bool = Field(False, description="Использовать AI для генерации ответа")


class AvitoMessengerStats(BaseModel):
    """Статистика мессенджера"""
    total_chats: int = Field(..., description="Общее количество чатов")
    active_chats: int = Field(..., description="Активные чаты")
    ai_enabled_chats: int = Field(..., description="Чаты с включенным AI")
    total_messages: int = Field(..., description="Общее количество сообщений")
    ai_messages: int = Field(..., description="Сообщений от AI")
    avg_response_time: Optional[float] = Field(None, description="Среднее время ответа (секунды)")

# Схемы для Messenger API

class AvitoChat(BaseModel):
    """Чат из Avito API"""
    id: str = Field(..., description="ID чата")
    user_id: str = Field(..., description="ID пользователя")
    item_id: Optional[int] = Field(None, description="ID объявления")
    created: str = Field(..., description="Время создания")
    updated: str = Field(..., description="Время обновления")
    unread_count: int = Field(0, description="Количество непрочитанных сообщений")
    last_message: Optional[Dict[str, Any]] = Field(None, description="Последнее сообщение")

class AvitoMessage(BaseModel):
    """Сообщение из Avito API"""
    id: str = Field(..., description="ID сообщения")
    type: str = Field(..., description="Тип сообщения")
    text: Optional[str] = Field(None, description="Текст сообщения")
    created: str = Field(..., description="Время создания")
    author_id: str = Field(..., description="ID автора")
    author_role: str = Field(..., description="Роль автора")

class AvitoChatsResponse(BaseModel):
    """Ответ со списком чатов"""
    chats: List[AvitoChat] = Field(..., description="Список чатов")
    total: int = Field(..., description="Общее количество чатов")
    limit: int = Field(..., description="Лимит")
    offset: int = Field(..., description="Смещение")

class AvitoMessagesResponse(BaseModel):
    """Ответ со списком сообщений"""
    messages: List[AvitoMessage] = Field(..., description="Список сообщений")
    total: int = Field(..., description="Общее количество сообщений")
    limit: int = Field(..., description="Лимит")
    offset: int = Field(..., description="Смещение")

class AvitoSendMessageRequest(BaseModel):
    """Запрос на отправку сообщения в Avito"""
    message: str = Field(..., min_length=1, max_length=1000, description="Текст сообщения")

class AvitoSendMessageResponse(BaseModel):
    """Ответ на отправку сообщения"""
    message_id: str = Field(..., description="ID отправленного сообщения")
    success: bool = Field(True, description="Успешность операции")

class AvitoWebhookSubscribeRequest(BaseModel):
    """Запрос на подписку webhook"""
    url: str = Field(..., description="URL для webhook уведомлений")
    events: List[str] = Field(["message"], description="События для подписки")

class AvitoWebhookUnsubscribeRequest(BaseModel):
    """Запрос на отписку webhook"""
    url: str = Field(..., description="URL для отписки")

class AvitoWebhookResponse(BaseModel):
    """Ответ webhook операций"""
    success: bool = Field(..., description="Успешность операции")
    webhook_id: Optional[str] = Field(None, description="ID webhook подписки")

class AvitoWebhookEvent(BaseModel):
    """Событие webhook от Avito"""
    event: str = Field(..., description="Тип события")
    timestamp: str = Field(..., description="Время события")
    payload: Dict[str, Any] = Field(..., description="Данные события")


class AvitoWebhookMessagePayload(BaseModel):
    """Payload для webhook события нового сообщения"""
    chat_id: str = Field(..., description="ID чата")
    message_id: str = Field(..., description="ID сообщения")
    user_id: str = Field(..., description="ID пользователя")
    item_id: Optional[int] = Field(None, description="ID объявления")
    text: str = Field(..., description="Текст сообщения")
    timestamp: str = Field(..., description="Время сообщения")
    author_role: str = Field(..., description="Роль автора (buyer/seller)")


class AvitoWebhookStatusPayload(BaseModel):
    """Payload для webhook события изменения статуса"""
    chat_id: str = Field(..., description="ID чата")
    status: str = Field(..., description="Новый статус чата")
    timestamp: str = Field(..., description="Время изменения")


class AvitoWebhookRequest(BaseModel):
    """Входящий webhook запрос от Avito"""
    events: List[AvitoWebhookEvent] = Field(..., description="Список событий")


class AvitoWebhookResponse(BaseModel):
    """Ответ на webhook запрос"""
    status: str = Field("ok", description="Статус обработки")
    processed_events: int = Field(..., description="Количество обработанных событий")

class AvitoSyncChatsRequest(BaseModel):
    """Запрос на синхронизацию чатов"""
    limit: int = Field(100, ge=1, le=1000, description="Лимит чатов для синхронизации")
    force_sync: bool = Field(False, description="Принудительная синхронизация")

class AvitoSyncChatsResponse(BaseModel):
    """Ответ на синхронизацию чатов"""
    synced_chats: int = Field(..., description="Количество синхронизированных чатов")
    created_chats: int = Field(..., description="Количество созданных чатов")
    total_chats: int = Field(..., description="Общее количество чатов в Avito")
    success: bool = Field(True, description="Успешность операции")
