"""
Модель персональных настроек пользователя
"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserSettings(BaseModel):
    """Персональные настройки пользователя"""

    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    timezone = Column(String(50), default="Europe/Moscow")
    language = Column(String(10), default="ru")
    theme = Column(String(20), default="light")

    # Настройки уведомлений
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    telegram_notifications = Column(Boolean, default=True)

    # AI настройки
    ai_enabled = Column(Boolean, default=True)
    ai_model = Column(String(100), default="deepseek/deepseek-chat")
    ai_temperature = Column(Integer, default=70)  # 0-100
    ai_max_tokens = Column(Integer, default=4000)

    # Настройки сервисов
    service_settings = Column(JSON, default=dict)  # Настройки для каждого сервиса

    # Настройки процессов
    process_settings = Column(JSON, default=dict)  # Настройки автоматизации

    # Дополнительные настройки
    dashboard_layout = Column(JSON, default=dict)  # Layout дашборда
    shortcuts = Column(JSON, default=dict)  # Горячие клавиши
    custom_fields = Column(JSON, default=dict)  # Пользовательские поля

    # Связи
    user = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id})>"
