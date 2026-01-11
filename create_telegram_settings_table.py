#!/usr/bin/env python3
"""
Миграция для создания таблицы telegram_settings
"""
import os
import sqlite3

from src.aicrm.core.config import settings


def create_telegram_settings_table():
    """Создает таблицу telegram_settings в базе данных"""

    # Получаем путь к базе данных из URL
    database_url = settings.database_url
    if database_url.startswith("sqlite+aiosqlite:///"):
        db_path = database_url.replace("sqlite+aiosqlite:///./", "")
    elif database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
    else:
        print(f"Неподдерживаемый тип базы данных: {database_url}")
        return

    # Если путь относительный, делаем его абсолютным
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)

    print(f"Подключаемся к базе данных: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли уже таблица
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='telegram_settings'
        """
        )

        if cursor.fetchone():
            print("Таблица telegram_settings уже существует")
            return

        # Создаем таблицу telegram_settings
        cursor.execute(
            """
            CREATE TABLE telegram_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Основные настройки бота
                bot_token TEXT,
                webhook_url VARCHAR,
                webhook_secret VARCHAR,

                -- Настройки автоответчика
                auto_reply_enabled BOOLEAN DEFAULT 0,
                auto_reply_message TEXT,

                -- Настройки AI
                ai_enabled BOOLEAN DEFAULT 1,
                ai_model VARCHAR DEFAULT 'gpt-4',
                ai_temperature REAL DEFAULT 0.7,
                ai_max_tokens INTEGER DEFAULT 1000,

                -- Системные настройки
                notification_email VARCHAR,
                sync_interval INTEGER DEFAULT 300,
                max_concurrent_chats INTEGER DEFAULT 10
            )
        """
        )

        # Создаем индексы для производительности
        cursor.execute(
            "CREATE INDEX idx_telegram_settings_created_at ON telegram_settings(created_at)"
        )

        # Вставляем настройки по умолчанию
        cursor.execute(
            """
            INSERT INTO telegram_settings (
                auto_reply_enabled, ai_enabled, ai_model, ai_temperature, ai_max_tokens,
                sync_interval, max_concurrent_chats
            ) VALUES (
                0, 1, 'gpt-4', 0.7, 1000,
                300, 10
            )
        """
        )

        conn.commit()
        print("Таблица telegram_settings создана успешно")
        print("Добавлены настройки по умолчанию")

    except Exception as e:
        print(f"Ошибка при создании таблицы telegram_settings: {e}")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    create_telegram_settings_table()
