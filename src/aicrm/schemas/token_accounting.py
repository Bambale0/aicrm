"""
Схемы для учета токенов AI - OpenAPI 3.1.0 compliant
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenQuotaSetRequest(BaseModel):
    """
    Запрос на установку квоты токенов
    """

    entity_type: str = Field(..., description="Тип сущности")
    entity_id: int = Field(..., description="ID сущности (компании или пользователя)")
    quota_type: str = Field(..., description="Тип квоты")
    limit_tokens: Optional[int] = Field(
        None, ge=0, description="Лимит токенов (NULL = безлимит)"
    )
    alert_threshold: Optional[int] = Field(
        None, ge=1, le=99, description="Порог для уведомления (%)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity_type": "company",
                "entity_id": 123,
                "quota_type": "monthly",
                "limit_tokens": 1000000,
                "alert_threshold": 80,
            }
        }
    )


class TokenQuotaResponse(BaseModel):
    """
    Ответ с информацией о квоте токенов
    """

    id: int = Field(..., description="ID квоты")
    entity_type: str = Field(..., description="Тип сущности")
    entity_id: int = Field(..., description="ID сущности")
    quota_type: str = Field(..., description="Тип квоты")
    limit_tokens: Optional[int] = Field(None, description="Лимит токенов")
    used_tokens: int = Field(..., description="Использованные токены")
    reset_at: Optional[datetime] = Field(None, description="Дата сброса")
    alert_threshold: Optional[int] = Field(None, description="Порог уведомления")
    is_active: bool = Field(..., description="Активна ли квота")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class TokenUsageStats(BaseModel):
    """
    Статистика использования токенов
    """

    entity_type: str = Field(..., description="Тип сущности")
    entity_id: int = Field(..., description="ID сущности")
    quota_type: str = Field(..., description="Тип квоты")
    limit_tokens: Optional[int] = Field(None, description="Лимит токенов")
    used_tokens: int = Field(..., description="Использованные токены")
    remaining_tokens: Optional[int] = Field(None, description="Оставшиеся токены")
    percentage_used: float = Field(..., description="Процент использования")
    reset_at: Optional[datetime] = Field(None, description="Дата сброса")
    daily_avg_usage: float = Field(..., description="Среднее дневное использование")
    top_workflows_by_tokens: List[Dict[str, Any]] = Field(
        ..., description="Топ workflow по использованию токенов"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity_type": "company",
                "entity_id": 123,
                "quota_type": "monthly",
                "limit_tokens": 1000000,
                "used_tokens": 750000,
                "remaining_tokens": 250000,
                "percentage_used": 75.0,
                "reset_at": "2025-12-01T00:00:00Z",
                "daily_avg_usage": 25000.0,
                "top_workflows_by_tokens": [
                    {
                        "workflow_id": "wf_123",
                        "workflow_name": "Обработка заказов",
                        "total_tokens": 500000,
                    }
                ],
            }
        }
    )


class TokenTransactionResponse(BaseModel):
    """
    Ответ с информацией о транзакции токенов
    """

    id: int = Field(..., description="ID транзакции")
    quota_id: Optional[int] = Field(None, description="ID квоты")
    workflow_execution_id: Optional[str] = Field(
        None, description="ID выполнения workflow"
    )
    ai_provider: str = Field(..., description="Провайдер AI")
    ai_model: str = Field(..., description="Модель AI")
    prompt_tokens: int = Field(..., description="Токены в запросе")
    completion_tokens: int = Field(..., description="Токены в ответе")
    total_tokens: int = Field(..., description="Общее количество токенов")
    estimated_cost: Optional[float] = Field(None, description="Расчетная стоимость")
    request_payload: Optional[Dict[str, Any]] = Field(
        None, description="Пейлоад запроса"
    )
    response_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Метаданные ответа"
    )
    timestamp: datetime = Field(..., description="Время транзакции")


class TokenQuotaListResponse(BaseModel):
    """
    Ответ со списком квот токенов
    """

    quotas: List[TokenQuotaResponse] = Field(..., description="Список квот")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")


class TokenTransactionListResponse(BaseModel):
    """
    Ответ со списком транзакций токенов
    """

    transactions: List[TokenTransactionResponse] = Field(
        ..., description="Список транзакций"
    )
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")


class TokenQuotaUpdateRequest(BaseModel):
    """
    Запрос на обновление квоты токенов
    """

    limit_tokens: Optional[int] = Field(None, ge=0, description="Новый лимит токенов")
    alert_threshold: Optional[int] = Field(
        None, ge=1, le=99, description="Новый порог уведомления"
    )
    is_active: Optional[bool] = Field(None, description="Активна ли квота")


class TokenAlertInfo(BaseModel):
    """
    Информация об алерте токенов
    """

    quota_id: int = Field(..., description="ID квоты")
    entity_type: str = Field(..., description="Тип сущности")
    entity_id: int = Field(..., description="ID сущности")
    current_usage: int = Field(..., description="Текущее использование")
    limit_tokens: int = Field(..., description="Лимит токенов")
    percentage_used: float = Field(..., description="Процент использования")
    alert_threshold: int = Field(..., description="Порог уведомления")
