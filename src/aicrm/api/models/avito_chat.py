"""
Модель для настроек чатов Avito
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

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
    unread_count = Column(
        Integer, default=0, nullable=False, index=True
    )  # Количество непрочитанных сообщений
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
        return (
            f"<AvitoChatSettings(chat_id={self.chat_id}, ai_enabled={self.ai_enabled})>"
        )


class AvitoGlobalSettings(BaseModel):
    """Глобальные настройки интеграции с Avito"""

    __tablename__ = "avito_global_settings"

    # API учетные данные
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Webhook настройки
    webhook_url = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)

    # Настройки автоответчика
    auto_reply_enabled = Column(Boolean, default=False)
    auto_reply_message = Column(
        String,
        default="Спасибо за ваше сообщение. Мы свяжемся с вами в ближайшее время.",
    )

    # AI настройки по умолчанию
    ai_enabled = Column(Boolean, default=True)
    ai_model = Column(String, default="gpt-4")
    ai_temperature = Column(Integer, default=70)  # 0-100
    ai_max_tokens = Column(Integer, default=1000)

    # Системные настройки
    notification_email = Column(String, nullable=True)
    sync_interval = Column(Integer, default=300)  # секунды
    max_concurrent_chats = Column(Integer, default=10)

    # Статус интеграции
    is_active = Column(Boolean, default=False)
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)

    @property
    def ai_temperature_float(self) -> float:
        """Температура в формате float (0.0-1.0)"""
        return self.ai_temperature / 100.0

    def update_last_sync(self):
        """Обновление времени последней синхронизации"""
        self.last_sync_at = datetime.utcnow()

    def set_error(self, error_message: str):
        """Установка ошибки"""
        self.last_error = error_message

    def clear_error(self):
        """Очистка ошибки"""
        self.last_error = None

    def __repr__(self) -> str:
        return f"<AvitoGlobalSettings(is_active={self.is_active}, client_id={self.client_id})>"
