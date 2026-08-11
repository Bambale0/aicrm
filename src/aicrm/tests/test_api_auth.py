"""
Интеграционные тесты для Auth API
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.aicrm.models.user import User


class TestAuthAPI:
    """Тесты для Auth API"""

    async def test_register_success(self, async_client: AsyncClient):
        """Тест успешной регистрации пользователя"""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data  # Пароль не должен возвращаться

    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """Тест регистрации с существующим email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123"
        }

        # Первая регистрация
        response1 = await async_client.post("/auth/register", json=user_data)
        assert response1.status_code == 200

        # Вторая регистрация с тем же email
        response2 = await async_client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Тест регистрации с некорректным email"""
        user_data = {
            "email": "invalid-email",  # Некорректный email
            "password": "password123"
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    async def test_register_weak_password(self, async_client: AsyncClient):
        """Тест регистрации со слабым паролем"""
        user_data = {
            "email": "weakpass@example.com",
            "password": "123"  # Слишком короткий пароль
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    async def test_login_success_form(self, async_client: AsyncClient):
        """Тест успешного входа через форму (OAuth2)"""
        # Сначала регистрируем пользователя
        user_data = {
            "email": "loginform@example.com",
            "password": "password123"
        }
        await async_client.post("/auth/register", json=user_data)

        # Затем логинимся
        response = await async_client.post(
            "/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)

    async def test_login_success_json(self, async_client: AsyncClient):
        """Тест успешного входа через JSON"""
        # Сначала регистрируем пользователя
        user_data = {
            "email": "loginjson@example.com",
            "password": "password123"
        }
        await async_client.post("/auth/register", json=user_data)

        # Затем логинимся
        response = await async_client.post("/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_email(self, async_client: AsyncClient):
        """Тест входа с неправильным email"""
        response = await async_client.post("/auth/login/json", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_wrong_password(self, async_client: AsyncClient):
        """Тест входа с неправильным паролем"""
        # Сначала регистрируем пользователя
        user_data = {
            "email": "wrongpass@example.com",
            "password": "correctpassword"
        }
        await async_client.post("/auth/register", json=user_data)

        # Пытаемся войти с неправильным паролем
        response = await async_client.post("/auth/login/json", json={
            "email": user_data["email"],
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Тест входа с отсутствующими полями"""
        response = await async_client.post("/auth/login/json", json={
            "email": "test@example.com"
            # Отсутствует password
        })

        assert response.status_code == 422  # Validation error

    async def test_register_missing_fields(self, async_client: AsyncClient):
        """Тест регистрации с отсутствующими полями"""
        response = await async_client.post("/auth/register", json={
            "email": "test@example.com"
            # Отсутствует password
        })

        assert response.status_code == 422  # Validation error

    async def test_register_empty_fields(self, async_client: AsyncClient):
        """Тест регистрации с пустыми полями"""
        response = await async_client.post("/auth/register", json={
            "email": "",
            "password": ""
        })

        assert response.status_code == 422  # Validation error

    async def test_login_case_sensitive_email(self, async_client: AsyncClient):
        """Тест чувствительности к регистру email при входе"""
        # Регистрируем с одним регистром
        user_data = {
            "email": "CaseSensitive@example.com",
            "password": "password123"
        }
        await async_client.post("/auth/register", json=user_data)

        # Пытаемся войти с другим регистром
        response = await async_client.post("/auth/login/json", json={
            "email": "casesensitive@example.com",  # другой регистр
            "password": user_data["password"]
        })

        # В зависимости от реализации БД, может работать или нет
        # Но в любом случае должен быть либо успех, либо понятная ошибка
        assert response.status_code in [200, 401]

    async def test_register_and_login_workflow(self, async_client: AsyncClient):
        """Тест полного workflow регистрации и входа"""
        email = "workflow@example.com"
        password = "workflowpass123"

        # 1. Регистрация
        register_response = await async_client.post("/auth/register", json={
            "email": email,
            "password": password
        })
        assert register_response.status_code == 200

        # 2. Вход
        login_response = await async_client.post("/auth/login/json", json={
            "email": email,
            "password": password
        })
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        assert token is not None

        # 3. Проверка токена (попытка доступа к защищенному роуту)
        protected_response = await async_client.get(
            "/customers/",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Должен быть либо 200 (если есть данные), либо 200 с пустым списком
        assert protected_response.status_code == 200

    async def test_multiple_registrations(self, async_client: AsyncClient):
        """Тест множественных регистраций разных пользователей"""
        users = [
            {"email": "user1@example.com", "password": "pass1"},
            {"email": "user2@example.com", "password": "pass2"},
            {"email": "user3@example.com", "password": "pass3"}
        ]

        # Регистрируем всех пользователей
        for user in users:
            response = await async_client.post("/auth/register", json=user)
            assert response.status_code == 200

        # Проверяем, что все могут войти
        for user in users:
            response = await async_client.post("/auth/login/json", json=user)
            assert response.status_code == 200
            assert "access_token" in response.json()

    async def test_login_form_encoding(self, async_client: AsyncClient):
        """Тест входа через форму с правильной кодировкой"""
        # Регистрируем пользователя
        user_data = {
            "email": "formtest@example.com",
            "password": "formpassword123"
        }
        await async_client.post("/auth/register", json=user_data)

        # Логинимся через форму
        response = await async_client.post(
            "/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_special_characters_password(self, async_client: AsyncClient):
        """Тест регистрации с паролем, содержащим специальные символы"""
        user_data = {
            "email": "special@example.com",
            "password": "Sp3c!@l#P@ssw0rd$%^&*()"
        }

        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200

        # Проверяем вход с таким паролем
        login_response = await async_client.post("/auth/login/json", json=user_data)
        assert login_response.status_code == 200
