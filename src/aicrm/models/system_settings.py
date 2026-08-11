"""
Модель системных настроек
"""

from sqlalchemy import JSON, Boolean, Column, Integer, String, Text

from .base import BaseModel


class SystemSettings(BaseModel):
    """Модель глобальных системных настроек"""

    __tablename__ = "system_settings"

    # Общие настройки
    site_name = Column(String, nullable=False, default="AICRM")
    site_description = Column(Text, nullable=True)
    admin_email = Column(String, nullable=True)
    support_email = Column(String, nullable=True)

    # Настройки безопасности
    session_timeout_minutes = Column(Integer, nullable=False, default=60)
    max_login_attempts = Column(Integer, nullable=False, default=5)
    lockout_duration_minutes = Column(Integer, nullable=False, default=15)
    password_min_length = Column(Integer, nullable=False, default=8)
    require_2fa = Column(Boolean, default=False)

    # Настройки мониторинга
    enable_monitoring = Column(Boolean, default=True)
    monitoring_interval_seconds = Column(Integer, default=60)
    alert_email_enabled = Column(Boolean, default=True)
    performance_thresholds = Column(
        JSON, nullable=True
    )  # {"cpu_percent": 80, "memory_percent": 85}

    # Настройки логирования
    log_level = Column(String, default="INFO")
    log_retention_days = Column(Integer, default=30)
    enable_audit_log = Column(Boolean, default=True)

    # Настройки кэширования
    redis_enabled = Column(Boolean, default=True)
    redis_host = Column(String, default="localhost")
    redis_port = Column(Integer, default=6379)
    cache_ttl_seconds = Column(Integer, default=3600)

    # Email SMTP настройки (инкапсулированные)
    smtp_enabled = Column(Boolean, default=False)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True, default=587)
    smtp_user = Column(String, nullable=True)
    smtp_password = Column(Text, nullable=True)  # Зашифрованный
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    smtp_from_email = Column(String, nullable=True)
    smtp_from_name = Column(String, nullable=True)

    # Telegram настройки
    telegram_enabled = Column(Boolean, default=False)
    telegram_bot_token = Column(Text, nullable=True)  # Зашифрованный
    telegram_chat_id = Column(String, nullable=True)
    telegram_webhook_url = Column(String, nullable=True)
    telegram_notification_enabled = Column(Boolean, default=True)

    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True)
    email_notifications_enabled = Column(Boolean, default=True)
    websocket_notifications_enabled = Column(Boolean, default=True)
    push_notifications_enabled = Column(Boolean, default=False)

    # Контакты для уведомлений об ошибках
    admin_contacts = Column(
        JSON, nullable=True
    )  # [{"email": "...", "telegram_id": "...", "phone": "..."}]
    critical_contacts = Column(
        JSON, nullable=True
    )  # [{"email": "...", "telegram_id": "...", "phone": "..."}]

    # Настройки бэкапа
    auto_backup_enabled = Column(Boolean, default=True)
    backup_frequency_hours = Column(Integer, default=24)
    backup_retention_days = Column(Integer, default=7)
    backup_path = Column(String, nullable=True)

    # Настройки обновлений
    auto_update_enabled = Column(Boolean, default=False)
    update_check_frequency_hours = Column(Integer, default=24)
    update_channel = Column(String, default="stable")  # stable, beta, nightly

    def __repr__(self) -> str:
        return f"<SystemSettings(id={self.id}, site_name={self.site_name})>"
