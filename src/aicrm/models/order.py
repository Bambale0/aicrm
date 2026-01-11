"""
Модель заказа
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_DESIGN = "in_design"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    """Модель заказа"""

    __tablename__ = "orders"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    items = Column(JSON)  # Детали заказа (продукты, количества, размеры)
    notes = Column(Text)  # Примечания к заказу
    requirements = Column(Text)  # Специфические требования клиента
    deadline = Column(DateTime)  # Желаемый срок выполнения
    source = Column(String, default="website")  # website, telegram, avito, phone, email

    # Связи
    customer = relationship("Customer", back_populates="orders")
    production_steps = relationship(
        "ProductionStep", back_populates="order", cascade="all, delete-orphan"
    )
    communications = relationship(
        "Communication", back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def status_display(self) -> str:
        """Человеко-читаемый статус"""
        statuses = {
            OrderStatus.PENDING: "Ожидает обработки",
            OrderStatus.IN_DESIGN: "В дизайне",
            OrderStatus.IN_PRODUCTION: "В производстве",
            OrderStatus.READY: "Готов",
            OrderStatus.DELIVERED: "Доставлен",
            OrderStatus.CANCELLED: "Отменен",
        }
        return statuses.get(self.status, str(self.status))

    @property
    def is_overdue(self) -> bool:
        """Проверка просрочки заказа"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return False
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline

    @property
    def progress_percentage(self) -> float:
        """Расчет общего прогресса заказа"""
        if self.status == OrderStatus.DELIVERED:
            return 100.0
        elif self.status == OrderStatus.CANCELLED:
            return 0.0

        # Расчет на основе этапов производства
        steps = self.production_steps
        if not steps:
            return 0.0

        total_steps = len(steps)
        completed_steps = len([s for s in steps if s.status.name == "COMPLETED"])
        in_progress_steps = len([s for s in steps if s.status.name == "IN_PROGRESS"])

        if total_steps == 0:
            return 0.0

        # Завершенные этапы + половина прогресса для этапов в работе
        progress = ((completed_steps + in_progress_steps * 0.5) / total_steps) * 100
        return min(progress, 100.0)

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """Проверка возможности перехода в новый статус"""
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.IN_DESIGN, OrderStatus.CANCELLED],
            OrderStatus.IN_DESIGN: [OrderStatus.IN_PRODUCTION, OrderStatus.CANCELLED],
            OrderStatus.IN_PRODUCTION: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def update_status(self, new_status: OrderStatus):
        """Обновление статуса с проверкой валидности"""
        if self.can_transition_to(new_status):
            self.status = new_status
            self.updated_at = datetime.utcnow()
        else:
            raise ValueError(
                f"Невозможно изменить статус с {self.status} на {new_status}"
            )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, customer_id={self.customer_id}, status={self.status}, amount={self.total_amount})>"
