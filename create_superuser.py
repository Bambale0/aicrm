#!/usr/bin/env python3
"""
Скрипт для создания или обновления суперпользователя
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session

from aicrm.core.database import SessionLocal
from aicrm.models.user import User


def create_or_update_superuser():
    """Создание или обновление суперпользователя"""
    db: Session = SessionLocal()

    try:
        # Ищем существующего пользователя
        user = db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()

        if user:
            # Обновляем существующего
            user.hashed_password = User.get_password_hash("25896311Aaa")
            user.is_superuser = True
            user.role = "superuser"
            user.is_active = True
            user.full_name = "Super User Igor"
            print(f"Обновлен существующий пользователь: {user.email}")
        else:
            # Создаем нового
            user = User(
                email="iloveigor@chillcreative.ru",
                hashed_password=User.get_password_hash("25896311Aaa"),
                full_name="Super User Igor",
                is_superuser=True,
                role="superuser",
                is_active=True,
            )
            db.add(user)
            print(f"Создан новый суперпользователь: {user.email}")

        db.commit()
        db.refresh(user)
        print(
            f"Суперпользователь готов: {user.email}, is_superuser: {user.is_superuser}"
        )

    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_or_update_superuser()
