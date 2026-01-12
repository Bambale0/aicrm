"""
API роутер для управления пользовательскими настройками
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, get_db
from ...models.user import User
from ...schemas.user_settings import (
    ProcessSettingsUpdate,
    ServiceSettingsUpdate,
    UserSettings,
    UserSettingsUpdate,
)
from ...services.user_settings_service import UserSettingsService
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["user-settings"],
    responses={
        401: {"description": "Не авторизован"},
        403: {"description": "Доступ запрещен"},
        404: {"description": "Не найдено"},
    },
)


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"


@router.get("/settings", response_model=UserSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получение настроек текущего пользователя"""
    settings = UserSettingsService.get_or_create_user_settings(db, current_user.id)
    return UserSettings.from_orm(settings)


@router.put("/settings", response_model=UserSettings)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление настроек текущего пользователя"""
    updates = settings_update.dict(exclude_unset=True)
    settings = UserSettingsService.update_user_settings(db, current_user.id, updates)

    if not settings:
        raise HTTPException(status_code=500, detail="Не удалось обновить настройки")

    return UserSettings.from_orm(settings)


@router.post("/settings/reset", response_model=UserSettings)
async def reset_user_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Сброс настроек пользователя к значениям по умолчанию"""
    settings = UserSettingsService.reset_user_settings(db, current_user.id)
    return settings


@router.put("/settings/service", response_model=UserSettings)
async def update_service_settings(
    service_update: ServiceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление настроек конкретного сервиса"""
    settings = UserSettingsService.update_service_settings(
        db, current_user.id, service_update.service_name, service_update.settings
    )
    return settings


@router.get("/settings/service/{service_name}")
async def get_service_settings(
    service_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение настроек конкретного сервиса"""
    settings = UserSettingsService.get_service_settings(
        db, current_user.id, service_name
    )
    return {"service_name": service_name, "settings": settings}


@router.put("/settings/process", response_model=UserSettings)
async def update_process_settings(
    process_update: ProcessSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление настроек конкретного процесса"""
    settings = UserSettingsService.update_process_settings(
        db, current_user.id, process_update.process_id, process_update.settings
    )
    return settings


@router.get("/settings/process/{process_id}")
async def get_process_settings(
    process_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение настроек конкретного процесса"""
    settings = UserSettingsService.get_process_settings(db, current_user.id, process_id)
    return {"process_id": process_id, "settings": settings}


@router.get("/dashboard")
async def get_dashboard_config(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получение конфигурации дашборда пользователя"""
    settings = UserSettingsService.get_or_create_user_settings(db, current_user.id)
    return {
        "layout": settings.dashboard_layout or {},
        "shortcuts": settings.shortcuts or {},
        "custom_fields": settings.custom_fields or {},
    }


@router.put("/dashboard/layout")
async def update_dashboard_layout(
    layout: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление layout дашборда"""
    UserSettingsService.update_user_settings(
        db, current_user.id, {"dashboard_layout": layout}
    )
    return {"message": "Dashboard layout updated", "layout": layout}


@router.put("/dashboard/shortcuts")
async def update_shortcuts(
    shortcuts: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление горячих клавиш"""
    UserSettingsService.update_user_settings(
        db, current_user.id, {"shortcuts": shortcuts}
    )
    return {"message": "Shortcuts updated", "shortcuts": shortcuts}


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получение профиля пользователя с настройками"""
    settings = UserSettingsService.get_or_create_user_settings(db, current_user.id)

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "company_name": current_user.company_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
        },
        "settings": {
            "timezone": settings.timezone,
            "language": settings.language,
            "theme": settings.theme,
            "notifications": {
                "email": settings.email_notifications,
                "push": settings.push_notifications,
                "sms": settings.sms_notifications,
                "telegram": settings.telegram_notifications,
            },
            "ai": {
                "enabled": settings.ai_enabled,
                "model": settings.ai_model,
                "temperature": settings.ai_temperature,
                "max_tokens": settings.ai_max_tokens,
            },
        },
    }