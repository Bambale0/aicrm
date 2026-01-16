"""
Маршруты для управления коммуникациями
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_active_user, get_db
from ...models.communication import Communication
from ...models.customer import Customer
from ...models.order import Order
from ...models.user import User
from ..schemas.communication import Communication as CommunicationSchema
from ..schemas.communication import (
    CommunicationCreate,
    CommunicationSearch,
    CommunicationStats,
    CommunicationUpdate,
)

router = APIRouter(prefix="/communications", tags=["communications"])


@router.get("/ping")
async def ping():
    return "pong"


@router.get("/", response_model=List[CommunicationSchema])
async def get_communications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    order_id: Optional[int] = Query(None),
    direction: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение списка коммуникаций с фильтрами"""
    query = db.query(Communication)

    # Применяем фильтры
    if channel:
        query = query.filter(Communication.channel == channel)
    if customer_id:
        query = query.filter(Communication.customer_id == customer_id)
    if order_id:
        query = query.filter(Communication.order_id == order_id)
    if direction:
        query = query.filter(Communication.direction == direction)
    if sentiment:
        query = query.filter(Communication.sentiment == sentiment)

    # Поиск по содержимому сообщения
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Communication.message_content.ilike(search_filter),
                Communication.intent.ilike(search_filter),
            )
        )

    # Сортировка по дате создания (новые сверху)
    query = query.order_by(desc(Communication.created_at))

    communications = query.offset(skip).limit(limit).all()
    return communications


@router.get("/{communication_id}", response_model=CommunicationSchema)
async def get_communication(
    communication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение коммуникации по ID"""
    communication = (
        db.query(Communication).filter(Communication.id == communication_id).first()
    )
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")
    return communication


@router.post("/", response_model=CommunicationSchema)
async def create_communication(
    communication_data: CommunicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создание новой коммуникации"""
    # Проверяем существование связанных сущностей
    if communication_data.customer_id:
        customer = (
            db.query(Customer)
            .filter(Customer.id == communication_data.customer_id)
            .first()
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    if communication_data.order_id:
        order = db.query(Order).filter(Order.id == communication_data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    # Создаем коммуникацию
    communication = Communication(**communication_data.dict(), user_id=current_user.id)

    db.add(communication)
    db.commit()
    db.refresh(communication)

    return communication


@router.put("/{communication_id}", response_model=CommunicationSchema)
async def update_communication(
    communication_id: int,
    communication_data: CommunicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновление коммуникации"""
    communication = (
        db.query(Communication).filter(Communication.id == communication_id).first()
    )
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")

    # Обновляем поля
    for field, value in communication_data.dict(exclude_unset=True).items():
        setattr(communication, field, value)

    db.commit()
    db.refresh(communication)

    return communication


@router.delete("/{communication_id}")
async def delete_communication(
    communication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удаление коммуникации"""
    communication = (
        db.query(Communication).filter(Communication.id == communication_id).first()
    )
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")

    db.delete(communication)
    db.commit()

    return {"message": "Communication deleted successfully"}


@router.post("/search", response_model=List[CommunicationSchema])
async def search_communications(
    search_data: CommunicationSearch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Расширенный поиск коммуникаций"""
    query = db.query(Communication)

    # Фильтры по каналам
    if search_data.channels:
        query = query.filter(Communication.channel.in_(search_data.channels))

    # Фильтры по направлениям
    if search_data.directions:
        query = query.filter(Communication.direction.in_(search_data.directions))

    # Фильтры по sentiment
    if search_data.sentiments:
        query = query.filter(Communication.sentiment.in_(search_data.sentiments))

    # Поиск по тексту
    if search_data.query:
        search_filter = f"%{search_data.query}%"
        query = query.filter(
            or_(
                Communication.message_content.ilike(search_filter),
                Communication.intent.ilike(search_filter),
            )
        )

    # Фильтр по дате
    if search_data.date_from:
        query = query.filter(Communication.created_at >= search_data.date_from)
    if search_data.date_to:
        query = query.filter(Communication.created_at <= search_data.date_to)

    # Фильтр по клиенту или заказу
    if search_data.customer_id:
        query = query.filter(Communication.customer_id == search_data.customer_id)
    if search_data.order_id:
        query = query.filter(Communication.order_id == search_data.order_id)

    # Сортировка
    if search_data.sort_by == "date":
        order_by = (
            desc(Communication.created_at)
            if search_data.sort_order == "desc"
            else Communication.created_at
        )
    else:
        order_by = desc(Communication.created_at)  # по умолчанию по дате

    query = query.order_by(order_by)

    # Пагинация
    communications = query.offset(search_data.skip).limit(search_data.limit).all()

    return communications


@router.get("/stats/summary", response_model=CommunicationStats)
async def get_communication_stats(
    channel: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение статистики коммуникаций"""
    from datetime import datetime

    from sqlalchemy import func

    query = db.query(
        func.count(Communication.id).label("total_count"),
        func.count(func.distinct(Communication.customer_id)).label("unique_customers"),
        func.avg(func.length(Communication.message_content)).label(
            "avg_message_length"
        ),
    )

    # Применяем фильтры
    if channel:
        query = query.filter(Communication.channel == channel)
    if customer_id:
        query = query.filter(Communication.customer_id == customer_id)

    # Безопасный парсинг дат с обработкой ошибок
    if date_from:
        try:
            date_from_parsed = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(Communication.created_at >= date_from_parsed)
        except (ValueError, AttributeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_from format. Expected ISO format, got: {date_from}",
            )

    if date_to:
        try:
            date_to_parsed = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(Communication.created_at <= date_to_parsed)
        except (ValueError, AttributeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_to format. Expected ISO format, got: {date_to}",
            )

    result = query.first()

    # Статистика по каналам
    channel_stats = (
        db.query(Communication.channel, func.count(Communication.id).label("count"))
        .group_by(Communication.channel)
        .all()
    )

    # Статистика по sentiment
    sentiment_stats = (
        db.query(Communication.sentiment, func.count(Communication.id).label("count"))
        .filter(Communication.sentiment.isnot(None))
        .group_by(Communication.sentiment)
        .all()
    )

    # Безопасное извлечение данных из результата
    total_count = getattr(result, "total_count", 0) or 0
    unique_customers = getattr(result, "unique_customers", 0) or 0
    avg_message_length = getattr(result, "avg_message_length", 0) or 0

    return {
        "total_communications": total_count,
        "unique_customers": unique_customers,
        "average_message_length": float(avg_message_length),
        "channels_breakdown": {stat.channel: stat.count for stat in channel_stats},
        "sentiment_breakdown": {stat.sentiment: stat.count for stat in sentiment_stats},
    }
