#!/usr/bin/env python3
"""
Миграция: добавление колонки extra_data в таблицу tasks
"""
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.sql import text
from aicrm.core.database import engine

def add_extra_data_column():
    """Добавление колонки extra_data в таблицу tasks"""
    # Создаем колонку
    with engine.connect() as conn:
        try:
            # Для SQLite используем ALTER TABLE
            conn.execute(text("ALTER TABLE tasks ADD COLUMN extra_data TEXT"))
            conn.commit()
            print("✅ Колонка extra_data успешно добавлена в таблицу tasks")
        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            # Если колонка уже существует, это нормально
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️ Колонка extra_data уже существует")
            else:
                raise

if __name__ == "__main__":
    add_extra_data_column()
