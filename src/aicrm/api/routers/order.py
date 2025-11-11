"""
API роутер для заказов
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...services.production import ProductionService
from ...models.order import Order, OrderStatus
from ...models.customer import Customer
from ..schemas.order import (
    OrderCreate, OrderResponse, OrderUpdate, OrderListResponse,
    ProductionProgressResponse, StepUpdateRequest
)

router = APIRouter()


def get_production_service(db: Session = Depends(get_db)) -> ProductionService:
    """Зависимость для получения сервиса производства"""
    return ProductionService(db)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    production_service: ProductionService = Depends(get_production_service)
):
    """
    Создание заказа с автоматическим workflow производства
    """
    # Проверяем существование клиента
    customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Клиент с ID {order_data.customer_id} не найден"
        )

    # Рассчитываем общую стоимость (простая логика)
    total_amount = sum(item.quantity * 500 for item in order_data.items)  # 500 руб за единицу

    # Создаем заказ
    order = Order(
        customer_id=order_data.customer_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        items=[item.dict() for item in order_data.items],
        requirements=order_data.requirements,
        deadline=order_data.deadline,
        notes=order_data.notes,
        source=order_data.source
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # Автоматическое создание производственного workflow
    await production_service.create_production_workflow(order.id)

    # Обновляем заказ после создания workflow
    db.refresh(order)

    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        status_display=order.status_display,
        total_amount=float(order.total_amount),
        items=order.items,
        requirements=order.requirements,
        deadline=order.deadline,
        notes=order.notes,
        source=order.source,
        progress_percentage=order.progress_percentage,
        is_overdue=order.is_overdue,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    status: Optional[OrderStatus] = Query(None, description="Фильтр по статусу"),
    customer_id: Optional[int] = Query(None, description="Фильтр по клиенту"),
    db: Session = Depends(get_db)
):
    """
    Получение списка заказов с пагинацией и фильтрами
    """
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    total = query.count()
    orders = query.offset((page - 1) * per_page).limit(per_page).all()

    return OrderListResponse(
        orders=[
            OrderResponse(
                id=order.id,
                customer_id=order.customer_id,
                status=order.status,
                status_display=order.status_display,
                total_amount=float(order.total_amount),
                items=order.items,
                requirements=order.requirements,
                deadline=order.deadline,
                notes=order.notes,
                source=order.source,
                progress_percentage=order.progress_percentage,
                is_overdue=order.is_overdue,
                created_at=order.created_at,
                updated_at=order.updated_at
            ) for order in orders
        ],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    Получение информации о конкретном заказе
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )

    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        status_display=order.status_display,
        total_amount=float(order.total_amount),
        items=order.items,
        requirements=order.requirements,
        deadline=order.deadline,
        notes=order.notes,
        source=order.source,
        progress_percentage=order.progress_percentage,
        is_overdue=order.is_overdue,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновление информации о заказе
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )

    # Обновляем поля
    update_data = order_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            order.update_status(value)
        else:
            setattr(order, field, value)

    db.commit()
    db.refresh(order)

    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        status_display=order.status_display,
        total_amount=float(order.total_amount),
        items=order.items,
        requirements=order.requirements,
        deadline=order.deadline,
        notes=order.notes,
        source=order.source,
        progress_percentage=order.progress_percentage,
        is_overdue=order.is_overdue,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("/{order_id}/production-progress", response_model=ProductionProgressResponse)
async def get_production_progress(
    order_id: int,
    db: Session = Depends(get_db),
    production_service: ProductionService = Depends(get_production_service)
):
    """
    Получение прогресса производства заказа
    """
    # Проверяем существование заказа
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )

    progress = await production_service.update_progress(order_id)
    return ProductionProgressResponse(**progress)


@router.post("/{order_id}/production-steps/{step_id}/start")
async def start_production_step(
    order_id: int,
    step_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    production_service: ProductionService = Depends(get_production_service)
):
    """
    Начать выполнение этапа производства
    """
    try:
        step = await production_service.start_step(step_id, user_id)
        return {"message": f"Этап '{step.name}' успешно запущен", "step_id": step.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{order_id}/production-steps/{step_id}/complete")
async def complete_production_step(
    order_id: int,
    step_id: int,
    step_data: StepUpdateRequest,
    db: Session = Depends(get_db),
    production_service: ProductionService = Depends(get_production_service)
):
    """
    Завершить выполнение этапа производства
    """
    try:
        step = await production_service.complete_step(
            step_id,
            step_data.actual_hours,
            step_data.notes
        )
        return {"message": f"Этап '{step.name}' успешно завершен", "step_id": step.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/production/overdue")
async def get_overdue_production_steps(
    db: Session = Depends(get_db),
    production_service: ProductionService = Depends(get_production_service)
):
    """
    Получение списка просроченных этапов производства
    """
    overdue_steps = await production_service.get_overdue_steps()
    return {"overdue_steps": overdue_steps, "count": len(overdue_steps)}


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """
    Удаление заказа (только для заказов в статусе PENDING)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можно удалять только заказы в статусе 'Ожидает обработки'"
        )

    db.delete(order)
    db.commit()

    return {"message": f"Заказ {order_id} успешно удален"}
