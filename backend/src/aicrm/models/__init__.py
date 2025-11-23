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
from .telegram_settings import TelegramSettings
from .ai_usage import AIUsage
from .ai_prompt import AIPrompt
from .ai_settings import AISettings
from .category import Category
from .service import Service
from .product import Product
from .automation import (
    Process, Stage, Trigger, Robot, RobotActionConfig,
    EntityType, TriggerEvent, RobotAction
)
from .automation_log import AutomationLog
from .email_template import EmailTemplate
from .plugin import (
    Plugin, PluginAction, PluginHook, PluginPermission,
    PluginRegistry, PluginTemplate
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
    "TelegramSettings",
    "AIUsage",
    "AIPrompt",
    "AISettings",
    "Category",
    "Service",
    "Product",
    "EmailTemplate",
    # Automation models
    "Process",
    "Stage",
    "Trigger",
    "Robot",
    "RobotActionConfig",
    "EntityType",
    "TriggerEvent",
    "RobotAction",
    "AutomationLog"
]
