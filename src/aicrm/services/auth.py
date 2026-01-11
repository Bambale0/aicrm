"""
Сервис аутентификации с поддержкой сессий
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import User
from ..utils.logging import get_logger
from .session_service import session_service

logger = get_logger(__name__)


class AuthService:
    """Сервис для работы с аутентификацией"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
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
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
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

    @staticmethod
    async def authenticate_user_async(
        db: Session, email: str, password: str
    ) -> Optional[User]:
        """Асинхронная версия аутентификации пользователя"""
        return await asyncio.to_thread(
            AuthService.authenticate_user, db, email, password
        )

    @staticmethod
    async def get_current_user_async(db: Session, token: str) -> Optional[User]:
        """Асинхронная версия получения пользователя по токену"""
        return await asyncio.to_thread(AuthService.get_current_user, db, token)

    @staticmethod
    async def create_user_async(db: Session, user_data: dict) -> User:
        """Асинхронная версия создания пользователя"""
        return await asyncio.to_thread(AuthService.create_user, db, user_data)

    @staticmethod
    async def login_with_session(
        db: Session, email: str, password: str, request: Request = None
    ) -> Optional[Dict[str, Any]]:
        """Аутентификация с созданием сессии"""
        user = await AuthService.authenticate_user_async(db, email, password)
        if not user:
            logger.warning("Failed login attempt", email=email)
            return None

        # Собираем данные для сессии
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "ip_address": request.client.host if request else None,
            "user_agent": request.headers.get("user-agent") if request else None,
        }

        # Создаем сессию в Redis
        async with session_service:
            session_id = await session_service.create_session(user.id, user_data)

        # Создаем JWT токен
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "session_id": session_id}
        )

        logger.info(
            "User logged in successfully",
            user_id=user.id,
            email=email,
            session_id=session_id,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data,
            "session_id": session_id,
        }

    @staticmethod
    async def get_current_user_from_session(
        session_id: str, db: Session
    ) -> Optional[User]:
        """Получение пользователя по сессии"""
        async with session_service:
            session_data = await session_service.get_session(session_id)

        if not session_data:
            return None

        user_id = session_data["user_id"]
        # Используем асинхронную версию для получения пользователя
        user = await asyncio.to_thread(
            lambda: db.query(User).filter(User.id == user_id).first()
        )

        if user:
            logger.debug(
                "User retrieved from session", user_id=user_id, session_id=session_id
            )

        return user

    @staticmethod
    async def logout_session(session_id: str) -> bool:
        """Выход из системы с удалением сессии"""
        async with session_service:
            success = await session_service.delete_session(session_id)

        if success:
            logger.info("User logged out", session_id=session_id)

        return success

    @staticmethod
    async def logout_all_sessions(user_id: int) -> int:
        """Выход из всех сессий пользователя"""
        async with session_service:
            count = await session_service.delete_user_sessions(user_id)

        logger.info(
            "User logged out from all sessions", user_id=user_id, sessions_count=count
        )
        return count


auth_service = AuthService()
