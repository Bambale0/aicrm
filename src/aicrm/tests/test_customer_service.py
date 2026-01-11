"""
Юнит-тесты для CustomerService
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from src.aicrm.models.customer import Customer
from src.aicrm.services.customer import CustomerService


class TestCustomerService:
    """Тесты для CustomerService"""

    @pytest.fixture
    def mock_db(self):
        """Мок для сессии базы данных"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def sample_customer_data(self):
        """Пример данных клиента"""
        return {
            "name": "Иван Иванов",
            "email": "ivan@example.com",
            "phone": "+7-999-123-45-67",
            "address": "Москва, ул. Ленина, 10",
        }

    @pytest.fixture
    def sample_customer(self, sample_customer_data):
        """Пример объекта клиента"""
        customer = Customer(**sample_customer_data)
        customer.id = 1
        customer.total_orders = 0
        customer.total_spent = 0.00
        customer.loyalty_level = "bronze"
        return customer

    def test_create_customer_success(
        self, mock_db, sample_customer_data, sample_customer
    ):
        """Тест успешного создания клиента"""
        # Настройка мока
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        # Вызов метода
        result = CustomerService.create_customer(mock_db, sample_customer_data)

        # Проверки
        assert result.name == sample_customer_data["name"]
        assert result.email == sample_customer_data["email"]
        assert result.id == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_customer_found(self, mock_db, sample_customer):
        """Тест получения существующего клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_customer
        )

        result = CustomerService.get_customer(mock_db, 1)

        assert result == sample_customer
        mock_db.query.assert_called_once_with(Customer)

    def test_get_customer_not_found(self, mock_db):
        """Тест получения несуществующего клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.get_customer(mock_db, 999)

        assert result is None

    def test_get_customers_no_filters(self, mock_db, sample_customer):
        """Тест получения списка клиентов без фильтров"""
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            sample_customer
        ]

        result = CustomerService.get_customers(mock_db)

        assert len(result) == 1
        assert result[0] == sample_customer

    def test_get_customers_with_search(self, mock_db, sample_customer):
        """Тест получения списка клиентов с поиском"""
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            sample_customer
        ]

        result = CustomerService.get_customers(mock_db, search="Иван")

        assert len(result) == 1
        # Проверяем, что был вызван фильтр с поиском
        query_mock = mock_db.query.return_value
        filter_mock = query_mock.filter
        filter_mock.assert_called()

    def test_update_customer_success(self, mock_db, sample_customer):
        """Тест успешного обновления клиента"""
        update_data = {"phone": "+7-999-999-99-99", "address": "СПб, Невский пр."}

        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_customer
        )

        result = CustomerService.update_customer(mock_db, 1, update_data)

        assert result == sample_customer
        assert sample_customer.phone == update_data["phone"]
        assert sample_customer.address == update_data["address"]
        mock_db.commit.assert_called_once()

    def test_update_customer_not_found(self, mock_db):
        """Тест обновления несуществующего клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.update_customer(mock_db, 999, {"name": "Test"})

        assert result is None

    def test_delete_customer_success(self, mock_db, sample_customer):
        """Тест успешного удаления клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_customer
        )

        result = CustomerService.delete_customer(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_customer)
        mock_db.commit.assert_called_once()

    def test_delete_customer_not_found(self, mock_db):
        """Тест удаления несуществующего клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.delete_customer(mock_db, 999)

        assert result is False

    def test_get_customer_stats_success(self, mock_db, sample_customer):
        """Тест получения статистики клиента"""
        # Настройка мока для статистики заказов
        mock_stats = MagicMock()
        mock_stats.last_order_date = None
        mock_stats.average_order_value = 833.33

        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_customer
        )

        # Мокаем сложный запрос статистики
        mock_query = mock_db.query.return_value.filter.return_value
        mock_query.first.return_value = mock_stats

        result = CustomerService.get_customer_stats(mock_db, 1)

        assert result is not None
        assert isinstance(result, dict)
        assert "total_orders" in result
        assert "total_spent" in result
        assert "loyalty_level" in result
        assert "last_order_date" in result
        assert "average_order_value" in result

    def test_get_customer_stats_not_found(self, mock_db):
        """Тест получения статистики несуществующего клиента"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CustomerService.get_customer_stats(mock_db, 999)

        assert result is None

    def test_search_customers(self, mock_db, sample_customer):
        """Тест поиска клиентов"""
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            sample_customer
        ]

        result = CustomerService.search_customers(mock_db, "Иван")

        assert len(result) == 1
        assert result[0] == sample_customer
