"""Модель услуги"""

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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Service(Base):
    """Услуга"""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    description_short = Column(String(500))

    # Категория услуги
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Ценообразование
    price_min = Column(Float)
    price_max = Column(Float)
    price_type = Column(String(50), default="fixed")  # 'fixed', 'hourly', 'project'

    # Время выполнения
    duration_hours = Column(Float)  # в часах
    duration_days = Column(Integer)

    # Спецификация работ
    work_included = Column(JSON)  # что входит в услугу
    additional_services = Column(JSON)  # дополнительные услуги

    # Требования
    requirements = Column(JSON)  # что нужно от клиента

    # Портфолио/примеры
    portfolio_images = Column(JSON)
    portfolio_projects = Column(JSON)

    # Статус
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Гарантии
    warranty_info = Column(Text)
    free_visit = Column(Boolean, default=False)

    # Регионы обслуживания
    service_area = Column(String(255))  # "Москва и МО", "Вся Россия", etc.

    # Контакты исполнителя
    contractor_name = Column(String(255))
    contractor_contact = Column(String(255))

    # СЕО
    seo_title = Column(String(255))
    seo_description = Column(Text)
    seo_keywords = Column(String(500))

    # Статистика
    view_count = Column(Integer, default=0)
    inquiry_count = Column(Integer, default=0)
    avg_rating = Column(Float)

    # Отношения
    category = relationship("Category", backref="services")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}', price_min={self.price_min}, price_max={self.price_max})>"


class ServiceTag(Base):
    """Теги услуг"""

    __tablename__ = "service_tags"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    tag = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)

    # Отношения
    service = relationship("Service", backref="tags")
