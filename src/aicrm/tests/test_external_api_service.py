"""
Unit тесты для ExternalAPIService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import Timeout

from ..services.external_api_service import ExternalAPIService


class TestExternalAPIService:
    """Тесты для сервиса внешних API"""

    @pytest.fixture
    def api_service(self):
        """Сервис внешних API"""
        return ExternalAPIService()

    @pytest.mark.asyncio
    async def test_call_api_get_success(self, api_service):
        """Тест успешного GET запроса"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.url = "https://api.example.com/test"
            mock_response.json.return_value = {"result": "success"}

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await api_service.call_api("GET", "https://api.example.com/test")

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["json"] == {"result": "success"}
        assert result["url"] == "https://api.example.com/test"

    @pytest.mark.asyncio
    async def test_call_api_post_with_json(self, api_service):
        """Тест POST запроса с JSON данными"""
        request_data = {"key": "value"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 201
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"id": 123}

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await api_service.call_api(
                "POST",
                "https://api.example.com/items",
                json_data=request_data
            )

        assert result["success"] is True
        assert result["status_code"] == 201
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["url"] == "https://api.example.com/items"
        assert "Content-Type" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_call_api_with_auth(self, api_service):
        """Тест запроса с аутентификацией"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await api_service.call_api(
                "GET",
                "https://api.example.com/protected",
                auth=("user", "pass"),
                api_key="test_key"
            )

        call_args = mock_client.request.call_args
        assert call_args[1]["auth"] == ("user", "pass")
        assert call_args[1]["headers"]["X-API-Key"] == "test_key"

    @pytest.mark.asyncio
    async def test_call_api_with_bearer_token(self, api_service):
        """Тест запроса с Bearer токеном"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await api_service.call_api(
                "GET",
                "https://api.example.com/protected",
                bearer_token="token123"
            )

        call_args = mock_client.request.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer token123"

    @pytest.mark.asyncio
    async def test_call_api_failure(self, api_service):
        """Тест неудачного запроса"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = False
            mock_response.status_code = 404
            mock_response.text = "Not Found"

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await api_service.call_api("GET", "https://api.example.com/missing")

        assert result["success"] is False
        assert result["status_code"] == 404

    @pytest.mark.asyncio
    async def test_call_api_with_retry(self, api_service):
        """Тест запроса с повторными попытками при ошибке"""
        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            mock_client = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Первая попытка - TimeoutException
            # Вторая попытка - успешный ответ
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            from httpx import TimeoutException
            mock_client.request.side_effect = [TimeoutException("Timeout"), mock_response]

            result = await api_service.call_api("GET", "https://api.example.com/retry")

        assert result["success"] is True
        assert mock_client.request.call_count == 2  # Две попытки
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_api_max_retries_exceeded(self, api_service):
        """Тест превышения максимального количества retry"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            from httpx import TimeoutException
            mock_client.request.side_effect = TimeoutException("Timeout")

            result = await api_service.call_api("GET", "https://api.example.com/fail")

        assert result["success"] is False
        assert "error" in result
        assert "Timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_call_webhook_success(self, api_service):
        """Тест успешного вызова webhook"""
        payload = {"event": "test", "data": {"id": 123}}
        secret = "webhook_secret"

        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {"success": True, "status_code": 200}

            result = await api_service.call_webhook(
                "https://webhook.example.com/notify",
                "user_created",
                payload,
                secret
            )

        mock_call_api.assert_called_once()
        call_args = mock_call_api.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://webhook.example.com/notify"
        assert call_args[1]["json_data"] == payload
        assert "X-Event-Type" in call_args[1]["headers"]
        assert call_args[1]["headers"]["X-Event-Type"] == "user_created"
        assert "X-Signature" in call_args[1]["headers"]

    @pytest.mark.asyncio
    async def test_call_rest_api_get(self, api_service):
        """Тест вызова REST API - GET"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {"success": True, "json": {"items": []}}

            result = await api_service.call_rest_api(
                "https://api.example.com",
                "/users",
                "GET",
                params={"limit": 10}
            )

        mock_call_api.assert_called_once_with(
            "GET",
            "https://api.example.com/users",
            params={"limit": 10}
        )

    @pytest.mark.asyncio
    async def test_call_rest_api_post(self, api_service):
        """Тест вызова REST API - POST"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {"success": True}

            result = await api_service.call_rest_api(
                "https://api.example.com",
                "orders",
                "POST",
                json_data={"product": "tshirt", "quantity": 1}
            )

        call_args = mock_call_api.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://api.example.com/orders"
        assert call_args[1]["json_data"] == {"product": "tshirt", "quantity": 1}

    @pytest.mark.asyncio
    async def test_call_graphql_success(self, api_service):
        """Тест успешного вызова GraphQL"""
        query = "query { users { id name } }"
        variables = {"limit": 10}

        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {
                "success": True,
                "json": {"data": {"users": [{"id": 1, "name": "John"}]}}
            }

            result = await api_service.call_graphql(
                "https://api.example.com/graphql",
                query,
                variables
            )

        call_args = mock_call_api.call_args
        assert call_args[0][1] == "https://api.example.com/graphql"
        assert call_args[1]["json_data"]["query"] == query
        assert call_args[1]["json_data"]["variables"] == variables

        assert result["data"] == {"users": [{"id": 1, "name": "John"}]}

    @pytest.mark.asyncio
    async def test_call_soap_api(self, api_service):
        """Тест вызова SOAP API"""
        soap_action = "GetUser"
        soap_body = "<soap:GetUser><id>123</id></soap:GetUser>"

        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {"success": True, "text": "<response>OK</response>"}

            result = await api_service.call_soap_api(
                "https://soap.example.com/service",
                soap_action,
                soap_body
            )

        call_args = mock_call_api.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]["data"] == soap_body
        assert call_args[1]["headers"]["SOAPAction"] == soap_action

    @pytest.mark.asyncio
    async def test_batch_call_success(self, api_service):
        """Тест пакетного вызова API"""
        calls = [
            {"method": "GET", "url": "https://api.example.com/users"},
            {"method": "POST", "url": "https://api.example.com/orders", "json_data": {"item": "test"}}
        ]

        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.side_effect = [
                {"success": True, "data": "users"},
                {"success": True, "data": "orders"}
            ]

            results = await api_service.batch_call(calls, max_concurrent=2)

        assert len(results) == 2
        assert all(isinstance(r, dict) for r in results)

    @pytest.mark.asyncio
    async def test_batch_call_with_exceptions(self, api_service):
        """Тест пакетного вызова с исключениями"""
        calls = [
            {"method": "GET", "url": "https://api.example.com/fail"},
            {"method": "GET", "url": "https://api.example.com/success"}
        ]

        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.side_effect = [
                Exception("Network error"),
                {"success": True}
            ]

            results = await api_service.batch_call(calls)

        assert len(results) == 2
        # Первый результат - исключение
        assert isinstance(results[0], Exception)
        # Второй результат - успешный
        assert results[1]["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, api_service):
        """Тест успешной проверки здоровья"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.5

            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            result = await api_service.health_check("https://api.example.com/health")

        assert result["healthy"] is True
        assert result["status_code"] == 200
        assert result["response_time"] == 0.5

    @pytest.mark.asyncio
    async def test_health_check_failure(self, api_service):
        """Тест неудачной проверки здоровья"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection refused")

            result = await api_service.health_check("https://api.example.com/health")

        assert result["healthy"] is False
        assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_get_with_pagination_single_page(self, api_service):
        """Тест получения данных с пагинацией - одна страница"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {
                "success": True,
                "json": {"data": [{"id": 1}, {"id": 2}], "has_more": False}
            }

            result = await api_service.get_with_pagination(
                "https://api.example.com/items",
                page_param="page",
                limit_param="per_page"
            )

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_get_with_pagination_multiple_pages(self, api_service):
        """Тест получения данных с пагинацией - несколько страниц"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            # Первая страница
            mock_call_api.side_effect = [
                {
                    "success": True,
                    "json": {"data": [{"id": 1}, {"id": 2}], "has_more": True}
                },
                {
                    "success": True,
                    "json": {"data": [{"id": 3}], "has_more": False}
                }
            ]

            result = await api_service.get_with_pagination(
                "https://api.example.com/items",
                max_pages=2
            )

        assert len(result) == 3
        assert mock_call_api.call_count == 2

    @pytest.mark.asyncio
    async def test_get_with_pagination_empty_response(self, api_service):
        """Тест получения данных с пагинацией - пустой ответ"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {
                "success": True,
                "json": {"data": []}
            }

            result = await api_service.get_with_pagination("https://api.example.com/items")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_with_pagination_api_error(self, api_service):
        """Тест получения данных с пагинацией - ошибка API"""
        with patch.object(api_service, "call_api", new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = {"success": False}

            result = await api_service.get_with_pagination("https://api.example.com/items")

        assert result == []

    def test_init_default_values(self, api_service):
        """Тест инициализации с значениями по умолчанию"""
        assert api_service.timeout == Timeout(30.0, connect=10.0)
        assert api_service.max_retries == 3
        assert api_service.retry_delay == 1.0
