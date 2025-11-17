"""
Сервис для управления пользователями
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.user import User
from ..core.database import get_db


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить список пользователей"""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: dict) -> User:
        """Создать нового пользователя"""
        # Хеширование пароля
        if "password" in user_data:
            user_data["hashed_password"] = User.get_password_hash(user_data.pop("password"))

        user = User(**user_data)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("User with this email already exists")

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: dict) -> Optional[User]:
        """Обновить пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Хеширование пароля, если он обновляется
        if "password" in user_data:
            user_data["hashed_password"] = User.get_password_hash(user_data.pop("password"))

        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Email already taken by another user")

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Удалить пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def get_user_count(db: Session) -> int:
        """Получить количество пользователей"""
        return db.query(User).count()


user_service = UserService()
