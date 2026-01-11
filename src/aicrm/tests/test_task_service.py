"""
Юнит-тесты для TaskService
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.aicrm.models.task import Task
from src.aicrm.services.task import TaskService


class TestTaskService:
    """Тесты для TaskService"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock()

    @pytest.fixture
    def sample_task_data(self):
        """Пример данных задачи"""
        return {
            "title": "Подготовить дизайн",
            "description": "Создать макет для футболки",
            "priority": "high",
            "assigned_to": 2,
            "due_date": datetime.utcnow() + timedelta(days=3),
            "estimated_hours": 8,
        }

    @pytest.fixture
    def sample_task(self, sample_task_data):
        """Пример объекта задачи"""
        task = Task(**sample_task_data)
        task.id = 1
        task.created_by = 1
        task.status = "todo"
        return task

    def test_create_task_success(self, mock_db, sample_task_data, sample_task):
        """Тест успешного создания задачи"""
        # Настройка мока
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        # Вызов метода
        result = TaskService.create_task(mock_db, sample_task_data, created_by=1)

        # Проверки
        assert result.title == sample_task_data["title"]
        assert result.created_by == 1
        assert result.status == "todo"
        assert result.id == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_task_found(self, mock_db, sample_task):
        """Тест получения существующей задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task

        result = TaskService.get_task(mock_db, 1)

        assert result == sample_task

    def test_get_task_not_found(self, mock_db):
        """Тест получения несуществующей задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.get_task(mock_db, 999)

        assert result is None

    def test_get_tasks_no_filters(self, mock_db, sample_task):
        """Тест получения списка задач без фильтров"""
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            sample_task
        ]

        result = TaskService.get_tasks(mock_db)

        assert len(result) == 1
        assert result[0] == sample_task

    def test_get_tasks_with_filters(self, mock_db, sample_task):
        """Тест получения списка задач с фильтрами"""
        # Настраиваем мок для цепочки вызовов
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.filter.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            sample_task
        ]

        result = TaskService.get_tasks(
            mock_db, assigned_to=2, status="todo", priority="high"
        )

        assert len(result) == 1
        # Проверяем, что фильтры были применены
        filter_mock = mock_query.filter
        filter_mock.assert_called()

    def test_update_task_success(self, mock_db, sample_task):
        """Тест успешного обновления задачи"""
        update_data = {"status": "in_progress", "description": "Обновленное описание"}

        mock_db.query.return_value.filter.return_value.first.return_value = sample_task

        result = TaskService.update_task(mock_db, 1, update_data)

        assert result == sample_task
        assert sample_task.status == update_data["status"]
        assert sample_task.description == update_data["description"]
        mock_db.commit.assert_called_once()

    def test_update_task_not_found(self, mock_db):
        """Тест обновления несуществующей задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.update_task(mock_db, 999, {"title": "Test"})

        assert result is None

    def test_delete_task_success(self, mock_db, sample_task):
        """Тест успешного удаления задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task

        result = TaskService.delete_task(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_task)
        mock_db.commit.assert_called_once()

    def test_delete_task_not_found(self, mock_db):
        """Тест удаления несуществующей задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.delete_task(mock_db, 999)

        assert result is False

    def test_complete_task_success(self, mock_db, sample_task):
        """Тест успешного завершения задачи"""
        sample_task.status = "in_progress"

        mock_db.query.return_value.filter.return_value.first.return_value = sample_task

        result = TaskService.complete_task(mock_db, 1)

        assert result == sample_task
        assert sample_task.status == "done"
        assert sample_task.completed_at is not None
        mock_db.commit.assert_called_once()

    def test_complete_task_not_found(self, mock_db):
        """Тест завершения несуществующей задачи"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = TaskService.complete_task(mock_db, 999)

        assert result is None
