"""
Модель Telegram чата
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class TelegramChat(BaseModel):
    """Модель для хранения информации о Telegram чатах"""

    __tablename__ = "telegram_chats"

    chat_id = Column(
        String, nullable=False, unique=True, index=True
    )  # Telegram chat ID
    chat_type = Column(String, nullable=False)  # private, group, supergroup, channel
    title = Column(String)  # Название чата (для групп)
    username = Column(String)  # Username пользователя (для приватных чатов)
    first_name = Column(String)  # Имя пользователя
    last_name = Column(String)  # Фамилия пользователя

    # Связь с клиентом CRM
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    customer = relationship("Customer", back_populates="telegram_chats")

    # Статус подписки
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)

    # Настройки
    language = Column(String, default="ru")
    notifications_enabled = Column(Boolean, default=True)

    # Статистика
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime)

    @property
    def display_name(self) -> str:
        """Человеко-читаемое имя чата"""
        if self.chat_type == "private":
            name_parts = []
            if self.first_name:
                name_parts.append(self.first_name)
            if self.last_name:
                name_parts.append(self.last_name)
            if self.username:
                name_parts.append(f"(@{self.username})")
            return " ".join(name_parts) if name_parts else f"Chat {self.chat_id}"
        else:
            return self.title or f"{self.chat_type.title()} {self.chat_id}"

    @property
    def is_private(self) -> bool:
        """Проверка, является ли чат приватным"""
        return self.chat_type == "private"

    def increment_message_count(self):
        """Увеличение счетчика сообщений"""
        self.message_count += 1
        self.last_message_at = self.updated_at

    def __repr__(self) -> str:
        return f"<TelegramChat(chat_id={self.chat_id}, type={self.chat_type}, customer_id={self.customer_id})>"
