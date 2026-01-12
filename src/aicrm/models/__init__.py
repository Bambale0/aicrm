"""
Модели базы данных
"""

from .ai_prompt import AIPrompt
from .ai_settings import AISettings
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
from .automation_log import AutomationLog
from .avito_chat import AvitoChatSettings, AvitoGlobalSettings
from .base import Base, BaseModel
from .campaign import Campaign
from .category import Category
from .communication import Communication
from .customer import Customer
from .email_template import EmailTemplate
from .order import Order
from .organization import Organization
from .plugin import (
    Plugin,
    PluginAction,
    PluginHook,
    PluginPermission,
    PluginRegistry,
    PluginTemplate,
)
from .product import Product
from .production_step import ProductionStep
from .service import Service
from .system_settings import SystemSettings
from .task import Task
from .telegram_chat import TelegramChat
from .telegram_settings import TelegramSettings
from .user import User
from .user_settings import UserSettings

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
    "Organization",
    "Campaign",
    "SystemSettings",
    "UserSettings",
    # Automation models
    "Process",
    "Stage",
    "Trigger",
    "Robot",
    "RobotActionConfig",
    "EntityType",
    "TriggerEvent",
    "RobotAction",
    "AutomationLog",
    # Plugin models
    "Plugin",
    "PluginAction",
    "PluginHook",
    "PluginPermission",
    "PluginRegistry",
    "PluginTemplate",
]
