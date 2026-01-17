"""
Тесты для TokenAccountingService - учет токенов AI
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from ..models.token_accounting import TokenQuota, TokenTransaction
from ..services.token_accounting_service import TokenAccountingService


class TestTokenAccountingService:
    """Тесты сервиса учета токенов"""

    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def token_service(self, mock_db):
        """Сервис учета токенов с моками"""
        return TokenAccountingService(mock_db)

    @pytest.mark.asyncio
    async def test_create_or_update_quota_new(self, token_service, mock_db):
        """Тест создания новой квоты"""
        # Мокаем, что квота не найдена
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Мокаем добавление в БД
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.id = 1
        mock_quota.entity_type = "company"
        mock_quota.entity_id = 123
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = await token_service.create_or_update_quota(
            entity_type="company",
            entity_id=123,
            quota_type="monthly",
            limit_tokens=10000,
            alert_threshold=80,
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_or_update_quota_existing(self, token_service, mock_db):
        """Тест обновления существующей квоты"""
        # Мокаем существующую квоту
        mock_existing_quota = MagicMock(spec=TokenQuota)
        mock_existing_quota.id = 1
        mock_existing_quota.limit_tokens = 5000
        mock_existing_quota.alert_threshold = 70

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing_quota
        )
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = await token_service.create_or_update_quota(
            entity_type="company",
            entity_id=123,
            quota_type="monthly",
            limit_tokens=10000,
            alert_threshold=80,
        )

        assert result is mock_existing_quota
        assert mock_existing_quota.limit_tokens == 10000
        assert mock_existing_quota.alert_threshold == 80

    @pytest.mark.asyncio
    async def test_check_quota_success(self, token_service, mock_db):
        """Тест успешной проверки квоты"""
        # Мокаем квоту
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.id = 1
        mock_quota.limit_tokens = 10000
        mock_quota.used_tokens = 5000
        mock_quota.alert_threshold = 80

        # Мокаем методы
        token_service._get_active_quota = MagicMock(return_value=mock_quota)

        # Мокаем транзакцию
        mock_transaction = MagicMock(spec=TokenTransaction)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = await token_service.check_quota_and_record_transaction(
            entity_type="company",
            entity_id=123,
            ai_provider="openrouter",
            ai_model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            estimated_cost=0.01,
        )

        assert result["success"] is True
        assert result["transaction"] is not None
        assert result["alert_triggered"] is False  # 5050/10000 = 50.5% < 80%
        assert mock_quota.used_tokens == 5100  # 5000 + 100

    @pytest.mark.asyncio
    async def test_check_quota_exceeded(self, token_service, mock_db):
        """Тест превышения квоты"""
        # Мокаем квоту
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.id = 1
        mock_quota.limit_tokens = 1000
        mock_quota.used_tokens = 950

        token_service._get_active_quota = MagicMock(return_value=mock_quota)

        result = await token_service.check_quota_and_record_transaction(
            entity_type="company",
            entity_id=123,
            ai_provider="openrouter",
            ai_model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert result["success"] is False
        assert result["error"] == "QUOTA_EXCEEDED"
        assert result["quota"] is mock_quota

    @pytest.mark.asyncio
    async def test_check_quota_alert_triggered(self, token_service, mock_db):
        """Тест срабатывания алерта"""
        # Мокаем квоту
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.id = 1
        mock_quota.limit_tokens = 1000
        mock_quota.used_tokens = 850  # 85% использования
        mock_quota.alert_threshold = 80

        token_service._get_active_quota = MagicMock(return_value=mock_quota)

        # Мокаем транзакцию
        mock_transaction = MagicMock(spec=TokenTransaction)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = await token_service.check_quota_and_record_transaction(
            entity_type="company",
            entity_id=123,
            ai_provider="openrouter",
            ai_model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert result["success"] is True
        assert result["alert_triggered"] is True  # (850+150)/1000 = 100% > 80%

    def test_get_quota_usage_stats_with_quota(self, token_service, mock_db):
        """Тест получения статистики использования с квотой"""
        # Мокаем квоту
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.id = 1
        mock_quota.limit_tokens = 10000
        mock_quota.used_tokens = 7500
        mock_quota.reset_at = datetime.utcnow() + timedelta(days=15)
        mock_quota.created_at = datetime.utcnow() - timedelta(days=10)

        token_service._get_active_quota = MagicMock(return_value=mock_quota)

        # Мокаем топ workflow
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            MagicMock(
                workflow_execution_id="wf_1", total_tokens=5000, transaction_count=10
            )
        ]

        result = token_service.get_quota_usage_stats("company", 123)

        assert result is not None
        assert result["limit_tokens"] == 10000
        assert result["used_tokens"] == 7500
        assert result["percentage_used"] == 75.0
        assert result["remaining_tokens"] == 2500
        assert "top_workflows_by_tokens" in result

    def test_get_quota_usage_stats_no_quota(self, token_service, mock_db):
        """Тест получения статистики без квоты"""
        token_service._get_active_quota = MagicMock(return_value=None)

        result = token_service.get_quota_usage_stats("company", 123)

        assert result is None

    def test_get_quota_alerts(self, token_service, mock_db):
        """Тест получения алертов о превышении лимитов"""
        # Мокаем квоты
        mock_quotas = [
            MagicMock(
                id=1,
                entity_type="company",
                entity_id=123,
                used_tokens=8500,
                limit_tokens=10000,
                alert_threshold=80,
            ),
            MagicMock(
                id=2,
                entity_type="user",
                entity_id=456,
                used_tokens=500,
                limit_tokens=1000,
                alert_threshold=90,
            ),
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_quotas

        result = token_service.get_quota_alerts()

        # Только первая квота должна сработать (85% > 80%)
        assert len(result) == 1
        assert result[0]["quota_id"] == 1
        assert result[0]["percentage_used"] == 85.0

    @pytest.mark.asyncio
    async def test_reset_monthly_quotas(self, token_service, mock_db):
        """Тест сброса месячных квот"""
        now = datetime.utcnow()
        past_reset = now - timedelta(days=1)

        # Мокаем сброс квот
        mock_db.query.return_value.filter.return_value.update.return_value = (
            5  # 5 сброшенных квот
        )

        result = await token_service.reset_monthly_quotas()

        assert result == 5

    def test_get_transaction_history(self, token_service, mock_db):
        """Тест получения истории транзакций"""
        mock_transactions = [
            MagicMock(
                id=1,
                quota_id=1,
                ai_provider="openrouter",
                ai_model="gpt-4",
                total_tokens=150,
                estimated_cost=0.01,
                created_at=datetime.utcnow(),
            )
        ]

        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            mock_transactions
        )
        mock_db.query.return_value.order_by.return_value = mock_query

        result = token_service.get_transaction_history(limit=10)

        assert len(result) == 1
        assert result[0].id == 1

    def test_get_active_quota_found(self, token_service, mock_db):
        """Тест поиска активной квоты - найдена"""
        mock_quota = MagicMock(spec=TokenQuota)
        mock_quota.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        result = token_service._get_active_quota("company", 123, "monthly")

        assert result is mock_quota

    def test_get_active_quota_not_found(self, token_service, mock_db):
        """Тест поиска активной квоты - не найдена"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = token_service._get_active_quota("company", 123, "monthly")

        assert result is None

    def test_calculate_next_reset(self, token_service):
        """Тест расчета следующей даты сброса"""
        # Текущая дата - январь
        jan_date = datetime(2024, 1, 15, 10, 0, 0)

        # Следующий сброс должен быть 1 февраля
        next_reset = token_service._calculate_next_reset(jan_date)
        expected = datetime(2024, 2, 1, 0, 0, 0)

        assert next_reset == expected

        # Текущая дата - декабрь
        dec_date = datetime(2024, 12, 15, 10, 0, 0)

        # Следующий сброс должен быть 1 января следующего года
        next_reset_dec = token_service._calculate_next_reset(dec_date)
        expected_dec = datetime(2025, 1, 1, 0, 0, 0)

        assert next_reset_dec == expected_dec


