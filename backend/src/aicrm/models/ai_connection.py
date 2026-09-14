"""Persisted settings for the external AI API used by the CRM."""
from sqlalchemy import Column, String, Text

from .base import BaseModel


class AIConnectionSettings(BaseModel):
    __tablename__ = "ai_connection_settings"

    encrypted_api_key = Column(Text, nullable=True)
    selected_model = Column(String(255), nullable=True)
