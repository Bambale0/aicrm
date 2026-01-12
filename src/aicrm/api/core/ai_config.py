"""
Конфигурация AI провайдеров
"""

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings


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
    DEFAULT_MODEL: str = "deepseek/deepseek-chat"
    FALLBACK_MODELS: list = ["moonshotai/kimi-k2", "openai/gpt-5-nano"]

    # Ограничения скорости
    REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS: int = 4000

    model_config = {
        "env_file": [".env", "../.env", "../../.env"],
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Allow extra fields from environment
    }


ai_config = AIConfig()
