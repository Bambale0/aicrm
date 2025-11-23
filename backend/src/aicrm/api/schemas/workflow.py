"""
Схемы для Workflow Engine
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...models.automation import EntityType


class WorkflowTrigger(BaseModel):
    """Запрос на запуск workflow"""
    workflow_id: str
    entity_type: EntityType
    entity_id: int
    trigger_data: Optional[Dict[str, Any]] = None


class WorkflowExecution(BaseModel):
    """Результат запуска workflow"""
    execution_id: str
    workflow_id: str
    entity_type: EntityType
    entity_id: int
    status: str


class WorkflowStepStatus(BaseModel):
    """Статус шага workflow"""
    step_id: str
    name: str
    status: str
    executed_at: Optional[str] = None
    error: Optional[str] = None


class WorkflowStatus(BaseModel):
    """Статус выполнения workflow"""
    execution_id: str
    workflow_id: str
    name: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    steps: List[WorkflowStepStatus]


class WorkflowInfo(BaseModel):
    """Информация о workflow"""
    id: str
    name: str
    entity_type: str
    description: str
    steps_count: int


class WorkflowList(BaseModel):
    """Список доступных workflow"""
    workflows: List[WorkflowInfo]
