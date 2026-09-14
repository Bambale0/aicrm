#!/usr/bin/env python3
"""
Скрипт для создания администратора
"""
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.orm import Session
from aicrm.core.database import get_default_engine
from aicrm.models import Base
from aicrm.models.user import User
from sqlalchemy.orm import sessionmaker

def create_admin_user():
    """Создание администратора из переменных окружения."""
    admin_email = os.environ.get("AICRM_ADMIN_EMAIL")
    admin_password = os.environ.get("AICRM_ADMIN_PASSWORD")
    admin_name = os.environ.get("AICRM_ADMIN_NAME")

    if not admin_email or not admin_password or not admin_name:
        raise RuntimeError(
            "Set AICRM_ADMIN_EMAIL, AICRM_ADMIN_PASSWORD and AICRM_ADMIN_NAME before running this script"
        )

    engine = get_default_engine()
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            existing_user.full_name = admin_name
            existing_user.hashed_password = User.get_password_hash(admin_password)
            existing_user.is_active = True
            existing_user.is_superuser = True
            existing_user.role = "admin"
            db.commit()
            print(f"Administrator updated: {admin_email}")
            return

        user = User(
            email=admin_email,
            hashed_password=User.get_password_hash(admin_password),
            full_name=admin_name,
            is_active=True,
            is_superuser=True,
            role="admin",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        print(f"Administrator created: {admin_email}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
