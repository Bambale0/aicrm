"""
Схемы для коммуникаций
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class CommunicationBase(BaseModel):
    """Базовая схема коммуникации"""
    channel: str  # telegram, avito, email, phone, website
    direction: str  # inbound, outbound
    message_content: str
    message_type: Optional[str] = "text"  # text, image, file, voice
    customer_id: Optional[int] = None
    order_id: Optional[int] = None
    ai_response_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None  # positive, neutral, negative
    intent: Optional[str] = None  # order, complaint, question, etc.


class CommunicationCreate(CommunicationBase):
    """Схема создания коммуникации"""
    # Наследует все поля от CommunicationBase


class CommunicationUpdate(BaseModel):
    """Схема обновления коммуникации"""
    message_content: Optional[str] = None
    message_type: Optional[str] = None
    customer_id: Optional[int] = None
    order_id: Optional[int] = None
    ai_response_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None


class Communication(CommunicationBase):
    """Схема коммуникации для ответов"""
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Дополнительные поля для отображения
    customer_name: Optional[str] = None
    order_number: Optional[str] = None
    user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CommunicationSearch(BaseModel):
    """Схема для расширенного поиска коммуникаций"""
    query: Optional[str] = None
    channels: Optional[List[str]] = None
    directions: Optional[List[str]] = None
    sentiments: Optional[List[str]] = None
    customer_id: Optional[int] = None
    order_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = "date"  # date, channel, sentiment
    sort_order: Optional[str] = "desc"  # asc, desc
    skip: int = 0
    limit: int = 100


class CommunicationStats(BaseModel):
    """Статистика коммуникаций"""
    total_communications: int
    unique_customers: int
    average_message_length: float
    channels_breakdown: Dict[str, int]  # {telegram: 150, avito: 89, ...}
    sentiment_breakdown: Dict[str, int]  # {positive: 120, neutral: 89, negative: 30}


class CommunicationChannelStats(BaseModel):
    """Статистика по каналам коммуникаций"""
    channel: str
    total_messages: int
    inbound_messages: int
    outbound_messages: int
    unique_customers: int
    average_response_time: Optional[float] = None  # в минутах
    sentiment_distribution: Dict[str, int]


class CommunicationTimeline(BaseModel):
    """Хронология коммуникаций для клиента"""
    customer_id: int
    customer_name: str
    communications: List[Communication]
    total_count: int
    last_communication_date: Optional[datetime] = None
