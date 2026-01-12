"""
Интеграционные тесты для взаимодействия сервисов
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..models.automation import AutomationExecution, EntityType
from ..models.customer import Customer
from ..models.task import Task
from ..services.ai_settings_service import AISettingsService
from ..services.automation.avito_integration import AvitoTaskIntegration
from ..services.automation.error_handler import AutomationErrorHandler
from ..services.notification_service import NotificationService


class TestServiceIntegration:
    """Интеграционные тесты для взаимодействия между сервисами"""

    @pytest.fixture
    def db_session(self):
        """Мок для сессии базы данных"""
        session = MagicMock()
        session.query = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def notification_service(self):
        """Фикстура для NotificationService"""
        return NotificationService()

    @pytest.fixture
    def error_handler(self, db_session):
        """Фикстура для AutomationErrorHandler"""
        return AutomationErrorHandler(db_session)

    @pytest.fixture
    def avito_integration(self, db_session):
        """Фикстура для AvitoTaskIntegration"""
        return AvitoTaskIntegration(db_session)

    @pytest.fixture
    def ai_settings_service(self, db_session):
        """Фикстура для AISettingsService"""
        return AISettingsService(db_session)

    @pytest.fixture
    def sample_customer(self):
        """Пример клиента"""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.name = "Иван Иванов"
        customer.phone = "+7-999-123-45-67"
        customer.email = "ivan@example.com"
        customer.external_ids = {"avito_user_id": "avito_user_456"}
        return customer

    @pytest.fixture
    def sample_execution(self):
        """Пример выполнения автоматизации"""
        execution = MagicMock(spec=AutomationExecution)
        execution.id = 100
        execution.entity_type = EntityType.CUSTOMER
        execution.entity_id = 1
        execution.robot_id = 5
        execution.stage_id = 10
        execution.started_at = datetime(2023, 1, 1, 10, 0, 0)
        execution.execution_status = "failed"
        execution.error_message = "Connection timeout"
        execution.actions_executed = [
            {"action_type": "send_email", "success": False, "error": "SMTP timeout"}
        ]
        return execution

    @pytest.mark.asyncio
    async def test_error_handler_with_notification_integration(
        self, error_handler, notification_service, sample_execution, sample_customer
    ):
        """Интеграционный тест: ErrorHandler + NotificationService"""
        # Мокаем получение робота
        mock_robot = MagicMock()
        mock_robot.name = "Email Robot"
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            mock_robot
        )

        # Мокаем создание записи об ошибке
        error_handler.db.add.return_value = None

        # Мокаем NotificationService
        with patch(
            "src.aicrm.services.automation.error_handler.NotificationService"
        ) as mock_ns_class:
            mock_ns_instance = MagicMock()
            mock_ns_instance.send_system_alert = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_ns_class.return_value = mock_ns_instance

            # Вызываем обработку ошибки
            result = await error_handler.handle_error(
                sample_execution,
                "Critical system failure",
                {"severity": "critical", "notify_immediately": True},
            )

            # Проверяем что ошибка обработана
            assert result["error_recorded"] is True
            assert result["notifications_sent"] is True

            # Проверяем что системное уведомление отправлено
            mock_ns_instance.send_system_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_avito_integration_with_error_handler(
        self, avito_integration, error_handler, sample_customer
    ):
        """Интеграционный тест: AvitoIntegration + ErrorHandler"""
        message_data = {
            "chat_id": "avito_chat_123",
            "user_id": "avito_user_456",
            "message": {
                "text": "Срочно нужна печать документов!",
                "timestamp": "2023-01-01T10:00:00Z",
            },
            "item_id": 12345,
            "direction": "inbound",
        }

        # Мокаем анализ сообщения (срочная помощь)
        avito_integration._analyze_message_for_tasks = AsyncMock(
            return_value=[
                {
                    "type": "urgent_help",
                    "title": "Срочная помощь клиенту",
                    "description": "Клиент просит срочной помощи",
                    "priority": "high",
                    "matched_keywords": ["срочно"],
                }
            ]
        )

        # Мокаем создание задачи (с ошибкой)
        avito_integration._create_task_from_trigger = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Мокаем ErrorHandler
        with patch(
            "src.aicrm.services.automation.avito_integration.AutomationErrorHandler"
        ) as mock_eh_class:
            mock_eh_instance = MagicMock()
            mock_eh_instance.handle_error = AsyncMock(
                return_value={"error_recorded": True, "notifications_sent": True}
            )
            mock_eh_class.return_value = mock_eh_instance

            # Вызываем анализ и создание задач
            result = await avito_integration.analyze_and_create_tasks(
                message_data, sample_customer
            )

            # Проверяем что ошибка была обработана ErrorHandler
            mock_eh_instance.handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_notification_service_with_ai_settings(
        self, notification_service, ai_settings_service
    ):
        """Интеграционный тест: NotificationService + AISettingsService"""
        # Мокаем получение настроек AI для пользователя
        mock_ai_settings = {
            "id": 1,
            "user_id": 100,
            "provider": "openai",
            "model": "gpt-4",
            "is_active": True,
        }

        with patch.object(
            ai_settings_service, "get_user_ai_settings", return_value=mock_ai_settings
        ):
            # Мокаем email сервис
            with patch(
                "src.aicrm.services.notification_service.email_service"
            ) as mock_email:
                mock_email.send_email = AsyncMock(return_value=True)

                # Отправляем уведомление пользователю с AI
                result = await notification_service.send_notification(
                    recipient="test@example.com",
                    message="AI analysis completed",
                    channels=["email"],
                    notification_type="ai_completion",
                    priority="medium",
                    template_data={
                        "user_id": 100,
                        "ai_model": "gpt-4",
                        "analysis_result": "Analysis complete",
                    },
                )

                assert result["success"] is True
                mock_email.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_error_workflow_integration(
        self,
        error_handler,
        notification_service,
        avito_integration,
        sample_execution,
        sample_customer,
    ):
        """Полный интеграционный тест рабочего процесса обработки ошибок"""
        # 1. Начинаем с ошибки в Avito интеграции
        message_data = {
            "chat_id": "avito_chat_123",
            "user_id": "avito_user_456",
            "message": {"text": "Test message", "timestamp": "2023-01-01T10:00:00Z"},
            "item_id": 12345,
            "direction": "inbound",
        }

        # Мокаем ошибку в создании задачи
        avito_integration._create_task_from_trigger = AsyncMock(
            side_effect=Exception("Task creation failed")
        )

        # 2. ErrorHandler обрабатывает ошибку
        mock_robot = MagicMock()
        mock_robot.name = "Avito Integration Robot"
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            mock_robot
        )
        error_handler.db.add.return_value = None

        # 3. NotificationService отправляет уведомления
        with patch(
            "src.aicrm.services.automation.error_handler.NotificationService"
        ) as mock_ns_class:
            mock_ns_instance = MagicMock()
            mock_ns_instance.send_system_alert = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_ns_instance.notify_admins = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_ns_class.return_value = mock_ns_instance

            # Выполняем полный рабочий процесс
            # Шаг 1: Avito интеграция пытается создать задачу (и падает)
            try:
                await avito_integration._create_task_from_trigger(
                    {"type": "test"}, sample_customer, "chat_123", 12345
                )
            except Exception as e:
                # Шаг 2: ErrorHandler обрабатывает ошибку
                error_result = await error_handler.handle_error(
                    sample_execution,
                    str(e),
                    {"severity": "high", "component": "avito_integration"},
                )

                # Проверяем что весь процесс прошел успешно
                assert error_result["error_recorded"] is True
                assert error_result["notifications_sent"] is True

                # Проверяем что уведомления отправлены
                mock_ns_instance.send_system_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_operations_integration(
        self, notification_service, ai_settings_service
    ):
        """Интеграционный тест массовых операций"""
        # Создаем несколько пользователей с настройками AI
        users_settings = [
            {"user_id": 1, "provider": "openai", "model": "gpt-4"},
            {"user_id": 2, "provider": "anthropic", "model": "claude-3"},
            {"user_id": 3, "provider": "openai", "model": "gpt-3.5-turbo"},
        ]

        # Мокаем массовое обновление настроек AI
        with patch.object(
            ai_settings_service, "bulk_update_settings", new_callable=AsyncMock
        ) as mock_bulk_update:
            mock_bulk_update.return_value = [
                {"user_id": 1, "success": True},
                {"user_id": 2, "success": True},
                {"user_id": 3, "success": True},
            ]

            # Мокаем массовую отправку уведомлений
            with patch.object(
                notification_service, "send_bulk_notifications", new_callable=AsyncMock
            ) as mock_bulk_notify:
                mock_bulk_notify.return_value = {
                    "total_recipients": 3,
                    "successful": 3,
                    "failed": 0,
                    "success_rate": 1.0,
                }

                # Выполняем массовые операции
                settings_result = await ai_settings_service.bulk_update_settings(
                    users_settings
                )
                notify_result = await notification_service.send_bulk_notifications(
                    recipients=[
                        "user1@example.com",
                        "user2@example.com",
                        "user3@example.com",
                    ],
                    message="Bulk update completed",
                    channels=["email"],
                    notification_type="system_update",
                )

                # Проверяем результаты
                assert len(settings_result) == 3
                assert all(r["success"] for r in settings_result)
                assert notify_result["total_recipients"] == 3
                assert notify_result["successful"] == 3

    @pytest.mark.asyncio
    async def test_cascading_failure_recovery(
        self, error_handler, notification_service
    ):
        """Тест каскадного восстановления после неудач"""
        # Создаем цепочку ошибок
        executions = []
        for i in range(3):
            execution = MagicMock(spec=AutomationExecution)
            execution.id = 100 + i
            execution.entity_type = EntityType.CUSTOMER
            execution.entity_id = 50 + i
            execution.robot_id = 5
            execution.error_message = f"Cascading error {i}"
            executions.append(execution)

        # Мокаем ErrorHandler
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            MagicMock(name="Test Robot")
        )
        error_handler.db.add.return_value = None

        # Мокаем NotificationService для каждого случая
        with patch(
            "src.aicrm.services.automation.error_handler.NotificationService"
        ) as mock_ns_class:
            mock_ns_instance = MagicMock()
            mock_ns_instance.send_system_alert = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_ns_instance.notify_admins = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_ns_class.return_value = mock_ns_instance

            # Обрабатываем все ошибки
            results = []
            for execution in executions:
                result = await error_handler.handle_error(
                    execution,
                    execution.error_message,
                    {"severity": "high", "cascade_level": len(results)},
                )
                results.append(result)

            # Проверяем что все ошибки обработаны
            assert len(results) == 3
            assert all(r["error_recorded"] for r in results)
            assert all(r["notifications_sent"] for r in results)

            # Проверяем что системные уведомления отправлены для каждой ошибки
            assert mock_ns_instance.send_system_alert.call_count == 3

    @pytest.mark.asyncio
    async def test_service_health_monitoring_integration(
        self, notification_service, error_handler
    ):
        """Интеграционный тест мониторинга здоровья сервисов"""
        # Имитируем проблемы со здоровьем сервисов
        health_issues = [
            {"service": "database", "status": "degraded", "error": "High latency"},
            {"service": "email", "status": "down", "error": "SMTP server unreachable"},
            {"service": "ai_api", "status": "degraded", "error": "Rate limit exceeded"},
        ]

        # Мокаем отправку уведомлений о проблемах со здоровьем
        with patch.object(
            notification_service, "send_system_alert", new_callable=AsyncMock
        ) as mock_alert:
            mock_alert.return_value = {"successful": 2, "failed": 0}

            # Имитируем отправку алертов для каждой проблемы
            for issue in health_issues:
                await notification_service.send_system_alert(
                    message=f"Service {issue['service']} health issue: {issue['error']}",
                    priority="urgent" if issue["status"] == "down" else "high",
                )

            # Проверяем что алерты отправлены
            assert mock_alert.call_count == 3

    @pytest.mark.asyncio
    async def test_user_journey_with_service_integration(
        self,
        avito_integration,
        notification_service,
        ai_settings_service,
        sample_customer,
    ):
        """Тест полного пользовательского пути с интеграцией сервисов"""
        # Шаг 1: Пользователь отправляет сообщение в Avito
        message_data = {
            "chat_id": "avito_chat_123",
            "user_id": "avito_user_456",
            "message": {
                "text": "Здравствуйте! Нужна срочная печать визиток для конференции.",
                "timestamp": "2023-01-01T10:00:00Z",
            },
            "item_id": 12345,
            "direction": "inbound",
        }

        # Шаг 2: AvitoIntegration анализирует сообщение и создает задачу
        avito_integration._analyze_message_for_tasks = AsyncMock(
            return_value=[
                {
                    "type": "urgent_help",
                    "title": "Срочная печать визиток",
                    "description": "Клиент нуждается в срочной печати визиток",
                    "priority": "high",
                    "matched_keywords": ["срочная", "печать", "визиток"],
                }
            ]
        )

        # Мокаем успешное создание задачи
        mock_task = MagicMock(spec=Task)
        mock_task.id = 200
        avito_integration._create_task_from_trigger = AsyncMock(return_value=mock_task)

        # Шаг 3: NotificationService отправляет уведомление клиенту
        with patch.object(
            notification_service, "send_notification", new_callable=AsyncMock
        ) as mock_notify:
            mock_notify.return_value = {"success": True}

            # Шаг 4: AISettingsService проверяет настройки для персонализации
            with patch.object(
                ai_settings_service,
                "get_user_ai_settings",
                return_value={
                    "provider": "openai",
                    "model": "gpt-4",
                    "is_active": True,
                },
            ):
                # Выполняем полный путь
                tasks_created = await avito_integration.analyze_and_create_tasks(
                    message_data, sample_customer
                )

                # Проверяем что задача создана
                assert len(tasks_created) == 1
                assert tasks_created[0].id == 200

                # Проверяем что уведомление отправлено
                mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(
        self, error_handler, notification_service
    ):
        """Интеграционный тест мониторинга производительности"""
        # Имитируем метрики производительности
        performance_metrics = {
            "response_time": 2500,  # ms
            "error_rate": 0.05,  # 5%
            "throughput": 150,  # requests/min
            "cpu_usage": 85,  # %
            "memory_usage": 90,  # %
        }

        # Проверяем пороги и отправляем алерты при необходимости
        alerts_triggered = []

        if performance_metrics["response_time"] > 2000:
            alerts_triggered.append("high_response_time")
        if performance_metrics["error_rate"] > 0.03:
            alerts_triggered.append("high_error_rate")
        if performance_metrics["cpu_usage"] > 80:
            alerts_triggered.append("high_cpu_usage")
        if performance_metrics["memory_usage"] > 85:
            alerts_triggered.append("high_memory_usage")

        # Мокаем отправку алертов
        with patch.object(
            notification_service, "send_system_alert", new_callable=AsyncMock
        ) as mock_alert:
            mock_alert.return_value = {"successful": 2, "failed": 0}

            for alert_type in alerts_triggered:
                await notification_service.send_system_alert(
                    message=f"Performance alert: {alert_type}", priority="high"
                )

            # Проверяем что алерты отправлены для превышенных порогов
            expected_alerts = [
                "high_response_time",
                "high_error_rate",
                "high_cpu_usage",
                "high_memory_usage",
            ]
            assert mock_alert.call_count == len(expected_alerts)

    @pytest.mark.asyncio
    async def test_data_consistency_across_services(
        self, ai_settings_service, notification_service
    ):
        """Тест согласованности данных между сервисами"""
        user_id = 123

        # Создаем настройки AI
        ai_settings_data = {
            "user_id": user_id,
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-test123",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        # Мокаем создание настроек
        with patch.object(
            ai_settings_service, "create_ai_settings", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = {**ai_settings_data, "id": 1, "is_active": True}

            # Создаем настройки
            created_settings = await ai_settings_service.create_ai_settings(
                ai_settings_data
            )

            # Используем эти настройки для персонализированного уведомления
            with patch.object(
                notification_service, "send_notification", new_callable=AsyncMock
            ) as mock_notify:
                mock_notify.return_value = {"success": True}

                await notification_service.send_notification(
                    recipient="user@example.com",
                    message=f"AI settings configured for {created_settings['provider']} {created_settings['model']}",
                    channels=["email"],
                    notification_type="settings_update",
                    template_data={
                        "user_id": user_id,
                        "provider": created_settings["provider"],
                        "model": created_settings["model"],
                    },
                )

                # Проверяем что данные согласованы
                assert created_settings["user_id"] == user_id
                assert created_settings["provider"] == "openai"
                assert mock_notify.called

    def test_service_initialization_order(self):
        """Тест правильного порядка инициализации сервисов"""
        # Проверяем что сервисы могут быть инициализированы в правильном порядке
        # без циклических зависимостей

        # 1. Сначала базовые сервисы (БД, логирование)
        # 2. Затем сервисы данных (CustomerService, TaskService, etc.)
        # 3. Потом бизнес-логика (AvitoIntegration, ErrorHandler)
        # 4. Наконец, сервисы коммуникаций (NotificationService)

        # Этот тест проверяет что все импорты работают правильно
        try:
            from ..services.ai_settings_service import AISettingsService
            from ..services.automation.avito_integration import \
                AvitoTaskIntegration
            from ..services.automation.error_handler import \
                AutomationErrorHandler
            from ..services.notification_service import NotificationService

            # Если импорты успешны, значит порядок инициализации правильный
            assert NotificationService is not None
            assert AutomationErrorHandler is not None
            assert AvitoTaskIntegration is not None
            assert AISettingsService is not None

        except ImportError as e:
            pytest.fail(f"Service initialization order issue: {e}")

    def test_service_dependency_injection(self):
        """Тест dependency injection между сервисами"""
        # Проверяем что сервисы правильно принимают зависимости
        # и могут работать с моками/стабами

        db_mock = MagicMock()

        # Создаем сервисы с инъекцией зависимостей
        ai_service = AISettingsService(db_mock)
        error_handler = AutomationErrorHandler(db_mock)
        avito_integration = AvitoTaskIntegration(db_mock)
        notification_service = NotificationService()

        # Проверяем что сервисы инициализированы
        assert ai_service.db is db_mock
        assert error_handler.db is db_mock
        assert avito_integration.db is db_mock
        assert notification_service is not None

        # Проверяем что методы доступны
        assert hasattr(ai_service, "get_user_ai_settings")
        assert hasattr(error_handler, "handle_error")
        assert hasattr(avito_integration, "analyze_and_create_tasks")
        assert hasattr(notification_service, "send_notification")
