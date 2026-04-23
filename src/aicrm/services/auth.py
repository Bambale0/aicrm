"""
Сервис аутентификации
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import User


class AuthService:
    """Сервис для работы с аутентификацией"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """Получение текущего пользователя по токену"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            email: str = payload.get("sub")
            if email is None:
                return None
        except JWTError:
            return None

        user = db.query(User).filter(User.email == email).first()
        return user

    @staticmethod
    def create_user(db: Session, user_data: dict) -> User:
        """Создание нового пользователя"""
        hashed_password = User.get_password_hash(user_data.pop("password"))
        user_data["hashed_password"] = hashed_password

        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


auth_service = AuthService()
