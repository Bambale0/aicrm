"""Universal process automation persistence."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class AutomationProcess(BaseModel):
    __tablename__ = "automation_processes"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    stages = relationship(
        "AutomationStage",
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="AutomationStage.order_index",
    )
    rules = relationship(
        "AutomationRule",
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="AutomationRule.priority, AutomationRule.id",
    )
    instances = relationship(
        "AutomationInstance",
        back_populates="process",
        cascade="all, delete-orphan",
    )


class AutomationStage(BaseModel):
    __tablename__ = "automation_stages"

    process_id = Column(Integer, ForeignKey("automation_processes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False, index=True)
    color = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    process = relationship("AutomationProcess", back_populates="stages")


class AutomationRule(BaseModel):
    __tablename__ = "automation_rules_v2"

    process_id = Column(Integer, ForeignKey("automation_processes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    conditions = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=False)
    priority = Column(Integer, default=100, nullable=False, index=True)
    stop_after_match = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    process = relationship("AutomationProcess", back_populates="rules")


class AutomationInstance(BaseModel):
    __tablename__ = "automation_instances"

    process_id = Column(Integer, ForeignKey("automation_processes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="running", index=True)
    current_stage_id = Column(Integer, ForeignKey("automation_stages.id", ondelete="SET NULL"), nullable=True, index=True)
    variables = Column(JSON, nullable=False, default=dict)
    external_ref = Column(String(255), nullable=True, index=True)

    process = relationship("AutomationProcess", back_populates="instances")


class AutomationExecution(BaseModel):
    __tablename__ = "automation_executions_v3"

    process_id = Column(Integer, ForeignKey("automation_processes.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id = Column(Integer, ForeignKey("automation_rules_v2.id", ondelete="SET NULL"), nullable=True, index=True)
    instance_id = Column(Integer, ForeignKey("automation_instances.id", ondelete="SET NULL"), nullable=True, index=True)

    correlation_id = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    action_index = Column(Integer, nullable=True)

    status = Column(String(30), nullable=False, default="running", index=True)
    duration_ms = Column(Integer, nullable=True)
    input_data = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
