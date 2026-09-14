"""Persisted settings and usage telemetry for the external AI API."""
from sqlalchemy import Column, ForeignKey, Integer, String, Text

from .base import BaseModel


class AIConnectionSettings(BaseModel):
    __tablename__ = "ai_connection_settings"

    encrypted_api_key = Column(Text, nullable=True)
    selected_model = Column(String(255), nullable=True)


class AIUsageEvent(BaseModel):
    """Immutable token usage reported by the upstream AI API."""

    __tablename__ = "ai_usage_events"

    connection_id = Column(
        Integer,
        ForeignKey("ai_connection_settings.id"),
        nullable=False,
        index=True,
    )
    operation = Column(String(100), nullable=False, index=True)
    model = Column(String(255), nullable=False, index=True)
    provider_request_id = Column(String(255), nullable=True, index=True)

    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    prompt_cache_hit_tokens = Column(Integer, default=0, nullable=False)
    prompt_cache_miss_tokens = Column(Integer, default=0, nullable=False)
    reasoning_tokens = Column(Integer, default=0, nullable=False)
