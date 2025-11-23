#!/usr/bin/env python3
"""
Миграционный скрипт для добавления полей для верификации email и названия компании в модель User
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import Column, String, MetaData, Table, text
from backend.src.aicrm.core.database import get_default_engine


async def migrate_user_fields():
    """Добавить новые колонки в таблицу users"""
    print("Добавление новых полей в таблицу users...")
    print("- company_name: VARCHAR(255) - название компании")
    print("- email_verified: BOOLEAN DEFAULT FALSE - статус верификации email")
    print("- email_verification_token: VARCHAR - токен верификации")
    print("- email_verification_expires: TIMESTAMP - срок действия токена")

    engine = get_default_engine()

    columns_to_add = [
        ("company_name", "VARCHAR(255)"),
        ("email_verified", "BOOLEAN DEFAULT FALSE"),
        ("email_verification_token", "VARCHAR"),
        ("email_verification_expires", "TIMESTAMP")
    ]

    try:
        with engine.connect() as conn:
            for column_name, column_type in columns_to_add:
                # Проверяем, существует ли колонка
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = :column_name
                """), {"column_name": column_name})

                if result.fetchone():
                    print(f"Колонка {column_name} уже существует")
                    continue

                # Добавляем колонку
                if column_name == "email_verified":
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                else:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))

                print(f"✅ Колонка {column_name} успешно добавлена")

            conn.commit()

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_user_fields())
