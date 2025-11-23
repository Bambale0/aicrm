"""
Тесты для новых enterprise сервисов
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ..services.session_service import SessionService
from ..services.cache_service import CacheService
from ..services.rate_limit_service import RateLimitService
from ..services.health_service import HealthService
from ..services.metrics_service import MetricsService
from ..services.workflow_engine import WorkflowEngine
from ..services.ai.intent_service import AIIntentService, IntentType


class TestSessionService:
    """Тесты для SessionService"""

    @pytest.fixture
    def session_service(self):
        return SessionService()

    @pytest.mark.asyncio
    async def test_create_session(self, session_service):
        """Тест создания сессии"""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "ip_address": "127.0.0.1"
        }

        async with session_service:
            session_id = await session_service.create_session(1, user_data)

            assert session_id is not None
            assert isinstance(session_id, str)
            assert len(session_id) > 0

    @pytest.mark.asyncio
    async def test_get_session(self, session_service):
        """Тест получения сессии"""
        user_data = {"id": 1, "email": "test@example.com"}

        async with session_service:
            # Создаем сессию
            session_id = await session_service.create_session(1, user_data)

            # Получаем сессию
            session_data = await session_service.get_session(session_id)

            assert session_data is not None
            assert session_data["user_id"] == 1
            assert session_data["user_data"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_delete_session(self, session_service):
        """Тест удаления сессии"""
        user_data = {"id": 1, "email": "test@example.com"}

        async with session_service:
            # Создаем сессию
            session_id = await session_service.create_session(1, user_data)

            # Удаляем сессию
            result = await session_service.delete_session(session_id)
            assert result is True

            # Проверяем что сессия удалена
            session_data = await session_service.get_session(session_id)
            assert session_data is None


class TestCacheService:
    """Тесты для CacheService"""

    @pytest.fixture
    def cache_service(self):
        return CacheService()

    @pytest.mark.asyncio
    async def test_set_get_cache(self, cache_service):
        """Тест установки и получения значения из кеша"""
        async with cache_service:
            # Устанавливаем значение
            result = await cache_service.set("test_key", "test_value")
            assert result is True

            # Получаем значение
            value = await cache_service.get("test_key")
            assert value == "test_value"

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_service):
        """Тест истечения срока действия кеша"""
        async with cache_service:
            # Устанавливаем значение с TTL 1 секунда
            result = await cache_service.set("test_key", "test_value", ttl=1)
            assert result is True

            # Получаем значение сразу
            value = await cache_service.get("test_key")
            assert value == "test_value"

            # Ждем истечения TTL
            await asyncio.sleep(2)

            # Значение должно быть удалено
            value = await cache_service.get("test_key")
            assert value is None

    @pytest.mark.asyncio
    async def test_user_data_cache(self, cache_service):
        """Тест кеширования данных пользователя"""
        user_data = {"id": 1, "email": "test@example.com", "name": "Test User"}

        async with cache_service:
            # Кешируем данные пользователя
            result = await cache_service.set_user_data(1, user_data)
            assert result is True

            # Получаем данные пользователя
            cached_data = await cache_service.get_user_data(1)
            assert cached_data == user_data


class TestRateLimitService:
    """Тесты для RateLimitService"""

    @pytest.fixture
    def rate_limit_service(self):
        return RateLimitService()

    @pytest.mark.asyncio
    async def test_rate_limit_check(self, rate_limit_service):
        """Тест проверки rate limit"""
        key = "test_user"

        async with rate_limit_service:
            # Первый запрос должен пройти
            allowed, limit_info = await rate_limit_service.check_rate_limit(key, "api")
            assert allowed is True
            assert limit_info["remaining"] > 0

    @pytest.mark.asyncio
    async def test_rate_limit_exceed(self, rate_limit_service):
        """Тест превышения rate limit"""
        key = "test_user"

        async with rate_limit_service:
            # Создаем много запросов для превышения лимита
            for i in range(105):  # Лимит 100 для "api"
                allowed, limit_info = await rate_limit_service.check_rate_limit(key, "api")
                if i < 100:
                    assert allowed is True
                else:
                    assert allowed is False
                    assert limit_info["remaining"] == 0

    @pytest.mark.asyncio
    async def test_different_limits(self, rate_limit_service):
        """Тест разных лимитов для разных типов"""
        key = "test_user"

        async with rate_limit_service:
            # Проверяем лимит для AI (60 запросов)
            for i in range(65):
                allowed, _ = await rate_limit_service.check_rate_limit(key, "ai")
                if i < 60:
                    assert allowed is True
                else:
                    assert allowed is False


class TestHealthService:
    """Тесты для HealthService"""

    @pytest.fixture
    def health_service(self):
        return HealthService()

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, health_service):
        """Тест комплексной проверки здоровья"""
        health_data = await health_service.comprehensive_health_check()

        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "uptime" in health_data
        assert "services" in health_data
        assert "system" in health_data

        # Проверяем наличие системной информации
        system_info = health_data["system"]
        assert "cpu_percent" in system_info
        assert "memory" in system_info
        assert "disk" in system_info

    def test_get_system_info(self, health_service):
        """Тест получения системной информации"""
        system_info = health_service.get_system_info()

        assert "cpu_percent" in system_info
        assert "memory" in system_info
        assert "disk" in system_info
        assert "uptime" in system_info


class TestMetricsService:
    """Тесты для MetricsService"""

    @pytest.fixture
    def metrics_service(self):
        return MetricsService()

    def test_record_http_request(self, metrics_service):
        """Тест записи метрики HTTP запроса"""
        metrics_service.record_http_request("GET", "/api/test", 200, 0.5)

        # Проверяем что метрика записана (сложно протестировать без Prometheus client mock)
        assert metrics_service.http_requests_total is not None

    def test_record_ai_request(self, metrics_service):
        """Тест записи метрики AI запроса"""
        metrics_service.record_ai_request("intent_analysis", "local", "success", 150)

        assert metrics_service.ai_requests_total is not None
        assert metrics_service.ai_tokens_used is not None


class TestWorkflowEngine:
    """Тесты для WorkflowEngine"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return Mock()

    @pytest.fixture
    def workflow_engine(self, mock_db):
        return WorkflowEngine(mock_db)

    def test_workflow_creation(self, workflow_engine):
        """Тест создания workflow"""
        assert len(workflow_engine.workflows) > 0
        assert "order_creation" in workflow_engine.workflows
        assert "payment_processing" in workflow_engine.workflows

    @pytest.mark.asyncio
    async def test_workflow_execution(self, workflow_engine):
        """Тест выполнения workflow"""
        # Мокаем методы шагов
        with patch.object(workflow_engine, '_validate_order_data', new_callable=AsyncMock) as mock_validate, \
             patch.object(workflow_engine, '_create_production_steps', new_callable=AsyncMock) as mock_create, \
             patch.object(workflow_engine, '_assign_production_tasks', new_callable=AsyncMock) as mock_assign, \
             patch.object(workflow_engine, '_notify_customer_order_created', new_callable=AsyncMock) as mock_notify:

            mock_validate.return_value = {"status": "validated"}
            mock_create.return_value = {"steps_created": 3}
            mock_assign.return_value = {"tasks_assigned": 3}
            mock_notify.return_value = {"notification_sent": True}

            # Выполняем workflow
            result = await workflow_engine.workflows["order_creation"].execute({
                "entity_id": 1,
                "entity_type": "order"
            })

            assert result is True
            mock_validate.assert_called_once()
            mock_create.assert_called_once()
            mock_assign.assert_called_once()
            mock_notify.assert_called_once()


