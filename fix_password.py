#!/usr/bin/env python3
"""
Исправление пароля администратора
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session

from aicrm.core.database import SessionLocal
from aicrm.models.user import User


def fix_password():
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()
        if user:
            # Новый короткий пароль
            new_password = "123"
            user.hashed_password = User.get_password_hash(new_password)
            db.commit()
            print(f"Пароль изменен на: {new_password}")
        else:
            print("Пользователь не найден")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_password()
