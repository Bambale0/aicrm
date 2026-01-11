#!/usr/bin/env python3
"""
Скрипт для создания таблицы email_templates
"""
import os
import sys

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.aicrm.core.database import engine
from src.aicrm.models import Base


def create_email_templates_table():
    """Создание таблицы email_templates"""
    try:
        print("Создание таблицы email_templates...")
        Base.metadata.create_all(
            bind=engine, tables=[Base.metadata.tables["email_templates"]]
        )
        print("✅ Таблица email_templates успешно создана!")
    except Exception as e:
        print(f"❌ Ошибка при создании таблицы: {e}")
        return False
    return True


if __name__ == "__main__":
    success = create_email_templates_table()
    sys.exit(0 if success else 1)
