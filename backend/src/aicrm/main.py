from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import (
    ai_router,
    auth_router,
    automation_router,
    housing_router,
    messengers_router,
    user_router,
)
from .core.config import settings
from .core.database import get_default_engine
from .utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="ЖКХ CRM API",
    description="Заявки, жители, подрядчики, диспетчерская, мессенджеры и роботизация",
    version="1.3.0",
)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix="/auth")
app.include_router(ai_router)
app.include_router(user_router)
app.include_router(housing_router)
app.include_router(messengers_router)
app.include_router(automation_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


def _dependency_health():
    services = {"database": "healthy", "redis": "healthy"}

    try:
        from sqlalchemy import text

        with get_default_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        services["database"] = "unhealthy"
        logger.error("database_health_failed", error_type=type(exc).__name__)

    try:
        import redis

        client = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        client.close()
    except Exception as exc:
        services["redis"] = "unhealthy"
        logger.error("redis_health_failed", error_type=type(exc).__name__)

    status = "healthy" if all(value == "healthy" for value in services.values()) else "unhealthy"
    return status, services


@app.get("/health/ready")
async def readiness_check(response: Response):
    overall, services = _dependency_health()
    if overall != "healthy":
        response.status_code = 503
    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
    }
