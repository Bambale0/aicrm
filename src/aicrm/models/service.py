"""
Модель услуг для системы
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, Numeric
from .base import BaseModel


class Service(BaseModel):
    """Модель для хранения услуг"""

    __tablename__ = "services"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    duration_hours = Column(Float, nullable=True)  # Продолжительность услуги в часах
    unit = Column(String(50), default="шт", nullable=False)  # Единица измерения

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', price={self.price}, category='{self.category}', active={self.is_active})>"
