"""
Модель настроек Telegram
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from .base import BaseModel


class TelegramSettings(BaseModel):
    """Модель настроек Telegram бота"""

    __tablename__ = "telegram_settings"

    # Основные настройки бота
    bot_token = Column(Text, nullable=True)  # API токен бота
    webhook_url = Column(String, nullable=True)  # URL для webhook
    webhook_secret = Column(String, nullable=True)  # Секрет для webhook

    # Настройки автоответчика
    auto_reply_enabled = Column(Boolean, default=False)
    auto_reply_message = Column(Text, nullable=True)

    # Настройки AI
    ai_enabled = Column(Boolean, default=True)
    ai_model = Column(String, default="gpt-4")
    ai_temperature = Column(Float, default=0.7)
    ai_max_tokens = Column(Integer, default=1000)

    # Системные настройки
    notification_email = Column(String, nullable=True)
    sync_interval = Column(Integer, default=300)  # интервал синхронизации в секундах
    max_concurrent_chats = Column(Integer, default=10)

    def __repr__(self) -> str:
        return f"<TelegramSettings(id={self.id}, ai_enabled={self.ai_enabled})>"
