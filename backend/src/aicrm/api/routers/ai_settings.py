"""
API роутер для управления настройками AI
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.dependencies import get_db
from ...services.ai_settings_service import AISettingsService
from pydantic import BaseModel, Field


class AISettingsUpdate(BaseModel):
    """Модель для обновления настроек AI"""
    default_model: Optional[str] = Field(None, description="Модель по умолчанию")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: Optional[int] = Field(None, gt=0, description="Максимальное количество токенов")

    provider: Optional[str] = Field(None, description="Провайдер AI")
    openrouter_api_key: Optional[str] = Field(None, description="API ключ OpenRouter")
    openai_api_key: Optional[str] = Field(None, description="API ключ OpenAI")
    huggingface_api_key: Optional[str] = Field(None, description="API ключ HuggingFace")

    auto_reply_enabled: Optional[bool] = Field(None, description="Включить автоответы")
    auto_reply_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Температура для автоответов")
    auto_reply_max_tokens: Optional[int] = Field(None, gt=0, description="Максимум токенов для автоответов")

    rate_limit_per_minute: Optional[int] = Field(None, gt=0, description="Лимит запросов в минуту")
    cache_enabled: Optional[bool] = Field(None, description="Включить кеширование")
    log_level: Optional[str] = Field(None, description="Уровень логирования")

    fallback_model: Optional[str] = Field(None, description="Резервная модель")
    premium_model: Optional[str] = Field(None, description="Премиум модель")

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля для гибкости


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
    fallback_model: Optional[str] = None
    premium_model: Optional[str] = None
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
async def get_ai_settings(db: Session = Depends(get_db)):
    """Получить текущие настройки AI"""
    settings = AISettingsService.get_or_create_settings(db)
    # Конвертируем datetime в строки
    settings_dict = {
        "id": settings.id,
        "default_model": settings.default_model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "provider": settings.provider,
        "auto_reply_enabled": settings.auto_reply_enabled,
        "auto_reply_temperature": settings.auto_reply_temperature,
        "auto_reply_max_tokens": settings.auto_reply_max_tokens,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cache_enabled": settings.cache_enabled,
        "log_level": settings.log_level,
        "fallback_model": settings.fallback_model,
        "premium_model": settings.premium_model,
        "created_at": settings.created_at.isoformat() if settings.created_at else None,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
    }
    return AISettingsResponse(**settings_dict)


@router.put("/", response_model=AISettingsResponse)
async def update_ai_settings(
    updates: AISettingsUpdate,
    db: Session = Depends(get_db)
):
    """Обновить настройки AI"""
    # Получаем текущие настройки
    current_settings = AISettingsService.get_or_create_settings(db)

    # Получаем данные для обновления, исключая None значения
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if update_data:  # Проверяем, что есть что обновлять
        updated_settings = AISettingsService.update_settings(
            db, current_settings.id, update_data
        )
        if not updated_settings:
            raise HTTPException(status_code=400, detail="Не удалось обновить настройки")
    else:
        # Если нет изменений, возвращаем текущие настройки
        updated_settings = current_settings

    # Конвертируем datetime в строки для ответа
    settings_dict = {
        "id": updated_settings.id,
        "default_model": updated_settings.default_model,
        "temperature": updated_settings.temperature,
        "max_tokens": updated_settings.max_tokens,
        "provider": updated_settings.provider,
        "auto_reply_enabled": updated_settings.auto_reply_enabled,
        "auto_reply_temperature": updated_settings.auto_reply_temperature,
        "auto_reply_max_tokens": updated_settings.auto_reply_max_tokens,
        "rate_limit_per_minute": updated_settings.rate_limit_per_minute,
        "cache_enabled": updated_settings.cache_enabled,
        "log_level": updated_settings.log_level,
        "fallback_model": updated_settings.fallback_model,
        "premium_model": updated_settings.premium_model,
        "created_at": updated_settings.created_at.isoformat() if updated_settings.created_at else None,
        "updated_at": updated_settings.updated_at.isoformat() if updated_settings.updated_at else None
    }
    return AISettingsResponse(**settings_dict)


@router.post("/update", response_model=AISettingsResponse)
async def partial_update_ai_settings(
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Частично обновить настройки AI (POST для совместимости)"""
    # Получаем текущие настройки
    current_settings = AISettingsService.get_or_create_settings(db)

    # Фильтруем только допустимые поля
    allowed_fields = {
        'default_model', 'temperature', 'max_tokens',
        'openrouter_api_key', 'openai_api_key', 'huggingface_api_key',
        'provider', 'auto_reply_enabled', 'auto_reply_temperature',
        'auto_reply_max_tokens', 'rate_limit_per_minute',
        'cache_enabled', 'log_level', 'fallback_model', 'premium_model'
    }

    update_data = {k: v for k, v in updates.items() if k in allowed_fields}

    if update_data:  # Проверяем, что есть что обновлять
        updated_settings = AISettingsService.update_settings(
            db, current_settings.id, update_data
        )
        if not updated_settings:
            raise HTTPException(status_code=400, detail="Не удалось обновить настройки")
    else:
        # Если нет изменений, возвращаем текущие настройки
        updated_settings = current_settings

    # Конвертируем datetime в строки для ответа
    settings_dict = {
        "id": updated_settings.id,
        "default_model": updated_settings.default_model,
        "temperature": updated_settings.temperature,
        "max_tokens": updated_settings.max_tokens,
        "provider": updated_settings.provider,
        "auto_reply_enabled": updated_settings.auto_reply_enabled,
        "auto_reply_temperature": updated_settings.auto_reply_temperature,
        "auto_reply_max_tokens": updated_settings.auto_reply_max_tokens,
        "rate_limit_per_minute": updated_settings.rate_limit_per_minute,
        "cache_enabled": updated_settings.cache_enabled,
        "log_level": updated_settings.log_level,
        "fallback_model": updated_settings.fallback_model,
        "premium_model": updated_settings.premium_model,
        "created_at": updated_settings.created_at.isoformat() if updated_settings.created_at else None,
        "updated_at": updated_settings.updated_at.isoformat() if updated_settings.updated_at else None
    }
    return AISettingsResponse(**settings_dict)


