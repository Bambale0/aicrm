"""
Схемы для AI Orchestrator Workflows - OpenAPI 3.1.0 compliant
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Перечисления для типов
class EventType(str):
    """Типы событий-триггеров"""

    ON_ORDER_CREATED = "ON_ORDER_CREATED"
    ON_LEAD_ADD = "ON_LEAD_ADD"
    ON_PRODUCTION_STEP_COMPLETE = "ON_PRODUCTION_STEP_COMPLETE"
    ON_CUSTOMER_CREATED = "ON_CUSTOMER_CREATED"
    ON_DEAL_STATUS_CHANGED = "ON_DEAL_STATUS_CHANGED"


class ActionType(str):
    """Типы действий"""

    SEND_NOTIFICATION = "send_notification"
    CREATE_TASK = "create_task"
    UPDATE_ENTITY = "update_entity"
    CALL_AI = "call_ai"
    MAKE_HTTP_REQUEST = "make_http_request"


class ExecutionStatus(str):
    """Статусы выполнения"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Схемы запросов
class WorkflowCreateFromPromptRequest(BaseModel):
    """
    Запрос на создание workflow из текстового описания
    """

    prompt: str = Field(
        ..., description="Текстовое описание бизнес-сценария на естественном языке"
    )
    name: Optional[str] = Field(None, description="Человеко-читаемое название workflow")
    is_active: bool = Field(
        True, description="Активировать правило сразу после создания"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Когда приходит заказ с типом 'Срочный' и суммой больше 100000, отправляй уведомление в Telegram-чат 'urgent_orders', создавай задачу с высоким приоритетом менеджеру Ивану и обновляй поле 'статус_обработки' заказа на 'Взято в работу'.",
                "name": "Обработка срочных VIP-заказов",
                "is_active": True,
            }
        }
    )


class WorkflowUpdateRequest(BaseModel):
    """
    Запрос на обновление workflow
    """

    name: Optional[str] = Field(None, description="Новое название workflow")
    trigger: Optional[Dict[str, Any]] = Field(
        None, description="Новая конфигурация триггера"
    )
    conditions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Новый список условий"
    )
    actions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Новый список действий"
    )
    is_active: Optional[bool] = Field(None, description="Активность workflow")


class TestEventRequest(BaseModel):
    """
    Запрос на тестирование workflow
    """

    event_type: str = Field(..., description="Тип события")
    payload: Dict[str, Any] = Field(..., description="Пейлоад события")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "ON_ORDER_CREATED",
                "payload": {
                    "order_id": 789,
                    "order_type": "Срочный",
                    "total": 150000,
                    "customer_city": "Москва",
                },
            }
        }
    )


class IncomingEvent(BaseModel):
    """
    Входящее событие от основной CRM
    """

    event_id: str = Field(..., description="Уникальный ID события")
    event_type: str = Field(..., description="Тип события")
    entity_type: str = Field(..., description="Тип сущности")
    entity_id: int | str = Field(..., description="ID сущности")
    payload: Dict[str, Any] = Field(..., description="Данные события")
    timestamp: datetime = Field(..., description="Время события")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "event_abc123",
                "event_type": "ON_ORDER_CREATED",
                "entity_type": "order",
                "entity_id": 456,
                "payload": {"total": 75000, "status": "new"},
                "timestamp": "2024-01-15T12:30:00Z",
            }
        }
    )


class CrmConnectorConfig(BaseModel):
    """
    Конфигурация коннектора к API основной CRM
    """

    base_url: str = Field(..., description="Базовый URL API CRM")
    api_key: str = Field(..., description="API ключ для аутентификации")
    auth_type: str = Field("bearer", description="Тип аутентификации")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "base_url": "https://api.your-crm.com/v1",
                "api_key": "your-secret-key",
                "auth_type": "bearer",
            }
        }
    )


# Схемы ответов
class TriggerDefinition(BaseModel):
    """
    Определение триггера
    """

    event_type: str = Field(..., description="Тип события-триггера")


class Condition(BaseModel):
    """
    Условие для выполнения workflow
    """

    field_path: str = Field(..., description="Путь к полю в payload события")
    operator: str = Field(..., description="Оператор сравнения")
    value: Any = Field(..., description="Значение для сравнения")


class Action(BaseModel):
    """
    Действие в workflow
    """

    name: str = Field(..., description="Название действия")
    type: str = Field(..., description="Тип действия")
    config: Dict[str, Any] = Field(..., description="Конфигурация действия")


class WorkflowDetailResponse(BaseModel):
    """
    Детальная информация о workflow
    """

    id: int = Field(..., description="ID workflow")
    name: str = Field(..., description="Название workflow")
    description_ai: Optional[str] = Field(None, description="Пояснение от AI")
    trigger: TriggerDefinition = Field(..., description="Конфигурация триггера")
    conditions: List[Condition] = Field(..., description="Список условий")
    actions: List[Action] = Field(..., description="Список действий")
    is_active: bool = Field(..., description="Активен ли workflow")
    created_at: datetime = Field(..., description="Время создания")
    created_by: Optional[int] = Field(None, description="ID создателя")


class WorkflowSummaryResponse(BaseModel):
    """
    Краткая информация о workflow
    """

    id: int = Field(..., description="ID workflow")
    name: str = Field(..., description="Название workflow")
    is_active: bool = Field(..., description="Активен ли workflow")
    created_at: datetime = Field(..., description="Время создания")


class PaginatedWorkflowList(BaseModel):
    """
    Пагинированный список workflow
    """

    workflows: List[WorkflowSummaryResponse] = Field(..., description="Список workflow")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")


class WorkflowTestResponse(BaseModel):
    """
    Результат тестирования workflow
    """

    workflow_id: int = Field(..., description="ID workflow")
    triggered: bool = Field(..., description="Сработал ли триггер")
    conditions_met: bool = Field(..., description="Выполнены ли условия")
    actions_executed: List[Dict[str, Any]] = Field(
        ..., description="Результаты выполнения действий"
    )
    execution_time: float = Field(..., description="Время выполнения в секундах")


class ExecutionLogEntry(BaseModel):
    """
    Запись в логе выполнения
    """

    id: int = Field(..., description="ID выполнения")
    workflow_id: int = Field(..., description="ID workflow")
    workflow_name: str = Field(..., description="Название workflow")
    trigger_event: Dict[str, Any] = Field(..., description="Исходное событие")
    execution_status: str = Field(..., description="Статус выполнения")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class PaginatedExecutionList(BaseModel):
    """
    Пагинированный список выполнений
    """

    executions: List[ExecutionLogEntry] = Field(..., description="Список выполнений")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")


class ActionExecutionDetail(BaseModel):
    """
    Детали выполнения действия
    """

    action_name: str = Field(..., description="Название действия")
    action_type: str = Field(..., description="Тип действия")
    execution_status: str = Field(..., description="Статус выполнения")
    execution_result: Optional[Dict[str, Any]] = Field(
        None, description="Результат выполнения"
    )
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")


class ExecutionDetailResponse(BaseModel):
    """
    Детальная информация о выполнении workflow
    """

    id: int = Field(..., description="ID выполнения")
    workflow_id: int = Field(..., description="ID workflow")
    workflow_name: str = Field(..., description="Название workflow")
    trigger_event: Dict[str, Any] = Field(..., description="Исходное событие")
    execution_status: str = Field(..., description="Статус выполнения")
    execution_result: Optional[Dict[str, Any]] = Field(
        None, description="Общий результат"
    )
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    action_executions: List[ActionExecutionDetail] = Field(
        ..., description="Выполненные действия"
    )
