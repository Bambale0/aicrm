"""
Сервис для работы с системными настройками
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models.system_settings import SystemSettings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SystemSettingsService:
    """Сервис для управления системными настройками"""

    @staticmethod
    def get_settings(db: Session) -> Optional[SystemSettings]:
        """Получить текущие системные настройки"""
        result = db.execute(select(SystemSettings).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    def create_default_settings(db: Session) -> SystemSettings:
        """Создать настройки по умолчанию"""
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info("Created default system settings")
        return settings

    @staticmethod
    def get_or_create_settings(db: Session) -> SystemSettings:
        """Получить настройки или создать по умолчанию"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            settings = SystemSettingsService.create_default_settings(db)
        return settings

    @staticmethod
    def update_settings(
        db: Session, settings_id: int, updates: Dict[str, Any]
    ) -> Optional[SystemSettings]:
        """Обновить системные настройки"""
        # Фильтруем только допустимые поля
        allowed_fields = {
            "site_name",
            "site_description",
            "admin_email",
            "support_email",
            "session_timeout_minutes",
            "max_login_attempts",
            "lockout_duration_minutes",
            "password_min_length",
            "require_2fa",
            "enable_monitoring",
            "monitoring_interval_seconds",
            "alert_email_enabled",
            "performance_thresholds",
            "log_level",
            "log_retention_days",
            "enable_audit_log",
            "redis_enabled",
            "redis_host",
            "redis_port",
            "cache_ttl_seconds",
            "smtp_enabled",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_password",
            "smtp_use_tls",
            "smtp_use_ssl",
            "smtp_from_email",
            "smtp_from_name",
            "telegram_enabled",
            "telegram_bot_token",
            "telegram_chat_id",
            "telegram_webhook_url",
            "telegram_notification_enabled",
            "notifications_enabled",
            "email_notifications_enabled",
            "websocket_notifications_enabled",
            "push_notifications_enabled",
            "auto_backup_enabled",
            "backup_frequency_hours",
            "backup_retention_days",
            "backup_path",
            "auto_update_enabled",
            "update_check_frequency_hours",
            "update_channel",
        }

        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return None

        db.execute(
            update(SystemSettings)
            .where(SystemSettings.id == settings_id)
            .values(**filtered_updates)
        )
        db.commit()

        # Возвращаем обновленные настройки
        result = db.execute(
            select(SystemSettings).where(SystemSettings.id == settings_id)
        )
        updated_settings = result.scalar_one_or_none()
        logger.info(f"Updated system settings: {list(filtered_updates.keys())}")
        return updated_settings

    @staticmethod
    def save_settings(db: Session, settings_data: Dict[str, Any]) -> SystemSettings:
        """
        Сохранить настройки системы (создать или обновить)

        Args:
            db: Сессия базы данных
            settings_data: Данные настроек

        Returns:
            SystemSettings: Сохраненные настройки
        """
        # Получаем существующие настройки
        existing_settings = SystemSettingsService.get_settings(db)

        if existing_settings:
            # Обновляем существующие
            updated_settings = SystemSettingsService.update_settings(
                db, existing_settings.id, settings_data
            )
            if updated_settings:
                return updated_settings
            else:
                # Если обновление не удалось (нет разрешенных полей), возвращаем существующие
                return existing_settings
        else:
            # Создаем новые настройки
            new_settings = SystemSettings()

            # Фильтруем только допустимые поля
            allowed_fields = {
                "site_name",
                "site_description",
                "admin_email",
                "support_email",
                "session_timeout_minutes",
                "max_login_attempts",
                "lockout_duration_minutes",
                "password_min_length",
                "require_2fa",
                "enable_monitoring",
                "monitoring_interval_seconds",
                "alert_email_enabled",
                "performance_thresholds",
                "log_level",
                "log_retention_days",
                "enable_audit_log",
                "redis_enabled",
                "redis_host",
                "redis_port",
                "cache_ttl_seconds",
                "smtp_enabled",
                "smtp_host",
                "smtp_port",
                "smtp_user",
                "smtp_password",
                "smtp_use_tls",
                "smtp_use_ssl",
                "smtp_from_email",
                "smtp_from_name",
                "telegram_enabled",
                "telegram_bot_token",
                "telegram_chat_id",
                "telegram_webhook_url",
                "telegram_notification_enabled",
                "notifications_enabled",
                "email_notifications_enabled",
                "websocket_notifications_enabled",
                "push_notifications_enabled",
                "auto_backup_enabled",
                "backup_frequency_hours",
                "backup_retention_days",
                "backup_path",
                "auto_update_enabled",
                "update_check_frequency_hours",
                "update_channel",
            }

            # Применяем значения
            for field, value in settings_data.items():
                if field in allowed_fields and hasattr(new_settings, field):
                    setattr(new_settings, field, value)

            db.add(new_settings)
            db.commit()
            db.refresh(new_settings)
            logger.info("Created new system settings")
            return new_settings

    @staticmethod
    def get_smtp_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию SMTP"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "enabled": False,
                "host": None,
                "port": 587,
                "user": None,
                "password": None,
                "use_tls": True,
                "use_ssl": False,
                "from_email": None,
                "from_name": None,
            }

        return {
            "enabled": settings.smtp_enabled,
            "host": settings.smtp_host,
            "port": settings.smtp_port or 587,
            "user": settings.smtp_user,
            "password": settings.smtp_password,
            "use_tls": settings.smtp_use_tls,
            "use_ssl": settings.smtp_use_ssl,
            "from_email": settings.smtp_from_email,
            "from_name": settings.smtp_from_name,
        }

    @staticmethod
    def get_telegram_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию Telegram"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "enabled": False,
                "bot_token": None,
                "chat_id": None,
                "webhook_url": None,
                "notification_enabled": True,
            }

        return {
            "enabled": settings.telegram_enabled,
            "bot_token": settings.telegram_bot_token,
            "chat_id": settings.telegram_chat_id,
            "webhook_url": settings.telegram_webhook_url,
            "notification_enabled": settings.telegram_notification_enabled,
        }

    @staticmethod
    def get_security_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию безопасности"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "session_timeout_minutes": 60,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 15,
                "password_min_length": 8,
                "require_2fa": False,
            }

        return {
            "session_timeout_minutes": settings.session_timeout_minutes,
            "max_login_attempts": settings.max_login_attempts,
            "lockout_duration_minutes": settings.lockout_duration_minutes,
            "password_min_length": settings.password_min_length,
            "require_2fa": settings.require_2fa,
        }

    @staticmethod
    def get_monitoring_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию мониторинга"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "enabled": True,
                "interval_seconds": 60,
                "alert_email_enabled": True,
                "performance_thresholds": {"cpu_percent": 80, "memory_percent": 85},
            }

        return {
            "enabled": settings.enable_monitoring,
            "interval_seconds": settings.monitoring_interval_seconds,
            "alert_email_enabled": settings.alert_email_enabled,
            "performance_thresholds": settings.performance_thresholds
            or {"cpu_percent": 80, "memory_percent": 85},
        }

    @staticmethod
    def get_notification_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию уведомлений"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "enabled": True,
                "email_enabled": True,
                "websocket_enabled": True,
                "push_enabled": False,
            }

        return {
            "enabled": settings.notifications_enabled,
            "email_enabled": settings.email_notifications_enabled,
            "websocket_enabled": settings.websocket_notifications_enabled,
            "push_enabled": settings.push_notifications_enabled,
        }

    @staticmethod
    def get_cache_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию кэширования"""
        settings = SystemSettingsService.get_settings(db)
        if not settings:
            return {
                "redis_enabled": True,
                "redis_host": "localhost",
                "redis_port": 6379,
                "cache_ttl_seconds": 3600,
            }

        return {
            "redis_enabled": settings.redis_enabled,
            "redis_host": settings.redis_host,
            "redis_port": settings.redis_port,
            "cache_ttl_seconds": settings.cache_ttl_seconds,
        }

    @staticmethod
    def test_smtp_connection(db: Session) -> Dict[str, bool]:
        """
        Тестировать SMTP подключение

        Returns:
            Dict с результатом теста
        """
        try:
            config = SystemSettingsService.get_smtp_config(db)
            if not config["enabled"] or not config["host"]:
                return {"success": False, "message": "SMTP not configured"}

            import smtplib

            if config["use_ssl"]:
                server = smtplib.SMTP_SSL(config["host"], config["port"])
            else:
                server = smtplib.SMTP(config["host"], config["port"])
                if config["use_tls"]:
                    server.starttls()

            if config["user"] and config["password"]:
                server.login(config["user"], config["password"])

            server.quit()
            return {"success": True, "message": "SMTP connection successful"}

        except Exception as e:
            logger.error(f"SMTP test failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def test_telegram_connection(db: Session) -> Dict[str, bool]:
        """
        Тестировать Telegram подключение

        Returns:
            Dict с результатом теста
        """
        try:
            config = SystemSettingsService.get_telegram_config(db)
            if not config["enabled"] or not config["bot_token"]:
                return {"success": False, "message": "Telegram not configured"}

            # Простая проверка токена (можно расширить до реального API вызова)
            if len(config["bot_token"].split(":")) != 2:
                return {"success": False, "message": "Invalid bot token format"}

            return {"success": True, "message": "Telegram token format valid"}

        except Exception as e:
            logger.error(f"Telegram test failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def reset_to_defaults(db: Session) -> SystemSettings:
        """
        Сбросить настройки к значениям по умолчанию

        Returns:
            SystemSettings: Настройки по умолчанию
        """
        default_settings = {
            "site_name": "AICRM",
            "site_description": "AI-powered Communication Relationship Manager",
            "session_timeout_minutes": 60,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 15,
            "password_min_length": 8,
            "require_2fa": False,
            "enable_monitoring": True,
            "monitoring_interval_seconds": 60,
            "alert_email_enabled": True,
            "performance_thresholds": {"cpu_percent": 80, "memory_percent": 85},
            "log_level": "INFO",
            "log_retention_days": 30,
            "enable_audit_log": True,
            "redis_enabled": True,
            "redis_host": "localhost",
            "redis_port": 6379,
            "cache_ttl_seconds": 3600,
            "smtp_enabled": False,
            "notifications_enabled": True,
            "email_notifications_enabled": True,
            "websocket_notifications_enabled": True,
            "push_notifications_enabled": False,
            "auto_backup_enabled": True,
            "backup_frequency_hours": 24,
            "backup_retention_days": 7,
            "auto_update_enabled": False,
            "update_check_frequency_hours": 24,
            "update_channel": "stable",
        }

        return SystemSettingsService.save_settings(db, default_settings)
