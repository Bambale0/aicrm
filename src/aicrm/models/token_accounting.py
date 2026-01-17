"""
Модели для учета токенов AI
"""

from sqlalchemy import (
    DECIMAL,
    UUID,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class TokenQuota(BaseModel):
    """Модель квот токенов для компаний и пользователей"""

    __tablename__ = "token_quotas"

    entity_type = Column(String(20), nullable=False, index=True)  # 'company' или 'user'
    entity_id = Column(
        Integer, nullable=False, index=True
    )  # ID компании или пользователя
    quota_type = Column(
        String(50), nullable=False
    )  # 'monthly', 'total', 'per_workflow'
    limit_tokens = Column(Integer, nullable=True)  # Лимит (NULL = безлимит)
    used_tokens = Column(Integer, default=0)
    reset_at = Column(DateTime, nullable=True)  # Дата сброса для monthly
    alert_threshold = Column(
        Integer, nullable=True
    )  # Порог для уведомления (например, 80%)
    is_active = Column(Boolean, default=True)

    # Связи с транзакциями
    transactions = relationship(
        "TokenTransaction", back_populates="quota", cascade="all, delete-orphan"
    )

    __table_args__ = {"schema": "public"}

    def __repr__(self) -> str:
        return f"<TokenQuota(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id}, quota_type={self.quota_type}, used={self.used_tokens}, limit={self.limit_tokens})>"


class TokenTransaction(BaseModel):
    """Модель детальных транзакций токенов"""

    __tablename__ = "token_transactions"

    quota_id = Column(Integer, ForeignKey("token_quotas.id"), nullable=True, index=True)
    workflow_execution_id = Column(
        String, nullable=True
    )  # Связь с запуском workflow (если есть)

    # Провайдер и модель AI
    ai_provider = Column(
        String(20), nullable=False
    )  # 'openrouter', 'openai', 'huggingface'
    ai_model = Column(String(100), nullable=False)  # 'gpt-4', 'llama-3.1-8b-instruct'

    # Статистика токенов
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)  # Вычисляемое поле

    # Стоимость и метаданные
    estimated_cost = Column(
        DECIMAL(10, 6), nullable=True
    )  # Расчетная стоимость в USD/RUB
    request_payload = Column(JSONB, nullable=True)  # Промпт и метаданные запроса
    response_metadata = Column(JSONB, nullable=True)  # Метаданные ответа

    # Связи
    quota = relationship("TokenQuota", back_populates="transactions")

    __table_args__ = {"schema": "public"}

    def __repr__(self) -> str:
        return f"<TokenTransaction(id={self.id}, model={self.ai_model}, tokens={self.total_tokens}, cost={self.estimated_cost})>"


# Модели для AI Orchestrator Workflows
class Workflow(BaseModel):
    """Модель workflow - последовательность действий по триггеру"""

    __tablename__ = "workflows"

    name = Column(String(255), nullable=False)
    description_ai = Column(Text, nullable=True)  # Пояснение от AI
    trigger = Column(JSONB, nullable=False)  # Конфигурация триггера
    conditions = Column(JSONB, nullable=False, default=list)  # Список условий
    actions = Column(JSONB, nullable=False, default=list)  # Список действий
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=True)  # ID пользователя-создателя

    # Связи
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )

    __table_args__ = {"schema": "public"}

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, active={self.is_active})>"


class WorkflowExecution(BaseModel):
    """Модель выполнения workflow"""

    __tablename__ = "workflow_executions"

    workflow_id = Column(
        Integer, ForeignKey("workflows.id"), nullable=False, index=True
    )
    trigger_event = Column(JSONB, nullable=False)  # Исходное событие
    execution_status = Column(
        String(50), default="pending"
    )  # 'pending', 'running', 'completed', 'failed'
    execution_result = Column(JSONB, nullable=True)  # Результаты выполнения
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Связи
    workflow = relationship("Workflow", back_populates="executions")
    action_executions = relationship(
        "ActionExecution", back_populates="execution", cascade="all, delete-orphan"
    )

    __table_args__ = {"schema": "public"}

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, status={self.execution_status})>"


class ActionExecution(BaseModel):
    """Модель выполнения отдельного действия"""

    __tablename__ = "action_executions"

    execution_id = Column(
        Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True
    )
    action_name = Column(String(255), nullable=False)
    action_type = Column(
        String(50), nullable=False
    )  # 'send_notification', 'create_task', etc.
    action_config = Column(JSONB, nullable=False)  # Конфигурация действия
    execution_status = Column(
        String(50), default="pending"
    )  # 'pending', 'running', 'completed', 'failed'
    execution_result = Column(JSONB, nullable=True)  # Результат выполнения
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Связи
    execution = relationship("WorkflowExecution", back_populates="action_executions")

    __table_args__ = {"schema": "public"}

    def __repr__(self) -> str:
        return f"<ActionExecution(id={self.id}, action={self.action_name}, status={self.execution_status})>"
