"""
Маршруты для управления клиентами
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_active_user, get_db
from ...models.user import User
from ...services.cached_customer_service import cached_customer_service
from ..schemas.customer import CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/ping")
async def ping():
    return "pong"


@router.post("/", response_model=dict)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создание нового клиента"""
    customer = await cached_customer_service.create_customer_cached(
        db, customer_data.dict()
    )
    return customer


@router.get("/", response_model=List[dict])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение списка клиентов с кешированием"""
    customers = await cached_customer_service.get_customers_cached(
        db, skip, limit, search
    )
    return customers


@router.get("/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение клиента по ID с кешированием"""
    customer = await cached_customer_service.get_customer_cached(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновление данных клиента с инвалидацией кеша"""
    customer = await cached_customer_service.update_customer_cached(
        db, customer_id, customer_data.dict(exclude_unset=True)
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удаление клиента с инвалидацией кеша"""
    success = await cached_customer_service.delete_customer_cached(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}


@router.get("/{customer_id}/stats", response_model=dict)
async def get_customer_stats(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение статистики клиента с кешированием"""
    stats = await cached_customer_service.get_customer_stats_cached(db, customer_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Customer not found")
    return stats


@router.get("/search/", response_model=List[dict])
async def search_customers(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Поиск клиентов с кешированием"""
    customers = await cached_customer_service.search_customers_cached(db, q, limit)
    return customers