@router.patch("/", response_model=AISettingsResponse)
async def patch_ai_settings(
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Частично обновить настройки AI"""
    # Получаем текущие настройки
    current_settings = AISettingsService.get_or_create_settings(db)

    # Фильтруем только допустимые поля
    allowed_fields = {
        'default_model', 'temperature', 'max_tokens',
        'openrouter_api_key', 'openai_api_key', 'huggingface_api_key',
        'provider', 'auto_reply_enabled', 'auto_reply_temperature',
        'auto_reply_max_tokens', 'rate_limit_per_minute',
        'cache_enabled', 'log_level', 'fallback_model', 'premium_model'
    }

    update_data = {k: v for k, v in updates.items() if k in allowed_fields}

    if update_data:  # Проверяем, что есть что обновлять
        updated_settings = AISettingsService.update_settings(
            db, current_settings.id, update_data
        )
        if not updated_settings:
            raise HTTPException(status_code=400, detail="Не удалось обновить настройки")
    else:
        # Если нет изменений, возвращаем текущие настройки
        updated_settings = current_settings

    # Конвертируем datetime в строки для ответа
    settings_dict = {
        "id": updated_settings.id,
        "default_model": updated_settings.default_model,
        "temperature": updated_settings.temperature,
        "max_tokens": updated_settings.max_tokens,
        "provider": updated_settings.provider,
        "auto_reply_enabled": updated_settings.auto_reply_enabled,
        "auto_reply_temperature": updated_settings.auto_reply_temperature,
        "auto_reply_max_tokens": updated_settings.auto_reply_max_tokens,
        "rate_limit_per_minute": updated_settings.rate_limit_per_minute,
        "cache_enabled": updated_settings.cache_enabled,
        "log_level": updated_settings.log_level,
        "fallback_model": updated_settings.fallback_model,
        "premium_model": updated_settings.premium_model,
        "created_at": updated_settings.created_at.isoformat() if updated_settings.created_at else None,
        "updated_at": updated_settings.updated_at.isoformat() if updated_settings.updated_at else None
    }
    return AISettingsResponse(**settings_dict)


@router.get("/model-config")
async def get_model_config(db: Session = Depends(get_db)):
    """Получить конфигурацию текущей модели"""
    return AISettingsService.get_current_model_config(db)


@router.get("/auto-reply-config")
async def get_auto_reply_config(db: Session = Depends(get_db)):
    """Получить конфигурацию автоответов"""
    return AISettingsService.get_auto_reply_config(db)


@router.get("/rate-limit")
async def get_rate_limit(db: Session = Depends(get_db)):
    """Получить текущий лимит запросов"""
    rate_limit = AISettingsService.get_rate_limit(db)
    return {"rate_limit_per_minute": rate_limit}


@router.get("/cache-enabled")
async def is_cache_enabled(db: Session = Depends(get_db)):
    """Проверить, включено ли кеширование"""
    cache_enabled = AISettingsService.is_cache_enabled(db)
    return {"cache_enabled": cache_enabled}
