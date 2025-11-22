#!/usr/bin/env python3
"""
Изменение пароля для пользователя Игоря
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.aicrm.models.user import User
from backend.src.aicrm.core.database import get_default_engine
from sqlalchemy.orm import sessionmaker

def change_igor_password():
    """Изменить пароль пользователя Игоря"""
    new_password = "25896311Aaa"
    email = "iloveigor@chillcreative.ru"

    print(f"🔐 Изменение пароля для {email}...")

    engine = get_default_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.email == email).first()

            if not user:
                print("❌ Пользователь не найден!")
                return

            print(f"Найден пользователь: {user.email}")

            # Хешируем новый пароль
            hashed_password = User.get_password_hash(new_password)
            user.hashed_password = hashed_password

            db.commit()
            db.refresh(user)

            print("✅ Пароль успешно изменен!")
            print(f"   Email: {user.email}")
            print(f"   Компания: {getattr(user, 'company_name', 'не указана')}")
            print(f"   Новый пароль: {len(new_password)} символов")

            # Тестируем новый пароль
            if user.verify_password(new_password):
                print("✅ Верификация нового пароля прошла успешно!")
            else:
                print("❌ Ошибка верификации нового пароля!")
                raise Exception("Пароль не совпадает с хешом")

        except Exception as e:
            print(f"❌ Ошибка при изменении пароля: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    print("🚀 Изменение пароля для Игоря...")
    change_igor_password()
    print("✅ Готово!")
