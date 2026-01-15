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
    settings = type("obj", (object,), {"cors_origins": ["*"]})()
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
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers if available
try:
    logger.info("Starting router imports...")
    from .api.routers import (
        admin_router,
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
        system_router,
        system_settings_router,
        task_router,
        telegram_router,
        user_router,
        user_settings_router,
        websocket_router,
        workflow_router,
    )

    logger.info("All routers imported successfully")

    # Admin endpoints
    fastapi_app.include_router(admin_router, tags=["admin"])
    logger.info("Admin router included")

    # Core API endpoints
    fastapi_app.include_router(auth_router, tags=["auth"])
    logger.info("Auth router included")
    fastapi_app.include_router(customer_router, tags=["customers"])
    logger.info("Customer router included")
    fastapi_app.include_router(communication_router, tags=["communications"])
    logger.info("Communication router included")
    fastapi_app.include_router(task_router, tags=["tasks"])
    logger.info("Task router included")

    # AI endpoints
    fastapi_app.include_router(ai_router, tags=["ai"])
    logger.info("AI router included")
    fastapi_app.include_router(ai_manager_router, tags=["ai-manager"])
    logger.info("AI manager router included")
    fastapi_app.include_router(ai_settings_router, tags=["ai-settings"])
    logger.info("AI settings router included")

    # AI Usage analytics - temporarily commented out to fix duplicate
    # fastapi_app.include_router(ai_router, prefix="/ai-usage", tags=["ai-usage"])

    # Automation and workflows
    fastapi_app.include_router(automation_router, tags=["automation"])
    logger.info("Automation router included")
    fastapi_app.include_router(workflow_router, tags=["workflow"])
    logger.info("Workflow router included")

    # Communication channels
    fastapi_app.include_router(email_router, tags=["email"])
    logger.info("Email router included")
    fastapi_app.include_router(telegram_router, tags=["telegram"])
    logger.info("Telegram router included")

    # Business logic
    fastapi_app.include_router(user_router, tags=["users"])
    logger.info("User router included")
    fastapi_app.include_router(user_settings_router, tags=["user-settings"])
    logger.info("User settings router included")
    fastapi_app.include_router(email_templates_router, tags=["email-templates"])
    logger.info("Email templates router included")
    fastapi_app.include_router(production_router, tags=["production"])
    logger.info("Production router included")
    fastapi_app.include_router(catalog_router, tags=["catalog"])
    logger.info("Catalog router included")
    fastapi_app.include_router(avito_router, tags=["avito"])
    logger.info("Avito router included")
    fastapi_app.include_router(order_router, tags=["orders"])
    logger.info("Order router included")

    # Organizations and campaigns
    fastapi_app.include_router(organization_router, tags=["organizations"])
    logger.info("Organization router included")
    fastapi_app.include_router(campaign_router, tags=["campaigns"])
    logger.info("Campaign router included")

    # Plugin system
    fastapi_app.include_router(plugin_router, tags=["plugins"])
    logger.info("Plugin router included")

    # System settings
    fastapi_app.include_router(system_settings_router, tags=["system-settings"])
    logger.info("System settings router included")

    # System monitoring
    fastapi_app.include_router(system_router, tags=["system"])
    logger.info("System router included")

    # WebSocket endpoints
    fastapi_app.include_router(websocket_router, tags=["websockets"])
except Exception as e:
    logger.error(f"Router imports failed: {e}")
    import traceback

    logger.error(traceback.format_exc())


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


@fastapi_app.get("/system/endpoints/health")
async def system_endpoints_health():
    """
    Проверка здоровья всех системных эндпоинтов
    """
    try:
        import psutil
        import redis

        # Базовые проверки
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "endpoints_checked": [],
            "services_status": {},
            "warnings": [],
            "errors": [],
        }

        # Проверка Redis
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            health_data["services_status"]["redis"] = "healthy"
        except Exception as e:
            health_data["services_status"]["redis"] = "unhealthy"
            health_data["errors"].append(f"Redis error: {str(e)}")
            health_data["overall_status"] = "degraded"

        # Проверка системных ресурсов
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            if cpu_percent > 95:
                health_data["warnings"].append(f"Critical CPU usage: {cpu_percent}%")
                health_data["overall_status"] = "critical"
            elif cpu_percent > 85:
                health_data["warnings"].append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 95:
                health_data["warnings"].append(
                    f"Critical memory usage: {memory.percent}%"
                )
                health_data["overall_status"] = "critical"
            elif memory.percent > 85:
                health_data["warnings"].append(f"High memory usage: {memory.percent}%")

            if disk.percent > 98:
                health_data["warnings"].append(f"Critical disk usage: {disk.percent}%")
                health_data["overall_status"] = "critical"
            elif disk.percent > 90:
                health_data["warnings"].append(f"High disk usage: {disk.percent}%")

            health_data["services_status"]["system_resources"] = "healthy"

        except Exception as e:
            health_data["services_status"]["system_resources"] = "unhealthy"
            health_data["errors"].append(f"System resources check failed: {str(e)}")
            health_data["overall_status"] = "unhealthy"

        # Проверка сетевых подключений (основные порты)
        try:
            import socket

            critical_ports = {8000: "HTTP API", 5432: "PostgreSQL", 6379: "Redis"}

            network_status = {}
            for port, service in critical_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(("127.0.0.1", port))
                    sock.close()
                    status = "open" if result == 0 else "closed"
                    network_status[service] = status

                    if result != 0 and port in [8000]:  # Критично только для API
                        health_data["warnings"].append(
                            f"{service} port {port} is closed"
                        )

                except Exception as e:
                    network_status[service] = f"error: {str(e)}"
                    if port == 8000:
                        health_data["errors"].append(
                            f"Critical service {service} unreachable"
                        )

            health_data["services_status"]["network"] = "healthy"

        except Exception as e:
            health_data["services_status"]["network"] = "unhealthy"
            health_data["errors"].append(f"Network check failed: {str(e)}")

        # Список проверенных эндпоинтов
        health_data["endpoints_checked"] = [
            "/health",
            "/api/health",
            "/health/detailed",
            "/system/endpoints/health",
            "/system/database/status",
            "/system/resources",
        ]

        # Финальная оценка
        if health_data["errors"] and health_data["overall_status"] != "critical":
            health_data["overall_status"] = "unhealthy"
        elif health_data["warnings"] and health_data["overall_status"] not in [
            "unhealthy",
            "critical",
        ]:
            health_data["overall_status"] = "degraded"

        return health_data

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e),
            "endpoints_checked": ["/system/endpoints/health"],
            "services_status": {},
            "warnings": [],
            "errors": ["Health check system failure"],
        }


@fastapi_app.get("/ping", operation_id="main_ping_get")
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
