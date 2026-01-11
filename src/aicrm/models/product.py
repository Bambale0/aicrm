"""Модель товара/услуги"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .base import Base


class Product(Base):
    """Товар или услуга"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    description_short = Column(String(500))
    price = Column(Float, nullable=False)
    price_old = Column(Float)
    currency = Column(String(10), default="RUB")

    # Категория
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Тип: 'product' или 'service'
    type = Column(String(50), nullable=False, index=True)

    # Медиа
    images = Column(JSON)  # массив URL изображений
    main_image = Column(String(500))
    video_url = Column(String(500))

    # Техническая информация
    sku = Column(String(100), index=True)  # артикул
    barcode = Column(String(100))
    weight = Column(Float)  # вес в кг
    dimensions = Column(JSON)  # {"length": "", "width": "", "height": ""}

    # Характеристики
    specifications = Column(JSON)  # техникис свойства, состав, etc.

    # Статус
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Доставка
    delivery_info = Column(Text)
    pickup_available = Column(Boolean, default=True)
    delivery_available = Column(Boolean, default=True)

    # СЕО
    seo_title = Column(String(255))
    seo_description = Column(Text)
    seo_keywords = Column(String(500))

    # Статистика
    view_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    avg_rating = Column(Float)

    # Отношения
    category = relationship("Category", backref="products")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, type='{self.type}')>"


class ProductTag(Base):
    """Теги товаров"""

    __tablename__ = "product_tags"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    tag = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)

    # Отношения
    product = relationship("Product", backref="tags")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ProductTag(id={self.id}, product_id={self.product_id}, tag='{self.tag}')>"
