"""
Конфигурация приложения
"""

import os
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # База данных
    database_url: str = "postgresql+psycopg2://user:password@localhost/aicrm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # AI - устаревшие настройки (теперь в ai_config.py)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # Telegram
    telegram_bot_token: Optional[str] = None

    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None

    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # SMS
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_login: Optional[str] = None
    sms_password: Optional[str] = None
    sms_sender: Optional[str] = "AICRM"

    # Avito
    avito_client_id: Optional[str] = None
    avito_client_secret: Optional[str] = None
    avito_user_id: Optional[int] = None

    # App
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "https://dev.chillcreative.ru"]
    log_level: str = "INFO"

    # System monitoring
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = [".env", "src/.env"]
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment


settings = Settings()
