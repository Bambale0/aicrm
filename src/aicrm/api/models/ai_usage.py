"""
Модель учета использования AI токенов
"""

from sqlalchemy import Column, Float, Integer, String, Text

from .base import BaseModel


class AIUsage(BaseModel):
    """Модель учета использования AI токенов"""

    __tablename__ = "ai_usage"

    # Информация о запросе
    model_used = Column(String, nullable=False, index=True)
    endpoint = Column(String, nullable=False)  # chat, analyze-intent, etc.
    user_id = Column(Integer, nullable=True, index=True)  # если есть аутентификация

    # Статистика токенов
    prompt_tokens = Column(Float, default=0.0)  # токены в запросе
    completion_tokens = Column(Float, default=0.0)  # токены в ответе
    total_tokens = Column(Float, nullable=False)  # общая сумма токенов

    # Дополнительная информация
    request_id = Column(String, unique=True, nullable=False)  # уникальный ID запроса
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Временные метки для агрегации по месяцам
    month_year = Column(String, nullable=False, index=True)  # формат: YYYY-MM

    @staticmethod
    def generate_request_id() -> str:
        """Генерация уникального ID запроса"""
        import uuid

        return str(uuid.uuid4())

    @staticmethod
    def get_current_month_year() -> str:
        """Получение текущего месяца в формате YYYY-MM"""
        from datetime import datetime

        return datetime.utcnow().strftime("%Y-%m")

    def __repr__(self) -> str:
        return f"<AIUsage(id={self.id}, model={self.model_used}, tokens={self.total_tokens}, month={self.month_year})>"
