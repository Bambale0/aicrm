#!/usr/bin/env python3
"""
Инициализация базы данных для приложения
Создает все необходимые таблицы на старте системы
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent / "src"))

from aicrm.core.database import (create_master_database, get_default_engine,
                                 init_master_database)
from aicrm.models.base import Base
from aicrm.utils.logging import get_logger

# Импортируем все модели для регистрации в Base.metadata


logger = get_logger(__name__)


def init_database():
    """Инициализировать базу данных"""
    try:
        logger.info("Starting database initialization...")

        # Создание мастер-базы если нужно
        logger.info("Creating master database...")
        create_master_database()

        logger.info("Initializing master database structure...")
        init_master_database()

        # Создание основных таблиц в главной базе данных
        logger.info("Creating main database tables...")
        engine = get_default_engine()
        Base.metadata.create_all(bind=engine)

        logger.info("✅ Database initialization completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 Инициализация базы данных...")
    success = init_database()
    if success:
        print("✅ База данных инициализирована успешно!")
    else:
        print("❌ Ошибка инициализации базы данных!")
        sys.exit(1)
