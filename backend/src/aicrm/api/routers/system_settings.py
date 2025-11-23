"""
API роутер для управления системными настройками
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.dependencies import get_db
from ...services.system_settings_service import SystemSettingsService
from pydantic import BaseModel, Field


class SystemSettingsUpdate(BaseModel):
    """Модель для обновления системных настроек"""
    site_name: Optional[str] = Field(None, description="Название сайта")
    site_description: Optional[str] = Field(None, description="Описание сайта")
    admin_email: Optional[str] = Field(None, description="Email администратора")
    support_email: Optional[str] = Field(None, description="Email поддержки")

    session_timeout_minutes: Optional[int] = Field(None, gt=0, description="Таймаут сессии в минутах")
    max_login_attempts: Optional[int] = Field(None, gt=0, description="Максимум попыток входа")
    lockout_duration_minutes: Optional[int] = Field(None, gt=0, description="Длительность блокировки")
    password_min_length: Optional[int] = Field(None, gt=0, description="Минимальная длина пароля")
    require_2fa: Optional[bool] = Field(None, description="Требовать 2FA")

    enable_monitoring: Optional[bool] = Field(None, description="Включить мониторинг")
    monitoring_interval_seconds: Optional[int] = Field(None, gt=0, description="Интервал мониторинга")
    alert_email_enabled: Optional[bool] = Field(None, description="Включить email оповещения")
    performance_thresholds: Optional[Dict[str, Any]] = Field(None, description="Пороги производительности")

    log_level: Optional[str] = Field(None, description="Уровень логирования")
    log_retention_days: Optional[int] = Field(None, gt=0, description="Срок хранения логов")
    enable_audit_log: Optional[bool] = Field(None, description="Включить аудит лог")

    redis_enabled: Optional[bool] = Field(None, description="Включить Redis")
    redis_host: Optional[str] = Field(None, description="Redis хост")
    redis_port: Optional[int] = Field(None, gt=0, lt=65536, description="Redis порт")
    cache_ttl_seconds: Optional[int] = Field(None, gt=0, description="TTL кэша")

    notifications_enabled: Optional[bool] = Field(None, description="Включить уведомления")
    email_notifications_enabled: Optional[bool] = Field(None, description="Email уведомления")
    websocket_notifications_enabled: Optional[bool] = Field(None, description="WebSocket уведомления")
    push_notifications_enabled: Optional[bool] = Field(None, description="Push уведомления")

    auto_backup_enabled: Optional[bool] = Field(None, description="Автобэкап")
    backup_frequency_hours: Optional[int] = Field(None, gt=0, description="Частота бэкапов")
    backup_retention_days: Optional[int] = Field(None, gt=0, description="Срок хранения бэкапов")
    backup_path: Optional[str] = Field(None, description="Путь к бэкапам")

    auto_update_enabled: Optional[bool] = Field(None, description="Автообновления")
    update_check_frequency_hours: Optional[int] = Field(None, gt=0, description="Частота проверки обновлений")
    update_channel: Optional[str] = Field(None, description="Канал обновлений")

    class Config:
        extra = "allow"


class SystemSettingsResponse(BaseModel):
    """Модель ответа с системными настройками"""
    id: int
    site_name: str
    site_description: Optional[str] = None
    admin_email: Optional[str] = None
    support_email: Optional[str] = None
    session_timeout_minutes: int
    max_login_attempts: int
    lockout_duration_minutes: int
    password_min_length: int
    require_2fa: bool
    enable_monitoring: bool
    monitoring_interval_seconds: int
    alert_email_enabled: bool
    performance_thresholds: Optional[Dict[str, Any]] = None
    log_level: str
    log_retention_days: int
    enable_audit_log: bool
    redis_enabled: bool
    redis_host: str
    redis_port: int
    cache_ttl_seconds: int
    notifications_enabled: bool
    email_notifications_enabled: bool
    websocket_notifications_enabled: bool
    push_notifications_enabled: bool
    auto_backup_enabled: bool
    backup_frequency_hours: int
    backup_retention_days: int
    backup_path: Optional[str] = None
    auto_update_enabled: bool
    update_check_frequency_hours: int
    update_channel: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SMTPSettingsUpdate(BaseModel):
    """Модель для обновления SMTP настроек"""
    smtp_enabled: Optional[bool] = Field(None, description="Включить SMTP")
    smtp_host: Optional[str] = Field(None, description="SMTP сервер")
    smtp_port: Optional[int] = Field(None, gt=0, lt=65536, description="SMTP порт")
    smtp_user: Optional[str] = Field(None, description="SMTP пользователь")
    smtp_password: Optional[str] = Field(None, description="SMTP пароль")
    smtp_use_tls: Optional[bool] = Field(None, description="Использовать TLS")
    smtp_use_ssl: Optional[bool] = Field(None, description="Использовать SSL")
    smtp_from_email: Optional[str] = Field(None, description="Email отправителя")
    smtp_from_name: Optional[str] = Field(None, description="Имя отправителя")


class SMTPSettingsResponse(BaseModel):
    """Модель ответа с SMTP настройками"""
    smtp_enabled: bool
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None

    class Config:
        from_attributes = True


class TelegramSettingsUpdate(BaseModel):
    """Модель для обновления Telegram настроек"""
    telegram_enabled: Optional[bool] = Field(None, description="Включить Telegram")
    telegram_bot_token: Optional[str] = Field(None, description="Bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Chat ID")
    telegram_webhook_url: Optional[str] = Field(None, description="Webhook URL")
    telegram_notification_enabled: Optional[bool] = Field(None, description="Включить уведомления")


class TelegramSettingsResponse(BaseModel):
    """Модель ответа с Telegram настройками"""
    telegram_enabled: bool
    telegram_chat_id: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    telegram_notification_enabled: bool

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/settings",
    tags=["System Settings"],
    responses={404: {"description": "Not found"}},
)

# Импорты для аутентификации
from ...core.dependencies import get_current_user
from ...models.user import User

# Общие системные настройки
@router.get("/system/general", response_model=SystemSettingsResponse)
async def get_general_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SystemSettingsResponse:
    """
    Получить общие системные настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    settings = service.get_or_create_settings(db)
    return SystemSettingsResponse.from_orm(settings)

