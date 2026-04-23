"""
Схемы для задач
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    """Базовая схема задачи"""

    title: str
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    assigned_to: Optional[int] = None
    created_by: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    related_order_id: Optional[int] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None


class TaskCreate(TaskBase):
    """Схема создания задачи"""

    # Наследует все поля от TaskBase


class TaskUpdate(BaseModel):
    """Схема обновления задачи"""

    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    related_order_id: Optional[int] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None


class Task(TaskBase):
    """Схема задачи для ответов"""

    id: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
