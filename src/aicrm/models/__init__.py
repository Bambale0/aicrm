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
from .ai_usage import AIUsage
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
    "AIUsage",
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
