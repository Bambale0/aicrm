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
        request_data = {
            "message": "Хочу заказать футболку с логотипом",
            "context": {
                "customer_id": 1,
                "previous_messages": ["Привет, чем могу помочь?"]
            }
        }

        # Мокаем AI сервис
        mock_response = {
            "intent": "order",
            "confidence": 0.95,
            "response": "Отлично! Я помогу вам оформить заказ на футболку с логотипом. Расскажите подробнее о ваших пожеланиях.",
            "needs_human_intervention": False,
            "suggested_actions": ["create_order", "ask_design_details"]
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
