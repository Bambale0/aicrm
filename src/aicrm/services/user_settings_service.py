"""
Сервис для управления пользовательскими настройками
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..models.user_settings import UserSettings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class UserSettingsService:
    """Сервис для работы с пользовательскими настройками"""

    @staticmethod
    def get_user_settings(db: Session, user_id: int) -> Optional[UserSettings]:
        """Получение настроек пользователя"""
        return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    @staticmethod
    def create_user_settings(
        db: Session, user_id: int, settings_data: Dict[str, Any]
    ) -> UserSettings:
        """Создание настроек для пользователя"""
        settings = UserSettings(user_id=user_id, **settings_data)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info(f"Created user settings for user {user_id}")
        return settings

    @staticmethod
    def update_user_settings(
        db: Session, user_id: int, updates: Dict[str, Any]
    ) -> Optional[UserSettings]:
        """Обновление настроек пользователя"""
        settings = UserSettingsService.get_user_settings(db, user_id)
        if not settings:
            # Создаем настройки по умолчанию, если не существуют
            settings = UserSettingsService.create_user_settings(db, user_id, {})

        # Обновляем поля
        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        db.commit()
        db.refresh(settings)
        logger.info(f"Updated user settings for user {user_id}")
        return settings

    @staticmethod
    def get_or_create_user_settings(db: Session, user_id: int) -> UserSettings:
        """Получение или создание настроек пользователя"""
        settings = UserSettingsService.get_user_settings(db, user_id)
        if not settings:
            settings = UserSettingsService.create_user_settings(db, user_id, {})
        return settings

    @staticmethod
    def update_service_settings(
        db: Session, user_id: int, service_name: str, service_settings: Dict[str, Any]
    ) -> UserSettings:
        """Обновление настроек конкретного сервиса"""
        settings = UserSettingsService.get_or_create_user_settings(db, user_id)

        current_service_settings = settings.service_settings or {}
        current_service_settings[service_name] = service_settings
        settings.service_settings = current_service_settings

        db.commit()
        db.refresh(settings)
        logger.info(
            f"Updated service settings for user {user_id}, service {service_name}"
        )
        return settings

    @staticmethod
    def update_process_settings(
        db: Session, user_id: int, process_id: int, process_settings: Dict[str, Any]
    ) -> UserSettings:
        """Обновление настроек конкретного процесса"""
        settings = UserSettingsService.get_or_create_user_settings(db, user_id)

        current_process_settings = settings.process_settings or {}
        current_process_settings[str(process_id)] = process_settings
        settings.process_settings = current_process_settings

        db.commit()
        db.refresh(settings)
        logger.info(
            f"Updated process settings for user {user_id}, process {process_id}"
        )
        return settings

    @staticmethod
    def get_service_settings(
        db: Session, user_id: int, service_name: str
    ) -> Dict[str, Any]:
        """Получение настроек конкретного сервиса"""
        settings = UserSettingsService.get_or_create_user_settings(db, user_id)
        return settings.service_settings.get(service_name, {})

    @staticmethod
    def get_process_settings(
        db: Session, user_id: int, process_id: int
    ) -> Dict[str, Any]:
        """Получение настроек конкретного процесса"""
        settings = UserSettingsService.get_or_create_user_settings(db, user_id)
        return settings.process_settings.get(str(process_id), {})

    @staticmethod
    def reset_user_settings(db: Session, user_id: int) -> UserSettings:
        """Сброс настроек пользователя к значениям по умолчанию"""
        settings = UserSettingsService.get_user_settings(db, user_id)
        if settings:
            # Удаляем существующие настройки
            db.delete(settings)

        # Создаем новые настройки по умолчанию
        default_settings = UserSettings(user_id=user_id)
        db.add(default_settings)
        db.commit()
        db.refresh(default_settings)

        logger.info(f"Reset user settings for user {user_id}")
        return default_settings
