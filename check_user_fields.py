#!/usr/bin/env python3
"""
Проверка существования новых полей в таблице users
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.aicrm.core.database import get_default_engine
from sqlalchemy import text

def check_user_fields():
    """Проверить, какие поля уже существуют в таблице users"""
    print("Проверка полей в таблице users...")

    engine = get_default_engine()

    expected_columns = [
        "company_name",
        "email_verified",
        "email_verification_token",
        "email_verification_expires"
    ]

    try:
        with engine.connect() as conn:
            # Получить все колонки таблицы users
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))

            existing_columns = {row[0]: (row[1], row[2]) for row in result.fetchall()}

            print("Найденные поля в таблице users:")
            print("-" * 50)
            for name, (data_type, nullable) in existing_columns.items():
                print(f"  {name}: {data_type} ({nullable})")

            print("\nПроверка ожидаемых полей:")
            print("-" * 30)

            all_exist = True
            for column in expected_columns:
                if column in existing_columns:
                    print(f"✅ {column}: существует")
                else:
                    print(f"❌ {column}: отсутствует")
                    all_exist = False

            if all_exist:
                print("\n🎉 Все необходимые поля присутствуют!")
                return True
            else:
                print("\n⚠️ Некоторые поля отсутствуют. Требуется миграция.")
                return False

    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False

if __name__ == "__main__":
    check_user_fields()
