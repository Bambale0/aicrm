"""
Модель товаров для системы
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from .base import BaseModel


class Product(BaseModel):
    """Модель для хранения товаров"""

    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sku = Column(String(100), unique=True, nullable=True)  # Артикул товара
    unit = Column(String(50), default="шт", nullable=False)  # Единица измерения
    weight_kg = Column(Numeric(8, 3), nullable=True)  # Вес в килограммах
    dimensions = Column(String(100), nullable=True)  # Габариты (например, "10x20x30 см")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, stock={self.stock_quantity}, active={self.is_active})>"
