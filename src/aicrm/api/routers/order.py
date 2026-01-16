"""
API роутер для заказов
"""

from __future__ import annotations

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.order import OrderStatus
from ...models.user import User
from ...schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
    ProductionProgressResponse,
    StepUpdateRequest,
)
from ...services.order_service import OrderService
from ...services.production import ProductionService
from .auth import get_current_active_user

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Зависимость для получения сервиса заказов"""
    return OrderService(db)


def get_production_service(db: Session = Depends(get_db)) -> ProductionService:
    """Зависимость для получения сервиса производства"""
    return ProductionService(db)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Создание заказа с автоматическим workflow производства
    """
    try:
        order = order_service.create_order(order_data, current_user)
        return order_service.to_response(order)
    except ValueError as e:
        logger.warning("Failed to create order", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(
        20, ge=1, le=100, description="Количество элементов на странице"
    ),
    status: Optional[OrderStatus] = Query(None, description="Фильтр по статусу"),
    customer_id: Optional[int] = Query(None, description="Фильтр по клиенту"),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение списка заказов с пагинацией и фильтрами
    """
    orders, total = order_service.get_orders(
        page=page, per_page=per_page, status=status, customer_id=customer_id
    )

    return OrderListResponse(
        orders=[order_service.to_response(order) for order in orders],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение информации о конкретном заказе
    """
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден",
        )

    return order_service.to_response(order)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    order_service: OrderService = Depends(get_order_service),
):
    """
    Обновление информации о заказе
    """
    try:
        order = order_service.update_order(order_id, order_data)
        return order_service.to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{order_id}/production-progress", response_model=ProductionProgressResponse
)
async def get_production_progress(
    order_id: int,
    production_service: ProductionService = Depends(get_production_service),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение прогресса производства заказа
    """
    # Проверяем существование заказа
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден",
        )

    progress = production_service.update_progress(order_id)
    return ProductionProgressResponse(**progress)


@router.post("/{order_id}/production-steps/{step_id}/start")
async def start_production_step(
    order_id: int,
    step_id: int,
    user_id: Optional[int] = None,
    production_service: ProductionService = Depends(get_production_service),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Начать выполнение этапа производства
    """
    # Проверяем существование заказа
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден",
        )

    try:
        step = production_service.start_step(step_id, user_id)  # type: ignore
        return {"message": f"Этап '{step.name}' успешно запущен", "step_id": step.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{order_id}/production-steps/{step_id}/complete")
async def complete_production_step(
    order_id: int,
    step_id: int,
    step_data: StepUpdateRequest,
    production_service: ProductionService = Depends(get_production_service),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Завершить выполнение этапа производства
    """
    # Проверяем существование заказа
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден",
        )

    try:
        step = production_service.complete_step(
            step_id, step_data.actual_hours, step_data.notes  # type: ignore
        )
        return {"message": f"Этап '{step.name}' успешно завершен", "step_id": step.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/production/overdue")
async def get_overdue_production_steps(
    production_service: ProductionService = Depends(get_production_service),
):
    """
    Получение списка просроченных этапов производства
    """
    overdue_steps = production_service.get_overdue_steps()
    return {"overdue_steps": overdue_steps, "count": len(overdue_steps)}


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
):
    """
    Удаление заказа (только для заказов в статусе PENDING)
    """
    try:
        order_service.delete_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
