"""
Модель организации для мультитенантной архитектуры
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .base import Base


class Organization(Base):
    """
    Организация (tenant) в мультитенантной системе.
    Каждая организация имеет свою отдельную базу данных.
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Контактная информация
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Настройки базы данных
    db_name = Column(String(100), unique=True, nullable=False)
    db_host = Column(String(255), default="localhost", nullable=False)
    db_port = Column(Integer, default=5432, nullable=False)
    db_username = Column(String(100), nullable=False)
    db_password_encrypted = Column(Text, nullable=False)  # Зашифрованный пароль
    
    # Статус организации
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # План подписки
    plan = Column(String(50), default="free", nullable=False)  # free, basic, premium, enterprise
    max_users = Column(Integer, default=5, nullable=False)
    max_storage_mb = Column(Integer, default=1000, nullable=False)  # 1GB по умолчанию
    
    # Даты
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"
