"""
Модели базы данных
"""

from .ai_usage import AIUsage
from .automation import (
    EntityType,
    Process,
    Robot,
    RobotAction,
    RobotActionConfig,
    Stage,
    Trigger,
    TriggerEvent,
)
from .avito_chat import AvitoChatSettings
from .base import Base, BaseModel
from .communication import Communication
from .customer import Customer
from .order import Order
from .production_step import ProductionStep
from .task import Task
from .user import User

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
    "AIUsage",
    # Automation models
    "Process",
    "Stage",
    "Trigger",
    "Robot",
    "RobotActionConfig",
    "EntityType",
    "TriggerEvent",
    "RobotAction",
]
