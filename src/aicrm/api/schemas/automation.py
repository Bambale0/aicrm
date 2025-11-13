"""
Pydantic схемы для автоматизации
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.automation import EntityType, TriggerEvent, RobotAction


class ProcessBase(BaseModel):
    """Базовая схема бизнес-процесса"""
    name: str = Field(..., description="Название процесса", example="Продажа полиграфии")
    description: Optional[str] = Field(None, description="Описание процесса")
    entity_type: EntityType = Field(..., description="Тип сущности")


class ProcessCreate(ProcessBase):
    """Схема создания процесса"""
    pass


class ProcessUpdate(BaseModel):
    """Схема обновления процесса"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProcessResponse(ProcessBase):
    """Схема ответа процесса"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StageBase(BaseModel):
    """Базовая схема стадии"""
    name: str = Field(..., description="Название стадии", example="Новая заявка")
    description: Optional[str] = Field(None, description="Описание стадии")
    entity_type: EntityType = Field(..., description="Тип сущности")
    process_id: int = Field(..., description="ID процесса")
    order_index: int = Field(0, description="Порядок стадии")
    color: Optional[str] = Field(None, description="HEX цвет", example="#FFEB3B")


class StageCreate(StageBase):
    """Схема создания стадии"""
    pass


class StageUpdate(BaseModel):
    """Схема обновления стадии"""
    name: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class StageResponse(StageBase):
    """Схема ответа стадии"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TriggerBase(BaseModel):
    """Базовая схема триггера"""
    name: str = Field(..., description="Название триггера", example="Клиент открыл КП")
    description: Optional[str] = Field(None, description="Описание триггера")
    entity_type: EntityType = Field(..., description="Тип сущности")
    event_type: TriggerEvent = Field(..., description="Тип события")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Условия срабатывания")
    target_stage_id: int = Field(..., description="ID целевой стадии")


class TriggerCreate(TriggerBase):
    """Схема создания триггера"""
    pass


class TriggerUpdate(BaseModel):
    """Схема обновления триггера"""
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    target_stage_id: Optional[int] = None
    is_active: Optional[bool] = None


class TriggerResponse(TriggerBase):
    """Схема ответа триггера"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RobotActionConfigBase(BaseModel):
    """Базовая схема конфигурации действия робота"""
    action_type: RobotAction = Field(..., description="Тип действия")
    execution_order: int = Field(..., description="Порядок выполнения", ge=1)
    config: Optional[Dict[str, Any]] = Field(None, description="Конфигурация действия")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Условия выполнения")
    delay_seconds: int = Field(0, description="Задержка выполнения", ge=0)


class RobotActionConfigCreate(RobotActionConfigBase):
    """Схема создания конфигурации действия"""
    pass


class RobotActionConfigUpdate(BaseModel):
    """Схема обновления конфигурации действия"""
    execution_order: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    delay_seconds: Optional[int] = None


class RobotActionConfigResponse(RobotActionConfigBase):
    """Схема ответа конфигурации действия"""
    id: int
    robot_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RobotBase(BaseModel):
    """Базовая схема робота"""
    name: str = Field(..., description="Название робота", example="Первичный контакт")
    description: Optional[str] = Field(None, description="Описание робота")
    entity_type: EntityType = Field(..., description="Тип сущности")
    stage_id: int = Field(..., description="ID стадии")


class RobotCreate(RobotBase):
    """Схема создания робота"""
    actions: List[RobotActionConfigCreate] = Field(..., description="Действия робота")


class RobotUpdate(BaseModel):
    """Схема обновления робота"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RobotResponse(RobotBase):
    """Схема ответа робота"""
    id: int
    actions: List[RobotActionConfigResponse]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Схемы для API эндпоинтов

class AutomationEventRequest(BaseModel):
    """Схема запроса события автоматизации"""
    event_data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные события")


class AutomationEventResponse(BaseModel):
    """Схема ответа события автоматизации"""
    message: str = Field(..., description="Сообщение о результате")
    result: Dict[str, Any] = Field(..., description="Результат обработки")


class MoveToStageRequest(BaseModel):
    """Схема запроса перемещения на стадию"""
    pass  # Пустая, так как все параметры в URL


class MoveToStageResponse(BaseModel):
    """Схема ответа перемещения на стадию"""
    message: str = Field(..., description="Сообщение о результате")
    result: Dict[str, Any] = Field(..., description="Результат перемещения")


# Специфические схемы для разных типов событий

class CustomerCreatedRequest(BaseModel):
    """Событие создания клиента"""
    pass


class CustomerUpdatedRequest(BaseModel):
    """Событие обновления клиента"""
    changes: Dict[str, Any] = Field(..., description="Изменения в клиенте")


class OrderCreatedRequest(BaseModel):
    """Событие создания заказа"""
    pass


class OrderStatusChangedRequest(BaseModel):
    """Событие изменения статуса заказа"""
    old_status: str = Field(..., description="Старый статус")
    new_status: str = Field(..., description="Новый статус")


class OrderCompletedRequest(BaseModel):
    """Событие завершения заказа"""
    pass


class PaymentReceivedRequest(BaseModel):
    """Событие получения оплаты"""
    amount: float = Field(..., description="Сумма оплаты", gt=0)


