"""
Integration tests using real database and external services.
These tests verify end-to-end functionality with actual database operations.
"""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from aicrm.core.database import get_db
from aicrm.main import app
from aicrm.models.base import Base
from aicrm.models.customer import Customer
from aicrm.models.order import Order
from aicrm.models.user import User
from aicrm.services.auth import auth_service

# Test database URL for integration tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # Rollback any changes after test
        await session.rollback()


@pytest.fixture(scope="function")
async def client(test_db_session):
    """Create test client with real database session."""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(base_url="http://testserver") as client:
        # Mount the app to the client
        from httpx import ASGITransport

        client._transport = ASGITransport(app=app)
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(test_db_session):
    """Create test user in database."""
    user = User(
        email="test@example.com",
        hashed_password=User.get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def admin_user(test_db_session):
    """Create admin user in database."""
    user = User(
        email="admin@example.com",
        hashed_password=User.get_password_hash("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_headers(test_user):
    """Create authentication headers for test user."""
    access_token = auth_service.create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
async def admin_auth_headers(admin_user):
    """Create authentication headers for admin user."""
    access_token = auth_service.create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}


class TestUserManagement:
    """Integration tests for user management functionality."""

    @pytest.mark.asyncio
    async def test_user_registration_and_login(self, client, test_db_session):
        """Test complete user registration and login flow."""
        # Register user
        register_data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
        }

        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 200

        # Verify user was created in database
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.full_name == "New User"
        assert not user.is_superuser

        # Login with created user
        login_data = {"email": "newuser@example.com", "password": "securepass123"}

        response = await client.post("/auth/login/json", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, auth_headers, test_user):
        """Test getting current user information."""
        response = await client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] == test_user.is_active


