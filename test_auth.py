#!/usr/bin/env python3
"""
Тест аутентификации
"""
import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session

from aicrm.core.database import SessionLocal
from aicrm.models.user import User
from aicrm.services.auth import auth_service


def test_auth():
    """Тест аутентификации"""
    db: Session = SessionLocal()

    try:
        # Находим пользователя
        user = db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()
        if not user:
            print("Пользователь не найден!")
            return

        print(f"Найден пользователь: {user.email}")
        print(f"Хеш пароля: {user.hashed_password}")

        # Проверяем пароль напрямую
        is_valid = user.verify_password("25896311Aaa")
        print(f"Проверка пароля напрямую: {is_valid}")

        # Проверяем через сервис
        auth_user = auth_service.authenticate_user(
            db, "iloveigor@chillcreative.ru", "25896311Aaa"
        )
        print(f"Аутентификация через сервис: {auth_user is not None}")

        if auth_user:
            print(f"Аутентифицированный пользователь: {auth_user.email}")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_auth()
