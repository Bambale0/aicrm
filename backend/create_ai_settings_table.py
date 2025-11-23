#!/usr/bin/env python3
"""
Миграция для создания таблицы ai_settings
"""
import sqlite3
import os
from src.aicrm.core.config import settings

def create_ai_settings_table():
    """Создает таблицу ai_settings в базе данных"""

    # Получаем путь к базе данных из URL
    database_url = settings.database_url
    if database_url.startswith('sqlite+aiosqlite:///'):
        db_path = database_url.replace('sqlite+aiosqlite:///', '')
    elif database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
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
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ai_settings'
        """)

        if cursor.fetchone():
            print("Таблица ai_settings уже существует")
            return

        # Создаем таблицу ai_settings
        cursor.execute("""
            CREATE TABLE ai_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Основные настройки
                default_model VARCHAR NOT NULL DEFAULT 'deepseek/deepseek-chat-v3.1',
                temperature REAL NOT NULL DEFAULT 0.7,
                max_tokens INTEGER NOT NULL DEFAULT 1000,

                -- API ключи (зашифрованные)
                openrouter_api_key TEXT,
                openai_api_key TEXT,
                huggingface_api_key TEXT,

                -- Настройки провайдера
                provider VARCHAR NOT NULL DEFAULT 'openrouter',

                -- Дополнительные настройки
                auto_reply_enabled BOOLEAN DEFAULT 1,
                auto_reply_temperature REAL DEFAULT 0.5,
                auto_reply_max_tokens INTEGER DEFAULT 500,

                -- Системные настройки
                rate_limit_per_minute INTEGER DEFAULT 60,
                cache_enabled BOOLEAN DEFAULT 1,
                log_level VARCHAR DEFAULT 'INFO',

                -- Настройки для конкретных моделей
                fallback_model VARCHAR,
                premium_model VARCHAR
            )
        """)

        # Создаем индексы для производительности
        cursor.execute("CREATE INDEX idx_ai_settings_provider ON ai_settings(provider)")
        cursor.execute("CREATE INDEX idx_ai_settings_created_at ON ai_settings(created_at)")

        # Вставляем настройки по умолчанию
        cursor.execute("""
            INSERT INTO ai_settings (
                default_model, temperature, max_tokens, provider,
                auto_reply_enabled, auto_reply_temperature, auto_reply_max_tokens,
                rate_limit_per_minute, cache_enabled, log_level
            ) VALUES (
                'deepseek/deepseek-chat-v3.1', 0.7, 1000, 'openrouter',
                1, 0.5, 500,
                60, 1, 'INFO'
            )
        """)

        conn.commit()
        print("Таблица ai_settings создана успешно")
        print("Добавлены настройки по умолчанию")

    except Exception as e:
        print(f"Ошибка при создании таблицы ai_settings: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_ai_settings_table()
