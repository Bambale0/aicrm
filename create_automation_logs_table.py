#!/usr/bin/env python3
"""
Скрипт для создания таблицы automation_logs
"""
import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from aicrm.core.database import engine
from aicrm.models import Base


def create_automation_logs_table():
    """Создание таблицы automation_logs"""
    # Создаем таблицы, если они не существуют
    Base.metadata.create_all(bind=engine)

    print("Таблица automation_logs создана успешно!")


if __name__ == "__main__":
    create_automation_logs_table()
