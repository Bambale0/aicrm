Чистая модульная структура

Современный стек технологий (FastAPI, SQLAlchemy 2.0, Pydantic)

Полноценная аутентификация и безопасность

Хорошая документация API

Поддержка разработки и продакшена

🚀 Рекомендации по улучшению:
1. Оптимизация структуры проекта
python
# Рекомендуемая структура
src/aicrm/
├── core/
│   ├── config.py          # Конфигурация приложения
│   ├── database.py        # Настройки БД
│   ├── security.py        # JWT, хеширование
│   └── dependencies.py    # FastAPI зависимости
├── models/
│   ├── base.py           # Базовая модель
│   ├── user.py           # Пользователи
│   ├── customer.py       # Клиенты
│   ├── order.py          # Заказы
│   └── production.py     # Производство
├── schemas/
│   ├── auth.py           # Схемы аутентификации
│   ├── customer.py       # Схемы клиентов
│   └── order.py          # Схемы заказов
├── api/
│   ├── v1/               # Version 1 API
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   └── orders.py
│   │   └── __init__.py
│   └── deps.py           # Зависимости API
├── services/
│   ├── auth.py           # Сервис аутентификации
│   ├── customer.py       # Сервис клиентов
│   ├── order.py          # Сервис заказов
│   └── ai.py            # AI сервис
├── utils/
│   ├── security.py       # Утилиты безопасности
│   ├── validators.py     # Кастомные валидаторы
│   └── helpers.py        # Вспомогательные функции
└── tests/
    ├── conftest.py       # Фикстуры pytest
    ├── test_api/
    ├── test_services/
    └── test_models/
2. Улучшенная конфигурация
python
# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
3. Расширенные модели данных
python
# models/order.py
from sqlalchemy import Column, Integer, String, DateTime, Decimal, Text, Enum, JSON
from sqlalchemy.orm import relationship
from .base import Base
import enum

class OrderStatus(enum.Enum):
    PENDING = "pending"
    IN_DESIGN = "in_design"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(Decimal(10, 2))
    items = Column(JSON)  # Детали заказа
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    production_steps = relationship("ProductionStep", back_populates="order")
    communications = relationship("Communication", back_populates="order")
4. AI Module Enhancement
python
# services/ai.py
import httpx
from enum import Enum
from typing import Dict, Any, Optional
from core.config import settings

class AIIntent(Enum):
    ORDER = "order"
    QUESTION = "question"
    COMPLAINT = "complaint"
    OTHER = "other"

class AIService:
    def __init__(self):
        self.providers = {
            "openai": OpenAIClient(),
            "openrouter": OpenRouterClient(),
            "anthropic": AnthropicClient()
        }
    
    async def analyze_intent(self, message: str) -> AIIntent:
        """Анализ намерения сообщения с использованием AI"""
        prompt = f"""
        Проанализируй намерение пользователя в следующем сообщении:
        "{message}"
        
        Возможные варианты:
        - order: пользователь хочет сделать заказ
        - question: пользователь задает вопрос
        - complaint: пользователь жалуется
        - other: другое
        
        Верни только одно слово (order/question/complaint/other)
        """
        
        response = await self.providers["openrouter"].complete(prompt)
        return AIIntent(response.strip().lower())
    
    async def generate_response(self, intent: AIIntent, context: Dict[str, Any]) -> str:
        """Генерация контекстного ответа"""
        templates = {
            AIIntent.ORDER: "Отлично! Я помогу вам оформить заказ...",
            AIIntent.QUESTION: "Спасибо за вопрос! Вот что я могу рассказать...",
            AIIntent.COMPLAINT: "Приношу извинения за неудобства. Наш менеджер свяжется с вами...",
            AIIntent.OTHER: "Благодарю за обращение! Чем еще могу помочь?"
        }
        return templates.get(intent, "Благодарю за обращение!")
5. Production Workflow Service
python
# services/production.py
from sqlalchemy.orm import Session
from models.order import Order, OrderStatus
from models.production import ProductionStep, StepStatus
from typing import List

class ProductionService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_production_workflow(self, order_id: int) -> List[ProductionStep]:
        """Автоматическое создание workflow производства"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        # Стандартные этапы для печати на одежде
        steps_config = [
            {"name": "Подготовка макета", "duration_hours": 24},
            {"name": "Подготовка материалов", "duration_hours": 12},
            {"name": "Печать", "duration_hours": 48},
            {"name": "Пост-обработка", "duration_hours": 24},
            {"name": "Контроль качества", "duration_hours": 6},
        ]
        
        steps = []
        for i, config in enumerate(steps_config):
            step = ProductionStep(
                order_id=order_id,
                name=config["name"],
                sequence_number=i + 1,
                status=StepStatus.PENDING,
                estimated_hours=config["duration_hours"]
            )
            self.db.add(step)
            steps.append(step)
        
        self.db.commit()
        return steps
    
    async def update_progress(self, order_id: int) -> Dict[str, Any]:
        """Обновление прогресса производства"""
        steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id
        ).all()
        
        total_steps = len(steps)
        completed_steps = len([s for s in steps if s.status == StepStatus.COMPLETED])
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress": round(progress, 2),
            "current_step": next((s for s in steps if s.status == StepStatus.IN_PROGRESS), None)
        }
6. Enhanced API Endpoints
python
# api/v1/endpoints/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from services.order import OrderService
from services.production import ProductionService
from schemas.order import OrderCreate, OrderResponse, OrderUpdate

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создание заказа с автоматическим workflow"""
    order_service = OrderService(db)
    production_service = ProductionService(db)
    
    # Создание заказа
    order = await order_service.create_order(order_data, current_user.id)
    
    # Автоматическое создание производственного workflow
    await production_service.create_production_workflow(order.id)
    
    return order

@router.get("/{order_id}/production-progress")
async def get_production_progress(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получение прогресса производства заказа"""
    production_service = ProductionService(db)
    progress = await production_service.update_progress(order_id)
    return progress
7. Docker Optimization
dockerfile
# Многоступенчатый Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim as runtime

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.aicrm.main:app", "--host", "0.0.0.0", "--port", "8000"]
8. Monitoring & Logging
python
# utils/logging.py
import structlog
import logging

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )