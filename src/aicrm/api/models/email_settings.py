"""Модель настроек email"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from .base import Base


class EmailSettings(Base):
    """Настройки email для пользователя"""

    __tablename__ = "email_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, nullable=False, index=True
    )  # ID пользователя из user таблицы

    # SMTP настройки
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), nullable=False)
    smtp_password = Column(
        Text, nullable=False
    )  # Храним зашифрованным в реальной системе
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)

    # IMAP настройки
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, default=993)
    imap_username = Column(String(255), nullable=False)
    imap_password = Column(Text, nullable=False)  # Храним зашифрованным
    imap_use_ssl = Column(Boolean, default=True)

    # Общие настройки
    default_from_email = Column(String(255), nullable=False)
    default_from_name = Column(String(255))
    signature = Column(Text)

    # Автоответчик
    auto_reply_enabled = Column(Boolean, default=False)
    auto_reply_message = Column(Text)

    # Статус
    is_active = Column(Boolean, default=True)  # Включены ли данные настройки
    test_status = Column(
        String(50), default="not_tested"
    )  # "not_tested", "passed", "failed"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EmailSettings(user_id={self.user_id}, smtp_host='{self.smtp_host}', is_active={self.is_active})>"
