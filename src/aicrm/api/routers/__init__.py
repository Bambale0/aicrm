"""
API роутеры
"""

from .auth import router as auth_router
from .customer import router as customer_router
from .websocket import router as websocket_router

__all__ = ["auth_router", "customer_router", "websocket_router"]
