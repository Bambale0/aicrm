"""
Схемы для API заказов
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..models.order import OrderStatus


class OrderItem(BaseModel):
    """Элемент заказа"""

    product_type: str = Field(..., description="Тип продукта (футболка, худи, etc.)")
    quantity: int = Field(..., gt=0, description="Количество")
    size: Optional[str] = Field(None, description="Размер")
    color: Optional[str] = Field(None, description="Цвет")
    design_url: Optional[str] = Field(None, description="URL дизайна")


class OrderCreate(BaseModel):
    """Создание нового заказа"""

    customer_id: int
    items: List[OrderItem]
    requirements: Optional[str] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None
    source: str = "website"


class OrderUpdate(BaseModel):
    """Обновление заказа"""

    status: Optional[OrderStatus] = None
    items: Optional[List[OrderItem]] = None
    requirements: Optional[str] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Ответ с информацией о заказе"""

    id: int
    customer_id: int
    status: OrderStatus
    status_display: str
    total_amount: float
    items: Optional[List[Dict[str, Any]]] = None
    requirements: Optional[str] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None
    source: str
    progress_percentage: float
    is_overdue: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionStepResponse(BaseModel):
    """Ответ с информацией об этапе производства"""

    id: int
    name: str
    description: Optional[str] = None
    status: str
    sequence_number: int
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    notes: Optional[str] = None
    is_overdue: bool
    progress_percentage: float

    model_config = ConfigDict(from_attributes=True)


class ProductionProgressResponse(BaseModel):
    """Ответ с прогрессом производства"""

    total_steps: int
    completed_steps: int
    in_progress_steps: int
    pending_steps: int
    progress: float
    current_step: Optional[str] = None
    next_step: Optional[str] = None
    is_overdue: bool
    steps: List[ProductionStepResponse]


class OrderListResponse(BaseModel):
    """Ответ со списком заказов"""

    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int


class StepUpdateRequest(BaseModel):
    """Запрос на обновление этапа"""

    status: Optional[str] = None
    actual_hours: Optional[float] = None
    notes: Optional[str] = None
    assigned_user_id: Optional[int] = None
