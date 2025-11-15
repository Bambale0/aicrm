"""
API роутеры
"""
from .auth import router as auth_router
from .customer import router as customer_router
from .email import router as email_router
from .telegram import router as telegram_router

__all__ = ["auth_router", "customer_router", "email_router", "telegram_router"]
