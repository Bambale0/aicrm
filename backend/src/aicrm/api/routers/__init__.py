"""
Инициализация роутеров API
"""
from .auth import router as auth_router
from .customer import router as customer_router
from .communication import router as communication_router
from .ai import router as ai_router
from .ai_manager import router as ai_manager_router
from .order import router as order_router
from .avito import router as avito_router
from .task import router as task_router
from .automation import router as automation_router
from .email import router as email_router
from .telegram import router as telegram_router
from .user import router as user_router
from .ai_settings import router as ai_settings_router
from .workflow import router as workflow_router
from .email_templates import router as email_templates_router
from .production import router as production_router
from .catalog import router as catalog_router
from .organization import router as organization_router
from .campaign import router as campaign_router
from .plugin import router as plugin_router
from .websocket import router as websocket_router
from .system_settings import router as system_settings_router

__all__ = [
    "auth_router",
    "customer_router",
    "communication_router",
    "ai_router",
    "ai_manager_router",
    "order_router",
    "avito_router",
    "task_router",
    "automation_router",
    "email_router",
    "telegram_router",
    "user_router",
    "ai_settings_router",
    "workflow_router",
    "email_templates_router",
    "production_router",
    "catalog_router",
    "organization_router",
    "campaign_router",
    "plugin_router",
    "websocket_router",
    "system_settings_router",
]
