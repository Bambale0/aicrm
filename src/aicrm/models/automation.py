"""
Модели автоматизации в стиле Bitrix24
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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


class Process(Base):
    """Бизнес-процесс"""

    __tablename__ = "processes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    entity_type = Column(Enum(EntityType), nullable=False)

    # Стадии процесса
    stages = relationship(
        "Stage", back_populates="process", cascade="all, delete-orphan"
    )

    is_active = Column(Boolean, default=True)
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
    incoming_triggers = relationship(
        "Trigger", back_populates="target_stage", foreign_keys="Trigger.target_stage_id"
    )

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
    target_stage = relationship(
        "Stage", back_populates="incoming_triggers", foreign_keys=[target_stage_id]
    )

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
    actions = relationship(
        "RobotActionConfig",
        back_populates="robot",
        cascade="all, delete-orphan",
        order_by="RobotActionConfig.execution_order",
    )

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
