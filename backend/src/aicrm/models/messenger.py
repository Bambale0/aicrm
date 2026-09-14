"""Generic messenger connector persistence."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

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



class MessengerChannel(BaseModel):
    """Admin-managed external chat/channel bound to a messenger integration."""

    __tablename__ = "messenger_channels"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "external_chat_id",
            "purpose",
            name="uq_messenger_channel_integration_chat_purpose",
        ),
    )

    integration_id = Column(
        Integer,
        ForeignKey("messenger_integrations.id"),
        nullable=False,
        index=True,
    )
    external_chat_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    purpose = Column(String(50), nullable=False, index=True)
    channel_type = Column(String(50), nullable=True)
    status = Column(String(50), default="configured", nullable=False, index=True)
    provider_data = Column(JSON, nullable=True)
    last_health_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
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



class MessengerIntakeSession(BaseModel):
    """Durable private-chat intake state for resident service requests."""

    __tablename__ = "messenger_intake_sessions"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            name="uq_messenger_intake_session_conversation",
        ),
    )

    conversation_id = Column(
        Integer,
        ForeignKey("messenger_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_user_id = Column(String(255), nullable=True, index=True)
    state = Column(String(50), default="full_name", nullable=False, index=True)

    full_name = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    problem = Column(Text, nullable=True)

    resident_id = Column(
        Integer,
        ForeignKey("housing_residents.id"),
        nullable=True,
        index=True,
    )
    request_id = Column(
        Integer,
        ForeignKey("housing_requests.id"),
        nullable=True,
        index=True,
    )
    completed_at = Column(DateTime, nullable=True)


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

class OperatorAlert(BaseModel):
    __tablename__ = "operator_alerts"

    conversation_id = Column(Integer, ForeignKey("messenger_conversations.id"), nullable=True, index=True)
    request_id = Column(Integer, ForeignKey("housing_requests.id"), nullable=True, index=True)
    kind = Column(String(50), default="problem", nullable=False, index=True)
    severity = Column(String(30), default="normal", nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(30), default="new", nullable=False, index=True)
    payload = Column(JSON, nullable=True)
