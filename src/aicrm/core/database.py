"""
Настройка базы данных
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import settings

# Используем URL из настроек
DATABASE_URL = settings.database_url
# Для SQLite используем aiosqlite драйвер
if DATABASE_URL.startswith("sqlite") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
# Для PostgreSQL в продакшене используем asyncpg
elif not settings.debug and DATABASE_URL.startswith("postgresql"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2", "postgresql+asyncpg")

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    poolclass=StaticPool if settings.debug else None,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
