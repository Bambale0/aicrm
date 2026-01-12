"""
Схемы для аутентификации
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None  # Название компании
    email_verified: bool = False  # Подтвержден ли email
    is_active: bool = True
    is_superuser: bool = False
    role: str = "user"


class UserCreate(UserBase):
    """Схема создания пользователя"""

    password: str


class UserRegister(UserBase):
    """Схема регистрации пользователя"""

    password: str


class EmailVerificationRequest(BaseModel):
    """Схема запроса верификации email"""

    token: str


class ResendVerificationRequest(BaseModel):
    """Схема запроса повторной отправки верификации"""

    email: EmailStr


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    """Схема пользователя для ответов"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Схема токена"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные токена"""

    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Запрос на вход"""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Ответ на вход с сессией"""

    access_token: str
    token_type: str = "bearer"
    user: dict
    session_id: str


class SessionInfo(BaseModel):
    """Информация о сессии"""

    session_id: str
    user_id: int
    created_at: str
    last_activity: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
