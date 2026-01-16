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
from .avito_chat import AvitoChatSettings
from .base import Base, BaseModel
from .campaign import Campaign, CampaignAISettings
from .category import Category
from .communication import Communication
from .customer import Customer
from .email_settings import EmailSettings
from .email_template import EmailTemplate
from .order import Order
from .organization import Organization
from .plugin import Plugin
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
    "UserSettings",
    "Customer",
    "Order",
    "ProductionStep",
    "Communication",
    "Task",
    "AvitoChatSettings",
    "AIUsage",
    "AIPrompt",
    "AISettings",
    "Organization",
    "Campaign",
    "CampaignAISettings",
    "Category",
    "EmailSettings",
    "EmailTemplate",
    "Plugin",
    "Product",
    "Service",
    "SystemSettings",
    "TelegramChat",
    "TelegramSettings",
    "AutomationLog",
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
