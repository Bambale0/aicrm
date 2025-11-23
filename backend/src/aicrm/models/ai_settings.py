"""
Модель настроек AI
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text
from .base import BaseModel


class AISettings(BaseModel):
    """Модель глобальных настроек AI"""

    __tablename__ = "ai_settings"

    # Основные настройки
    default_model = Column(String, nullable=False, default="deepseek/deepseek-chat-v3.1")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=1000)

    # API ключи (зашифрованные)
    openrouter_api_key = Column(Text, nullable=True)
    openai_api_key = Column(Text, nullable=True)
    huggingface_api_key = Column(Text, nullable=True)

    # Настройки провайдера
    provider = Column(String, nullable=False, default="openrouter")  # openrouter, openai, huggingface

    # Дополнительные настройки
    auto_reply_enabled = Column(Boolean, default=True)
    auto_reply_temperature = Column(Float, default=0.5)
    auto_reply_max_tokens = Column(Integer, default=500)

    # Системные настройки
    rate_limit_per_minute = Column(Integer, default=60)
    cache_enabled = Column(Boolean, default=True)
    log_level = Column(String, default="INFO")

    # Настройки для конкретных моделей
    fallback_model = Column(String, nullable=True)  # модель для fallback при ошибках
    premium_model = Column(String, nullable=True)   # модель для премиум пользователей

    def __repr__(self) -> str:
        return f"<AISettings(id={self.id}, provider={self.provider}, default_model={self.default_model})>"
