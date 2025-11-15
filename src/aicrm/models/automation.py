"""
Модели автоматизации в стиле Bitrix24
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

from .base import Base


class EntityType(enum.Enum):
    """Типы сущностей для автоматизации"""
    CUSTOMER = "customer"
    ORDER = "order"
    TASK = "task"
    PRODUCTION_STEP = "production_step"
    COMMUNICATION = "communication"


class TriggerEvent(enum.Enum):
    """События триггеров"""
    # Заказы
    ORDER_CREATED = "order_created"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_COMPLETED = "order_completed"
    PAYMENT_RECEIVED = "payment_received"

    # Задачи
    TASK_CREATED = "task_created"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_COMPLETED = "task_completed"
    DEADLINE_APPROACHING = "deadline_approaching"

    # Производство
    PRODUCTION_STARTED = "production_started"
    PRODUCTION_STEP_COMPLETED = "production_step_completed"
    PRODUCTION_COMPLETED = "production_completed"
    PRODUCTION_OVERDUE = "production_overdue"

    # Клиенты
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_LOYALTY_CHANGED = "customer_loyalty_changed"

    # Коммуникации
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    EMAIL_OPENED = "email_opened"

    # Avito интеграция
    AVITO_MESSAGE_RECEIVED = "avito_message_received"
    AVITO_CHAT_CREATED = "avito_chat_created"
    AVITO_CHAT_CLOSED = "avito_chat_closed"


class RobotAction(enum.Enum):
    """Действия роботов"""
    # Коммуникации
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_TELEGRAM = "send_telegram"
    CREATE_MESSAGE = "create_message"

    # Задачи и процессы
    CREATE_TASK = "create_task"
    UPDATE_TASK_STATUS = "update_task_status"
    CREATE_PRODUCTION_STEP = "create_production_step"
    UPDATE_ORDER_STATUS = "update_order_status"

    # Уведомления
    NOTIFY_USER = "notify_user"
    NOTIFY_GROUP = "notify_group"

    # Обновления данных
    UPDATE_FIELD = "update_field"
    CREATE_COMMUNICATION = "create_communication"

    # AI действия
    ANALYZE_INTENT = "analyze_intent"
    GENERATE_RESPONSE = "generate_response"
    SEND_STANDARD_RESPONSE = "send_standard_response"
    ESCALATE_COMPLEX_QUERY = "escalate_complex_query"

    # Внешние интеграции
    CALL_EXTERNAL_API = "call_external_api"
    CALL_WEBHOOK = "call_webhook"
    CALL_GRAPHQL = "call_graphql"
    CALL_SOAP = "call_soap"

    # Календарь и планирование
    CREATE_CALENDAR_EVENT = "create_calendar_event"
    UPDATE_CALENDAR_EVENT = "update_calendar_event"
    SEND_CALENDAR_INVITE = "send_calendar_invite"


class Process(Base):
    """Бизнес-процесс"""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    entity_type = Column(Enum(EntityType), nullable=False)

    # Стадии процесса
    stages = relationship("Stage", back_populates="process", cascade="all, delete-orphan")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AutomationExecution(Base):
    """Выполнение автоматизации"""
    __tablename__ = "automation_executions"

    id = Column(Integer, primary_key=True)

    # Контекст выполнения
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)

    # Что выполнялось
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=True)
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=True)

    # Связи
    trigger = relationship("Trigger")
    robot = relationship("Robot")
    stage = relationship("Stage")

    # Результаты выполнения
    actions_executed = Column(JSON)  # Список выполненных действий с результатами
    execution_status = Column(String(50), default="running")  # running, completed, failed, partial
    error_message = Column(Text)

    # Метрики производительности
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)

    # Статистика
    actions_total = Column(Integer, default=0)
    actions_successful = Column(Integer, default=0)
    actions_failed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Stage(Base):
    """Стадия бизнес-процесса"""
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    entity_type = Column(Enum(EntityType), nullable=False)
    process_id = Column(Integer, ForeignKey("processes.id"))

    # Связи
    process = relationship("Process", back_populates="stages")

    # Роботы, привязанные к этой стадии
    robots = relationship("Robot", back_populates="stage", cascade="all, delete-orphan")

    # Триггеры, ведущие на эту стадию
    incoming_triggers = relationship("Trigger", back_populates="target_stage",
                                   foreign_keys="Trigger.target_stage_id")

    order_index = Column(Integer, default=0)
    color = Column(String(7))  # HEX цвет для визуализации
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trigger(Base):
    """Триггер автоматизации"""
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Контекст триггера
    entity_type = Column(Enum(EntityType), nullable=False)
    event_type = Column(Enum(TriggerEvent), nullable=False)

    # Условия срабатывания
    conditions = Column(JSON)  # {field: value, operator: "equals", ...}

    # Целевая стадия
    target_stage_id = Column(Integer, ForeignKey("stages.id"))
    target_stage = relationship("Stage", back_populates="incoming_triggers",
                               foreign_keys=[target_stage_id])

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Robot(Base):
    """Робот автоматизации"""
    __tablename__ = "robots"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Контекст робота
    entity_type = Column(Enum(EntityType), nullable=False)

    # Стадия, на которой срабатывает робот
    stage_id = Column(Integer, ForeignKey("stages.id"))
    stage = relationship("Stage", back_populates="robots")

    # Последовательные действия
    actions = relationship("RobotActionConfig", back_populates="robot",
                          cascade="all, delete-orphan", order_by="RobotActionConfig.execution_order")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RobotActionConfig(Base):
    """Конфигурация действия робота"""
    __tablename__ = "robot_actions_config"

    id = Column(Integer, primary_key=True)
    robot_id = Column(Integer, ForeignKey("robots.id"))

    # Связи
    robot = relationship("Robot", back_populates="actions")

    # Действие
    action_type = Column(Enum(RobotAction), nullable=False)
    execution_order = Column(Integer, nullable=False)

    # Конфигурация действия
    config = Column(JSON)  # {template: "welcome_email", delay: 3600, ...}

    # Условия выполнения
    conditions = Column(JSON)
    delay_seconds = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class AutomationError(Base):
    """Модель для логирования ошибок автоматизации"""
    __tablename__ = "automation_errors"

    id = Column(Integer, primary_key=True)

    # Контекст ошибки
    automation_execution_id = Column(Integer, ForeignKey("automation_executions.id"))
    robot_id = Column(Integer, ForeignKey("robots.id"))
    trigger_id = Column(Integer, ForeignKey("triggers.id"))

    # Связи
    automation_execution = relationship("AutomationExecution")
    robot = relationship("Robot")
    trigger = relationship("Trigger")

    # Детали ошибки
    error_type = Column(String(100), nullable=False)  # network, api, validation, timeout, etc.
    error_code = Column(String(50))  # HTTP status, API error code
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON)  # Дополнительные детали ошибки

    # Контекст выполнения
    entity_type = Column(Enum(EntityType))
    entity_id = Column(Integer)
    action_type = Column(Enum(RobotAction))

    # Обработка ошибки
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)

    # Уведомления
    notified_admin = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
