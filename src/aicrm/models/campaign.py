"""
Модель кампаний с AI настройками
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Campaign(BaseModel):
    """Модель маркетинговых кампаний"""

    __tablename__ = "campaigns"

    # Основная информация
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Настройки кампании
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="draft")  # draft, active, paused, completed

    # Связи
    organization = relationship("Organization")
    ai_settings = relationship(
        "CampaignAISettings", uselist=False, back_populates="campaign"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"


class CampaignAISettings(BaseModel):
    """Модель AI настроек для конкретных кампаний"""

    __tablename__ = "campaign_ai_settings"

    campaign_id = Column(
        Integer, ForeignKey("campaigns.id"), nullable=False, unique=True
    )

    # Основные настройки AI (могут переопределять глобальные)
    default_model = Column(
        String, nullable=False, default="deepseek/deepseek-chat-v3.1"
    )
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=1000)

    # API ключи для кампании (зашифрованные)
    openrouter_api_key = Column(Text, nullable=True)
    openai_api_key = Column(Text, nullable=True)
    huggingface_api_key = Column(Text, nullable=True)

    # Настройки провайдера для кампании
    provider = Column(String, nullable=False, default="openrouter")

    # Автоматические ответы для кампании
    auto_reply_enabled = Column(Boolean, default=True)
    auto_reply_temperature = Column(Float, default=0.5)
    auto_reply_max_tokens = Column(Integer, default=500)

    # Специфические настройки для кампании
    custom_prompt = Column(Text, nullable=True)  # кастомный промпт для кампании
    target_audience = Column(String(255), nullable=True)  # целевая аудитория
    brand_voice = Column(String(100), nullable=True)  # стиль общения

    # Лимиты для кампании
    daily_token_limit = Column(Integer, nullable=True)
    monthly_token_limit = Column(Integer, nullable=True)

    # Связи
    campaign = relationship("Campaign", back_populates="ai_settings")

    def __repr__(self) -> str:
        return f"<CampaignAISettings(campaign_id={self.campaign_id}, provider={self.provider}, model={self.default_model})>"
