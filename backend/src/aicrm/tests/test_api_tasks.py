"""
Интеграционные тесты для Task API
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.aicrm.models.task import Task


class TestTaskAPI:
    """Тесты для Task API"""

    @pytest.fixture
    async def auth_token(self, async_client: AsyncClient):
        """Получение токена аутентификации"""
        # Регистрируем пользователя
        response = await async_client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "testpass123"
        })

        # Логинимся
        response = await async_client.post("/auth/login/json", json={
            "email": "test@example.com",
            "password": "testpass123"
        })

        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.fixture
    async def test_task(self, async_db: AsyncSession):
        """Создание тестовой задачи"""
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

    async def test_create_task_success(self, async_client: AsyncClient, auth_token: str):
        """Тест успешного создания задачи"""
        due_date = (datetime.utcnow() + timedelta(days=5)).isoformat()

        task_data = {
            "title": "Новая задача",
            "description": "Описание новой задачи",
            "priority": "high",
            "assigned_to": 1,
            "due_date": due_date,
            "estimated_hours": 8
        }

        response = await async_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["status"] == "todo"
        assert data["created_by"] == 1  # ID пользователя из токена

    async def test_create_task_unauthorized(self, async_client: AsyncClient):
        """Тест создания задачи без авторизации"""
        task_data = {
            "title": "Новая задача",
            "description": "Описание новой задачи"
        }

        response = await async_client.post("/tasks/", json=task_data)

        assert response.status_code == 401

    async def test_get_tasks_success(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест получения списка задач"""
        response = await async_client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Проверяем, что наша тестовая задача есть в списке
        task_found = any(t["id"] == test_task.id for t in data)
        assert task_found

    async def test_get_task_by_id_success(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест получения задачи по ID"""
        response = await async_client.get(
            f"/tasks/{test_task.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["title"] == test_task.title
        assert data["description"] == test_task.description
        assert data["status"] == test_task.status

    async def test_get_task_not_found(self, async_client: AsyncClient, auth_token: str):
        """Тест получения несуществующей задачи"""
        response = await async_client.get(
            "/tasks/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_task_success(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест успешного обновления задачи"""
        update_data = {
            "status": "in_progress",
            "description": "Обновленное описание задачи",
            "priority": "high"
        }

        response = await async_client.put(
            f"/tasks/{test_task.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == update_data["status"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["title"] == test_task.title  # Неизмененное поле

    async def test_update_task_not_found(self, async_client: AsyncClient, auth_token: str):
        """Тест обновления несуществующей задачи"""
        update_data = {"title": "Новая задача"}

        response = await async_client.put(
            "/tasks/99999",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    async def test_delete_task_success(self, async_client: AsyncClient, auth_token: str, async_db: AsyncSession):
        """Тест успешного удаления задачи"""
        # Создаем задачу для удаления
        task = Task(
            title="Задача для удаления",
            description="Будет удалена",
            assigned_to=1,
            created_by=1,
            status="todo"
        )
        async_db.add(task)
        await async_db.commit()
        await async_db.refresh(task)

        response = await async_client.delete(
            f"/tasks/{task.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Проверяем, что задача действительно удалена
        response = await async_client.get(
            f"/tasks/{task.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    async def test_delete_task_not_found(self, async_client: AsyncClient, auth_token: str):
        """Тест удаления несуществующей задачи"""
        response = await async_client.delete(
            "/tasks/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    async def test_complete_task_success(self, async_client: AsyncClient, auth_token: str, async_db: AsyncSession):
        """Тест успешного завершения задачи"""
        # Создаем задачу для завершения
        task = Task(
            title="Задача для завершения",
            description="Будет завершена",
            assigned_to=1,
            created_by=1,
            status="in_progress"
        )
        async_db.add(task)
        await async_db.commit()
        await async_db.refresh(task)

        response = await async_client.post(
            f"/tasks/{task.id}/complete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    async def test_complete_task_not_found(self, async_client: AsyncClient, auth_token: str):
        """Тест завершения несуществующей задачи"""
        response = await async_client.post(
            "/tasks/99999/complete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    async def test_get_tasks_with_filters(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест получения задач с фильтрами"""
        response = await async_client.get(
            "/tasks/",
            params={"status": "todo", "priority": "medium"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Проверяем, что наша задача соответствует фильтрам
        for task in data:
            if task["id"] == test_task.id:
                assert task["status"] == "todo"
                assert task["priority"] == "medium"

    async def test_get_tasks_pagination(self, async_client: AsyncClient, auth_token: str):
        """Тест пагинации списка задач"""
        response = await async_client.get(
            "/tasks/",
            params={"skip": 0, "limit": 5},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    async def test_get_tasks_assigned_filter(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест фильтрации задач по назначенному пользователю"""
        response = await async_client.get(
            "/tasks/",
            params={"assigned_to": 1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Проверяем, что все задачи назначены на пользователя 1
        for task in data:
            assert task["assigned_to"] == 1

    async def test_create_task_minimal_data(self, async_client: AsyncClient, auth_token: str):
        """Тест создания задачи с минимальными данными"""
        task_data = {
            "title": "Минимальная задача"
        }

        response = await async_client.post(
            "/tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["status"] == "todo"
        assert data["priority"] == "medium"  # Значение по умолчанию

    async def test_update_task_partial(self, async_client: AsyncClient, auth_token: str, test_task: Task):
        """Тест частичного обновления задачи"""
        # Обновляем только статус
        update_data = {"status": "in_progress"}

        response = await async_client.put(
            f"/tasks/{test_task.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["title"] == test_task.title  # Неизмененное поле
        assert data["description"] == test_task.description  # Неизмененное поле