@router.put("/system/general")
async def update_general_settings(
    updates: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить общие системные настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    settings = service.get_or_create_settings(db)
    update_dict = updates.dict(exclude_unset=True)
    updated = service.update_settings(db, settings.id, update_dict)

    return {"message": "General settings updated"}

@router.post("/system/reset")
async def reset_system_settings_to_defaults(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Сбросить системные настройки к значениям по умолчанию
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    default_settings = service.reset_to_defaults(db)
    return {
        "message": "System settings reset to defaults",
        "settings": SystemSettingsResponse.from_orm(default_settings)
    }

# Email/SMTP настройки
@router.get("/email/smtp", response_model=SMTPSettingsResponse)
async def get_smtp_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SMTPSettingsResponse:
    """
    Получить SMTP настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    config = service.get_smtp_config(db)
    return SMTPSettingsResponse(**config)

@router.put("/email/smtp")
async def update_smtp_settings(
    updates: SMTPSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить SMTP настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    settings = service.get_or_create_settings(db)
    update_dict = updates.dict(exclude_unset=True)
    updated = service.update_settings(db, settings.id, update_dict)

    return {"message": "SMTP settings updated"}

@router.post("/email/smtp/test")
async def test_smtp_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Протестировать SMTP подключение
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    result = service.test_smtp_connection(db)
    return result

# Telegram настройки
@router.get("/telegram", response_model=TelegramSettingsResponse)
async def get_telegram_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TelegramSettingsResponse:
    """
    Получить Telegram настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    config = service.get_telegram_config(db)
    return TelegramSettingsResponse(**config)

@router.put("/telegram")
async def update_telegram_settings(
    updates: TelegramSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить Telegram настройки
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    settings = service.get_or_create_settings(db)
    update_dict = updates.dict(exclude_unset=True)
    updated = service.update_settings(db, settings.id, update_dict)

    return {"message": "Telegram settings updated"}

@router.post("/telegram/test")
async def test_telegram_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Протестировать Telegram подключение
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")

    service = SystemSettingsService()
    result = service.test_telegram_connection(db)
    return result

# Конфигурационные эндпоинты
@router.get("/config/security")
async def get_security_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию безопасности
    """
    service = SystemSettingsService()
    return service.get_security_config(db)

@router.get("/config/monitoring")
async def get_monitoring_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию мониторинга
    """
    service = SystemSettingsService()
    return service.get_monitoring_config(db)

@router.get("/config/notifications")
async def get_notifications_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию уведомлений
    """
    service = SystemSettingsService()
    return service.get_notification_config(db)

@router.get("/config/cache")
async def get_cache_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию кэширования
    """
    service = SystemSettingsService()
    return service.get_cache_config(db)
