#!/usr/bin/env python3
"""
Миграционный скрипт с использованием суперпользователя PostgreSQL
"""
import asyncio
import sys
import os
from sqlalchemy import create_engine, text

# Настройки суперпользователя (из config.py по умолчанию)
SUPERUSER_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',  # Используем postgres вместо aicrm_user
    'password': 'postgres',
    'database': 'aicrm'
}

def create_superuser_engine():
    """Создать движок для суперпользователя"""
    database_url = f"postgresql+psycopg2://{SUPERUSER_CONFIG['user']}:{SUPERUSER_CONFIG['password']}@{SUPERUSER_CONFIG['host']}:{SUPERUSER_CONFIG['port']}/{SUPERUSER_CONFIG['database']}"
    return create_engine(database_url)

async def migrate_user_fields_superuser():
    """Добавить новые колонки в таблицу users с правами суперпользователя"""
    print("🔄 Добавление новых полей с правами суперпользователя...")
    print("Используется пользователь: postgres")

    engine = create_superuser_engine()

    columns_to_add = [
        ("company_name", "VARCHAR(255)"),
        ("email_verified", "BOOLEAN DEFAULT FALSE"),
        ("email_verification_token", "VARCHAR"),
        ("email_verification_expires", "TIMESTAMP")
    ]

    try:
        with engine.connect() as conn:
            # Сначала предоставляем себе права на таблицу
            print("🔑 Предоставление прав суперпользователю...")
            conn.execute(text("ALTER TABLE users OWNER TO postgres;"))
            conn.commit()

            for column_name, column_type in columns_to_add:
                # Проверяем, существует ли колонка
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = :column_name
                """), {"column_name": column_name})

                if result.fetchone():
                    print(f"✅ {column_name}: уже существует")
                    continue

                # Добавляем колонку
                if column_name == "email_verified":
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                else:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))

                print(f"✅ Колонка {column_name} успешно добавлена")
                conn.commit()

            # Возвращаем права оригинальному пользователю
            print("🔄 Возврат прав пользователю aicrm_user...")
            try:
                conn.execute(text("ALTER TABLE users OWNER TO aicrm_user;"))
                conn.execute(text("GRANT ALL PRIVILEGES ON TABLE users TO aicrm_user;"))
                conn.commit()
            except Exception as e:
                print(f"⚠️ Не удалось вернуть права aicrm_user: {e}")

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Суперпользовательская миграция полей пользователей...")
    asyncio.run(migrate_user_fields_superuser())
    print("✅ Миграция завершена!")
