"""
Схемы для аутентификации
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    role: str = "user"


class UserCreate(UserBase):
    """Схема создания пользователя"""

    password: str


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class User(UserBase):
    """Схема пользователя для ответов"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
