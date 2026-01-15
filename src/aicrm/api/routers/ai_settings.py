"""
API роутер для управления настройками AI
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...services.ai_settings_service import AISettingsService


class AISettingsUpdate(BaseModel):
    """Модель для обновления настроек AI"""

    default_model: Optional[str] = Field(None, description="Модель по умолчанию")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Температура генерации"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, description="Максимальное количество токенов"
    )

    provider: Optional[str] = Field(None, description="Провайдер AI")
    openrouter_api_key: Optional[str] = Field(None, description="API ключ OpenRouter")
    openai_api_key: Optional[str] = Field(None, description="API ключ OpenAI")
    huggingface_api_key: Optional[str] = Field(None, description="API ключ HuggingFace")

    auto_reply_enabled: Optional[bool] = Field(None, description="Включить автоответы")
    auto_reply_temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Температура для автоответов"
    )
    auto_reply_max_tokens: Optional[int] = Field(
        None, gt=0, description="Максимум токенов для автоответов"
    )

    rate_limit_per_minute: Optional[int] = Field(
        None, gt=0, description="Лимит запросов в минуту"
    )
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
    prefix="/ai/settings",
    tags=["AI Settings"],
    responses={404: {"description": "Not found"}},
)


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"


# Импорты для аутентификации
from ...core.dependencies import get_current_user
from ...models.user import User


@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> AISettingsResponse:
    """
    Получить текущие настройки AI
    """
    service = AISettingsService()
    settings = service.get_or_create_settings(db)
    return AISettingsResponse.from_orm(settings)


@router.put("/", response_model=AISettingsResponse)
async def update_ai_settings(
    updates: AISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    """
    Обновить настройки AI
    """
    service = AISettingsService()

    # Проверка прав администратора для обновления API ключей
    if any(
        key in updates.dict(exclude_unset=True)
        for key in ["openrouter_api_key", "openai_api_key", "huggingface_api_key"]
    ):
        if not hasattr(current_user, "role") or current_user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Admin required to update API keys"
            )

    settings = service.get_or_create_settings(db)
    updated = service.update_settings(db, settings.id, updates.dict(exclude_unset=True))

    if not updated:
        raise HTTPException(status_code=400, detail="No valid updates provided")

    return AISettingsResponse.from_orm(updated)


@router.post("/reset")
async def reset_ai_settings_to_defaults(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Сбросить настройки AI к значениям по умолчанию
    """
    service = AISettingsService()
    default_settings = service.reset_to_defaults(db)
    return {
        "message": "AI settings reset to defaults",
        "settings": AISettingsResponse.from_orm(default_settings),
    }


@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получить список доступных моделей AI
    """
    service = AISettingsService()
    return {
        "models": service.get_model_list(db),
        "current": service.get_current_model_config(db),
    }


@router.post("/validate-keys")
async def validate_api_keys(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Проверить валидность API ключей
    """
    service = AISettingsService()
    validation_results = service.validate_api_keys(db)
    return {
        "validation": validation_results,
        "valid_keys": [k for k, v in validation_results.items() if v],
    }


@router.get("/config")
async def get_model_config(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получить текущую конфигурацию модели для API
    """
    service = AISettingsService()
    return service.get_current_model_config(db)


@router.get("/auto-reply/config")
async def get_auto_reply_config(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию автоответов
    """
    service = AISettingsService()
    return service.get_auto_reply_config(db)


# Специфические эндпоинты для разных настроек
class OpenRouterSettingsUpdate(BaseModel):
    """Модель для обновления настроек OpenRouter"""

    openrouter_api_key: Optional[str] = Field(None, description="API ключ OpenRouter")
    default_model: Optional[str] = Field(None, description="Модель по умолчанию")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Температура генерации"
    )


@router.get("/openrouter", response_model=OpenRouterSettingsUpdate)
async def get_openrouter_settings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получить настройки OpenRouter
    """
    service = AISettingsService()
    settings = service.get_or_create_settings(db)
    return {
        "openrouter_api_key": getattr(settings, "openrouter_api_key", None),
        "default_model": settings.default_model,
        "temperature": settings.temperature,
    }


@router.put("/openrouter")
async def update_openrouter_settings(
    updates: OpenRouterSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновить настройки OpenRouter
    """
    if not hasattr(current_user, "role") or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")

    service = AISettingsService()
    settings = service.get_or_create_settings(db)
    update_dict = updates.dict(exclude_unset=True)
    service.update_settings(db, settings.id, update_dict)

    return {"message": "OpenRouter settings updated"}


class RateLimitSettings(BaseModel):
    """Модель для настроек лимитов"""

    rate_limit_per_minute: Optional[int] = Field(
        None, gt=0, description="Лимит запросов в минуту"
    )
    cache_enabled: Optional[bool] = Field(None, description="Включить кеширование")


@router.get("/limits", response_model=RateLimitSettings)
async def get_limits_settings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получить настройки лимитов
    """
    service = AISettingsService()
    settings = service.get_or_create_settings(db)
    return {
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cache_enabled": settings.cache_enabled,
    }


@router.put("/limits")
async def update_limits_settings(
    updates: RateLimitSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновить настройки лимитов
    """
    if not hasattr(current_user, "role") or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")

    service = AISettingsService()
    settings = service.get_or_create_settings(db)
    update_dict = updates.dict(exclude_unset=True)
    service.update_settings(db, settings.id, update_dict)

    return {"message": "Limits settings updated"}
