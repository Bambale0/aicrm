"""
Настройка базы данных
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import settings

# Используем URL из настроек
DATABASE_URL = settings.database_url

# Создаем sync URL для синхронного engine
sync_url = DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")

# Для SQLite используем обычный sqlite3 драйвер
if sync_url.startswith("sqlite"):
    sync_url = sync_url.replace("sqlite://", "sqlite://")

engine = create_engine(
    sync_url,
    echo=settings.debug,
    poolclass=StaticPool if sync_url.startswith("sqlite") else None,
    connect_args={"check_same_thread": False} if sync_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Асинхронная версия для API тестов
async_engine = create_async_engine(
    (
        DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        if DATABASE_URL.startswith("sqlite")
        else DATABASE_URL
    ),
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


# Алиас для совместимости
get_master_db = get_db


async def get_async_db() -> AsyncSession:
    """Получение асинхронной сессии базы данных"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
