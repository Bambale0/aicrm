"""
Интеграционные тесты для AI API
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestAIApi:
    """Тесты для AI API"""

    async def test_analyze_intent_success(self, async_client: AsyncClient):
        """Тест успешного анализа намерения"""
        # Сначала регистрируем и логинимся пользователя
        register_data = {
            "email": "test_ai@example.com",
            "password": "testpass123",
            "full_name": "Test AI User"
        }

        register_response = await async_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 200

        login_data = {
            "email": "test_ai@example.com",
            "password": "testpass123"
        }

        login_response = await async_client.post("/auth/login/json", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        request_data = {
            "message": "Хочу заказать футболку с логотипом",
            "context": {
                "customer_id": 1,
                "previous_messages": ["Привет, чем могу помочь?"]
            }
        }

        # Мокаем AI сервис
        with patch("src.aicrm.services.ai.intent_service.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_intent.return_value = "order"
            mock_service.generate_response.return_value = "Отлично! Я помогу вам оформить заказ на футболку с логотипом."
            mock_service._get_suggested_actions.return_value = ["create_order", "ask_design_details"]
            mock_service_class.return_value = mock_service

            with patch("src.aicrm.services.ai_usage_service.AIUsageService") as mock_usage_class:
                mock_usage = MagicMock()
                mock_usage.log_usage = MagicMock()
                mock_usage_class.return_value = mock_usage

                response = await async_client.post("/analyze-intent", json=request_data, headers={"Authorization": f"Bearer {token}"})

                assert response.status_code == 200
                data = response.json()
                assert data["intent"] == "order"
                assert "response" in data
                assert data["needs_human_intervention"] is False
                assert "suggested_actions" in data

    async def test_analyze_intent_ai_error(self, async_client: AsyncClient):
        """Тест ошибки AI при анализе намерения"""
        request_data = {
            "message": "Тестовое сообщение",
            "context": {}
        }

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.process_customer_message.side_effect = Exception("AI service error")
            mock_service_class.return_value = mock_service

            response = await async_client.post("/analyze-intent", json=request_data)

            assert response.status_code == 500
            assert "AI анализ не удался" in response.json()["detail"]

    async def test_generate_response_success(self, async_client: AsyncClient):
        """Тест успешной генерации ответа"""
        request_data = {
            "message": "Сколько стоит доставка?",
            "context": {"customer_id": 1}
        }

        with patch("src.aicrm.api.routers.ai.AIIntentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_intent.return_value = MagicMock(value="question")
            mock_service.generate_response.return_value = "Доставка осуществляется бесплатно при заказе от 3000 рублей."
            mock_service_class.return_value = mock_service

            response = await async_client.post("/generate-response", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "question"
            assert "доставка" in data["response"].lower()

    async def test_generate_response_error(self, async_client: AsyncClient):
        """Тест ошибки при генерации ответа"""
        request_data = {
            "message": "Тест",
            "context": {}
        }

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
            "messages": [
                {"role": "user", "content": "Привет, как дела?"}
            ],
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 100
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
        request_data = {
            "messages": [
                {"role": "user", "content": "Тестовое сообщение"}
            ]
        }

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
        request_data = {
            "messages": [
                {"role": "user", "content": "Тест"}
            ]
        }

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
            "context": "invalid_context"  # Неправильный тип контекста
        }

        response = await async_client.post("/analyze-intent", json=request_data)

        # Должен быть 422 Validation Error
        assert response.status_code == 422

    async def test_chat_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных для чата"""
        # Неправильные данные
        request_data = {
            "messages": [],  # Пустой список сообщений
            "temperature": 2.5  # Температура вне диапазона
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
                "customer_history": ["order_created", "payment_received"]
            }
        }

        mock_response = {
            "intent": "complaint",
            "confidence": 0.88,
            "response": "Извините за неудобства. Давайте разберемся с вашим заказом #123.",
            "needs_human_intervention": True,
            "suggested_actions": ["check_order_status", "contact_support"]
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
        models = ["deepseek/deepseek-coder:33b-instruct", "meta-llama/llama-3-70b-instruct"]

        for model in models:
            request_data = {
                "messages": [{"role": "user", "content": "Привет"}],
                "model": model
            }

            with patch("src.aicrm.api.routers.ai.UnifiedAIClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.chat_completion.return_value = f"Ответ от модели {model}"
                mock_client_class.return_value = mock_client

                response = await async_client.post("/chat", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert data["model_used"] == model

    async def test_ai_usage_logging_integration(self, async_client: AsyncClient, db_session):
        """Интеграционный тест логирования использования AI токенов"""
        from src.aicrm.services.ai_usage_service import AIUsageService

        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        test_user = User(
            email="test_ai_usage@example.com",
            hashed_password="hashed_password",
            full_name="Test AI User"
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
            user_agent="test-agent"
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

    async def test_monthly_usage_statistics_integration(self, async_client: AsyncClient, db_session):
        """Интеграционный тест получения месячной статистики использования"""
        from src.aicrm.services.ai_usage_service import AIUsageService

        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        test_user = User(
            email="test_monthly@example.com",
            hashed_password="hashed_password",
            full_name="Test Monthly User"
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
            user_id=test_user.id
        )

        await usage_service.log_usage(
            model_used="deepseek/deepseek-chat",
            endpoint="analyze-intent",
            total_tokens=50.0,
            user_id=test_user.id
        )

        await usage_service.log_usage(
            model_used="openai/gpt-4",
            endpoint="chat",
            total_tokens=200.0,
            user_id=test_user.id
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

    async def test_usage_history_integration(self, async_client: AsyncClient, db_session):
        """Интеграционный тест получения истории использования"""
        from src.aicrm.services.ai_usage_service import AIUsageService

        # Создаем тестового пользователя
        from src.aicrm.models.user import User
        test_user = User(
            email="test_history@example.com",
            hashed_password="hashed_password",
            full_name="Test History User"
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
            user_id=test_user.id
        )

        usage2 = await usage_service.log_usage(
            model_used="openai/gpt-4",
            endpoint="analyze-intent",
            total_tokens=125.0,
            user_id=test_user.id
        )

        # Получаем историю
        history = usage_service.get_usage_history(days=1, user_id=test_user.id, limit=10)

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

    async def test_ai_usage_api_endpoints_integration(self, async_client: AsyncClient, db_session):
        """Интеграционный тест API эндпоинтов для статистики AI использования"""

        # Создаем тестового пользователя и логируемся
        from src.aicrm.models.user import User
        test_user = User(
            email="test_api_stats@example.com",
            hashed_password="hashed_password",
            full_name="Test API Stats User"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        # Получаем токен для аутентификации
        login_response = await async_client.post("/auth/login/json", json={
            "email": "test_api_stats@example.com",
            "password": "test123"  # Это не сработает, нужно создать пользователя через API
        })

        # Вместо этого создадим пользователя через API
        register_response = await async_client.post("/auth/register", json={
            "email": "test_api_stats2@example.com",
            "password": "test123",
            "full_name": "Test API Stats User 2"
        })

        assert register_response.status_code == 200
        user_data = register_response.json()

        # Логируемся
        login_response = await async_client.post("/auth/login/json", json={
            "email": "test_api_stats2@example.com",
            "password": "test123"
        })

        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]

        # Используем AI чат для генерации использования токенов
        chat_response = await async_client.post("/chat", json={
            "messages": [{"role": "user", "content": "Hello, test message"}],
            "model": "deepseek/deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 50
        }, headers={"Authorization": f"Bearer {token}"})

        assert chat_response.status_code == 200

        # Проверяем месячную статистику через API
        monthly_response = await async_client.get("/usage/monthly", headers={"Authorization": f"Bearer {token}"})

        assert monthly_response.status_code == 200
        monthly_data = monthly_response.json()

        # Проверяем структуру ответа
        assert "total_tokens" in monthly_data
        assert "total_requests" in monthly_data
        assert "model_breakdown" in monthly_data
        assert monthly_data["total_requests"] >= 1
        assert monthly_data["total_tokens"] > 0

        # Проверяем историю использования через API
        history_response = await async_client.get("/usage/history", headers={"Authorization": f"Bearer {token}"})

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


class TestAIRouterUnit:
    """Unit тесты для AI роутера с моками"""

    def test_get_available_models_unit(self):
        """Unit тест получения списка моделей"""
        from src.aicrm.api.routers.ai import get_available_models

        # Мокаем OPENROUTER_MODELS
        with patch("src.aicrm.api.routers.ai.OPENROUTER_MODELS", [
            {"id": "model1", "name": "Model 1", "context_length": 4096}
        ]):
            result = get_available_models()
            assert result.models == [{"id": "model1", "name": "Model 1", "context_length": 4096}]
            assert result.current_provider == "openrouter"

    def test_get_ai_status_unit(self):
        """Unit тест получения статуса AI"""
        from src.aicrm.api.routers.ai import get_ai_status

        mock_client = MagicMock()
        mock_client.provider.value = "openrouter"

        with patch("src.aicrm.api.routers.ai.UnifiedAIClient", return_value=mock_client), \
             patch("src.aicrm.api.routers.ai.ai_config") as mock_config:

            mock_config.DEFAULT_MODEL = "test-model"

            result = get_ai_status(mock_client)
            assert result.provider == "openrouter"
            assert result.status == "active"
            assert result.default_model == "test-model"
            assert len(result.available_models) > 0

    def test_get_monthly_usage_unit(self):
        """Unit тест получения месячной статистики"""
        from src.aicrm.api.routers.ai import get_monthly_usage

        mock_db = MagicMock()
        mock_usage_service = MagicMock()
        mock_usage_service.get_monthly_usage.return_value = {
            "total_tokens": 1000.0,
            "total_requests": 10,
            "unique_models": 2
        }

        with patch("src.aicrm.api.routers.ai.AIUsageService", return_value=mock_usage_service):
            result = get_monthly_usage(year=2024, month=11, user_id=1, db=mock_db)
            assert result.total_tokens == 1000.0
            assert result.total_requests == 10
            assert result.unique_models == 2

    def test_get_usage_history_unit(self):
        """Unit тест получения истории использования"""
        from src.aicrm.api.routers.ai import get_usage_history

        mock_db = MagicMock()
        mock_usage_service = MagicMock()
        mock_usage_service.get_usage_history.return_value = [
            {"model_used": "model1", "total_tokens": 100}
        ]

        with patch("src.aicrm.api.routers.ai.AIUsageService", return_value=mock_usage_service):
            result = get_usage_history(days=30, user_id=1, limit=10, db=mock_db)
            assert len(result.history) == 1
            assert result.history[0]["model_used"] == "model1"

    def test_update_ai_settings_success(self):
        """Unit тест успешного обновления настроек AI"""
        from src.aicrm.api.routers.ai import update_ai_settings

        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_db = MagicMock()

        settings = {
            "default_model": "new-model",
            "temperature": 0.8,
            "max_tokens": 1000
        }

        with patch("src.aicrm.api.routers.ai.logger"):
            result = update_ai_settings(settings, mock_current_user, mock_db)
            assert result["success"] is True
            assert result["updated_settings"] == settings

    def test_update_ai_settings_invalid_temperature(self):
        """Unit тест валидации температуры"""
        from src.aicrm.api.routers.ai import update_ai_settings
        from fastapi import HTTPException

        mock_current_user = MagicMock()
        mock_db = MagicMock()

        settings = {"temperature": 3.0}  # Недопустимое значение

        with pytest.raises(HTTPException) as exc_info:
            update_ai_settings(settings, mock_current_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "Температура должна быть числом от 0.0 до 2.0" in exc_info.value.detail

    def test_update_ai_settings_invalid_max_tokens(self):
        """Unit тест валидации max_tokens"""
        from src.aicrm.api.routers.ai import update_ai_settings
        from fastapi import HTTPException

        mock_current_user = MagicMock()
        mock_db = MagicMock()

        settings = {"max_tokens": 10000}  # Недопустимое значение

        with pytest.raises(HTTPException) as exc_info:
            update_ai_settings(settings, mock_current_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "Максимальное количество токенов должно быть от 1 до 8000" in exc_info.value.detail

    def test_get_ai_service_dependency(self):
        """Тест зависимости get_ai_service"""
        from src.aicrm.api.routers.ai import get_ai_service

        service = get_ai_service()
        assert service is not None
        # Проверяем, что возвращается экземпляр AIIntentService
        from src.aicrm.services.ai.intent_service import AIIntentService
        assert isinstance(service, AIIntentService)

    def test_get_ai_client_dependency(self):
        """Тест зависимости get_ai_client"""
        from src.aicrm.api.routers.ai import get_ai_client

        client = get_ai_client()
        assert client is not None
        # Проверяем, что возвращается экземпляр UnifiedAIClient
        from src.aicrm.services.ai.client import UnifiedAIClient
        assert isinstance(client, UnifiedAIClient)
