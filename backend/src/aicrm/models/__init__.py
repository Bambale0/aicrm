"""Active database models for ЖКХ CRM."""

from .ai_connection import AIConnectionSettings
from .automation import (
    AutomationExecution,
    AutomationInstance,
    AutomationProcess,
    AutomationRule,
    AutomationStage,
)
from .base import Base, BaseModel
from .housing import (
    Building,
    ContractorCompany,
    Incident,
    Premise,
    RequestEvent,
    Resident,
    ServiceRequest,
)
from .messenger import (
    OperatorAlert,
    MessengerConversation,
    MessengerInboundEvent,
    MessengerIntegration,
    MessengerMessage,
)
from .user import User

__all__ = [
    "Base",
    "AIConnectionSettings",
    "BaseModel",
    "User",
    "Building",
    "Premise",
    "Resident",
    "ContractorCompany",
    "Incident",
    "ServiceRequest",
    "RequestEvent",
    "OperatorAlert",
    "MessengerIntegration",
    "MessengerConversation",
    "MessengerMessage",
    "MessengerInboundEvent",
    "AutomationProcess",
    "AutomationRule",
    "AutomationInstance",
    "AutomationStage",
    "AutomationExecution",
]
