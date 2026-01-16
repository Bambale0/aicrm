"""
Сервис для работы с заказами
"""

from __future__ import annotations

from typing import List, Optional

import structlog
from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.order import Order, OrderStatus
from ..models.user import User
from ..schemas.order import OrderCreate, OrderResponse, OrderUpdate
from .production import ProductionService

logger = structlog.get_logger(__name__)


class OrderService:
    """Сервис для управления заказами"""

    def __init__(self, db: Session):
        self.db = db
        self.production_service = ProductionService(db)

    def create_order(self, order_data: OrderCreate, current_user: User) -> Order:
        """
        Создание нового заказа с валидацией и автоматическим workflow

        WHY: Вынос бизнес-логики из API слоя для чистой архитектуры
        TRADE-OFF: Увеличение сложности, но улучшение тестируемости и maintainability
        """
        logger.info(
            "Creating new order",
            customer_id=order_data.customer_id,
            user_id=current_user.id,
        )

        # Проверяем существование клиента
        customer = (
            self.db.query(Customer)
            .filter(Customer.id == order_data.customer_id)
            .first()
        )
        if not customer:
            logger.warning("Customer not found", customer_id=order_data.customer_id)
            raise ValueError(f"Клиент с ID {order_data.customer_id} не найден")

        # Рассчитываем общую стоимость
        # TODO: Получить цены из продуктовой базы
        total_amount = sum(
            item.quantity * 500 for item in order_data.items
        )  # 500 руб за единицу

        # Создаем заказ
        order = Order(
            customer_id=order_data.customer_id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            items=[item.dict() for item in order_data.items],
            requirements=order_data.requirements,
            deadline=order_data.deadline,
            notes=order_data.notes,
            source=order_data.source,
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Автоматическое создание производственного workflow
        self.production_service.create_production_workflow(order.id)

        # Обновляем заказ после создания workflow
        self.db.refresh(order)

        logger.info(
            "Order created successfully", order_id=order.id, total_amount=total_amount
        )

        return order

    def get_orders(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
    ) -> tuple[List[Order], int]:
        """
        Получение списка заказов с пагинацией и фильтрами
        """
        query = self.db.query(Order)

        if status:
            query = query.filter(Order.status == status)
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)

        total = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()

        return orders, total

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Получение заказа по ID
        """
        return self.db.query(Order).filter(Order.id == order_id).first()

    def update_order(self, order_id: int, order_data: OrderUpdate) -> Order:
        """
        Обновление информации о заказе
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заказ с ID {order_id} не найден")

        # Обновляем поля
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                order.update_status(value)
            else:
                setattr(order, field, value)

        self.db.commit()
        self.db.refresh(order)

        logger.info("Order updated", order_id=order_id, fields=list(update_data.keys()))

        return order

    def delete_order(self, order_id: int) -> None:
        """
        Удаление заказа (только в статусе PENDING)
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заказ с ID {order_id} не найден")

        if order.status != OrderStatus.PENDING:
            raise ValueError(
                "Можно удалять только заказы в статусе 'Ожидает обработки'"
            )

        self.db.delete(order)
        self.db.commit()

        logger.info("Order deleted", order_id=order_id)

    def to_response(self, order: Order) -> OrderResponse:
        """
        Преобразование модели Order в OrderResponse

        WHY: Устранение дублирования кода преобразования
        TRADE-OFF: Дополнительный метод, но DRY
        """
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
            updated_at=order.updated_at,
        )
