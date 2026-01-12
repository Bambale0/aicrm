"""
Pydantic схемы для пользовательских настроек
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class UserSettingsBase(BaseModel):
    """Базовая схема настроек пользователя"""

    timezone: str = Field(default="Europe/Moscow", description="Часовой пояс")
    language: str = Field(default="ru", description="Язык интерфейса")
    theme: str = Field(default="light", description="Тема интерфейса")

    # Настройки уведомлений
    email_notifications: bool = Field(default=True, description="Email уведомления")
    push_notifications: bool = Field(default=True, description="Push уведомления")
    sms_notifications: bool = Field(default=False, description="SMS уведомления")
    telegram_notifications: bool = Field(
        default=True, description="Telegram уведомления"
    )

    # AI настройки
    ai_enabled: bool = Field(default=True, description="Включен ли AI")
    ai_model: str = Field(default="deepseek/deepseek-chat", description="Модель AI")
    ai_temperature: int = Field(
        default=70, ge=0, le=100, description="Температура AI (0-100)"
    )
    ai_max_tokens: int = Field(
        default=4000, description="Максимальное количество токенов"
    )


class UserSettingsCreate(UserSettingsBase):
    """Создание настроек пользователя"""

    pass


class UserSettingsUpdate(BaseModel):
    """Обновление настроек пользователя"""

    timezone: Optional[str] = Field(None, description="Часовой пояс")
    language: Optional[str] = Field(None, description="Язык интерфейса")
    theme: Optional[str] = Field(None, description="Тема интерфейса")

    # Настройки уведомлений
    email_notifications: Optional[bool] = Field(None, description="Email уведомления")
    push_notifications: Optional[bool] = Field(None, description="Push уведомления")
    sms_notifications: Optional[bool] = Field(None, description="SMS уведомления")
    telegram_notifications: Optional[bool] = Field(
        None, description="Telegram уведомления"
    )

    # AI настройки
    ai_enabled: Optional[bool] = Field(None, description="Включен ли AI")
    ai_model: Optional[str] = Field(None, description="Модель AI")
    ai_temperature: Optional[int] = Field(
        None, ge=0, le=100, description="Температура AI (0-100)"
    )
    ai_max_tokens: Optional[int] = Field(
        None, description="Максимальное количество токенов"
    )

    # Расширенные настройки
    service_settings: Optional[Dict[str, Any]] = Field(
        None, description="Настройки сервисов"
    )
    process_settings: Optional[Dict[str, Any]] = Field(
        None, description="Настройки процессов"
    )
    dashboard_layout: Optional[Dict[str, Any]] = Field(
        None, description="Layout дашборда"
    )
    shortcuts: Optional[Dict[str, Any]] = Field(None, description="Горячие клавиши")
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Пользовательские поля"
    )


class UserSettings(UserSettingsBase):
    """Полная схема настроек пользователя"""

    id: int = Field(..., description="ID настройки")
    user_id: int = Field(..., description="ID пользователя")

    # Расширенные настройки
    service_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Настройки сервисов"
    )
    process_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Настройки процессов"
    )
    dashboard_layout: Dict[str, Any] = Field(
        default_factory=dict, description="Layout дашборда"
    )
    shortcuts: Dict[str, Any] = Field(
        default_factory=dict, description="Горячие клавиши"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Пользовательские поля"
    )

    created_at: str = Field(..., description="Дата создания")
    updated_at: str = Field(..., description="Дата обновления")

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Конвертация из ORM объекта с датами"""
        data = {}
        for field in obj.__table__.columns:
            value = getattr(obj, field.name)
            if field.name in ["created_at", "updated_at"] and value:
                data[field.name] = value.isoformat()
            else:
                data[field.name] = value
        return cls(**data)


class ServiceSettingsUpdate(BaseModel):
    """Обновление настроек конкретного сервиса"""

    service_name: str = Field(..., description="Название сервиса")
    settings: Dict[str, Any] = Field(..., description="Настройки сервиса")


class ProcessSettingsUpdate(BaseModel):
    """Обновление настроек конкретного процесса"""

    process_id: int = Field(..., description="ID процесса")
    settings: Dict[str, Any] = Field(..., description="Настройки процесса")
