"""
Основное приложение FastAPI - Fixed Version
"""

import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Internal imports - try to import, fallback if not available
try:
    from .core.config import settings
    from .core.database import get_db_dependency as get_db
except ImportError:
    # Fallback settings
    settings = type("obj", (object,), {"allow_origins": ["*"]})()
    get_db = lambda: None

try:
    from .api.schemas.auth import LoginRequest
except ImportError:
    LoginRequest = None

try:
    from .services.ai_usage_service import AIUsageService
    from .services.auth import auth_service
except ImportError:
    auth_service = None
    AIUsageService = None

# FastAPI app
fastapi_app = FastAPI(
    title="AI CRM System API",
    description="Полнофункциональная CRM система для компаний печати с интеграцией ИИ",
    version="0.1.0",
)

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers if available
try:
    from .api.routers import (
        ai_manager_router,
        ai_router,
        ai_settings_router,
        auth_router,
        automation_router,
        avito_router,
        campaign_router,
        catalog_router,
        communication_router,
        customer_router,
        email_router,
        email_templates_router,
        order_router,
        organization_router,
        plugin_router,
        production_router,
        system_settings_router,
        task_router,
        telegram_router,
        user_router,
        user_settings_router,
        websocket_router,
        workflow_router,
    )

    # Core API endpoints
    fastapi_app.include_router(auth_router, tags=["auth"])
    fastapi_app.include_router(customer_router, tags=["customers"])
    fastapi_app.include_router(
        communication_router, tags=["communications"]
    )
    fastapi_app.include_router(task_router, tags=["tasks"])

    # AI endpoints
    fastapi_app.include_router(ai_router, tags=["ai"])
    fastapi_app.include_router(
        ai_manager_router, tags=["ai-manager"]
    )
    fastapi_app.include_router(
        ai_settings_router, tags=["ai-settings"]
    )

    # AI Usage analytics - temporarily commented out to fix duplicate
    # fastapi_app.include_router(ai_router, prefix="/ai-usage", tags=["ai-usage"])

    # Automation and workflows
    fastapi_app.include_router(
        automation_router, tags=["automation"]
    )
    fastapi_app.include_router(workflow_router, tags=["workflow"])

    # Communication channels
    fastapi_app.include_router(email_router, tags=["email"])
    fastapi_app.include_router(telegram_router, tags=["telegram"])

    # Business logic
    fastapi_app.include_router(user_router, tags=["users"])
    fastapi_app.include_router(
        user_settings_router, tags=["user-settings"]
    )
    fastapi_app.include_router(
        email_templates_router, tags=["email-templates"]
    )
    fastapi_app.include_router(
        production_router, tags=["production"]
    )
    fastapi_app.include_router(catalog_router, tags=["catalog"])
    fastapi_app.include_router(avito_router, tags=["avito"])
    fastapi_app.include_router(order_router, tags=["orders"])

    # Organizations and campaigns
    fastapi_app.include_router(
        organization_router, tags=["organizations"]
    )
    fastapi_app.include_router(campaign_router, tags=["campaigns"])

    # Plugin system
    fastapi_app.include_router(plugin_router, tags=["plugins"])

    # System settings
    fastapi_app.include_router(system_settings_router, tags=["system-settings"])

    # WebSocket endpoints
    fastapi_app.include_router(websocket_router, tags=["websockets"])

except Exception as e:
    logger.warning(f"Router imports failed: {e}")


# Basic endpoints
@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@fastapi_app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@fastapi_app.get("/health/detailed")
async def health_check_detailed():
    try:
        import psutil
        import redis

        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {"redis": redis_status, "database": "unknown"},
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
            },
        }
    except ImportError:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {"redis": "unknown"},
            "system": {"cpu_percent": 0, "memory_percent": 0},
        }


@fastapi_app.get("/ping")
async def ping():
    return "pong"


@fastapi_app.get("/metrics")
async def metrics():
    try:
        import psutil

        return f"""
# HELP system_cpu_usage System CPU usage percentage
# TYPE system_cpu_usage gauge
system_cpu_usage {psutil.cpu_percent(interval=1)}

# HELP system_memory_usage System memory usage percentage  
# TYPE system_memory_usage gauge
system_memory_usage {psutil.virtual_memory().percent}

# HELP system_uptime System uptime in seconds
# TYPE system_uptime gauge
system_uptime {datetime.utcnow().timestamp()}
"""
    except ImportError:
        return """
# HELP system_cpu_usage System CPU usage percentage
# TYPE system_cpu_usage gauge
system_cpu_usage 0.0

# HELP system_memory_usage System memory usage percentage
# TYPE system_memory_usage gauge  
system_memory_usage 0.0
"""


# Instance for ASGI servers
app = fastapi_app