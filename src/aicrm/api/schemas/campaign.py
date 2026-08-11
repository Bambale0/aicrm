"""
Схемы для кампаний и их AI настроек
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class CampaignCreate(BaseModel):
    """Создание новой кампании"""

    name: str = Field(..., description="Название кампании", max_length=255)
    description: Optional[str] = Field(None, description="Описание кампании")
    organization_id: int = Field(..., description="ID организации")


class CampaignUpdate(BaseModel):
    """Обновление кампании"""

    name: Optional[str] = Field(None, description="Название кампании", max_length=255)
    description: Optional[str] = Field(None, description="Описание кампании")
    is_active: Optional[bool] = Field(None, description="Активна ли кампания")
    status: Optional[str] = Field(None, description="Статус кампании")

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["draft", "active", "paused", "completed"]
            if v not in valid_statuses:
                raise ValueError(f"Статус должен быть одним из: {valid_statuses}")
        return v


class CampaignAISettingsCreate(BaseModel):
    """Создание AI настроек для кампании"""

    campaign_id: int = Field(..., description="ID кампании")

    # Основные настройки AI
    default_model: Optional[str] = Field(None, description="Модель AI по умолчанию")
    temperature: Optional[float] = Field(
        None, description="Температура генерации", ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        None, description="Максимальное количество токенов", ge=1, le=8000
    )

    # API ключи
    openrouter_api_key: Optional[str] = Field(None, description="API ключ OpenRouter")
    openai_api_key: Optional[str] = Field(None, description="API ключ OpenAI")
    huggingface_api_key: Optional[str] = Field(None, description="API ключ HuggingFace")

    # Настройки
    provider: Optional[str] = Field(None, description="Провайдер AI")
    auto_reply_enabled: Optional[bool] = Field(None, description="Включить автоответы")
    auto_reply_temperature: Optional[float] = Field(
        None, description="Температура автоответов", ge=0.0, le=2.0
    )
    auto_reply_max_tokens: Optional[int] = Field(
        None, description="Максимальные токены автоответов", ge=1, le=8000
    )

    # Специфические настройки
    custom_prompt: Optional[str] = Field(
        None, description="Кастомный промпт для кампании"
    )
    target_audience: Optional[str] = Field(
        None, description="Целевая аудитория", max_length=255
    )
    brand_voice: Optional[str] = Field(
        None, description="Стиль общения", max_length=100
    )

    # Лимиты
    daily_token_limit: Optional[int] = Field(None, description="Дневной лимит токенов")
    monthly_token_limit: Optional[int] = Field(
        None, description="Месячный лимит токенов"
    )


class CampaignAISettingsUpdate(BaseModel):
    """Обновление AI настроек кампании"""

    # Такие же поля как и в CampaignAISettingsCreate, но все опциональные
    default_model: Optional[str] = Field(None, description="Модель AI по умолчанию")
    temperature: Optional[float] = Field(
        None, description="Температура генерации", ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        None, description="Максимальное количество токенов", ge=1, le=8000
    )
    openrouter_api_key: Optional[str] = Field(None, description="API ключ OpenRouter")
    openai_api_key: Optional[str] = Field(None, description="API ключ OpenAI")
    huggingface_api_key: Optional[str] = Field(None, description="API ключ HuggingFace")
    provider: Optional[str] = Field(None, description="Провайдер AI")
    auto_reply_enabled: Optional[bool] = Field(None, description="Включить автоответы")
    auto_reply_temperature: Optional[float] = Field(
        None, description="Температура автоответов", ge=0.0, le=2.0
    )
    auto_reply_max_tokens: Optional[int] = Field(
        None, description="Максимальные токены автоответов", ge=1, le=8000
    )
    custom_prompt: Optional[str] = Field(
        None, description="Кастомный промпт для кампании"
    )
    target_audience: Optional[str] = Field(
        None, description="Целевая аудитория", max_length=255
    )
    brand_voice: Optional[str] = Field(
        None, description="Стиль общения", max_length=100
    )
    daily_token_limit: Optional[int] = Field(None, description="Дневной лимит токенов")
    monthly_token_limit: Optional[int] = Field(
        None, description="Месячный лимит токенов"
    )


class CampaignResponse(BaseModel):
    """Ответ с информацией о кампании"""

    id: int
    name: str
    description: Optional[str]
    organization_id: int
    is_active: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    ai_settings: Optional[Dict[str, Any]] = Field(
        None, description="AI настройки кампании"
    )


class CampaignListResponse(BaseModel):
    """Список кампаний"""

    campaigns: list[CampaignResponse]
    total: int
    page: int = 1
    per_page: int = 20


class CampaignAISettingsResponse(BaseModel):
    """Ответ с AI настройками кампании"""

    id: int
    campaign_id: int
    default_model: str
    temperature: float
    max_tokens: int
    provider: str
    auto_reply_enabled: bool
    auto_reply_temperature: float
    auto_reply_max_tokens: int
    custom_prompt: Optional[str]
    target_audience: Optional[str]
    brand_voice: Optional[str]
    daily_token_limit: Optional[int]
    monthly_token_limit: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    # Не возвращаем API ключи в ответе по безопасности!
    # openrouter_api_key: скрыто
    # openai_api_key: скрыто
