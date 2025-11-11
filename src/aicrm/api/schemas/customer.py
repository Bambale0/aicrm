"""
Схемы для клиентов
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CustomerBase(BaseModel):
    """Базовая схема клиента"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_info: Optional[dict] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Схема создания клиента"""
    pass


class CustomerUpdate(BaseModel):
    """Схема обновления клиента"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_info: Optional[dict] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class Customer(CustomerBase):
    """Схема клиента для ответов"""
    id: int
    total_orders: int
    total_spent: float
    loyalty_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerStats(BaseModel):
    """Статистика клиента"""
    total_orders: int
    total_spent: float
    loyalty_level: str
    last_order_date: Optional[datetime] = None
    average_order_value: float
