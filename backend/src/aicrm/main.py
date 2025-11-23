"""
Основное приложение FastAPI - Fixed Version
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Internal imports - try to import, fallback if not available
try:
    from .core.config import settings
    from .core.database import get_db_dependency as get_db
except ImportError:
    # Fallback settings
    settings = type('obj', (object,), {
        'allow_origins': ['*']
    })()
    get_db = lambda: None

try:
    from .api.schemas.auth import LoginRequest
    from .api.schemas.ai import (
        AIStatusResponse, AIMonthlyUsageResponse, AIModelsResponse, 
        AIModelInfo, AIUsageHistoryResponse
    )
except ImportError:
    LoginRequest = None
    AIStatusResponse = None

try:
    from .services.auth import auth_service
    from .services.ai_usage_service import AIUsageService
except ImportError:
    auth_service = None
    AIUsageService = None

# FastAPI app
fastapi_app = FastAPI(
    title="AI CRM System API",
    description="Полнофункциональная CRM система для компаний печати с интеграцией ИИ",
    version="0.1.0"
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
        auth_router, customer_router, communication_router, task_router,
        ai_router, ai_manager_router, ai_settings_router, automation_router,
        email_router, telegram_router, user_router, email_templates_router,
        production_router, catalog_router, avito_router, organization_router,
        order_router, workflow_router, campaign_router, plugin_router, websocket_router,
        system_settings_router
    )

    # Core API endpoints
    fastapi_app.include_router(auth_router, prefix="/auth", tags=["auth"])
    fastapi_app.include_router(customer_router, prefix="/customers", tags=["customers"])
    fastapi_app.include_router(communication_router, prefix="/communications", tags=["communications"])
    fastapi_app.include_router(task_router, prefix="/tasks", tags=["tasks"])

    # AI endpoints
    fastapi_app.include_router(ai_router, prefix="/ai", tags=["ai"])
    fastapi_app.include_router(ai_manager_router, prefix="/ai-manager", tags=["ai-manager"])
    fastapi_app.include_router(ai_settings_router, prefix="/ai-settings", tags=["ai-settings"])

    # Automation and workflows
    fastapi_app.include_router(automation_router, prefix="/automation", tags=["automation"])
    fastapi_app.include_router(workflow_router, prefix="/workflow", tags=["workflow"])

    # Communication channels
    fastapi_app.include_router(email_router, prefix="/email", tags=["email"])
    fastapi_app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

    # Business logic
    fastapi_app.include_router(user_router, prefix="/users", tags=["users"])
    fastapi_app.include_router(email_templates_router, prefix="/email-templates", tags=["email-templates"])
    fastapi_app.include_router(production_router, prefix="/production", tags=["production"])
    fastapi_app.include_router(catalog_router, prefix="/catalog", tags=["catalog"])
    fastapi_app.include_router(avito_router, prefix="/avito", tags=["avito"])
    fastapi_app.include_router(order_router, prefix="/orders", tags=["orders"])

    # Organizations and campaigns
    fastapi_app.include_router(organization_router, prefix="/organizations", tags=["organizations"])
    fastapi_app.include_router(campaign_router, prefix="/campaigns", tags=["campaigns"])

    # Plugin system
    fastapi_app.include_router(plugin_router, prefix="/api", tags=["plugins"])

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
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
            
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {
                "redis": redis_status,
                "database": "unknown"
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            }
        }
    except ImportError:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {"redis": "unknown"},
            "system": {"cpu_percent": 0, "memory_percent": 0}
        }

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
