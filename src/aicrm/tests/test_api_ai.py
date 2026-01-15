"""
Интеграционные тесты для AI API
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


class TestAIApi:
    """Тесты для AI API"""

    async def test_analyze_intent_success(self, async_client: AsyncClient):
        """Тест успешного анализа намерения"""
        request_data = {
            "message": "Хочу заказать футболку с логотипом",
            "context": {
                "customer_id": 1,
                "previous_messages": ["Привет, чем могу помочь?"],
            },
        }

        # Мокаем AI сервис
        mock_response = {
            "intent": "order",
            "confidence": 0.95,
            "response": "Отлично! Я помогу вам оформить заказ на футболку с логотипом. Расскажите подробнее о ваших пожеланиях.",
            "needs_human_intervention": False,
            "suggested_actions": ["create_order", "ask_design_details"],
        }

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.process_customer_message.return_value = mock_response
            mock_service_class.return_value = mock_service

            response = await async_client.post("/analyze-intent", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "order"
            assert data["confidence"] == 0.95
            assert "response" in data
            assert data["needs_human_intervention"] is False

    async def test_analyze_intent_ai_error(self, async_client: AsyncClient):
        """Тест ошибки AI при анализе намерения"""
        request_data = {"message": "Тестовое сообщение", "context": {}}

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.process_customer_message.side_effect = Exception(
                "AI service error"
            )
            mock_service_class.return_value = mock_service

            response = await async_client.post("/analyze-intent", json=request_data)

            assert response.status_code == 500
            assert "AI анализ не удался" in response.json()["detail"]

    async def test_generate_response_success(self, async_client: AsyncClient):
        """Тест успешной генерации ответа"""
        request_data = {
            "message": "Сколько стоит доставка?",
            "context": {"customer_id": 1},
        }

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_intent.return_value = MagicMock(value="question")
            mock_service.generate_response.return_value = (
                "Доставка осуществляется бесплатно при заказе от 3000 рублей."
            )
            mock_service_class.return_value = mock_service

            response = await async_client.post("/generate-response", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "question"
            assert "доставка" in data["response"].lower()

    async def test_generate_response_error(self, async_client: AsyncClient):
        """Тест ошибки при генерации ответа"""
        request_data = {"message": "Тест", "context": {}}

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_intent.side_effect = Exception("Generation failed")
            mock_service_class.return_value = mock_service

            response = await async_client.post("/generate-response", json=request_data)

            assert response.status_code == 500
            assert "Генерация ответа не удалась" in response.json()["detail"]

    async def test_chat_with_ai_success(self, async_client: AsyncClient):
        """Тест успешного чата с AI"""
        request_data = {
            "messages": [{"role": "user", "content": "Привет, как дела?"}],
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 100,
        }

        mock_response = "Привет! У меня все отлично, спасибо. Чем могу помочь?"

        with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await async_client.post("/chat", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == mock_response
            assert data["model_used"] == "test-model"
            assert "tokens_used" in data

    async def test_chat_with_ai_default_model(self, async_client: AsyncClient):
        """Тест чата с AI с моделью по умолчанию"""
        request_data = {"messages": [{"role": "user", "content": "Тестовое сообщение"}]}

        with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = "Ответ от AI"
            mock_client.provider.value = "openrouter"
            mock_client_class.return_value = mock_client

            response = await async_client.post("/chat", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["model_used"] == "openrouter"

    async def test_chat_with_ai_error(self, async_client: AsyncClient):
        """Тест ошибки при чате с AI"""
        request_data = {"messages": [{"role": "user", "content": "Тест"}]}

        with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.side_effect = Exception("AI chat failed")
            mock_client_class.return_value = mock_client

            response = await async_client.post("/chat", json=request_data)

            assert response.status_code == 502
            assert "AI чат не удался" in response.json()["detail"]

    async def test_get_available_models(self, async_client: AsyncClient):
        """Тест получения списка доступных моделей"""
        response = await async_client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "current_provider" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0

        # Проверяем структуру модели
        model = data["models"][0]
        assert "id" in model
        assert "name" in model
        assert "context_length" in model

    async def test_get_ai_status_success(self, async_client: AsyncClient):
        """Тест успешного получения статуса AI"""
        with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.provider.value = "openrouter"
            mock_client_class.return_value = mock_client

            response = await async_client.get("/status")

            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "openrouter"
            assert data["status"] == "active"
            assert "available_models" in data
            assert "default_model" in data

    async def test_get_ai_status_error(self, async_client: AsyncClient):
        """Тест ошибки при получении статуса AI"""
        with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.provider.side_effect = Exception("Status check failed")
            mock_client_class.return_value = mock_client

            response = await async_client.get("/status")

            assert response.status_code == 503
            assert "AI сервис недоступен" in response.json()["detail"]

    async def test_analyze_intent_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных для анализа намерения"""
        # Неправильные данные
        request_data = {
            "message": "",  # Пустое сообщение
            "context": "invalid_context",  # Неправильный тип контекста
        }

        response = await async_client.post("/analyze-intent", json=request_data)

        # Должен быть 422 Validation Error
        assert response.status_code == 422

    async def test_chat_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных для чата"""
        # Неправильные данные
        request_data = {
            "messages": [],  # Пустой список сообщений
            "temperature": 2.5,  # Температура вне диапазона
        }

        response = await async_client.post("/chat", json=request_data)

        assert response.status_code == 422

    async def test_analyze_intent_complex_context(self, async_client: AsyncClient):
        """Тест анализа намерения со сложным контекстом"""
        request_data = {
            "message": "У меня проблема с заказом #123",
            "context": {
                "customer_id": 1,
                "order_id": 123,
                "previous_intent": "complaint",
                "customer_history": ["order_created", "payment_received"],
            },
        }

        mock_response = {
            "intent": "complaint",
            "confidence": 0.88,
            "response": "Извините за неудобства. Давайте разберемся с вашим заказом #123.",
            "needs_human_intervention": True,
            "suggested_actions": ["check_order_status", "contact_support"],
        }

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.process_customer_message.return_value = mock_response
            mock_service_class.return_value = mock_service

            response = await async_client.post("/analyze-intent", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "complaint"
            assert data["needs_human_intervention"] is True
            assert "suggested_actions" in data

    async def test_chat_with_different_models(self, async_client: AsyncClient):
        """Тест чата с разными моделями"""
        models = [
            "deepseek/deepseek-coder:33b-instruct",
            "meta-llama/llama-3-70b-instruct",
        ]

        for model in models:
            request_data = {
                "messages": [{"role": "user", "content": "Привет"}],
                "model": model,
            }

            with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.chat_completion.return_value = f"Ответ от модели {model}"
                mock_client_class.return_value = mock_client

                response = await async_client.post("/chat", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert data["model_used"] == model

    async def test_ai_usage_logging_integration(
        self, async_client: AsyncClient, db_session
    ):
        """Интеграционный тест логирования использования AI токенов"""
        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        from src.aicrm.services.ai_usage_service import AIUsageService

        test_user = User(
            email="test_ai_usage@example.com",
            hashed_password="hashed_password",
            full_name="Test AI User",
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        # Тестируем логирование использования
        usage_service = AIUsageService(db_session)

        # Логируем использование токенов
        usage = await usage_service.log_usage(
            model_used="deepseek/deepseek-chat",
            endpoint="chat",
            total_tokens=150.5,
            prompt_tokens=50.0,
            completion_tokens=100.5,
            user_id=test_user.id,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        # Проверяем, что запись создана
        assert usage.id is not None
        assert usage.model_used == "deepseek/deepseek-chat"
        assert usage.endpoint == "chat"
        assert usage.total_tokens == 150.5
        assert usage.prompt_tokens == 50.0
        assert usage.completion_tokens == 100.5
        assert usage.user_id == test_user.id
        assert usage.ip_address == "127.0.0.1"
        assert usage.user_agent == "test-agent"
        assert usage.request_id is not None
        assert usage.month_year is not None

    async def test_monthly_usage_statistics_integration(
        self, async_client: AsyncClient, db_session
    ):
        """Интеграционный тест получения месячной статистики использования"""
        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        from src.aicrm.services.ai_usage_service import AIUsageService

        test_user = User(
            email="test_monthly@example.com",
            hashed_password="hashed_password",
            full_name="Test Monthly User",
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        usage_service = AIUsageService(db_session)

        # Логируем несколько использований
        await usage_service.log_usage(
            model_used="deepseek/deepseek-chat",
            endpoint="chat",
            total_tokens=100.0,
            user_id=test_user.id,
        )

        await usage_service.log_usage(
            model_used="deepseek/deepseek-chat",
            endpoint="analyze-intent",
            total_tokens=50.0,
            user_id=test_user.id,
        )

        await usage_service.log_usage(
            model_used="openai/gpt-4",
            endpoint="chat",
            total_tokens=200.0,
            user_id=test_user.id,
        )

        # Получаем статистику за текущий месяц
        stats = usage_service.get_monthly_usage(user_id=test_user.id)

        # Проверяем общую статистику
        assert stats["total_tokens"] == 350.0
        assert stats["total_requests"] == 3
        assert stats["unique_models"] == 2

        # Проверяем разбивку по моделям
        model_breakdown = {item["model"]: item for item in stats["model_breakdown"]}
        assert "deepseek/deepseek-chat" in model_breakdown
        assert "openai/gpt-4" in model_breakdown

        deepseek_stats = model_breakdown["deepseek/deepseek-chat"]
        assert deepseek_stats["tokens"] == 150.0
        assert deepseek_stats["requests"] == 2

        gpt4_stats = model_breakdown["openai/gpt-4"]
        assert gpt4_stats["tokens"] == 200.0
        assert gpt4_stats["requests"] == 1

    async def test_usage_history_integration(
        self, async_client: AsyncClient, db_session
    ):
        """Интеграционный тест получения истории использования"""
        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        from src.aicrm.services.ai_usage_service import AIUsageService

        test_user = User(
            email="test_history@example.com",
            hashed_password="hashed_password",
            full_name="Test History User",
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        usage_service = AIUsageService(db_session)

        # Логируем использование
        usage1 = await usage_service.log_usage(
            model_used="deepseek/deepseek-chat",
            endpoint="chat",
            total_tokens=75.0,
            user_id=test_user.id,
        )

        usage2 = await usage_service.log_usage(
            model_used="openai/gpt-4",
            endpoint="analyze-intent",
            total_tokens=125.0,
            user_id=test_user.id,
        )

        # Получаем историю
        history = usage_service.get_usage_history(
            days=1, user_id=test_user.id, limit=10
        )

        # Проверяем, что записи есть в истории (в обратном порядке)
        assert len(history) == 2

        # Последняя запись должна быть usage2
        latest_usage = history[0]
        assert latest_usage["model_used"] == "openai/gpt-4"
        assert latest_usage["endpoint"] == "analyze-intent"
        assert latest_usage["total_tokens"] == 125.0

        # Предыдущая запись должна быть usage1
        previous_usage = history[1]
        assert previous_usage["model_used"] == "deepseek/deepseek-chat"
        assert previous_usage["endpoint"] == "chat"
        assert previous_usage["total_tokens"] == 75.0

    async def test_ai_usage_api_endpoints_integration(
        self, async_client: AsyncClient, db_session
    ):
        """Интеграционный тест API эндпоинтов для статистики AI использования"""
        # Создаем тестового пользователя и логируемся
        from src.aicrm.models.user import User
        from src.aicrm.services.ai_usage_service import AIUsageService

        test_user = User(
            email="test_api_stats@example.com",
            hashed_password="hashed_password",
            full_name="Test API Stats User",
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        # Получаем токен для аутентификации
        login_response = await async_client.post(
            "/auth/login/json",
            json={
                "email": "test_api_stats@example.com",
                "password": "test123",  # Это не сработает, нужно создать пользователя через API
            },
        )

        # Вместо этого создадим пользователя через API
        register_response = await async_client.post(
            "/auth/register",
            json={
                "email": "test_api_stats2@example.com",
                "password": "test123",
                "full_name": "Test API Stats User 2",
            },
        )

        assert register_response.status_code == 200
        user_data = register_response.json()

        # Логируемся
        login_response = await async_client.post(
            "/auth/login/json",
            json={"email": "test_api_stats2@example.com", "password": "test123"},
        )

        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]

        # Используем AI чат для генерации использования токенов
        chat_response = await async_client.post(
            "/chat",
            json={
                "messages": [{"role": "user", "content": "Hello, test message"}],
                "model": "deepseek/deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 50,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert chat_response.status_code == 200

        # Проверяем месячную статистику через API
        monthly_response = await async_client.get(
            "/usage/monthly", headers={"Authorization": f"Bearer {token}"}
        )

        assert monthly_response.status_code == 200
        monthly_data = monthly_response.json()

        # Проверяем структуру ответа
        assert "total_tokens" in monthly_data
        assert "total_requests" in monthly_data
        assert "model_breakdown" in monthly_data
        assert monthly_data["total_requests"] >= 1
        assert monthly_data["total_tokens"] > 0

        # Проверяем историю использования через API
        history_response = await async_client.get(
            "/usage/history", headers={"Authorization": f"Bearer {token}"}
        )

        assert history_response.status_code == 200
        history_data = history_response.json()

        assert "history" in history_data
        assert len(history_data["history"]) >= 1

        # Проверяем структуру записи истории
        usage_record = history_data["history"][0]
        assert "model_used" in usage_record
        assert "endpoint" in usage_record
        assert "total_tokens" in usage_record
        assert "created_at" in usage_record
