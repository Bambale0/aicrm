#!/usr/bin/env python3
"""
Скрипт для создания администратора
"""
import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session, sessionmaker

from aicrm.core.database import get_default_engine
from aicrm.models import Base
from aicrm.models.user import User


def create_admin_user():
    """Создание администратора"""
    # Force postgres consistency with app
    import os

    osiron["DATABASE_URL"] = (
        "postgresql+psycopg2://aicrm_user:aicrm_password@localhost:5432/aicrm"
    )

    # Создаем таблицы, если они не существуют
    engine = get_default_engine()
    print(f"Using database: {engine.url}")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()

    try:
        # Проверяем, существует ли уже пользователь
        existing_user = (
            db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()
        )
        if existing_user:
            print("Пользователь уже существует!")
            print(f"Email: {existing_user.email}")
            print(f"Роль: {existing_user.role}")
            print(f"Superuser: {existing_user.is_superuser}")
            # Force recreate if we want to ensure it's in the same DB

        # Создаем нового пользователя
        user_data = {
            "email": "iloveigor@chillcreative.ru",
            "password": "25896311Aaa",
            "full_name": "Super Admin",
            "is_active": True,
            "is_superuser": True,
            "role": "admin",
        }

        hashed_password = User.get_password_hash(user_data.pop("password"))
        user_data["hashed_password"] = hashed_password

        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)

        print("Администратор создан успешно!")
        print(f"Email: {user.email}")
        print(f"Роль: {user.role}")
        print(f"Superuser: {user.is_superuser}")

    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
