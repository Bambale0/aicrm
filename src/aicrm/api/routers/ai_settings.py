"""
API роутер для управления настройками AI
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.ai_settings_service import AISettingsService
from ...models.ai_settings import AISettings
from pydantic import BaseModel, Field


class AISettingsUpdate(BaseModel):
    """Модель для обновления настроек AI"""
    default_model: str = Field(..., description="Модель по умолчанию")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(..., gt=0, description="Максимальное количество токенов")

    provider: str = Field(..., description="Провайдер AI")
    openrouter_api_key: str = Field(None, description="API ключ OpenRouter")
    openai_api_key: str = Field(None, description="API ключ OpenAI")
    huggingface_api_key: str = Field(None, description="API ключ HuggingFace")

    auto_reply_enabled: bool = Field(..., description="Включить автоответы")
    auto_reply_temperature: float = Field(..., ge=0.0, le=2.0, description="Температура для автоответов")
    auto_reply_max_tokens: int = Field(..., gt=0, description="Максимум токенов для автоответов")

    rate_limit_per_minute: int = Field(..., gt=0, description="Лимит запросов в минуту")
    cache_enabled: bool = Field(..., description="Включить кеширование")
    log_level: str = Field(..., description="Уровень логирования")

    fallback_model: str = Field(None, description="Резервная модель")
    premium_model: str = Field(None, description="Премиум модель")


class AISettingsResponse(BaseModel):
    """Модель ответа с настройками AI"""
    id: int
    default_model: str
    temperature: float
    max_tokens: int
    provider: str
    auto_reply_enabled: bool
    auto_reply_temperature: float
    auto_reply_max_tokens: int
    rate_limit_per_minute: int
    cache_enabled: bool
    log_level: str
    fallback_model: str = None
    premium_model: str = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/ai-settings",
    tags=["AI Settings"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings(db: AsyncSession = Depends(get_db)):
    """Получить текущие настройки AI"""
    settings = await AISettingsService.get_or_create_settings(db)
    return AISettingsResponse.from_orm(settings)


@router.put("/", response_model=AISettingsResponse)
async def update_ai_settings(
    updates: AISettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки AI"""
    # Получаем текущие настройки
    current_settings = await AISettingsService.get_or_create_settings(db)

    # Обновляем настройки
    updated_settings = await AISettingsService.update_settings(
        db, current_settings.id, updates.dict(exclude_unset=True)
    )

    if not updated_settings:
        raise HTTPException(status_code=400, detail="Не удалось обновить настройки")

    return AISettingsResponse.from_orm(updated_settings)


@router.get("/model-config")
async def get_model_config(db: AsyncSession = Depends(get_db)):
    """Получить конфигурацию текущей модели"""
    return await AISettingsService.get_current_model_config(db)


@router.get("/auto-reply-config")
async def get_auto_reply_config(db: AsyncSession = Depends(get_db)):
    """Получить конфигурацию автоответов"""
    return await AISettingsService.get_auto_reply_config(db)


@router.get("/rate-limit")
async def get_rate_limit(db: AsyncSession = Depends(get_db)):
    """Получить текущий лимит запросов"""
    rate_limit = await AISettingsService.get_rate_limit(db)
    return {"rate_limit_per_minute": rate_limit}


@router.get("/cache-enabled")
async def is_cache_enabled(db: AsyncSession = Depends(get_db)):
    """Проверить, включено ли кеширование"""
    cache_enabled = await AISettingsService.is_cache_enabled(db)
    return {"cache_enabled": cache_enabled}
