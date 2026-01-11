"""Модель категории товаров и услуг"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class Category(Base):
    """Категория товаров/услуг"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # 'product' или 'service'
    icon = Column(String(100))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Отношения
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}')>"
