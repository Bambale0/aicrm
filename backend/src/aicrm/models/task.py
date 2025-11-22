"""
Модель задачи
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel


class Task(BaseModel):
    """Модель задачи"""

    __tablename__ = "tasks"

    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="todo")  # todo, in_progress, done, cancelled
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    tags = Column(String)  # CSV теги
    related_order_id = Column(Integer, ForeignKey("orders.id"))
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    extra_data = Column(Text)  # Дополнительные данные для интеграций

    # Связи
    assigned_to_user = relationship("User", foreign_keys=[assigned_to], back_populates="tasks")
    created_by_user = relationship("User", foreign_keys=[created_by])

    @property
    def priority_display(self) -> str:
        """Человеко-читаемый приоритет"""
        priorities = {
            "low": "Низкий",
            "medium": "Средний",
            "high": "Высокий"
        }
        return priorities.get(self.priority, self.priority)

    @property
    def status_display(self) -> str:
        """Человеко-читаемый статус"""
        statuses = {
            "todo": "К выполнению",
            "in_progress": "В работе",
            "done": "Выполнена",
            "cancelled": "Отменена"
        }
        return statuses.get(self.status, self.status)

    def complete(self):
        """Завершение задачи"""
        self.status = "done"
        self.completed_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """Проверка просрочки"""
        if self.due_date and self.status not in ["done", "cancelled"]:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self) -> str:
        return f"<Task(title={self.title}, priority={self.priority}, status={self.status})>"
