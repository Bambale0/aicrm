"""
API роутеры
"""
from .auth import router as auth_router
from .customer import router as customer_router
from .communication import router as communication_router
from .email import router as email_router
from .telegram import router as telegram_router
from .ai_settings import router as ai_settings_router

__all__ = ["auth_router", "customer_router", "communication_router", "email_router", "telegram_router", "ai_settings_router"]
