from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db_dependency = get_db


def import_models() -> None:
    # Explicit imports make the active data model visible and prevent dead
    # legacy modules from being loaded implicitly.
    from ..models import ai_connection, automation, housing, messenger, user  # noqa: F401


def create_tables() -> None:
    from ..models.base import Base

    import_models()
    Base.metadata.create_all(bind=engine)


def get_default_engine():
    return engine