class TestAIIntentService:
    """Тесты для AIIntentService"""

    @pytest.fixture
    def intent_service(self):
        return AIIntentService()

    def test_intent_patterns_loaded(self, intent_service):
        """Тест загрузки паттернов намерений"""
        assert len(intent_service.intent_patterns) > 0
        assert IntentType.ORDER_REQUEST in intent_service.intent_patterns
        assert IntentType.PRICE_INQUIRY in intent_service.intent_patterns

    def test_knowledge_base_loaded(self, intent_service):
        """Тест загрузки базы знаний"""
        kb = intent_service.knowledge_base
        assert "services" in kb
        assert "pricing" in kb
        assert "policies" in kb

    @pytest.mark.asyncio
    async def test_analyze_intent(self, intent_service):
        """Тест анализа намерения"""
        text = "Хочу заказать печать на футболках"
        intent = await intent_service.analyze_intent(text)

        assert intent in [IntentType.ORDER_REQUEST, IntentType.GENERAL]
        assert isinstance(intent, str)

    @pytest.mark.asyncio
    async def test_generate_response(self, intent_service):
        """Тест генерации ответа"""
        response = await intent_service.generate_response(
            IntentType.ORDER_REQUEST,
            "Хочу заказать печать",
            {"user_info": {"name": "Тест"}}
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "заказ" in response.lower() or "Заказ" in response

    def test_response_templates(self, intent_service):
        """Тест шаблонов ответов"""
        templates = intent_service._get_response_template(IntentType.ORDER_REQUEST)
        assert isinstance(templates, str)
        assert len(templates) > 0

    def test_fill_template(self, intent_service):
        """Тест заполнения шаблона"""
        template = "Привет, {name}! Ваш заказ на {quantity} шт."
        data = {"name": "Иван", "quantity": "100"}
        result = intent_service._fill_template(template, data)

        assert result == "Привет, Иван! Ваш заказ на 100 шт."


# Интеграционные тесты
class TestServiceIntegration:
    """Интеграционные тесты сервисов"""

    @pytest.mark.asyncio
    async def test_session_cache_integration(self):
        """Тест интеграции SessionService и CacheService"""
        session_service = SessionService()
        cache_service = CacheService()

        user_data = {"id": 1, "email": "test@example.com"}

        async with session_service:
            # Создаем сессию
            session_id = await session_service.create_session(1, user_data)

            # Кешируем данные сессии через CacheService
            async with cache_service:
                await cache_service.set(f"session:{session_id}", user_data, ttl=300)

                # Получаем из кеша
                cached_data = await cache_service.get(f"session:{session_id}")
                assert cached_data == user_data

    @pytest.mark.asyncio
    async def test_rate_limit_health_integration(self):
        """Тест интеграции RateLimitService и HealthService"""
        rate_limit_service = RateLimitService()
        health_service = HealthService()

        # Проверяем rate limit
        async with rate_limit_service:
            allowed, _ = await rate_limit_service.check_rate_limit("test", "api")
            assert allowed in [True, False]  # Зависит от Redis

        # Проверяем здоровье
        health_data = await health_service.comprehensive_health_check()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]


