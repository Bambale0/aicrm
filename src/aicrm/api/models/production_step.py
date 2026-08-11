"""
Модель этапа производства
"""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ProductionStep(BaseModel):
    """Модель этапа производства"""

    __tablename__ = "production_steps"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)  # Название этапа
    description = Column(Text)  # Описание этапа
    sequence_number = Column(Integer, nullable=False)  # Порядок выполнения
    status = Column(Enum(StepStatus), default=StepStatus.PENDING)

    # Временные характеристики
    estimated_hours = Column(Float)  # Ожидаемое время выполнения
    actual_hours = Column(Float)  # Фактическое время выполнения
    started_at = Column(DateTime)  # Время начала
    completed_at = Column(DateTime)  # Время завершения

    # Исполнитель
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)  # Комментарии/примечания

    # Связи
    order = relationship("Order", back_populates="production_steps")
    assigned_to_user = relationship("User", back_populates="production_steps")

    @property
    def is_overdue(self) -> bool:
        """Проверка просрочки этапа"""
        if self.status in [StepStatus.COMPLETED, StepStatus.CANCELLED]:
            return False
        if not self.started_at or not self.estimated_hours:
            return False

        from datetime import timedelta

        expected_completion = self.started_at + timedelta(hours=self.estimated_hours)
        return datetime.utcnow() > expected_completion

    @property
    def progress_percentage(self) -> float:
        """Расчет прогресса этапа"""
        if self.status == StepStatus.COMPLETED:
            return 100.0
        elif self.status == StepStatus.IN_PROGRESS:
            # Для упрощения - 50% прогресса для этапов в работе
            return 50.0
        else:
            return 0.0

    def start_work(self):
        """Начать выполнение этапа"""
        if self.status == StepStatus.PENDING:
            self.status = StepStatus.IN_PROGRESS
            self.started_at = datetime.utcnow()

    def complete_work(self, actual_hours: float = None, notes: str = None):
        """Завершить выполнение этапа"""
        if self.status == StepStatus.IN_PROGRESS:
            self.status = StepStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            if actual_hours:
                self.actual_hours = actual_hours
            if notes:
                self.notes = notes

    def __repr__(self) -> str:
        return f"<ProductionStep(order_id={self.order_id}, name='{self.name}', status={self.status})>"
