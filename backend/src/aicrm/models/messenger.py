"""Generic messenger connector persistence."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from .base import BaseModel


class MessengerIntegration(BaseModel):
    __tablename__ = "messenger_integrations"

    provider = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="draft", nullable=False, index=True)
    credentials_encrypted = Column(Text, nullable=True)
    settings = Column(JSON, nullable=True)
    webhook_url = Column(String(1000), nullable=True)
    external_account_id = Column(String(255), nullable=True)
    last_health_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)


class MessengerConversation(BaseModel):
    __tablename__ = "messenger_conversations"

    integration_id = Column(Integer, ForeignKey("messenger_integrations.id"), nullable=False, index=True)
    external_chat_id = Column(String(255), nullable=False, index=True)
    resident_id = Column(Integer, ForeignKey("housing_residents.id"), nullable=True, index=True)
    status = Column(String(50), default="open", nullable=False, index=True)
    requires_attention = Column(Boolean, default=False, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=True, index=True)


class MessengerMessage(BaseModel):
    __tablename__ = "messenger_messages"

    conversation_id = Column(Integer, ForeignKey("messenger_conversations.id"), nullable=False, index=True)
    external_message_id = Column(String(255), nullable=True, index=True)
    direction = Column(String(20), nullable=False, index=True)
    message_type = Column(String(50), default="text", nullable=False)
    text = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    status = Column(String(50), default="received", nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)


class MessengerInboundEvent(BaseModel):
    __tablename__ = "messenger_inbound_events"

    integration_id = Column(Integer, ForeignKey("messenger_integrations.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    external_event_id = Column(String(255), nullable=True, index=True)
    status = Column(String(50), default="received", nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    error = Column(Text, nullable=True)