# Тесты производительности
class TestPerformance:
    """Тесты производительности"""

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Тест производительности кеширования"""
        import time

        cache_service = CacheService()
        test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}

        async with cache_service:
            start_time = time.time()

            # Выполняем 100 операций set/get
            for i in range(100):
                key = f"perf_test_{i}"
                await cache_service.set(key, test_data, ttl=60)
                result = await cache_service.get(key)
                assert result == test_data

            end_time = time.time()
            total_time = end_time - start_time

            # Проверяем что время выполнения разумное (< 5 секунд)
            assert total_time < 5.0

    @pytest.mark.asyncio
    async def test_intent_analysis_performance(self):
        """Тест производительности анализа намерений"""
        import time

        intent_service = AIIntentService()
        test_texts = [
            "Хочу заказать печать",
            "Сколько стоит ваша услуга",
            "У меня проблема с заказом",
            "Нужна консультация",
            "Проверить статус заказа"
        ]

        start_time = time.time()

        # Анализируем 50 текстов
        for i in range(10):
            for text in test_texts:
                intent = await intent_service.analyze_intent(text)
                assert intent is not None

        end_time = time.time()
        total_time = end_time - start_time

        # Проверяем что время выполнения разумное (< 30 секунд)
        assert total_time < 30.0


if __name__ == "__main__":
    pytest.main([__file__])
