"""
Интеграционные тесты для AI Orchestrator API - управление workflow и событиями
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestAIOrchestratorAPI:
    """Тесты для AI Orchestrator API"""

    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt_success(
        self, async_client: AsyncClient, test_user
    ):
        """Тест успешного создания workflow из промпта"""
        request_data = {
            "prompt": "Когда приходит заказ с типом 'Срочный' и суммой больше 50000, отправляй уведомление менеджеру и создавай задачу.",
            "name": "Обработка срочных заказов",
            "is_active": True,
        }

        # Мокаем AI клиент для генерации workflow
        mock_ai_response = """
        {
            "name": "Обработка срочных заказов",
            "description": "Workflow для обработки срочных VIP заказов",
            "trigger": {"event_type": "ON_ORDER_CREATED"},
            "conditions": [
                {"field_path": "order_type", "operator": "eq", "value": "Срочный"},
                {"field_path": "total", "operator": "gt", "value": 50000}
            ],
            "actions": [
                {"name": "Отправить уведомление", "type": "send_notification", "config": {"message": "Получен срочный заказ!"}},
                {"name": "Создать задачу", "type": "create_task", "config": {"title": "Обработать срочный заказ"}}
            ]
        }
        """

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = mock_ai_response
            mock_client_class.return_value = mock_client

            response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=request_data
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Обработка срочных заказов"
            assert data["is_active"] is True
            assert "trigger" in data
            assert "conditions" in data
            assert "actions" in data
            assert len(data["actions"]) == 2

    @pytest.mark.asyncio
    async def test_create_workflow_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных при создании workflow"""
        # Пустой промпт
        request_data = {"prompt": "", "name": "Test"}

        response = await async_client.post(
            "/ai-orchestrator/ai-workflows", json=request_data
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_list_workflows(self, async_client: AsyncClient):
        """Тест получения списка workflow"""
        # Сначала создаем workflow
        create_data = {
            "prompt": "Тестовый workflow для уведомлений",
            "name": "Test Workflow",
            "is_active": True,
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "Test Workflow",
                "description": "Test workflow",
                "trigger": {"event_type": "ON_ORDER_CREATED"},
                "conditions": [],
                "actions": [{"name": "Test", "type": "send_notification", "config": {}}]
            }
            """
            mock_client_class.return_value = mock_client

            # Создаем workflow
            create_response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=create_data
            )
            assert create_response.status_code == 201

            # Получаем список
            list_response = await async_client.get("/ai-orchestrator/ai-workflows")

            assert list_response.status_code == 200
            data = list_response.json()
            assert "workflows" in data
            assert "total" in data
            assert data["total"] >= 1

            # Проверяем структуру workflow
            workflow = data["workflows"][0]
            assert "id" in workflow
            assert "name" in workflow
            assert "is_active" in workflow
            assert "created_at" in workflow

    @pytest.mark.asyncio
    async def test_get_workflow_detail(self, async_client: AsyncClient):
        """Тест получения детальной информации о workflow"""
        # Создаем workflow сначала
        create_data = {
            "prompt": "Workflow для тестирования деталей",
            "name": "Detail Test Workflow",
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "Detail Test Workflow",
                "description": "Test workflow details",
                "trigger": {"event_type": "ON_CUSTOMER_CREATED"},
                "conditions": [{"field_path": "city", "operator": "eq", "value": "Москва"}],
                "actions": [{"name": "Welcome", "type": "send_notification", "config": {"message": "Добро пожаловать!"}}]
            }
            """
            mock_client_class.return_value = mock_client

            create_response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=create_data
            )
            assert create_response.status_code == 201
            workflow_data = create_response.json()
            workflow_id = workflow_data["id"]

            # Получаем детали
            detail_response = await async_client.get(
                f"/ai-orchestrator/ai-workflows/{workflow_id}"
            )

            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            assert detail_data["id"] == workflow_id
            assert detail_data["name"] == "Detail Test Workflow"
            assert detail_data["trigger"]["event_type"] == "ON_CUSTOMER_CREATED"
            assert len(detail_data["conditions"]) == 1
            assert len(detail_data["actions"]) == 1

    @pytest.mark.asyncio
    async def test_test_workflow(self, async_client: AsyncClient):
        """Тест тестирования workflow"""
        # Создаем workflow
        create_data = {"prompt": "Workflow для тестирования", "name": "Test Workflow"}

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "Test Workflow",
                "description": "Test workflow",
                "trigger": {"event_type": "ON_ORDER_CREATED"},
                "conditions": [{"field_path": "total", "operator": "gt", "value": 1000}],
                "actions": [{"name": "Test Action", "type": "send_notification", "config": {"message": "Test"}}]
            }
            """
            mock_client_class.return_value = mock_client

            create_response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=create_data
            )
            workflow_data = create_response.json()
            workflow_id = workflow_data["id"]

            # Тестируем workflow
            test_data = {
                "event_type": "ON_ORDER_CREATED",
                "payload": {"total": 2000, "order_id": 123},
            }

            test_response = await async_client.post(
                f"/ai-orchestrator/ai-workflows/{workflow_id}/test", json=test_data
            )

            assert test_response.status_code == 200
            test_result = test_response.json()
            assert test_result["workflow_id"] == workflow_id
            assert test_result["triggered"] is True
            assert test_result["conditions_met"] is True
            assert len(test_result["actions_executed"]) == 1

    @pytest.mark.asyncio
    async def test_handle_incoming_event(self, async_client: AsyncClient):
        """Тест обработки входящего события"""
        # Создаем активный workflow
        create_data = {
            "prompt": "Workflow для обработки событий заказов",
            "name": "Order Event Handler",
            "is_active": True,
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "Order Event Handler",
                "description": "Handles order events",
                "trigger": {"event_type": "ON_ORDER_CREATED"},
                "conditions": [],
                "actions": [{"name": "Process Order", "type": "send_notification", "config": {"message": "Order processed"}}]
            }
            """
            mock_client_class.return_value = mock_client

            # Создаем workflow
            create_response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=create_data
            )
            assert create_response.status_code == 201

            # Мокаем выполнение действия
            with patch(
                "src.aicrm.services.workflow_service.WorkflowService"
            ) as mock_service_class:
                mock_service = MagicMock()
                mock_execution = MagicMock()
                mock_execution.execution_status = "completed"
                mock_service.execute_workflow.return_value = mock_execution
                mock_service_class.return_value = mock_service

                # Отправляем событие
                event_data = {
                    "event_id": "event_123",
                    "event_type": "ON_ORDER_CREATED",
                    "entity_type": "order",
                    "entity_id": 456,
                    "payload": {"total": 1500, "status": "new"},
                }

                event_response = await async_client.post(
                    "/ai-orchestrator/events", json=event_data
                )

                assert event_response.status_code == 202
                response_data = event_response.json()
                assert "triggered_workflows" in response_data
                assert "message" in response_data

    @pytest.mark.asyncio
    async def test_get_execution_history(self, async_client: AsyncClient):
        """Тест получения истории выполнений"""
        # Создаем workflow и выполняем его
        create_data = {
            "prompt": "Workflow для истории выполнений",
            "name": "Execution History Test",
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "Execution History Test",
                "description": "Test execution history",
                "trigger": {"event_type": "ON_ORDER_CREATED"},
                "conditions": [],
                "actions": [{"name": "Test", "type": "send_notification", "config": {}}]
            }
            """
            mock_client_class.return_value = mock_client

            create_response = await async_client.post(
                "/ai-orchestrator/ai-workflows", json=create_data
            )
            workflow_data = create_response.json()
            workflow_id = workflow_data["id"]

            # Имитируем выполнение
            with patch(
                "src.aicrm.services.workflow_service.WorkflowService"
            ) as mock_service_class:
                mock_service = MagicMock()
                mock_executions = [
                    {
                        "id": 1,
                        "workflow_id": workflow_id,
                        "workflow_name": "Execution History Test",
                        "trigger_event": {"event_type": "ON_ORDER_CREATED"},
                        "execution_status": "completed",
                        "started_at": "2024-01-01T10:00:00Z",
                        "completed_at": "2024-01-01T10:00:05Z",
                        "error_message": None,
                    }
                ]
                mock_service.get_workflow_executions.return_value = mock_executions
                mock_service_class.return_value = mock_service

                # Получаем историю
                history_response = await async_client.get("/ai-orchestrator/executions")

                assert history_response.status_code == 200
                history_data = history_response.json()
                assert "executions" in history_data
                assert "total" in history_data
                assert len(history_data["executions"]) >= 1

    @pytest.mark.asyncio
    async def test_setup_crm_connector(self, async_client: AsyncClient):
        """Тест настройки коннектора к CRM"""
        connector_config = {
            "base_url": "https://api.crm.example.com/v1",
            "api_key": "test-api-key-123",
            "auth_type": "bearer",
        }

        response = await async_client.post(
            "/ai-orchestrator/system/connectors/crm", json=connector_config
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_workflow_with_token_accounting(self, async_client: AsyncClient):
        """Тест workflow с учётом токенов"""
        # Создаем workflow, который использует AI
        create_data = {
            "prompt": "Когда приходит запрос, анализируй его с помощью AI и отправь ответ",
            "name": "AI Analysis Workflow",
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = """
            {
                "name": "AI Analysis Workflow",
                "description": "Workflow with AI analysis",
                "trigger": {"event_type": "ON_CUSTOMER_MESSAGE"},
                "conditions": [],
                "actions": [
                    {"name": "AI Analysis", "type": "call_ai", "config": {"prompt": "Analyze this message: {{message}}"}},
                    {"name": "Send Response", "type": "send_notification", "config": {"message": "AI Response: {{ai_response}}"}}
                ]
            }
            """
            mock_client_class.return_value = mock_client

            # Мокаем сервис токенов
            with patch(
                "src.aicrm.services.token_accounting_service.TokenAccountingService"
            ) as mock_token_class:
                mock_token_service = MagicMock()
                mock_token_service.check_quota_and_record_transaction.return_value = {
                    "success": True,
                    "transaction": {"id": 1},
                    "alert_triggered": False,
                }
                mock_token_class.return_value = mock_token_service

                response = await async_client.post(
                    "/ai-orchestrator/ai-workflows", json=create_data
                )

                assert response.status_code == 201
                # Проверяем, что токены были учтены
                mock_token_service.check_quota_and_record_transaction.assert_called()


class TestTokenAccountingAPI:
    """Тесты для Token Accounting API"""

    @pytest.mark.asyncio
    async def test_set_token_quota(self, async_client: AsyncClient):
        """Тест установки квоты токенов"""
        quota_data = {
            "entity_type": "company",
            "entity_id": 123,
            "quota_type": "monthly",
            "limit_tokens": 100000,
            "alert_threshold": 80,
        }

        response = await async_client.post("/token-quotas", json=quota_data)

        assert response.status_code == 201
        data = response.json()
        assert data["entity_type"] == "company"
        assert data["entity_id"] == 123
        assert data["quota_type"] == "monthly"
        assert data["limit_tokens"] == 100000
        assert data["alert_threshold"] == 80
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_token_usage(self, async_client: AsyncClient):
        """Тест получения текущего баланса токенов"""
        # Сначала создаем квоту
        quota_data = {
            "entity_type": "company",
            "entity_id": 456,
            "quota_type": "monthly",
            "limit_tokens": 50000,
            "alert_threshold": 90,
        }

        await async_client.post("/token-quotas", json=quota_data)

        # Получаем статистику
        response = await async_client.get("/token-quotas/company/456/current")

        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "company"
        assert data["entity_id"] == 456
        assert data["limit_tokens"] == 50000
        assert "used_tokens" in data
        assert "percentage_used" in data
        assert "remaining_tokens" in data

    @pytest.mark.asyncio
    async def test_get_token_alerts(self, async_client: AsyncClient):
        """Тест получения алертов о превышении лимитов"""
        # Создаем квоту с превышением
        quota_data = {
            "entity_type": "company",
            "entity_id": 789,
            "quota_type": "monthly",
            "limit_tokens": 1000,
            "alert_threshold": 50,
        }

        await async_client.post("/token-quotas", json=quota_data)

        # Имитируем использование токенов через транзакцию
        with patch(
            "src.aicrm.services.token_accounting_service.TokenAccountingService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_alerts = [
                {
                    "quota_id": 1,
                    "entity_type": "company",
                    "entity_id": 789,
                    "current_usage": 800,
                    "limit_tokens": 1000,
                    "percentage_used": 80.0,
                    "alert_threshold": 50,
                }
            ]
            mock_service.get_quota_alerts.return_value = mock_alerts
            mock_service_class.return_value = mock_service

            response = await async_client.get("/token-quotas/alerts")

            assert response.status_code == 200
            alerts = response.json()
            assert len(alerts) == 1
            assert alerts[0]["percentage_used"] == 80.0

    @pytest.mark.asyncio
    async def test_get_token_transactions(self, async_client: AsyncClient):
        """Тест получения истории транзакций токенов"""
        response = await async_client.get("/token-quotas/transactions?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    @pytest.mark.asyncio
    async def test_reset_monthly_quotas(self, async_client: AsyncClient):
        """Тест сброса месячных квот"""
        with patch(
            "src.aicrm.services.token_accounting_service.TokenAccountingService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.reset_monthly_quotas.return_value = 5
            mock_service_class.return_value = mock_service

            response = await async_client.post("/token-quotas/reset-monthly")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["reset_count"] == 5

    @pytest.mark.asyncio
    async def test_token_quota_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных квоты токенов"""
        # Неправильные данные
        quota_data = {
            "entity_type": "invalid_type",  # Должен быть 'company' или 'user'
            "entity_id": -1,  # Отрицательный ID
            "quota_type": "invalid_quota",  # Неправильный тип квоты
            "limit_tokens": -100,  # Отрицательный лимит
            "alert_threshold": 150,  # Превышает 99%
        }

        response = await async_client.post("/token-quotas", json=quota_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_quota_not_found(self, async_client: AsyncClient):
        """Тест случая, когда квота не найдена"""
        response = await async_client.get("/token-quotas/company/99999/current")

        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_full_token_workflow_integration(self, async_client: AsyncClient):
        """Интеграционный тест полного workflow с токенами"""
        # 1. Создаем квоту
        quota_data = {
            "entity_type": "company",
            "entity_id": 999,
            "quota_type": "monthly",
            "limit_tokens": 10000,
            "alert_threshold": 80,
        }

        quota_response = await async_client.post("/token-quotas", json=quota_data)
        assert quota_response.status_code == 201

        # 2. Проверяем начальную статистику
        stats_response = await async_client.get("/token-quotas/company/999/current")
        assert stats_response.status_code == 200
        initial_stats = stats_response.json()
        assert initial_stats["used_tokens"] == 0
        assert initial_stats["percentage_used"] == 0.0

        # 3. Создаем workflow, который использует AI
        workflow_data = {
            "prompt": "Создай workflow, который анализирует сообщения клиентов с помощью AI",
            "name": "AI Customer Analysis",
        }

        with patch(
            "src.aicrm.services.workflow_service.UnifiedAIClient"
        ) as mock_ai_class:
            mock_ai = MagicMock()
            mock_ai.chat_completion.return_value = """
            {
                "name": "AI Customer Analysis",
                "description": "Analyzes customer messages with AI",
                "trigger": {"event_type": "ON_CUSTOMER_MESSAGE"},
                "conditions": [],
                "actions": [
                    {"name": "AI Analysis", "type": "call_ai", "config": {"prompt": "Analyze sentiment: {{message}}"}},
                    {"name": "Send Response", "type": "send_notification", "config": {"message": "Analysis complete"}}
                ]
            }
            """
            mock_ai_class.return_value = mock_ai

            # Мокаем учет токенов
            with patch(
                "src.aicrm.services.token_accounting_service.TokenAccountingService"
            ) as mock_token_class:
                mock_token_service = MagicMock()
                mock_token_service.check_quota_and_record_transaction.return_value = {
                    "success": True,
                    "transaction": {"id": 1},
                    "alert_triggered": False,
                }
                mock_token_class.return_value = mock_token_service

                workflow_response = await async_client.post(
                    "/ai-orchestrator/ai-workflows", json=workflow_data
                )
                assert workflow_response.status_code == 201

                # Проверяем, что токены были учтены при создании workflow
                mock_token_service.check_quota_and_record_transaction.assert_called()

        # 4. Проверяем обновленную статистику
        final_stats_response = await async_client.get(
            "/token-quotas/company/999/current"
        )
        assert final_stats_response.status_code == 200
        final_stats = final_stats_response.json()
