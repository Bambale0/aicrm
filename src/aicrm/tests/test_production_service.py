"""
Юнит-тесты для ProductionService
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.aicrm.services.production import ProductionService
from src.aicrm.models.order import Order, OrderStatus
from src.aicrm.models.production_step import ProductionStep, StepStatus


class TestProductionService:
    """Тесты для ProductionService"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock()

    @pytest.fixture
    def production_service(self, mock_db):
        """Фикстура для ProductionService"""
        return ProductionService(mock_db)

    @pytest.fixture
    def sample_order(self):
        """Пример заказа"""
        order = Order(
            customer_id=1,
            status=OrderStatus.PENDING,
            total_amount=1500.00,
            items=[{"product_type": "tshirt", "quantity": 3}],
            source="website"
        )
        order.id = 1
        return order

    @pytest.fixture
    def sample_step(self, sample_order):
        """Пример этапа производства"""
        step = ProductionStep(
            order_id=sample_order.id,
            name="Подготовка макета",
            description="Подготовка дизайн-макета",
            sequence_number=1,
            status=StepStatus.PENDING,
            estimated_hours=24
        )
        step.id = 1
        return step

    def test_create_production_workflow_success(self, production_service, mock_db, sample_order):
        """Тест успешного создания workflow производства"""
        # Настройка мока
        mock_db.query.return_value.filter.return_value.first.return_value = sample_order
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        # Вызов метода
        result = production_service.create_production_workflow(1)

        # Проверки
        assert len(result) == 5  # Стандартные 5 этапов
        assert result[0].name == "Подготовка макета"
        assert result[0].sequence_number == 1
        assert result[0].status == StepStatus.PENDING
        assert sample_order.status == OrderStatus.IN_DESIGN
        mock_db.commit.assert_called()

    def test_create_production_workflow_order_not_found(self, production_service, mock_db):
        """Тест создания workflow для несуществующего заказа"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Заказ с ID 999 не найден"):
            production_service.create_production_workflow(999)

    def test_update_progress_no_steps(self, production_service, mock_db):
        """Тест обновления прогресса для заказа без этапов"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = production_service.update_progress(1)

        assert result["total_steps"] == 0
        assert result["progress"] == 0.0
        assert result["current_step"] is None

    def test_update_progress_with_steps(self, production_service, mock_db, sample_step):
        """Тест обновления прогресса для заказа с этапами"""
        steps = [sample_step]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = steps

        result = production_service.update_progress(1)

        assert result["total_steps"] == 1
        assert result["completed_steps"] == 0
        assert result["progress"] == 0.0
        assert result["current_step"] is None

    def test_start_step_success(self, production_service, mock_db, sample_step):
        """Тест успешного запуска этапа"""
        sample_step.status = StepStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = sample_step

        result = production_service.start_step(1)

        assert result == sample_step
        assert sample_step.status == StepStatus.IN_PROGRESS
        assert sample_step.started_at is not None
        mock_db.commit.assert_called_once()

    def test_start_step_not_found(self, production_service, mock_db):
        """Тест запуска несуществующего этапа"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Этап с ID 999 не найден"):
            production_service.start_step(999)

    def test_start_step_already_in_progress(self, production_service, mock_db, sample_step):
        """Тест запуска этапа, который уже в работе"""
        sample_step.status = StepStatus.IN_PROGRESS
        mock_db.query.return_value.filter.return_value.first.return_value = sample_step

        with pytest.raises(ValueError, match="Этап .* уже в статусе"):
            production_service.start_step(1)

    def test_complete_step_success(self, production_service, mock_db, sample_step):
        """Тест успешного завершения этапа"""
        sample_step.status = StepStatus.IN_PROGRESS
        mock_db.query.return_value.filter.return_value.first.return_value = sample_step

        # Мокаем методы для проверки автоматического запуска следующего этапа
        with patch.object(production_service, '_check_and_start_next_step') as mock_check_next, \
             patch.object(production_service, '_check_order_completion') as mock_check_order:

            result = production_service.complete_step(1, actual_hours=20.5, notes="Готово")

        assert result == sample_step
        assert sample_step.status == StepStatus.COMPLETED
        assert sample_step.completed_at is not None
        assert sample_step.actual_hours == 20.5
        assert sample_step.notes == "Готово"
        mock_check_next.assert_called_once_with(1)
        mock_check_order.assert_called_once_with(1)

    def test_complete_step_not_found(self, production_service, mock_db):
        """Тест завершения несуществующего этапа"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Этап с ID 999 не найден"):
            production_service.complete_step(999)

    def test_complete_step_not_in_progress(self, production_service, mock_db, sample_step):
        """Тест завершения этапа, который не в работе"""
        sample_step.status = StepStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = sample_step

        with pytest.raises(ValueError, match="Этап .* не в работе"):
            production_service.complete_step(1)

    def test_check_and_start_next_step(self, production_service, mock_db, sample_step):
        """Тест автоматического запуска следующего этапа"""
        # Создаем два этапа: первый завершен, второй ожидает
        completed_step = sample_step
        completed_step.status = StepStatus.COMPLETED
        completed_step.order_id = 1

        pending_step = ProductionStep(
            order_id=1,
            name="Следующий этап",
            sequence_number=2,
            status=StepStatus.PENDING
        )

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            completed_step, pending_step
        ]

        production_service._check_and_start_next_step(1)

        assert pending_step.status == StepStatus.IN_PROGRESS
        assert pending_step.started_at is not None
        mock_db.commit.assert_called_once()

    def test_check_order_completion_all_done(self, production_service, mock_db, sample_order, sample_step):
        """Тест автоматического завершения заказа при завершении всех этапов"""
        sample_step.status = StepStatus.COMPLETED
        sample_order.production_steps = [sample_step]
        sample_order.status = OrderStatus.IN_PRODUCTION  # Меняем статус на допустимый для перехода

        mock_db.query.return_value.filter.return_value.first.return_value = sample_order

        production_service._check_order_completion(1)

        assert sample_order.status == OrderStatus.READY
        mock_db.commit.assert_called_once()

    def test_get_overdue_steps(self, production_service, mock_db, sample_step, sample_order):
        """Тест получения просроченных этапов"""
        # Настройка просроченного этапа
        sample_step.status = StepStatus.IN_PROGRESS
        sample_step.started_at = datetime.utcnow() - timedelta(hours=30)  # Просрочен
        sample_step.estimated_hours = 24
        sample_step.order = sample_order

        mock_db.query.return_value.filter.return_value.all.return_value = [sample_step]

        result = production_service.get_overdue_steps()

        assert len(result) == 1
        assert result[0]["step_id"] == 1
        assert "overdue_hours" in result[0]

    def test_reassign_step_success(self, production_service, mock_db, sample_step):
        """Тест успешного переназначения этапа"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_step

        result = production_service.reassign_step(1, 5)

        assert result == sample_step
        assert sample_step.assigned_user_id == 5
        mock_db.commit.assert_called_once()

    def test_reassign_step_not_found(self, production_service, mock_db):
        """Тест переназначения несуществующего этапа"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Этап с ID 999 не найден"):
            production_service.reassign_step(999, 5)
