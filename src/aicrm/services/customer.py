"""
Сервис управления клиентами
"""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.order import Order
from .automation.automation_service import AutomationService


class CustomerService:
    """Сервис для работы с клиентами"""

    @staticmethod
    def create_customer(db: Session, customer_data: dict) -> Customer:
        """Создание нового клиента"""
        customer = Customer(**customer_data)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    async def create_customer_with_automation(
        db: Session, customer_data: dict
    ) -> Customer:
        """Создание нового клиента с запуском автоматизации"""
        customer = CustomerService.create_customer(db, customer_data)

        # Запускаем автоматизацию
        automation_service = AutomationService(db)
        await automation_service.on_customer_created(customer.id)

        return customer

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        """Получение клиента по ID"""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_customers(
        db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Customer]:
        """Получение списка клиентов с фильтрацией"""
        query = db.query(Customer)

        if search:
            query = query.filter(
                (Customer.name.ilike(f"%{search}%"))
                | (Customer.email.ilike(f"%{search}%"))
                | (Customer.phone.ilike(f"%{search}%"))
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_customer(
        db: Session, customer_id: int, update_data: dict
    ) -> Optional[Customer]:
        """Обновление данных клиента"""
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(customer, key, value)

        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def delete_customer(db: Session, customer_id: int) -> bool:
        """Удаление клиента"""
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            return False

        db.delete(customer)
        db.commit()
        return True

    @staticmethod
    def get_customer_stats(db: Session, customer_id: int) -> Optional[dict]:
        """Получение статистики клиента"""
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        # Обновляем статистику клиента
        customer.update_stats()
        db.commit()

        # Получаем дополнительную статистику
        stats = (
            db.query(
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total_amount).label("total_spent"),
                func.max(Order.created_at).label("last_order_date"),
                func.avg(Order.total_amount).label("average_order_value"),
            )
            .filter(Order.customer_id == customer_id)
            .first()
        )

        return {
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
            "loyalty_level": customer.loyalty_level,
            "last_order_date": stats.last_order_date,
            "average_order_value": float(stats.average_order_value or 0),
        }

    @staticmethod
    def search_customers(db: Session, query: str, limit: int = 50) -> List[Customer]:
        """Поиск клиентов"""
        return (
            db.query(Customer)
            .filter(
                (Customer.name.ilike(f"%{query}%"))
                | (Customer.email.ilike(f"%{query}%"))
                | (Customer.phone.ilike(f"%{query}%"))
            )
            .limit(limit)
            .all()
        )


customer_service = CustomerService()
