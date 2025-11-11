"""
Конфигурация AI провайдеров
"""
from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional, Dict, Any


class AIProvider(str, Enum):
    OPENROUTER = "openrouter"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"


class AIConfig(BaseSettings):
    """Настройки AI провайдеров"""

    # Выбор провайдера
    AI_PROVIDER: AIProvider = AIProvider.OPENROUTER

    # Конфигурация OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Конфигурация Hugging Face (для будущей миграции)
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_BASE_URL: str = "https://api-inference.huggingface.co"

    # Конфигурация OpenAI (совместимая с OpenRouter)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    # Предпочтения моделей
    DEFAULT_MODEL: str = "deepseek/deepseek-coder:33b-instruct"
    FALLBACK_MODELS: list = [
        "meta-llama/llama-3-70b-instruct",
        "google/gemini-pro"
    ]

    # Ограничения скорости
    REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS: int = 4000

    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields from environment
    }


ai_config = AIConfig()