class TestTokenAccountingIntegration:
    """Интеграционные тесты учета токенов"""

    @pytest.mark.asyncio
    async def test_full_token_lifecycle(self, token_service, mock_db):
        """Тест полного жизненного цикла учета токенов"""
        # 1. Создание квоты
        quota = await token_service.create_or_update_quota(
            entity_type="company",
            entity_id=123,
            quota_type="monthly",
            limit_tokens=1000,
            alert_threshold=80,
        )

        # Проверяем, что квота создана
        assert quota is not None

        # 2. Проверка и запись транзакции
        result1 = await token_service.check_quota_and_record_transaction(
            entity_type="company",
            entity_id=123,
            ai_provider="openrouter",
            ai_model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert result1["success"] is True
        assert result1["alert_triggered"] is False

        # 3. Вторая транзакция с алертом
        result2 = await token_service.check_quota_and_record_transaction(
            entity_type="company",
            entity_id=123,
            ai_provider="openrouter",
            ai_model="gpt-4",
            prompt_tokens=700,
            completion_tokens=200,
        )

        # Должно сработать превышение квоты
        assert result2["success"] is False
        assert result2["error"] == "QUOTA_EXCEEDED"

        # 4. Получение статистики
        stats = token_service.get_quota_usage_stats("company", 123)
        assert stats["used_tokens"] == 150  # Только первая транзакция
        assert stats["percentage_used"] == 15.0

        # 5. Проверка алертов
        alerts = token_service.get_quota_alerts()
