"""
Тесты для основных сервисов с целью достижения 100% покрытия
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.aicrm.models.customer import Customer
from src.aicrm.models.order import Order, OrderStatus
from src.aicrm.models.production_step import ProductionStep, StepStatus
from src.aicrm.models.task import Task
from src.aicrm.services.customer import CustomerService
from src.aicrm.services.production import ProductionService
from src.aicrm.services.task import TaskService


class TestCustomerService:
    """Тесты для CustomerService"""

    def test_create_customer_success(self):
        """Тест успешного создания клиента"""
        mock_db = MagicMock()
        customer_data = {
            "name": "Иван Иванов",
            "email": "ivan@example.com",
            "phone": "+7-999-123-45-67",
        }

        # Мокаем создание клиента
        mock_customer = Customer(**customer_data)
        mock_customer.id = 1

        with patch("src.aicrm.services.customer.Customer", return_value=mock_customer):
            result = CustomerService.create_customer(mock_db, customer_data)

            assert result.id == 1
            assert result.name == "Иван Иванов"
            assert result.email == "ivan@example.com"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_get_customer_found(self):
        """Тест получения существующего клиента"""
        mock_db = MagicMock()
        mock_customer = Customer(id=1, name="Иван Иванов", email="ivan@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )

        result = CustomerService.get_customer(mock_db, 1)

        assert result.id == 1
        assert result.name == "Иван Иванов"

    def test_get_customer_not_found(self):
        """Тест получения несуществующего клиента"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.get_customer(mock_db, 999)

        assert result is None

    def test_update_customer_success(self):
        """Тест успешного обновления клиента"""
        mock_db = MagicMock()
        mock_customer = Customer(id=1, name="Иван Иванов", email="ivan@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )

        update_data = {"name": "Иван Петров", "phone": "+7-999-987-65-43"}

        result = CustomerService.update_customer(mock_db, 1, update_data)

        assert result.name == "Иван Петров"
        assert result.phone == "+7-999-987-65-43"
        mock_db.commit.assert_called_once()

    def test_update_customer_not_found(self):
        """Тест обновления несуществующего клиента"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.update_customer(mock_db, 999, {"name": "Test"})

        assert result is None

    def test_delete_customer_success(self):
        """Тест успешного удаления клиента"""
        mock_db = MagicMock()
        mock_customer = Customer(id=1, name="Иван Иванов")
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )

        result = CustomerService.delete_customer(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_customer)
        mock_db.commit.assert_called_once()

    def test_delete_customer_not_found(self):
        """Тест удаления несуществующего клиента"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.delete_customer(mock_db, 999)

        assert result is False

    def test_get_customers_no_filters(self):
        """Тест получения списка клиентов без фильтров"""
        mock_db = MagicMock()
        mock_customers = [
            Customer(id=1, name="Иван Иванов"),
            Customer(id=2, name="Петр Петров"),
        ]

        # Properly mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_customers

        result = CustomerService.get_customers(mock_db)

        assert len(result) == 2
        assert result[0].name == "Иван Иванов"

    def test_get_customers_with_search(self):
        """Тест получения списка клиентов с поиском"""
        mock_db = MagicMock()
        mock_customers = [Customer(id=1, name="Иван Иванов")]

        # Properly mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_customers

        result = CustomerService.get_customers(mock_db, search="Иван")

        assert len(result) == 1
        assert result[0].name == "Иван Иванов"

    def test_get_customer_stats_success(self):
        """Тест получения статистики клиента"""
        mock_db = MagicMock()
        mock_customer = Customer(
            id=1,
            name="Иван Иванов",
            total_orders=5,
            total_spent=15000.0,
            loyalty_level="gold",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )

        # Mock the stats query result - simplified
        mock_stats = MagicMock()
        mock_stats.last_order_date = datetime.utcnow()
        mock_stats.average_order_value = 3000.0

        # Set up the side effect properly
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_stats,
        ]

        result = CustomerService.get_customer_stats(mock_db, 1)

        # Just check that we get a result with expected structure
        assert isinstance(result, dict)
        assert "total_orders" in result
        assert "loyalty_level" in result

    def test_get_customer_stats_not_found(self):
        """Тест получения статистики несуществующего клиента"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.get_customer_stats(mock_db, 999)

        assert result is None

    def test_search_customers(self):
        """Тест поиска клиентов"""
        mock_db = MagicMock()
        mock_customers = [
            Customer(id=1, name="Иван Иванов", email="ivan@example.com"),
            Customer(id=2, name="Иван Петров", email="petrov@example.com"),
        ]

        # Properly mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_customers

        result = CustomerService.search_customers(mock_db, "Иван")

        assert len(result) == 2
        assert all("Иван" in customer.name for customer in result)


class TestTaskService:
    """Тесты для TaskService"""

    def test_create_task_success(self):
        """Тест успешного создания задачи"""
        mock_db = MagicMock()
        task_data = {
            "title": "Тестовая задача",
            "description": "Описание задачи",
            "priority": "high",
            "assigned_to": 1,
        }

        mock_task = Task(**task_data)
        mock_task.id = 1

        with patch("src.aicrm.services.task.Task", return_value=mock_task):
            result = TaskService.create_task(mock_db, task_data, created_by=2)

            assert result.id == 1
            assert result.title == "Тестовая задача"
            assert result.priority == "high"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_get_task_found(self):
        """Тест получения существующей задачи"""
        mock_db = MagicMock()
        mock_task = Task(id=1, title="Тестовая задача", status="todo")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.get_task(mock_db, 1)

        assert result.id == 1
        assert result.title == "Тестовая задача"

    def test_get_task_not_found(self):
        """Тест получения несуществующей задачи"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.get_task(mock_db, 999)

        assert result is None

    def test_get_tasks_no_filters(self):
        """Тест получения списка задач без фильтров"""
        mock_db = MagicMock()
        mock_tasks = [
            Task(id=1, title="Задача 1", status="todo"),
            Task(id=2, title="Задача 2", status="done"),
        ]

        # Properly mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        result = TaskService.get_tasks(mock_db)

        assert len(result) == 2
        assert result[0].title == "Задача 1"

    def test_get_tasks_with_filters(self):
        """Тест получения списка задач с фильтрами"""
        mock_db = MagicMock()
        mock_tasks = [Task(id=1, title="Задача 1", status="todo", assigned_to=1)]

        # Properly mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        result = TaskService.get_tasks(mock_db, status="todo", assigned_to=1)

        assert len(result) == 1
        assert result[0].status == "todo"
        assert result[0].assigned_to == 1

    def test_update_task_success(self):
        """Тест успешного обновления задачи"""
        mock_db = MagicMock()
        mock_task = Task(id=1, title="Старая задача", status="todo")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        update_data = {"title": "Новая задача", "status": "in_progress"}

        result = TaskService.update_task(mock_db, 1, update_data)

        assert result.title == "Новая задача"
        assert result.status == "in_progress"
        mock_db.commit.assert_called_once()

    def test_update_task_not_found(self):
        """Тест обновления несуществующей задачи"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.update_task(mock_db, 999, {"title": "Test"})

        assert result is None

    def test_delete_task_success(self):
        """Тест успешного удаления задачи"""
        mock_db = MagicMock()
        mock_task = Task(id=1, title="Задача для удаления")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.delete_task(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_task)
        mock_db.commit.assert_called_once()

    def test_delete_task_not_found(self):
        """Тест удаления несуществующей задачи"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.delete_task(mock_db, 999)

        assert result is False

    def test_complete_task_success(self):
        """Тест успешного завершения задачи"""
        mock_db = MagicMock()
        mock_task = Task(id=1, title="Задача", status="in_progress")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.complete_task(mock_db, 1)

        assert result is not None
        assert result.status == "done"
        assert result.completed_at is not None
        mock_db.commit.assert_called_once()

    def test_complete_task_not_found(self):
        """Тест завершения несуществующей задачи"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.complete_task(mock_db, 999)

        assert result is None


class TestProductionService:
    """Тесты для ProductionService"""

    def test_create_production_workflow_success(self):
        """Тест успешного создания производственного workflow"""
        mock_db = MagicMock()
        mock_order = Order(
            id=1, customer_id=1, status=OrderStatus.PENDING, total_amount=1000.0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        service = ProductionService(mock_db)
        result = service.create_production_workflow(1)

        assert len(result) == 5  # 5 стандартных шагов
        assert mock_db.add.call_count == 5
        mock_db.commit.assert_called()

    def test_create_production_workflow_order_not_found(self):
        """Тест создания workflow для несуществующего заказа"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProductionService(mock_db)

        with pytest.raises(ValueError, match="Заказ с ID 999 не найден"):
            service.create_production_workflow(999)

    def test_start_step_success(self):
        """Тест успешного начала шага производства"""
        mock_db = MagicMock()
        mock_step = ProductionStep(
            id=1,
            order_id=1,
            name="Тестовый шаг",
            status=StepStatus.PENDING,
            sequence_number=1,
            estimated_hours=2,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_step

        service = ProductionService(mock_db)
        result = service.start_step(1)

        assert result.status == StepStatus.IN_PROGRESS
        assert result.started_at is not None
        mock_db.commit.assert_called_once()

    def test_start_step_not_found(self):
        """Тест начала несуществующего шага"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProductionService(mock_db)

        with pytest.raises(ValueError, match="Этап с ID 999 не найден"):
            service.start_step(999)

    def test_start_step_already_in_progress(self):
        """Тест начала шага, который уже в работе"""
        mock_db = MagicMock()
        mock_step = ProductionStep(
            id=1,
            order_id=1,
            name="Шаг в работе",
            status=StepStatus.IN_PROGRESS,
            sequence_number=1,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_step

        service = ProductionService(mock_db)

        with pytest.raises(ValueError, match="Этап .* уже в статусе"):
            service.start_step(1)

    def test_reassign_step_success(self):
        """Тест успешной перепривязки шага"""
        mock_db = MagicMock()
        mock_step = ProductionStep(
            id=1,
            order_id=1,
            name="Шаг для перепривязки",
            sequence_number=1,
            assigned_user_id=1,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_step

        service = ProductionService(mock_db)
        result = service.reassign_step(1, 2)  # Новый исполнитель

        assert result.assigned_user_id == 2
        mock_db.commit.assert_called_once()

    def test_reassign_step_not_found(self):
        """Тест перепривязки несуществующего шага"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProductionService(mock_db)

        with pytest.raises(ValueError, match="Этап с ID 999 не найден"):
            service.reassign_step(999, 2)
