#!/usr/bin/env python3
"""
Подтверждение email для пользователя Игоря
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.aicrm.models.user import User
from backend.src.aicrm.core.database import get_default_engine
from sqlalchemy.orm import sessionmaker

def verify_igor_email():
    """Подтвердить email пользователя Игоря"""
    print("✉️ Подтверждение email для iloveigor@chillcreative.ru...")

    engine = get_default_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()

            if not user:
                print("❌ Пользователь не найден!")
                return

            print(f"Найден пользователь: {user.email}")
            print(f"Текущий статус: {'подтвержден' if getattr(user, 'email_verified', False) else 'не подтвержден'}")

            if getattr(user, 'email_verified', False):
                print("✅ Email уже подтвержден!")
                return

            # Подтверждаем email
            user.email_verified = True
            user.email_verification_token = None  # Очищаем токен
            user.email_verification_expires = None  # Очищаем срок действия

            db.commit()
            db.refresh(user)

            print("✅ Email успешно подтвержден!")
            print(f"   Email: {user.email}")
            print(f"   Компания: {getattr(user, 'company_name', 'не указана')}")
            print(f"   Статус: {'Email подтвержден' if user.email_verified else 'Email не подтвержден'}")

        except Exception as e:
            print(f"❌ Ошибка при подтверждении email: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    print("🚀 Подтверждение email для Игоря...")
    verify_igor_email()
    print("✅ Готово!")
