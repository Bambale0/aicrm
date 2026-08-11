"""
Модель логов автоматизации
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from .base import BaseModel


class AutomationLog(BaseModel):
    """Модель логов выполнения автоматизаций"""

    __tablename__ = "automation_logs"

    timestamp = Column(DateTime, nullable=False, index=True)  # Время выполнения
    level = Column(String, nullable=False, index=True)  # error, warning, success, info
    message = Column(Text, nullable=False)  # Сообщение лога
    process_id = Column(Integer, index=True)  # ID процесса автоматизации
    stage_id = Column(Integer, index=True)  # ID стадии
    details = Column(JSON)  # Дополнительные детали выполнения

    def __repr__(self) -> str:
        return f"<AutomationLog(level={self.level}, process_id={self.process_id}, stage_id={self.stage_id})>"
