#!/usr/bin/env python3
"""
Создание тестового пользователя для Игоря (iloveigor@chillcreative.ru)
с компанией Chill Creative
"""
import asyncio
import sys
import os
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.aicrm.models.user import User
from backend.src.aicrm.core.database import get_default_engine
from sqlalchemy.orm import sessionmaker

def create_igor_test_user():
    """Создать тестового пользователя для Игоря"""
    print("🏗️ Создание тестового пользователя для Игоря...")

    engine = get_default_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        try:
            # Проверяем, существует ли пользователь
            existing_user = db.query(User).filter(User.email == "iloveigor@chillcreative.ru").first()

            if existing_user:
                print("✅ Пользователь уже существует!")
                print(f"   Email: {existing_user.email}")
                print(f"   Компания: {getattr(existing_user, 'company_name', 'не указана')}")
                print(f"   Статус email: {'подтвержден' if getattr(existing_user, 'email_verified', False) else 'не подтвержден'}")

                # Обновляем информацию если нужно
                if not getattr(existing_user, 'company_name', None):
                    existing_user.company_name = "Chill Creative"
                    db.commit()
                    print("✅ Компания обновлена!")

                return existing_user

            # Создание нового пользователя
            print("👤 Создание нового пользователя...")

            user = User(
                email="iloveigor@chillcreative.ru",
                full_name="Игорь",
                company_name="Chill Creative",
                hashed_password=User.get_password_hash("testpassword123"),  # Тестовый пароль
                is_active=True,
                is_superuser=False,
                role="user",
                email_verified=True  # Для тестирования - сразу подтверждаем email
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            print("✅ Пользователь успешно создан!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Компания: {user.company_name}")
            print(f"   Email подтвержден: {'да' if user.email_verified else 'нет'}")

            return user

        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    print("🚀 Создание тестового аккаунта для Игоря...")
    user = create_igor_test_user()
    print("✅ Готово!")
