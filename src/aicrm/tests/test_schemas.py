"""
Юнит-тесты для API схем (Pydantic моделей)
"""
import pytest
from datetime import datetime, date, timedelta

from src.aicrm.api.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItem,
    ProductionProgressResponse, ProductionStepResponse, StepUpdateRequest,
    OrderListResponse
)
from src.aicrm.api.schemas.customer import (
    CustomerCreate, CustomerUpdate, Customer
)
from src.aicrm.api.schemas.task import (
    TaskCreate, TaskUpdate, Task
)
from src.aicrm.models.order import OrderStatus


class TestOrderSchemas:
    """Тесты для схем заказов"""

    def test_order_item_creation(self):
        """Тест создания OrderItem"""
        item = OrderItem(
            product_type="tshirt",
            quantity=3,
            size="L",
            color="black",
            design_url="https://example.com/design.jpg"
        )

        assert item.product_type == "tshirt"
        assert item.quantity == 3
        assert item.size == "L"
        assert item.color == "black"
        assert item.design_url == "https://example.com/design.jpg"

    def test_order_item_quantity_validation(self):
        """Тест валидации количества в OrderItem"""
        # Корректное количество
        OrderItem(product_type="tshirt", quantity=1)

        # Некорректное количество
        with pytest.raises(ValueError):
            OrderItem(product_type="tshirt", quantity=0)

        with pytest.raises(ValueError):
            OrderItem(product_type="tshirt", quantity=-1)

    def test_order_create_validation(self):
        """Тест валидации OrderCreate"""
        deadline = datetime.utcnow()

        order = OrderCreate(
            customer_id=1,
            items=[
                OrderItem(product_type="tshirt", quantity=2),
                OrderItem(product_type="hoodie", quantity=1)
            ],
            requirements="Срочный заказ",
            deadline=deadline,
            notes="Доставить к вечеру",
            source="website"
        )

        assert order.customer_id == 1
        assert len(order.items) == 2
        assert order.requirements == "Срочный заказ"
        assert order.source == "website"

    def test_order_update_validation(self):
        """Тест валидации OrderUpdate"""
        update = OrderUpdate(
            status=OrderStatus.IN_PRODUCTION,
            requirements="Измененные требования",
            deadline=datetime.utcnow() + timedelta(days=5)
        )

        assert update.status == OrderStatus.IN_PRODUCTION
        assert update.requirements == "Измененные требования"

    def test_order_response_creation(self):
        """Тест создания OrderResponse"""
        response = OrderResponse(
            id=1,
            customer_id=1,
            status=OrderStatus.IN_PRODUCTION,
            status_display="В производстве",
            total_amount=2500.00,
            items=[{"product_type": "tshirt", "quantity": 2}],
            requirements="Тестовые требования",
            deadline=datetime.utcnow(),
            notes="Тестовые заметки",
            source="website",
            progress_percentage=45.5,
            is_overdue=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert response.id == 1
        assert response.status == OrderStatus.IN_PRODUCTION
        assert response.total_amount == 2500.00
        assert response.progress_percentage == 45.5

    def test_production_step_response_creation(self):
        """Тест создания ProductionStepResponse"""
        response = ProductionStepResponse(
            id=1,
            name="Подготовка макета",
            description="Подготовка дизайн-макета",
            status="in_progress",
            sequence_number=1,
            estimated_hours=24.0,
            actual_hours=20.5,
            started_at=datetime.utcnow(),
            completed_at=None,
            assigned_user_id=2,
            notes="В работе",
            is_overdue=False,
            progress_percentage=50.0
        )

        assert response.id == 1
        assert response.name == "Подготовка макета"
        assert response.status == "in_progress"
        assert response.progress_percentage == 50.0

    def test_production_progress_response_creation(self):
        """Тест создания ProductionProgressResponse"""
        steps = [
            ProductionStepResponse(
                id=1, name="Этап 1", status="completed", sequence_number=1,
                is_overdue=False, progress_percentage=100.0
            ),
            ProductionStepResponse(
                id=2, name="Этап 2", status="in_progress", sequence_number=2,
                is_overdue=False, progress_percentage=50.0
            )
        ]

        response = ProductionProgressResponse(
            total_steps=2,
            completed_steps=1,
            in_progress_steps=1,
            pending_steps=0,
            progress=75.0,
            current_step="Этап 2",
            next_step=None,
            is_overdue=False,
            steps=steps
        )

        assert response.total_steps == 2
        assert response.progress == 75.0
        assert response.current_step == "Этап 2"
        assert len(response.steps) == 2

    def test_step_update_request_validation(self):
        """Тест валидации StepUpdateRequest"""
        request = StepUpdateRequest(
            status="completed",
            actual_hours=25.5,
            notes="Завершено успешно",
            assigned_user_id=3
        )

        assert request.status == "completed"
        assert request.actual_hours == 25.5
        assert request.notes == "Завершено успешно"
        assert request.assigned_user_id == 3

    def test_order_list_response_creation(self):
        """Тест создания OrderListResponse"""
        orders = [
            OrderResponse(
                id=1, customer_id=1, status=OrderStatus.READY,
                status_display="Готов", total_amount=1500.00,
                source="website", progress_percentage=100.0,
                is_overdue=False, created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            OrderResponse(
                id=2, customer_id=2, status=OrderStatus.IN_PRODUCTION,
                status_display="В производстве", total_amount=3200.00,
                source="avito", progress_percentage=60.0,
                is_overdue=False, created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

        response = OrderListResponse(
            orders=orders,
            total=2,
            page=1,
            per_page=20
        )

        assert len(response.orders) == 2
        assert response.total == 2
        assert response.page == 1
        assert response.per_page == 20


class TestCustomerSchemas:
    """Тесты для схем клиентов"""

    def test_customer_create_validation(self):
        """Тест валидации CustomerCreate"""
        customer = CustomerCreate(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+7-999-123-45-67",
            address="Москва, ул. Ленина, 10",
            contact_info={"telegram": "@ivanov"},
            notes="Постоянный клиент"
        )

        assert customer.name == "Иван Иванов"
        assert customer.email == "ivan@example.com"
        assert customer.phone == "+7-999-123-45-67"
        assert customer.contact_info == {"telegram": "@ivanov"}

    def test_customer_create_required_fields(self):
        """Тест обязательных полей CustomerCreate"""
        # Минимум обязательных полей
        customer = CustomerCreate(name="Иван Иванов")

        assert customer.name == "Иван Иванов"
        assert customer.email is None

    def test_customer_update_validation(self):
        """Тест валидации CustomerUpdate"""
        update = CustomerUpdate(
            name="Иван Петров",
            phone="+7-999-999-99-99",
            address="СПб, Невский пр.",
            notes="Обновленная информация"
        )

        assert update.name == "Иван Петров"
        assert update.phone == "+7-999-999-99-99"

    def test_customer_response_creation(self):
        """Тест создания Customer"""
        response = Customer(
            id=1,
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+7-999-123-45-67",
            address="Москва, ул. Ленина, 10",
            contact_info={"telegram": "@ivanov"},
            total_orders=5,
            total_spent=12500.00,
            loyalty_level="gold",
            notes="VIP клиент",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert response.id == 1
        assert response.name == "Иван Иванов"
        assert response.loyalty_level == "gold"
        assert response.total_spent == 12500.00


class TestTaskSchemas:
    """Тесты для схем задач"""

    def test_task_create_validation(self):
        """Тест валидации TaskCreate"""
        due_date = datetime.utcnow() + timedelta(days=3)

        task = TaskCreate(
            title="Подготовить дизайн",
            description="Создать макет для футболки",
            priority="high",
            assigned_to=2,
            due_date=due_date,
            estimated_hours=8,
            tags="design,urgent"
        )

        assert task.title == "Подготовить дизайн"
        assert task.priority == "high"
        assert task.assigned_to == 2
        assert task.estimated_hours == 8

    def test_task_create_required_fields(self):
        """Тест обязательных полей TaskCreate"""
        task = TaskCreate(title="Тестовая задача")

        assert task.title == "Тестовая задача"
        assert task.priority == "medium"  # default value

    def test_task_update_validation(self):
        """Тест валидации TaskUpdate"""
        update = TaskUpdate(
            title="Обновленный заголовок",
            status="in_progress",
            priority="medium",
            description="Обновленное описание",
            assigned_to=3,
            due_date=datetime.utcnow() + timedelta(days=5),
            estimated_hours=12,
            actual_hours=10,
            tags="updated,important"
        )

        assert update.title == "Обновленный заголовок"
        assert update.status == "in_progress"
        assert update.assigned_to == 3

    def test_task_response_creation(self):
        """Тест создания Task"""
        response = Task(
            id=1,
            title="Подготовить дизайн",
            description="Создать макет для футболки",
            priority="high",
            status="in_progress",
            assigned_to=2,
            created_by=1,
            due_date=datetime.utcnow() + timedelta(days=3),
            completed_at=None,
            tags="design,urgent",
            related_order_id=5,
            estimated_hours=8,
            actual_hours=6,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert response.id == 1
        assert response.title == "Подготовить дизайн"
        assert response.priority == "high"
        assert response.status == "in_progress"
