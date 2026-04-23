"""
Модель для настроек чатов Avito
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class AvitoChatSettings(BaseModel):
    """Настройки чата Avito"""

    __tablename__ = "avito_chat_settings"

    chat_id = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Настройки AI
    ai_enabled = Column(Boolean, default=True, nullable=False)
    ai_model = Column(String, default="deepseek/deepseek-coder:33b-instruct")
    ai_temperature = Column(Integer, default=70)  # 0-100, будет делиться на 100

    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Статистика чата
    message_count = Column(Integer, default=0, nullable=False)
    unread_count = Column(Integer, default=0, nullable=False, index=True)  # Количество непрочитанных сообщений
    last_message_at = Column(DateTime, nullable=True)
    last_ai_response_at = Column(DateTime, nullable=True)

    # Дополнительные настройки
    settings = Column(JSON, default=dict, nullable=False)  # Гибкие настройки

    # Связи
    customer = relationship("Customer", back_populates="avito_chat_settings")

    @property
    def ai_temperature_float(self) -> float:
        """Температура в формате float (0.0-1.0)"""
        return self.ai_temperature / 100.0

    def update_last_message(self):
        """Обновление времени последнего сообщения"""
        self.last_message_at = datetime.utcnow()
        self.message_count += 1

    def update_last_ai_response(self):
        """Обновление времени последнего AI ответа"""
        self.last_ai_response_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<AvitoChatSettings(chat_id={self.chat_id}, ai_enabled={self.ai_enabled})>"