class TestCustomerManagement:
    """Integration tests for customer management."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_customer(
        self, client, auth_headers, test_db_session
    ):
        """Test creating a customer and retrieving it."""
        customer_data = {
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "+1234567890",
            "company": "Test Company",
        }

        # Create customer
        response = await client.post(
            "/customers/", json=customer_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_customer = response.json()
        customer_id = created_customer["id"]

        # Retrieve customer
        response = await client.get(f"/customers/{customer_id}", headers=auth_headers)
        assert response.status_code == 200

        retrieved_customer = response.json()
        assert retrieved_customer["name"] == customer_data["name"]
        assert retrieved_customer["email"] == customer_data["email"]

        # Verify in database
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        db_customer = result.scalar_one_or_none()
        assert db_customer is not None
        assert db_customer.name == customer_data["name"]

    @pytest.mark.asyncio
    async def test_customer_search(self, client, auth_headers):
        """Test customer search functionality."""
        # Create multiple customers
        customers_data = [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
            {"name": "Bob Johnson", "email": "bob@example.com"},
        ]

        for customer_data in customers_data:
            await client.post("/customers/", json=customer_data, headers=auth_headers)

        # Search for customers
        response = await client.get(
            "/customers/search/?query=john", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["customers"]) >= 1
        assert any(c["name"] == "John Doe" for c in data["customers"])


class TestOrderManagement:
    """Integration tests for order management."""

    @pytest.mark.asyncio
    async def test_create_order_with_production_workflow(
        self, client, auth_headers, test_db_session
    ):
        """Test creating an order with automatic production workflow creation."""
        # First create a customer
        customer_data = {"name": "Order Customer", "email": "order@example.com"}
        customer_response = await client.post(
            "/customers/", json=customer_data, headers=auth_headers
        )
        customer_id = customer_response.json()["id"]

        # Create order
        order_data = {
            "customer_id": customer_id,
            "items": [
                {
                    "product_type": "t-shirt",
                    "quantity": 10,
                    "size": "M",
                    "color": "black",
                }
            ],
            "requirements": "Test order with production workflow",
            "source": "website",
        }

        response = await client.post("/orders/", json=order_data, headers=auth_headers)
        assert response.status_code == 200

        created_order = response.json()
        order_id = created_order["id"]

        # Verify order was created
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(Order).where(Order.id == order_id)
        )
        db_order = result.scalar_one_or_none()
        assert db_order is not None
        assert db_order.customer_id == customer_id

        # Check production steps were created automatically
        response = await client.get(
            f"/orders/{order_id}/production-progress", headers=auth_headers
        )
        assert response.status_code == 200

        progress_data = response.json()
        assert progress_data["total_steps"] > 0
        assert "steps" in progress_data

    @pytest.mark.asyncio
    async def test_production_step_management(self, client, auth_headers):
        """Test production step lifecycle management."""
        # Create order first (this will create production steps)
        customer_data = {"name": "Production Test", "email": "prod@example.com"}
        customer_response = await client.post(
            "/customers/", json=customer_data, headers=auth_headers
        )
        customer_id = customer_response.json()["id"]

        order_data = {
            "customer_id": customer_id,
            "items": [{"product_type": "t-shirt", "quantity": 5}],
            "requirements": "Production test",
        }
        order_response = await client.post(
            "/orders/", json=order_data, headers=auth_headers
        )
        order_id = order_response.json()["id"]

        # Get production progress
        response = await client.get(
            f"/orders/{order_id}/production-progress", headers=auth_headers
        )
        progress_data = response.json()

        first_step = progress_data["steps"][0]
        step_id = first_step["id"]

        # Start production step
        response = await client.post(
            f"/orders/{order_id}/production-steps/{step_id}/start",
            json={"user_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Complete production step
        response = await client.post(
            f"/orders/{order_id}/production-steps/{step_id}/complete",
            json={"actual_hours": 2.5, "notes": "Completed successfully"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify step was completed
        response = await client.get(
            f"/orders/{order_id}/production-progress", headers=auth_headers
        )
        updated_progress = response.json()

        completed_step = next(
            step for step in updated_progress["steps"] if step["id"] == step_id
        )
        assert completed_step["status"] == "completed"
        assert completed_step["actual_hours"] == 2.5


class TestTaskManagement:
    """Integration tests for task management."""

    @pytest.mark.asyncio
    async def test_task_crud_operations(self, client, auth_headers, test_db_session):
        """Test complete task CRUD operations."""
        task_data = {
            "title": "Integration Test Task",
            "description": "Testing task management integration",
            "priority": "high",
            "due_date": "2025-12-01T00:00:00Z",
        }

        # Create task
        response = await client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 200

        created_task = response.json()
        task_id = created_task["id"]

        # Retrieve task
        response = await client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        retrieved_task = response.json()
        assert retrieved_task["title"] == task_data["title"]

        # Update task
        update_data = {"status": "in_progress"}
        response = await client.put(
            f"/tasks/{task_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200

        # Complete task
        response = await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)
        assert response.status_code == 200

        # Verify in database
        from sqlalchemy import select

        from aicrm.models.task import Task

        result = await test_db_session.execute(select(Task).where(Task.id == task_id))
        db_task = result.scalar_one_or_none()
        assert db_task is not None
        assert db_task.status == "completed"
        assert db_task.completed_at is not None


class TestHealthChecks:
    """Integration tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoints(self, client):
        """Test all health check endpoints."""
        endpoints = ["/health", "/"]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data or "message" in data

    @pytest.mark.asyncio
    async def test_openapi_specification(self, client):
        """Test OpenAPI specification is accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

        response = await client.get("/redoc")
        assert response.status_code == 200

        response = await client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        assert "paths" in spec
        assert "components" in spec


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        protected_endpoints = ["/customers/", "/orders/", "/tasks/", "/auth/me"]

        for endpoint in protected_endpoints:
            response = await client.get(endpoint)
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_not_found_errors(self, client, auth_headers):
        """Test 404 errors for non-existent resources."""
        response = await client.get("/customers/99999", headers=auth_headers)
        assert response.status_code == 404

        response = await client.get("/orders/99999", headers=auth_headers)
        assert response.status_code == 404

        response = await client.get("/tasks/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_errors(self, client, auth_headers):
        """Test input validation errors."""
        # Invalid email format
        invalid_customer = {"name": "Test", "email": "invalid-email", "phone": "123"}

        response = await client.post(
            "/customers/", json=invalid_customer, headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

        # Missing required fields
        incomplete_order = {
            "customer_id": 1
            # Missing items and other required fields
        }

        response = await client.post(
            "/orders/", json=incomplete_order, headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
