"""
Конфигурация pytest с фикстурами для тестирования
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.aicrm.core.database import get_db
from src.aicrm.models import Base
from src.aicrm.main import app
from src.aicrm.models.customer import Customer
from src.aicrm.models.order import Order
from src.aicrm.models.task import Task
from src.aicrm.models.production_step import ProductionStep


@pytest.fixture(scope="session")
def engine():
    """Создание тестовой базы данных SQLite в памяти"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False  # Отключаем логи SQL для тестов
    )
    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Создание всех таблиц в тестовой базе данных"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    """Фикстура для сессии базы данных"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Фикстура для FastAPI TestClient с тестовой БД"""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_customer(db_session):
    """Фикстура с примером клиента"""
    customer = Customer(
        name="Иван Иванов",
        email="ivan@example.com",
        phone="+7-999-123-45-67",
        address="Москва, ул. Ленина, 10"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def sample_order(db_session, sample_customer):
    """Фикстура с примером заказа"""
    from src.aicrm.models.order import OrderStatus

    order = Order(
        customer_id=sample_customer.id,
        status=OrderStatus.PENDING,
        total_amount=1500.00,
        items=[{"product_type": "tshirt", "quantity": 3}],
        source="website"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def sample_task(db_session):
    """Фикстура с примером задачи"""
    task = Task(
        title="Подготовить дизайн",
        description="Создать макет для футболки",
        priority="high",
        assigned_to=2,
        created_by=1,
        status="todo"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_production_step(db_session, sample_order):
    """Фикстура с примером этапа производства"""
    from src.aicrm.models.production_step import ProductionStep, StepStatus

    step = ProductionStep(
        order_id=sample_order.id,
        name="Подготовка макета",
        description="Подготовка дизайн-макета",
        sequence_number=1,
        status=StepStatus.PENDING,
        estimated_hours=24
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)
    return step


# Асинхронные фикстуры для API тестов

@pytest.fixture(scope="session")
def async_engine():
    """Создание асинхронной тестовой базы данных"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    return engine


@pytest.fixture(scope="session")
async def async_tables(async_engine):
    """Создание всех таблиц в асинхронной тестовой базе данных"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_db(async_engine, async_tables):
    """Фикстура для асинхронной сессии базы данных"""
    async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def async_client(async_db):
    """Фикстура для httpx AsyncClient с тестовой БД"""
    from src.aicrm.core.database import get_async_db

    async def override_get_async_db():
        return async_db

    app.dependency_overrides[get_async_db] = override_get_async_db

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(async_db):
    """Создание тестового пользователя для API тестов"""
    from src.aicrm.models.user import User
    from src.aicrm.services.auth import auth_service

    user = User(
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("testpass123"),
        is_active=True
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest.fixture
async def test_customer_api(async_db):
    """Создание тестового клиента для API тестов"""
    customer = Customer(
        name="Иван Иванов",
        email="ivan@example.com",
        phone="+7-999-123-45-67",
        address="Москва, ул. Ленина, 10"
    )
    async_db.add(customer)
    await async_db.commit()
    await async_db.refresh(customer)
    return customer


@pytest.fixture
async def test_task_api(async_db):
    """Создание тестовой задачи для API тестов"""
    from datetime import datetime, timedelta

    task = Task(
        title="Тестовая задача",
        description="Описание тестовой задачи",
        priority="medium",
        assigned_to=1,
        created_by=1,
        due_date=datetime.utcnow() + timedelta(days=3),
        status="todo"
    )
    async_db.add(task)
    await async_db.commit()
    await async_db.refresh(task)
    return task
