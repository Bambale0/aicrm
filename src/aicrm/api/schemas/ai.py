"""
Схемы для AI API - OpenAPI 3.0.0 compliant
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...services.ai.intent_service import IntentType


class AIAnalysisRequest(BaseModel):
    """
    Запрос на анализ намерения сообщения с помощью AI.

    Анализирует входящее сообщение клиента и определяет его намерение,
    генерирует соответствующий ответ.
    """

    message: str = Field(
        ...,
        description="Текст сообщения для анализа",
        example="Хочу заказать печать на 50 футболках",
        min_length=1,
        max_length=10000,
    )

    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Дополнительный контекст для анализа",
        example={
            "customer_name": "Иван Петров",
            "previous_orders": 3,
            "customer_type": "regular",
        },
    )

    model: Optional[str] = Field(
        None,
        description="Модель AI для использования",
        example="deepseek/deepseek-chat-v3.1",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Сколько стоит печать логотипа на футболке?",
                "context": {
                    "customer_name": "Анна Сидорова",
                    "preferred_contact": "email",
                },
            }
        }


class AIAnalysisResponse(BaseModel):
    """
    Ответ с результатом AI анализа сообщения.

    Содержит определенное намерение, сгенерированный ответ
    и рекомендации по дальнейшим действиям.
    """

    intent: IntentType = Field(
        ..., description="Определенное намерение пользователя", example="question"
    )

    response: str = Field(
        ...,
        description="Сгенерированный AI ответ",
        example="Здравствуйте! Стоимость печати логотипа начинается от 500 рублей за единицу при заказе от 10 штук.",
    )

    needs_human_intervention: bool = Field(
        ..., description="Требуется ли вмешательство человека", example=False
    )

    suggested_actions: List[str] = Field(
        ...,
        description="Рекомендуемые действия системы",
        example=["send_price_list", "schedule_followup"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "question",
                "response": "Спасибо за вопрос! Я подготовлю для вас подробный прайс-лист с ценами на печать.",
                "needs_human_intervention": False,
                "suggested_actions": ["send_price_list", "log_interaction"],
            }
        }


class AIChatRequest(BaseModel):
    """
    Запрос на прямой чат с AI моделью.

    Позволяет отправлять сообщения в формате чата
    с настройкой параметров генерации.
    """

    messages: List[Dict[str, str]] = Field(
        ...,
        description="Список сообщений в формате чата",
        example=[
            {"role": "system", "content": "Ты помощник компании по печати"},
            {"role": "user", "content": "Какие услуги вы предлагаете?"},
        ],
        min_items=1,
    )

    model: Optional[str] = Field(
        None,
        description="Модель AI для использования",
        example="deepseek/deepseek-coder:33b-instruct",
    )

    temperature: Optional[float] = Field(
        0.7,
        description="Температура генерации (0.0 - 2.0)",
        ge=0.0,
        le=2.0,
        example=0.7,
    )

    max_tokens: Optional[int] = Field(
        None,
        description="Максимальное количество токенов в ответе",
        ge=1,
        le=4000,
        example=1000,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "Ты эксперт по печати на текстиле"},
                    {"role": "user", "content": "Как подготовить дизайн для печати?"},
                ],
                "model": "deepseek/deepseek-coder:33b-instruct",
                "temperature": 0.7,
                "max_tokens": 1500,
            }
        }


class AIChatResponse(BaseModel):
    """
    Ответ от AI чата.

    Содержит сгенерированный текст и информацию
    о использованной модели.
    """

    response: str = Field(
        ...,
        description="Сгенерированный AI ответ",
        example="Для подготовки дизайна к печати рекомендуется использовать векторные форматы (SVG, AI, EPS) с разрешением не менее 300 DPI...",
    )

    model_used: str = Field(
        ...,
        description="Фактически использованная модель",
        example="deepseek/deepseek-coder:33b-instruct",
    )

    tokens_used: Optional[float] = Field(
        None, description="Количество использованных токенов", example=247.5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Отличный вопрос! Для печати на текстиле мы используем несколько технологий: DTG (прямая печать), вышивка, термотрансфер и шелкография. Выбор зависит от тиража, материала и требований к качеству.",
                "model_used": "deepseek/deepseek-coder:33b-instruct",
                "tokens_used": 156,
            }
        }


class AIModelInfo(BaseModel):
    """
    Информация о доступной AI модели.
    """

    id: str = Field(
        ...,
        description="Идентификатор модели",
        example="deepseek/deepseek-coder:33b-instruct",
    )
    name: str = Field(
        ..., description="Человеко-читаемое название", example="DeepSeek Coder 33B"
    )
    context_length: int = Field(
        ..., description="Максимальная длина контекста", example=16384
    )
    pricing: Dict[str, float] = Field(
        ..., description="Цены за токены", example={"input": 0.00035, "output": 0.00035}
    )


class AIModelsResponse(BaseModel):
    """
    Ответ со списком доступных AI моделей.
    """

    models: Dict[str, AIModelInfo] = Field(..., description="Словарь доступных моделей")
    current_provider: str = Field(
        ..., description="Текущий провайдер AI", example="openrouter"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "models": {
                    "deepseek-coder": {
                        "id": "deepseek/deepseek-coder:33b-instruct",
                        "name": "DeepSeek Coder 33B",
                        "context_length": 16384,
                        "pricing": {"input": 0.00035, "output": 0.00035},
                    }
                },
                "current_provider": "openrouter",
            }
        }


class AIStatusResponse(BaseModel):
    """
    Ответ со статусом AI сервиса.
    """

    provider: str = Field(..., description="Текущий провайдер", example="openrouter")
    status: str = Field(..., description="Статус сервиса", example="active")
    default_model: str = Field(
        ...,
        description="Модель по умолчанию",
        example="deepseek/deepseek-coder:33b-instruct",
    )
    available_models: List[str] = Field(..., description="Список доступных моделей")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openrouter",
                "status": "active",
                "default_model": "deepseek/deepseek-coder:33b-instruct",
                "available_models": [
                    "deepseek/deepseek-coder:33b-instruct",
                    "meta-llama/llama-3-70b-instruct",
                ],
            }
        }


class AIMonthlyUsageResponse(BaseModel):
    """
    Ответ со статистикой использования токенов за месяц.
    """

    period: Dict[str, Any] = Field(..., description="Период статистики")
    total_tokens: float = Field(
        ..., description="Общее количество токенов", example=15420.5
    )
    prompt_tokens: float = Field(..., description="Токены в запросах", example=8920.2)
    completion_tokens: float = Field(
        ..., description="Токены в ответах", example=6500.3
    )
    total_requests: int = Field(
        ..., description="Общее количество запросов", example=245
    )
    unique_models: int = Field(
        ..., description="Количество уникальных моделей", example=3
    )
    model_breakdown: List[Dict[str, Any]] = Field(
        ..., description="Статистика по моделям"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "period": {"year": 2025, "month": 11, "month_year": "2025-11"},
                "total_tokens": 15420.5,
                "prompt_tokens": 8920.2,
                "completion_tokens": 6500.3,
                "total_requests": 245,
                "unique_models": 3,
                "model_breakdown": [
                    {
                        "model": "deepseek/deepseek-chat-v3.1",
                        "tokens": 12000.5,
                        "requests": 180,
                    },
                    {
                        "model": "meta-llama/llama-3-70b-instruct",
                        "tokens": 3420.0,
                        "requests": 65,
                    },
                ],
            }
        }


class AIUsageHistoryResponse(BaseModel):
    """
    Ответ с историей использования токенов.
    """

    history: List[Dict[str, Any]] = Field(
        ..., description="Список записей использования"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "history": [
                    {
                        "id": 1,
                        "model_used": "deepseek/deepseek-chat-v3.1",
                        "endpoint": "chat",
                        "total_tokens": 245.7,
                        "created_at": "2025-11-13T10:30:00",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                ]
            }
        }
