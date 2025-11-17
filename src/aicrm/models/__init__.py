"""
Модели базы данных
"""
from .base import Base, BaseModel
from .user import User
from .customer import Customer
from .order import Order
from .production_step import ProductionStep
from .communication import Communication
from .task import Task
from .avito_chat import AvitoChatSettings, AvitoGlobalSettings
from .telegram_chat import TelegramChat
from .ai_usage import AIUsage
from .ai_prompt import AIPrompt
from .ai_settings import AISettings
from .service import Service
from .product import Product
from .automation import (
    Process, Stage, Trigger, Robot, RobotActionConfig,
    EntityType, TriggerEvent, RobotAction
)

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Customer",
    "Order",
    "ProductionStep",
    "Communication",
    "Task",
    "AvitoChatSettings",
    "AvitoGlobalSettings",
    "TelegramChat",
    "AIUsage",
    "AIPrompt",
    "AISettings",
    "Service",
    "Product",
    # Automation models
    "Process",
    "Stage",
    "Trigger",
    "Robot",
    "RobotActionConfig",
    "EntityType",
    "TriggerEvent",
    "RobotAction"
]
