"""
Сервис управления клиентами
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from ..models.customer import Customer
from ..models.order import Order


class CustomerService:
    """Сервис для работы с клиентами"""

    @staticmethod
    async def create_customer(db: AsyncSession, customer_data: dict) -> Customer:
        """Создание нового клиента"""
        customer = Customer(**customer_data)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def get_customer(db: AsyncSession, customer_id: int) -> Optional[Customer]:
        """Получение клиента по ID"""
        result = await db.execute(
            db.query(Customer).filter(Customer.id == customer_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_customers(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Customer]:
        """Получение списка клиентов с фильтрацией"""
        query = db.query(Customer)

        if search:
            query = query.filter(
                (Customer.name.ilike(f"%{search}%")) |
                (Customer.email.ilike(f"%{search}%")) |
                (Customer.phone.ilike(f"%{search}%"))
            )

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer_id: int,
        update_data: dict
    ) -> Optional[Customer]:
        """Обновление данных клиента"""
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(customer, key, value)

        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def delete_customer(db: AsyncSession, customer_id: int) -> bool:
        """Удаление клиента"""
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return False

        await db.delete(customer)
        await db.commit()
        return True

    @staticmethod
    async def get_customer_stats(db: AsyncSession, customer_id: int) -> Optional[dict]:
        """Получение статистики клиента"""
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        # Обновляем статистику клиента
        customer.update_stats()
        await db.commit()

        # Получаем дополнительную статистику
        result = await db.execute(
            db.query(
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total_amount).label("total_spent"),
                func.max(Order.created_at).label("last_order_date"),
                func.avg(Order.total_amount).label("average_order_value")
            ).filter(Order.customer_id == customer_id)
        )
        stats = result.first()

        return {
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
            "loyalty_level": customer.loyalty_level,
            "last_order_date": stats.last_order_date,
            "average_order_value": float(stats.average_order_value or 0)
        }

    @staticmethod
    async def search_customers(
        db: AsyncSession,
        query: str,
        limit: int = 50
    ) -> List[Customer]:
        """Поиск клиентов"""
        result = await db.execute(
            db.query(Customer).filter(
                (Customer.name.ilike(f"%{query}%")) |
                (Customer.email.ilike(f"%{query}%")) |
                (Customer.phone.ilike(f"%{query}%"))
            ).limit(limit)
        )
        return result.scalars().all()


customer_service = CustomerService()
