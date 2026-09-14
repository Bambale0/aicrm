"""Active API routers for ЖКХ CRM."""

from .ai import router as ai_router
from .auth import router as auth_router
from .automation import router as automation_router
from .housing import router as housing_router
from .messengers import router as messengers_router
from .user import router as user_router

__all__ = [
    "ai_router",
    "auth_router",
    "automation_router",
    "housing_router",
    "messengers_router",
    "user_router",
]
