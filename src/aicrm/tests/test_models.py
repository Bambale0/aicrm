"""
Юнит-тесты для моделей
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from src.aicrm.models.customer import Customer
from src.aicrm.models.task import Task
from src.aicrm.models.order import Order, OrderStatus
from src.aicrm.models.production_step import ProductionStep, StepStatus
from src.aicrm.models.ai_settings import AISettings


class TestCustomerModel:
    """Тесты для модели Customer"""

    def test_customer_creation(self):
        """Тест создания клиента"""
        customer = Customer(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+7-999-123-45-67",
            address="Москва, ул. Ленина, 10",
            total_orders=0,
            total_spent=0.00,
            loyalty_level="bronze"
        )

        assert customer.name == "Иван Иванов"
        assert customer.email == "ivan@example.com"
        assert customer.phone == "+7-999-123-45-67"
        assert customer.address == "Москва, ул. Ленина, 10"
        assert customer.total_orders == 0
        assert customer.total_spent == 0.00
        assert customer.loyalty_level == "bronze"

    def test_customer_repr(self):
        """Тест строкового представления клиента"""
        customer = Customer(
            name="Иван Иванов",
            email="ivan@example.com"
        )

        assert repr(customer) == "<Customer(name=Иван Иванов, email=ivan@example.com)>"

    def test_update_stats_bronze(self):
        """Тест обновления статистики - бронзовый уровень"""
        customer = Customer(name="Test", email="test@example.com")
        customer.total_spent = 500.00

        # Создаем мок заказов
        order1 = MagicMock()
        order1.total_amount = 300.00
        order2 = MagicMock()
        order2.total_amount = 200.00
        customer.orders = [order1, order2]

        customer.update_stats()

        assert customer.total_orders == 2
        assert customer.total_spent == 500.00
        assert customer.loyalty_level == "bronze"

    def test_update_stats_silver(self):
        """Тест обновления статистики - серебряный уровень"""
        customer = Customer(name="Test", email="test@example.com")
        customer.total_spent = 1500.00

        order = MagicMock()
        order.total_amount = 1500.00
        customer.orders = [order]

        customer.update_stats()

        assert customer.total_orders == 1
        assert customer.total_spent == 1500.00
        assert customer.loyalty_level == "silver"

    def test_update_stats_gold(self):
        """Тест обновления статистики - золотой уровень"""
        customer = Customer(name="Test", email="test@example.com")
        customer.total_spent = 6000.00

        order = MagicMock()
        order.total_amount = 6000.00
        customer.orders = [order]

        customer.update_stats()

        assert customer.loyalty_level == "gold"

    def test_update_stats_platinum(self):
        """Тест обновления статистики - платиновый уровень"""
        customer = Customer(name="Test", email="test@example.com")
        customer.total_spent = 15000.00

        order = MagicMock()
        order.total_amount = 15000.00
        customer.orders = [order]

        customer.update_stats()

        assert customer.loyalty_level == "platinum"


class TestTaskModel:
    """Тесты для модели Task"""

    def test_task_creation(self):
        """Тест создания задачи"""
        due_date = datetime.utcnow() + timedelta(days=3)

        task = Task(
            title="Подготовить дизайн",
            description="Создать макет для футболки",
            priority="high",
            status="todo",
            assigned_to=2,
            created_by=1,
            due_date=due_date,
            estimated_hours=8
        )

        assert task.title == "Подготовить дизайн"
        assert task.priority == "high"
        assert task.status == "todo"
        assert task.assigned_to == 2
        assert task.created_by == 1
        assert task.due_date == due_date

    def test_task_repr(self):
        """Тест строкового представления задачи"""
        task = Task(
            title="Тестовая задача",
            priority="medium",
            status="in_progress"
        )

        assert repr(task) == "<Task(title=Тестовая задача, priority=medium, status=in_progress)>"

    def test_priority_display(self):
        """Тест человеко-читаемого приоритета"""
        task = Task(title="Test", priority="high")
        assert task.priority_display == "Высокий"

        task.priority = "low"
        assert task.priority_display == "Низкий"

        task.priority = "unknown"
        assert task.priority_display == "unknown"

    def test_status_display(self):
        """Тест человеко-читаемого статуса"""
        task = Task(title="Test", status="done")
        assert task.status_display == "Выполнена"

        task.status = "in_progress"
        assert task.status_display == "В работе"

        task.status = "unknown"
        assert task.status_display == "unknown"

    def test_complete_task(self):
        """Тест завершения задачи"""
        task = Task(title="Test", status="in_progress")

        task.complete()

        assert task.status == "done"
        assert task.completed_at is not None

    def test_is_overdue_no_due_date(self):
        """Тест просрочки без даты выполнения"""
        task = Task(title="Test", status="in_progress")

        assert not task.is_overdue()

    def test_is_overdue_completed(self):
        """Тест просрочки для завершенной задачи"""
        task = Task(title="Test", status="done", due_date=datetime.utcnow() - timedelta(days=1))

        assert not task.is_overdue()

    def test_is_overdue_not_overdue(self):
        """Тест задачи, которая не просрочена"""
        task = Task(
            title="Test",
            status="in_progress",
            due_date=datetime.utcnow() + timedelta(days=1)
        )

        assert not task.is_overdue()

    def test_is_overdue_overdue(self):
        """Тест просроченной задачи"""
        task = Task(
            title="Test",
            status="in_progress",
            due_date=datetime.utcnow() - timedelta(days=1)
        )

        assert task.is_overdue()


class TestOrderModel:
    """Тесты для модели Order"""

    def test_order_creation(self):
        """Тест создания заказа"""
        deadline = datetime.utcnow() + timedelta(days=7)

        order = Order(
            customer_id=1,
            status=OrderStatus.PENDING,
            total_amount=1500.00,
            items=[{"product_type": "tshirt", "quantity": 3}],
            requirements="Срочный заказ",
            deadline=deadline,
            source="website"
        )

        assert order.customer_id == 1
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == 1500.00
        assert order.requirements == "Срочный заказ"
        assert order.source == "website"

    def test_order_repr(self):
        """Тест строкового представления заказа"""
        order = Order(
            customer_id=1,
            status=OrderStatus.IN_PRODUCTION,
            total_amount=2500.00
        )

        # Проверяем, что repr содержит правильную информацию
        repr_str = repr(order)
        assert "Order" in repr_str
        assert "customer_id=1" in repr_str
        assert "status=in_production" in repr_str

    def test_status_display(self):
        """Тест человеко-читаемого статуса"""
        order = Order(customer_id=1, status=OrderStatus.READY)
        assert order.status_display == "Готов"

        order.status = OrderStatus.DELIVERED
        assert order.status_display == "Доставлен"

    def test_is_overdue_no_deadline(self):
        """Тест просрочки без дедлайна"""
        order = Order(customer_id=1, status=OrderStatus.IN_PRODUCTION)

        assert not order.is_overdue

    def test_is_overdue_delivered(self):
        """Тест просрочки для доставленного заказа"""
        order = Order(
            customer_id=1,
            status=OrderStatus.DELIVERED,
            deadline=datetime.utcnow() - timedelta(days=1)
        )

        assert not order.is_overdue

    def test_is_overdue_overdue(self):
        """Тест просроченного заказа"""
        order = Order(
            customer_id=1,
            status=OrderStatus.IN_PRODUCTION,
            deadline=datetime.utcnow() - timedelta(days=1)
        )

        assert order.is_overdue

    def test_progress_percentage_no_steps(self):
        """Тест прогресса без этапов производства"""
        order = Order(customer_id=1, status=OrderStatus.PENDING)

        assert order.progress_percentage == 0.0

    def test_progress_percentage_delivered(self):
        """Тест прогресса для доставленного заказа"""
        order = Order(customer_id=1, status=OrderStatus.DELIVERED)

        assert order.progress_percentage == 100.0

    def test_progress_percentage_cancelled(self):
        """Тест прогресса для отмененного заказа"""
        order = Order(customer_id=1, status=OrderStatus.CANCELLED)

        assert order.progress_percentage == 0.0

    def test_progress_percentage_with_steps(self):
        """Тест прогресса с этапами производства"""
        order = Order(customer_id=1, status=OrderStatus.IN_PRODUCTION)

        # Мокаем этапы производства
        step1 = MagicMock()
        step1.status.name = "COMPLETED"
        step2 = MagicMock()
        step2.status.name = "IN_PROGRESS"
        step3 = MagicMock()
        step3.status.name = "PENDING"

        order.production_steps = [step1, step2, step3]

        # Расчет: 1 завершенный + 0.5 за in_progress = 1.5 из 3 = 50%
        assert order.progress_percentage == 50.0

    def test_can_transition_to_valid(self):
        """Тест валидных переходов статуса"""
        order = Order(customer_id=1, status=OrderStatus.PENDING)

        assert order.can_transition_to(OrderStatus.IN_DESIGN)
        assert order.can_transition_to(OrderStatus.CANCELLED)
        assert not order.can_transition_to(OrderStatus.DELIVERED)

    def test_update_status_valid(self):
        """Тест обновления статуса валидным переходом"""
        order = Order(customer_id=1, status=OrderStatus.PENDING)

        order.update_status(OrderStatus.IN_DESIGN)

        assert order.status == OrderStatus.IN_DESIGN
        assert order.updated_at is not None

    def test_update_status_invalid(self):
        """Тест обновления статуса невалидным переходом"""
        order = Order(customer_id=1, status=OrderStatus.PENDING)

        with pytest.raises(ValueError, match="Невозможно изменить статус"):
            order.update_status(OrderStatus.DELIVERED)


class TestProductionStepModel:
    """Тесты для модели ProductionStep"""

    def test_production_step_creation(self):
        """Тест создания этапа производства"""
        step = ProductionStep(
            order_id=1,
            name="Подготовка макета",
            description="Подготовка дизайн-макета",
            sequence_number=1,
            status=StepStatus.PENDING,
            estimated_hours=24
        )

        assert step.order_id == 1
        assert step.name == "Подготовка макета"
        assert step.sequence_number == 1
        assert step.status == StepStatus.PENDING
        assert step.estimated_hours == 24

    def test_production_step_repr(self):
        """Тест строкового представления этапа"""
        step = ProductionStep(
            order_id=1,
            name="Тестовый этап",
            status=StepStatus.IN_PROGRESS
        )

        assert repr(step) == "<ProductionStep(order_id=1, name='Тестовый этап', status=in_progress)>"

    def test_is_overdue_completed(self):
        """Тест просрочки для завершенного этапа"""
        step = ProductionStep(
            order_id=1,
            name="Test",
            status=StepStatus.COMPLETED,
            started_at=datetime.utcnow() - timedelta(hours=30),
            estimated_hours=24
        )

        assert not step.is_overdue

    def test_is_overdue_no_start_time(self):
        """Тест просрочки без времени начала"""
        step = ProductionStep(
            order_id=1,
            name="Test",
            status=StepStatus.IN_PROGRESS,
            estimated_hours=24
        )

        assert not step.is_overdue

    def test_is_overdue_no_estimate(self):
        """Тест просрочки без оценки времени"""
        step = ProductionStep(
            order_id=1,
            name="Test",
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow() - timedelta(hours=30)
        )

        assert not step.is_overdue

    def test_is_overdue_overdue(self):
        """Тест просроченного этапа"""
        step = ProductionStep(
            order_id=1,
            name="Test",
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow() - timedelta(hours=30),
            estimated_hours=24
        )

        assert step.is_overdue

    def test_progress_percentage_completed(self):
        """Тест прогресса завершенного этапа"""
        step = ProductionStep(order_id=1, name="Test", status=StepStatus.COMPLETED)

        assert step.progress_percentage == 100.0

    def test_progress_percentage_in_progress(self):
        """Тест прогресса этапа в работе"""
        step = ProductionStep(order_id=1, name="Test", status=StepStatus.IN_PROGRESS)

        assert step.progress_percentage == 50.0

    def test_progress_percentage_pending(self):
        """Тест прогресса ожидающего этапа"""
        step = ProductionStep(order_id=1, name="Test", status=StepStatus.PENDING)

        assert step.progress_percentage == 0.0

    def test_start_work(self):
        """Тест начала работы над этапом"""
        step = ProductionStep(order_id=1, name="Test", status=StepStatus.PENDING)

        step.start_work()

        assert step.status == StepStatus.IN_PROGRESS
        assert step.started_at is not None

    def test_complete_work(self):
        """Тест завершения работы над этапом"""
        step = ProductionStep(
            order_id=1,
            name="Test",
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )

        step.complete_work(actual_hours=20.5, notes="Готово")

        assert step.status == StepStatus.COMPLETED
        assert step.completed_at is not None
        assert step.actual_hours == 20.5
        assert step.notes == "Готово"


class TestCustomerModelExtended:
    """Расширенные тесты для модели Customer"""

    def test_customer_loyalty_calculation(self):
        """Тест расчета уровня лояльности"""
        from src.aicrm.models.customer import Customer

        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+7-999-123-45-67",
            address="Test Address"
        )

        # Тестируем разные уровни лояльности на основе суммы покупок
        # Создаем мок заказов для тестирования
        order1 = MagicMock()
        order1.total_amount = 500.00  # bronze уровень (< 1000)
        customer.orders = [order1]
        customer.update_stats()
        assert customer.loyalty_level == "bronze"

        order2 = MagicMock()
        order2.total_amount = 600.00  # итого 1100 > 1000 - silver уровень
        customer.orders = [order1, order2]
        customer.update_stats()
        assert customer.loyalty_level == "silver"

        order3 = MagicMock()
        order3.total_amount = 4500.00  # итого 5600 > 5000 - gold уровень
        customer.orders = [order1, order2, order3]
        customer.update_stats()
        assert customer.loyalty_level == "gold"

        order4 = MagicMock()
        order4.total_amount = 5000.00  # итого 10600 > 10000 - platinum уровень
        customer.orders = [order1, order2, order3, order4]
        customer.update_stats()
        assert customer.loyalty_level == "platinum"

    def test_customer_total_spent_calculation(self):
        """Тест расчета общей суммы заказов"""
        from src.aicrm.models.customer import Customer

        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+7-999-123-45-67",
            address="Test Address"
        )

        # Имитируем заказы
        customer.total_orders = 3
        customer.total_spent = 1500.50
        assert customer.total_spent == 1500.50


class TestAISettingsModel:
    """Тесты для модели AISettings"""

    def test_ai_settings_creation(self):
        """Тест создания настроек AI"""
        settings = AISettings(
            default_model="deepseek/deepseek-chat-v3.1",
            temperature=0.7,
            max_tokens=1000,
            provider="openrouter",
            auto_reply_enabled=True,
            auto_reply_temperature=0.5,
            auto_reply_max_tokens=500,
            rate_limit_per_minute=60,
            cache_enabled=True,
            log_level="INFO"
        )

        assert settings.default_model == "deepseek/deepseek-chat-v3.1"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.provider == "openrouter"
        assert settings.auto_reply_enabled is True
        assert settings.auto_reply_temperature == 0.5
        assert settings.auto_reply_max_tokens == 500
        assert settings.rate_limit_per_minute == 60
        assert settings.cache_enabled is True
        assert settings.log_level == "INFO"

    def test_ai_settings_repr(self):
        """Тест строкового представления настроек AI"""
        settings = AISettings(
            provider="openai",
            default_model="gpt-4"
        )

        assert repr(settings) == "<AISettings(id=None, provider=openai, default_model=gpt-4)>"

    def test_ai_settings_creation_empty(self):
        """Тест создания пустых настроек AI"""
        settings = AISettings()

        # Проверяем, что объект создан
        assert settings is not None
        assert isinstance(settings, AISettings)
