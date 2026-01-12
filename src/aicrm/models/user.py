"""
Модель пользователя
"""

from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from .base import BaseModel

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class User(BaseModel):
    """Модель пользователя системы"""

    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    company_name = Column(String)  # Название компании
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # admin, manager, user

    # Email verification
    email_verified = Column(Boolean, default=False)  # Подтвержден ли email
    email_verification_token = Column(String, nullable=True)  # Токен подтверждаения
    email_verification_expires = Column(DateTime, nullable=True)  # Срок действия токена

    # Связи
    tasks = relationship(
        "Task", foreign_keys="[Task.assigned_to]", back_populates="assigned_to_user"
    )
    production_steps = relationship("ProductionStep", back_populates="assigned_to_user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хеширование пароля"""
        # Ограничиваем длину пароля 72 байтами для bcrypt
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode("utf-8", errors="ignore")
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(password, self.hashed_password)

    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role})>"
