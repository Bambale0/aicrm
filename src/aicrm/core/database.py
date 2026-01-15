"""
Настройка базы данных
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import settings

# Используем URL из настроек
DATABASE_URL = settings.database_url

# Конфигурация для разных типов баз данных
if DATABASE_URL.startswith("sqlite"):
    # Для SQLite используем обычный sqlite3 драйвер
    sync_database_url = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
    async_database_url = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    connect_args = {"check_same_thread": False} if settings.debug else {}
    poolclass = StaticPool
elif DATABASE_URL.startswith("postgresql"):
    # Для PostgreSQL используем psycopg2 для sync и asyncpg для async
    sync_database_url = DATABASE_URL
    async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    connect_args = {}
    poolclass = None
else:
    # Для других баз данных
    sync_database_url = DATABASE_URL
    async_database_url = DATABASE_URL
    connect_args = {}
    poolclass = None

engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    poolclass=poolclass if settings.debug else None,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Асинхронная версия для API тестов
async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
)


def get_db() -> Session:
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncSession:
    """Получение асинхронной сессии базы данных"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


# Alias for compatibility
get_master_db = get_db