class TaskCreatedRequest(BaseModel):
    """Событие создания задачи"""
    pass


class TaskStatusChangedRequest(BaseModel):
    """Событие изменения статуса задачи"""
    old_status: str = Field(..., description="Старый статус")
    new_status: str = Field(..., description="Новый статус")


class TaskCompletedRequest(BaseModel):
    """Событие завершения задачи"""
    pass


class DeadlineApproachingRequest(BaseModel):
    """Событие приближения дедлайна"""
    hours_left: int = Field(..., description="Часов до дедлайна", gt=0)


class ProductionStartedRequest(BaseModel):
    """Событие начала производства"""
    pass


class ProductionStepCompletedRequest(BaseModel):
    """Событие завершения этапа производства"""
    pass


class ProductionCompletedRequest(BaseModel):
    """Событие завершения производства"""
    pass


class ProductionOverdueRequest(BaseModel):
    """Событие просрочки производства"""
    overdue_hours: float = Field(..., description="Часов просрочки", gt=0)


class MessageReceivedRequest(BaseModel):
    """Событие получения сообщения"""
    communication_id: int = Field(..., description="ID коммуникации")


class MessageSentRequest(BaseModel):
    """Событие отправки сообщения"""
    communication_id: int = Field(..., description="ID коммуникации")


class EmailOpenedRequest(BaseModel):
    """Событие открытия email"""
    communication_id: int = Field(..., description="ID коммуникации")


# Общие ответы для всех событий
class AutomationResultResponse(BaseModel):
    """Общий ответ автоматизации"""
    result: Dict[str, Any] = Field(..., description="Результат обработки события")


# ИИ-функционал для генерации цепочек автоматизации

class AutomationChainRequest(BaseModel):
    """Запрос на генерацию цепочки автоматизации"""
    description: str = Field(
        ...,
        description="Описание бизнес-процесса на естественном языке",
        example="Когда создается новый клиент, отправить приветственное email, создать задачу менеджеру и переместить в стадию 'Новый лид'"
    )
    entity_type: EntityType = Field(
        ...,
        description="Тип сущности для автоматизации",
        example="customer"
    )
    complexity_level: Optional[str] = Field(
        "medium",
        description="Уровень сложности: simple, medium, complex",
        pattern="^(simple|medium|complex)$"
    )


class GeneratedProcess(BaseModel):
    """Сгенерированный процесс"""
    name: str = Field(..., description="Название процесса")
    description: str = Field(..., description="Описание процесса")
    entity_type: EntityType = Field(..., description="Тип сущности")
    stages: List[Dict[str, Any]] = Field(..., description="Стадии процесса")
    triggers: List[Dict[str, Any]] = Field(..., description="Триггеры процесса")
    robots: List[Dict[str, Any]] = Field(..., description="Роботы процесса")


class AutomationChainResponse(BaseModel):
    """Ответ генерации цепочки автоматизации"""
    success: bool = Field(..., description="Успешность генерации")
    message: str = Field(..., description="Сообщение о результате")
    generated_process: Optional[GeneratedProcess] = Field(None, description="Сгенерированный процесс")
    applied_changes: Optional[Dict[str, Any]] = Field(None, description="Примененные изменения")
    error: Optional[str] = Field(None, description="Ошибка генерации")


class OptimizationRequest(BaseModel):
    """Запрос на оптимизацию цепочки"""
    optimization_goal: str = Field(
        ...,
        description="Цель оптимизации",
        pattern="^(performance|reliability|cost)$",
        example="performance"
    )


class OptimizationResponse(BaseModel):
    """Ответ оптимизации цепочки"""
    success: bool = Field(..., description="Успешность оптимизации")
    message: str = Field(..., description="Сообщение о результате")
    optimizations_applied: List[Dict[str, Any]] = Field(..., description="Примененные оптимизации")
    performance_improvements: Optional[Dict[str, Any]] = Field(None, description="Улучшения производительности")
    error: Optional[str] = Field(None, description="Ошибка оптимизации")


class ImprovementSuggestion(BaseModel):
    """Предложение по улучшению"""
    type: str = Field(..., description="Тип предложения: bottleneck, optimization, new_scenario")
    title: str = Field(..., description="Заголовок предложения")
    description: str = Field(..., description="Описание предложения")
    impact_level: str = Field(..., description="Уровень влияния: low, medium, high")
    implementation_complexity: str = Field(..., description="Сложность реализации: low, medium, high")
    estimated_benefit: Optional[str] = Field(None, description="Ожидаемая польза")
    suggested_actions: List[str] = Field(..., description="Предлагаемые действия")


class AutomationAnalysisResponse(BaseModel):
    """Ответ анализа автоматизации"""
    analysis_period: Dict[str, Any] = Field(..., description="Период анализа")
    total_processes: int = Field(..., description="Общее количество процессов")
    active_triggers: int = Field(..., description="Активных триггеров")
    executed_robots: int = Field(..., description="Выполненных роботов")
    success_rate: float = Field(..., description="Процент успешности")
    bottlenecks: List[Dict[str, Any]] = Field(..., description="Узкие места")
    suggestions: List[ImprovementSuggestion] = Field(..., description="Предложения по улучшению")
    performance_metrics: Dict[str, Any] = Field(..., description="Метрики производительности")
