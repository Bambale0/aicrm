"""
Маршруты для управления клиентами
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_async_db, get_current_active_user, get_db
from ...models.user import User
from ...services.customer import customer_service
from ..schemas.customer import CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/ping")
async def ping():
    return "pong"


@router.get("/count")
async def get_customers_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение общего количества клиентов в БД"""
    from sqlalchemy import func

    from ...models.customer import Customer

    count = (
        db.query(func.count(Customer.id)).filter(Customer.is_deleted == False).scalar()
    )
    return {"total_customers": count}


@router.get("/db/test")
async def test_database_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Тест подключения к БД и получение информации о клиентах"""
    try:
        from sqlalchemy import func, text

        from ...models.customer import Customer

        # Проверяем подключение
        result = db.execute(text("SELECT 1")).scalar()

        # Получаем статистику
        total_count = (
            db.query(func.count(Customer.id))
            .filter(Customer.is_deleted == False)
            .scalar()
        )

        # Получаем timestamp (работает с PostgreSQL и SQLite)
        from datetime import datetime

        timestamp = datetime.utcnow()

        return {
            "database_status": "connected",
            "connection_test": result,
            "total_customers": total_count,
            "timestamp": timestamp.isoformat() if timestamp else None,
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
        }


@router.post("/", response_model=dict)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создание нового клиента"""
    try:
        # Получаем данные из Pydantic модели
        data = customer_data.dict()
        print(f"[ROUTER] Creating customer with data: {data}")  # Debug log

        # Создаем клиента напрямую
        from ...models.customer import Customer

        customer = Customer(**data)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"[ROUTER] Customer created directly: {customer.id}")  # Debug log

        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "company": getattr(customer, "company", None),
            "created_at": (
                customer.created_at.isoformat() if customer.created_at else None
            ),
        }
    except Exception as e:
        print(f"[ROUTER] Error creating customer: {str(e)}")  # Debug log
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=400, detail=f"Error creating customer: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение списка клиентов"""
    customers = customer_service.get_customers(db, skip, limit, search)
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "company": getattr(c, "company", None),
            "total_orders": c.total_orders,
            "total_spent": float(c.total_spent) if c.total_spent else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in customers
    ]


@router.get("/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение клиента по ID"""
    customer = customer_service.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "company": getattr(customer, "company", None),
        "total_orders": customer.total_orders,
        "total_spent": float(customer.total_spent) if customer.total_spent else 0,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


@router.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновление данных клиента"""
    customer = customer_service.update_customer(
        db, customer_id, customer_data.dict(exclude_unset=True)
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "company": getattr(customer, "company", None),
        "total_orders": customer.total_orders,
        "total_spent": float(customer.total_spent) if customer.total_spent else 0,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удаление клиента"""
    success = customer_service.delete_customer(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}


@router.get("/{customer_id}/stats", response_model=dict)
async def get_customer_stats(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получение статистики клиента"""
    stats = customer_service.get_customer_stats(db, customer_id)
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
    """Поиск клиентов"""
    customers = customer_service.search_customers(db, q, limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "company": getattr(c, "company", None),
            "total_orders": c.total_orders,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in customers
    ]
