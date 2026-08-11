"""
Тесты для AutomationErrorHandler с интеграцией NotificationService
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..models.automation import AutomationError, AutomationExecution, EntityType
from ..services.automation.error_handler import AutomationErrorHandler
from ..services.notification_service import NotificationChannel, NotificationPriority


class TestAutomationErrorHandlerWithNotifications:
    """Тесты для обработчика ошибок автоматизации с уведомлениями"""

    @pytest.fixture
    def db_session(self):
        """Мок для сессии базы данных"""
        session = MagicMock()
        session.query = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        return session

    @pytest.fixture
    def error_handler(self, db_session):
        """Фикстура для AutomationErrorHandler"""
        return AutomationErrorHandler(db_session)

    @pytest.fixture
    def mock_notification_service(self):
        """Мок для NotificationService"""
        with patch(
            "src.aicrm.services.automation.error_handler.NotificationService"
        ) as mock:
            mock_instance = MagicMock()
            mock_instance.send_notification = AsyncMock(return_value={"success": True})
            mock_instance.send_system_alert = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock_instance.notify_admins = AsyncMock(
                return_value={"successful": 2, "failed": 0}
            )
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def sample_execution(self):
        """Пример выполнения автоматизации"""
        execution = MagicMock(spec=AutomationExecution)
        execution.id = 100
        execution.entity_type = EntityType.CUSTOMER
        execution.entity_id = 50
        execution.robot_id = 5
        execution.stage_id = 10
        execution.started_at = datetime(2023, 1, 1, 10, 0, 0)
        execution.execution_status = "failed"
        execution.error_message = "Connection timeout"
        execution.actions_executed = [
            {"action_type": "send_email", "success": False, "error": "SMTP timeout"}
        ]
        return execution

    @pytest.fixture
    def sample_robot(self):
        """Пример робота"""
        robot = MagicMock()
        robot.id = 5
        robot.name = "Email Robot"
        robot.entity_type = EntityType.CUSTOMER
        return robot

    @pytest.mark.asyncio
    async def test_handle_error_critical_notification(
        self, error_handler, sample_execution, sample_robot, mock_notification_service
    ):
        """Тест обработки критической ошибки с уведомлением"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Мокаем создание записи об ошибке
        mock_error = MagicMock(spec=AutomationError)
        mock_error.id = 200
        error_handler.db.add.return_value = None
        error_handler.db.refresh = MagicMock()

        result = await error_handler.handle_error(
            sample_execution,
            "Critical system failure",
            {"severity": "critical", "notify_immediately": True},
        )

        assert result["error_recorded"] is True
        assert result["notifications_sent"] is True

        # Проверяем что отправлено системное уведомление
        mock_notification_service.send_system_alert.assert_called_once()
        call_args = mock_notification_service.send_system_alert.call_args
        assert call_args[1]["priority"] == NotificationPriority.URGENT

    @pytest.mark.asyncio
    async def test_handle_error_with_retry_logic(
        self, error_handler, sample_execution, sample_robot, mock_notification_service
    ):
        """Тест обработки ошибки с логикой повторных попыток"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Мокаем создание записи об ошибке
        mock_error = MagicMock(spec=AutomationError)
        mock_error.id = 201
        error_handler.db.add.return_value = None

        # Мокаем проверку возможности повторной попытки
        error_handler._can_retry = AsyncMock(return_value=True)
        error_handler._schedule_retry = AsyncMock(return_value=True)

        result = await error_handler.handle_error(
            sample_execution,
            "Temporary network error",
            {"retryable": True, "max_retries": 3},
        )

        assert result["error_recorded"] is True
        assert result["retry_scheduled"] is True
        assert result["notifications_sent"] is True

        # Проверяем что уведомление отправлено
        mock_notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_non_retryable(
        self, error_handler, sample_execution, sample_robot, mock_notification_service
    ):
        """Тест обработки неисправимой ошибки"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Мокаем создание записи об ошибке
        mock_error = MagicMock(spec=AutomationError)
        mock_error.id = 202
        error_handler.db.add.return_value = None

        # Мокаем проверку возможности повторной попытки
        error_handler._can_retry = AsyncMock(return_value=False)

        result = await error_handler.handle_error(
            sample_execution,
            "Authentication failed: invalid credentials",
            {"retryable": False},
        )

        assert result["error_recorded"] is True
        assert result["retry_scheduled"] is False
        assert result["notifications_sent"] is True

        # Проверяем что отправлено уведомление администраторам
        mock_notification_service.notify_admins.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_with_custom_notification_channels(
        self, error_handler, sample_execution, sample_robot, mock_notification_service
    ):
        """Тест обработки ошибки с кастомными каналами уведомлений"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Мокаем создание записи об ошибке
        mock_error = MagicMock(spec=AutomationError)
        mock_error.id = 203
        error_handler.db.add.return_value = None

        result = await error_handler.handle_error(
            sample_execution,
            "Database connection error",
            {
                "notification_channels": [
                    NotificationChannel.EMAIL,
                    NotificationChannel.SMS,
                ],
                "notification_priority": NotificationPriority.HIGH,
            },
        )

        assert result["error_recorded"] is True
        assert result["notifications_sent"] is True

        # Проверяем что уведомление отправлено с правильными каналами
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args
        assert NotificationChannel.EMAIL in call_args[1]["channels"]
        assert NotificationChannel.SMS in call_args[1]["channels"]
        assert call_args[1]["priority"] == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_handle_error_with_fallback_actions(
        self, error_handler, sample_execution, sample_robot, mock_notification_service
    ):
        """Тест обработки ошибки с fallback действиями"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Мокаем создание записи об ошибке
        mock_error = MagicMock(spec=AutomationError)
        mock_error.id = 204
        error_handler.db.add.return_value = None

        # Мокаем fallback действия
        error_handler._execute_fallback_actions = AsyncMock(return_value=True)

        result = await error_handler.handle_error(
            sample_execution,
            "Primary action failed",
            {
                "fallback_actions": [
                    {
                        "type": "send_manual_notification",
                        "recipient": "manager@example.com",
                    }
                ]
            },
        )

        assert result["error_recorded"] is True
        assert result["fallback_executed"] is True
        assert result["notifications_sent"] is True

        # Проверяем что fallback действия выполнены
        error_handler._execute_fallback_actions.assert_called_once()

    @pytest.mark.asyncio
    async def test_can_retry_timeout_error(self, error_handler):
        """Тест проверки возможности повторной попытки для ошибки таймаута"""
        # Таймаут ошибки должны быть повторяемыми
        assert (
            await error_handler._can_retry("Connection timeout", {"max_retries": 3})
            is True
        )
        assert (
            await error_handler._can_retry("Network timeout", {"max_retries": 3})
            is True
        )

    @pytest.mark.asyncio
    async def test_can_retry_authentication_error(self, error_handler):
        """Тест проверки возможности повторной попытки для ошибки аутентификации"""
        # Ошибки аутентификации не должны быть повторяемыми
        assert (
            await error_handler._can_retry("Authentication failed", {"max_retries": 3})
            is False
        )
        assert (
            await error_handler._can_retry("Invalid credentials", {"max_retries": 3})
            is False
        )

    @pytest.mark.asyncio
    async def test_can_retry_validation_error(self, error_handler):
        """Тест проверки возможности повторной попытки для ошибки валидации"""
        # Ошибки валидации не должны быть повторяемыми
        assert (
            await error_handler._can_retry("Validation error", {"max_retries": 3})
            is False
        )
        assert (
            await error_handler._can_retry("Invalid data format", {"max_retries": 3})
            is False
        )

    @pytest.mark.asyncio
    async def test_schedule_retry_success(self, error_handler, sample_execution):
        """Тест успешного планирования повторной попытки"""
        # Мокаем создание отложенной задачи
        with patch(
            "src.aicrm.services.automation.error_handler.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            with patch(
                "src.aicrm.services.automation.error_handler.AutomationService"
            ) as mock_automation_service:
                mock_service_instance = MagicMock()
                mock_service_instance.move_to_stage = AsyncMock(
                    return_value={"success": True}
                )
                mock_automation_service.return_value = mock_service_instance

                result = await error_handler._schedule_retry(
                    sample_execution, 300, 1  # 5 минут задержки, 1 попытка
                )

                assert result is True
                mock_sleep.assert_called_once_with(300)
                mock_service_instance.move_to_stage.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_fallback_actions_email_fallback(
        self, error_handler, mock_notification_service
    ):
        """Тест выполнения fallback действия - отправка email"""
        fallback_action = {
            "type": "send_email",
            "recipient": "support@example.com",
            "subject": "Fallback notification",
            "message": "Primary action failed, manual intervention required",
        }

        result = await error_handler._execute_fallback_actions([fallback_action])

        assert result is True
        mock_notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_fallback_actions_create_task(self, error_handler):
        """Тест выполнения fallback действия - создание задачи"""
        with patch(
            "src.aicrm.services.automation.error_handler.TaskService"
        ) as mock_task_service:
            mock_service_instance = MagicMock()
            mock_service_instance.create_task = AsyncMock(
                return_value=MagicMock(id=300)
            )
            mock_task_service.return_value = mock_service_instance

            fallback_action = {
                "type": "create_task",
                "title": "Manual intervention required",
                "description": "Automation failed, manual processing needed",
                "priority": "high",
                "assigned_to": 1,
            }

            result = await error_handler._execute_fallback_actions([fallback_action])

            assert result is True
            mock_service_instance.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_fallback_actions_log_to_external_system(self, error_handler):
        """Тест выполнения fallback действия - логирование во внешнюю систему"""
        with patch(
            "src.aicrm.services.automation.error_handler.external_api_service"
        ) as mock_external_api:
            mock_external_api.log_error = AsyncMock(return_value=True)

            fallback_action = {
                "type": "log_to_external_system",
                "system": "monitoring",
                "error_details": {"severity": "high", "component": "automation"},
            }

            result = await error_handler._execute_fallback_actions([fallback_action])

            assert result is True
            mock_external_api.log_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_error_severity_critical(self, error_handler):
        """Тест определения критичности ошибки - критическая"""
        severity = error_handler._get_error_severity("Database connection lost")
        assert severity == "critical"

        severity = error_handler._get_error_severity("System out of memory")
        assert severity == "critical"

    @pytest.mark.asyncio
    async def test_get_error_severity_high(self, error_handler):
        """Тест определения критичности ошибки - высокая"""
        severity = error_handler._get_error_severity("Authentication failed")
        assert severity == "high"

        severity = error_handler._get_error_severity("Permission denied")
        assert severity == "high"

    @pytest.mark.asyncio
    async def test_get_error_severity_medium(self, error_handler):
        """Тест определения критичности ошибки - средняя"""
        severity = error_handler._get_error_severity("Connection timeout")
        assert severity == "medium"

        severity = error_handler._get_error_severity("Network error")
        assert severity == "medium"

    @pytest.mark.asyncio
    async def test_get_error_severity_low(self, error_handler):
        """Тест определения критичности ошибки - низкая"""
        severity = error_handler._get_error_severity("Invalid input format")
        assert severity == "low"

        severity = error_handler._get_error_severity("Validation error")
        assert severity == "low"

    @pytest.mark.asyncio
    async def test_create_error_record_success(
        self, error_handler, sample_execution, sample_robot
    ):
        """Тест успешного создания записи об ошибке"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        result = await error_handler._create_error_record(
            sample_execution,
            "Test error message",
            {"severity": "high", "component": "test"},
        )

        assert result is not None
        error_handler.db.add.assert_called_once()
        error_handler.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_error_record_with_actions_executed(
        self, error_handler, sample_execution, sample_robot
    ):
        """Тест создания записи об ошибке с выполненными действиями"""
        # Мокаем получение робота
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            sample_robot
        )

        # Устанавливаем actions_executed
        sample_execution.actions_executed = [
            {"action_type": "send_email", "success": False, "error": "SMTP timeout"},
            {"action_type": "update_status", "success": True},
        ]

        result = await error_handler._create_error_record(
            sample_execution, "Multiple action failures", {"severity": "medium"}
        )

        assert result is not None
        # Проверяем что actions_executed сохранены в записи об ошибке
        call_args = error_handler.db.add.call_args
        error_record = call_args[0][0]
        assert error_record.actions_executed == sample_execution.actions_executed

    @pytest.mark.asyncio
    async def test_send_error_notification_success(
        self, error_handler, mock_notification_service
    ):
        """Тест успешной отправки уведомления об ошибке"""
        error_details = {
            "execution_id": 100,
            "robot_name": "Test Robot",
            "error_message": "Test error",
            "severity": "high",
        }

        result = await error_handler._send_error_notification(
            error_details, NotificationPriority.HIGH, [NotificationChannel.EMAIL]
        )

        assert result is True
        mock_notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_error_notification_failure(
        self, error_handler, mock_notification_service
    ):
        """Тест неудачной отправки уведомления об ошибке"""
        mock_notification_service.send_notification.side_effect = Exception(
            "Notification failed"
        )

        error_details = {
            "execution_id": 100,
            "robot_name": "Test Robot",
            "error_message": "Test error",
            "severity": "high",
        }

        result = await error_handler._send_error_notification(
            error_details, NotificationPriority.HIGH, [NotificationChannel.EMAIL]
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_bulk_error_handling(self, error_handler, mock_notification_service):
        """Тест массовой обработки ошибок"""
        executions = []
        for i in range(3):
            execution = MagicMock(spec=AutomationExecution)
            execution.id = 100 + i
            execution.entity_type = EntityType.CUSTOMER
            execution.entity_id = 50 + i
            execution.robot_id = 5
            execution.error_message = f"Error {i}"
            executions.append(execution)

        # Мокаем получение робота
        robot = MagicMock()
        robot.name = "Bulk Test Robot"
        error_handler.db.query.return_value.filter.return_value.first.return_value = (
            robot
        )

        # Мокаем создание записей об ошибках
        error_handler.db.add.return_value = None

        results = await error_handler.handle_bulk_errors(
            executions, "Bulk processing failed", {"severity": "medium"}
        )

        assert len(results) == 3
        assert all(r["error_recorded"] for r in results)
        assert all(r["notifications_sent"] for r in results)

    def test_error_pattern_recognition(self, error_handler):
        """Тест распознавания паттернов ошибок"""
        # Тестируем различные типы ошибок
        patterns = {
            "Connection timeout": "timeout",
            "Authentication failed": "auth",
            "Permission denied": "permission",
            "Invalid input": "validation",
            "Database error": "database",
            "Network unreachable": "network",
        }

        for error_msg, expected_pattern in patterns.items():
            pattern = error_handler._recognize_error_pattern(error_msg)
            assert pattern == expected_pattern, f"Failed for {error_msg}"

    def test_error_recovery_suggestions(self, error_handler):
        """Тест предложений по восстановлению после ошибок"""
        suggestions = {
            "timeout": [
                "Check network connectivity",
                "Increase timeout values",
                "Retry operation",
            ],
            "auth": [
                "Verify credentials",
                "Check API keys",
                "Renew authentication token",
            ],
            "permission": [
                "Check user permissions",
                "Verify access rights",
                "Contact administrator",
            ],
            "validation": [
                "Check input data format",
                "Validate required fields",
                "Review data constraints",
            ],
            "database": [
                "Check database connectivity",
                "Verify table existence",
                "Check database locks",
            ],
            "network": [
                "Check network configuration",
                "Verify DNS resolution",
                "Test connectivity",
            ],
        }

        for error_type, expected_suggestions in suggestions.items():
            actual_suggestions = error_handler._get_recovery_suggestions(error_type)
            assert actual_suggestions == expected_suggestions

    def test_error_metrics_collection(self, error_handler):
        """Тест сбора метрик ошибок"""
        # Мокаем метрики сервис
        with patch(
            "src.aicrm.services.automation.error_handler.metrics_service"
        ) as mock_metrics:
            mock_metrics.increment_counter = MagicMock()
            mock_metrics.record_histogram = MagicMock()

            error_handler._collect_error_metrics("timeout", 30.5, "high")

            # Проверяем что метрики собраны
            mock_metrics.increment_counter.assert_called()
            mock_metrics.record_histogram.assert_called()

    def test_error_context_preservation(self, error_handler):
        """Тест сохранения контекста ошибки"""
        execution_context = {
            "user_id": 123,
            "session_id": "sess_456",
            "request_id": "req_789",
            "timestamp": datetime.now(),
            "user_agent": "TestAgent/1.0",
            "ip_address": "192.168.1.1",
        }

        preserved_context = error_handler._preserve_error_context(execution_context)

        # Проверяем что контекст сохранен
        assert preserved_context["user_id"] == 123
        assert preserved_context["session_id"] == "sess_456"
        assert "timestamp" in preserved_context

    def test_error_escalation_logic(self, error_handler):
        """Тест логики эскалации ошибок"""
        escalation_rules = {
            "critical": [
                "immediate_notification",
                "create_incident",
                "notify_management",
            ],
            "high": ["delayed_notification", "assign_to_specialist"],
            "medium": ["log_only", "monitor_trends"],
            "low": ["log_only"],
        }

        for severity, expected_actions in escalation_rules.items():
            actions = error_handler._get_escalation_actions(severity)
            assert actions == expected_actions
