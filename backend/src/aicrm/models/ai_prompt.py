"""
Модель AI промптов для системы
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from .base import BaseModel


class AIPrompt(BaseModel):
    """Модель для хранения AI промптов"""

    __tablename__ = "ai_prompts"

    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    model = Column(String(255), default="deepseek/deepseek-chat-v3.1")

    def __repr__(self) -> str:
        return f"<AIPrompt(id={self.id}, name='{self.name}', category='{self.category}', active={self.is_active})>"
