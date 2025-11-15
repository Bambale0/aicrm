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
from .avito_chat import AvitoChatSettings
from .telegram_chat import TelegramChat
from .ai_usage import AIUsage
from .ai_prompt import AIPrompt
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
    "TelegramChat",
    "AIUsage",
    "AIPrompt",
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
