"""
Сервис для вызовов внешних API
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
import httpx
import json
from urllib.parse import urljoin, urlparse

from ..core.config import settings

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """Сервис для вызовов внешних API"""

    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3
        self.retry_delay = 1.0

    async def call_api(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        auth: Optional[tuple] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Вызов внешнего API

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE, etc.)
            url: URL для вызова
            headers: HTTP заголовки
            params: Query параметры
            data: Form data
            json_data: JSON data
            auth: Basic auth tuple (username, password)
            api_key: API ключ для заголовка
            bearer_token: Bearer токен для авторизации

        Returns:
            Dict с результатом вызова
        """
        try:
            # Подготовка заголовков
            request_headers = headers or {}
            if api_key:
                request_headers["X-API-Key"] = api_key
            elif bearer_token:
                request_headers["Authorization"] = f"Bearer {bearer_token}"

            # Подготовка данных запроса
            request_data = None
            if json_data:
                request_headers["Content-Type"] = "application/json"
                request_data = json.dumps(json_data)
            elif data:
                request_data = data

            # Выполнение запроса с повторными попытками
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.request(
                            method=method.upper(),
                            url=url,
                            headers=request_headers,
                            params=params,
                            content=request_data,
                            auth=auth
                        )

                        # Обработка ответа
                        result = {
                            "success": response.is_success,
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "url": str(response.url)
                        }

                        # Попытка распарсить JSON ответ
                        try:
                            result["json"] = response.json()
                        except:
                            result["text"] = response.text

                        # Логирование
                        if response.is_success:
                            logger.info(f"API call successful: {method} {url} -> {response.status_code}")
                        else:
                            logger.warning(f"API call failed: {method} {url} -> {response.status_code}: {response.text[:200]}")

                        return result

                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    logger.warning(f"API call attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

        except Exception as e:
            logger.error(f"API call error: {method} {url} -> {e}")
            return {
                "success": False,
                "error": str(e),
                "method": method,
                "url": url
            }

    async def call_webhook(
        self,
        url: str,
        event_type: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Вызов webhook с подписью

        Args:
            url: URL webhook
            event_type: Тип события
            payload: Данные события
            secret: Секрет для подписи

        Returns:
            Dict с результатом вызова
        """
        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": event_type
        }

        if secret:
            import hmac
            import hashlib
            import base64

            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).digest()
            headers["X-Signature"] = base64.b64encode(signature).decode()

        return await self.call_api(
            method="POST",
            url=url,
            headers=headers,
            json_data=payload
        )

    async def call_rest_api(
        self,
        base_url: str,
        endpoint: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Вызов REST API с базовым URL

        Args:
            base_url: Базовый URL API
            endpoint: Эндпоинт (может начинаться с /)
            method: HTTP метод
            **kwargs: Дополнительные параметры для call_api

        Returns:
            Dict с результатом вызова
        """
        # Формирование полного URL
        if endpoint.startswith("/"):
            full_url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
        else:
            full_url = urljoin(base_url.rstrip("/") + "/", endpoint)

        return await self.call_api(method=method, url=full_url, **kwargs)

    async def call_graphql(
        self,
        url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Вызов GraphQL API

        Args:
            url: GraphQL endpoint URL
            query: GraphQL запрос
            variables: Переменные запроса
            headers: Дополнительные заголовки

        Returns:
            Dict с результатом вызова
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"

        return await self.call_api(
            method="POST",
            url=url,
            headers=request_headers,
            json_data=payload
        )

    async def call_soap_api(
        self,
        url: str,
        soap_action: str,
        soap_body: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Вызов SOAP API

        Args:
            url: SOAP endpoint URL
            soap_action: SOAP Action
            soap_body: XML тело запроса
            headers: Дополнительные заголовки

        Returns:
            Dict с результатом вызова
        """
        request_headers = headers or {}
        request_headers.update({
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": soap_action
        })

        return await self.call_api(
            method="POST",
            url=url,
            headers=request_headers,
            data=soap_body
        )

    async def batch_call(
        self,
        calls: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Пакетный вызов нескольких API

        Args:
            calls: Список словарей с параметрами вызовов
            max_concurrent: Максимальное количество одновременных вызовов

        Returns:
            List с результатами всех вызовов
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def call_with_semaphore(call_params):
            async with semaphore:
                return await self.call_api(**call_params)

        tasks = [call_with_semaphore(call) for call in calls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def health_check(self, url: str, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Проверка здоровья API

        Args:
            url: URL для проверки
            timeout: Таймаут в секундах

        Returns:
            Dict с результатом проверки
        """
        try:
            timeout_obj = httpx.Timeout(timeout)
            async with httpx.AsyncClient(timeout=timeout_obj) as client:
                response = await client.get(url)

                return {
                    "healthy": response.is_success,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "url": url
                }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "url": url
            }

    async def get_with_pagination(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        page_param: str = "page",
        limit_param: str = "limit",
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получение данных с пагинацией

        Args:
            url: Базовый URL
            params: Базовые параметры
            page_param: Название параметра страницы
            limit_param: Название параметра лимита
            max_pages: Максимальное количество страниц

        Returns:
            List всех полученных элементов
        """
        all_items = []
        page = 1

        while page <= max_pages:
            request_params = params.copy() if params else {}
            request_params[page_param] = page

            result = await self.call_api("GET", url, params=request_params)

            if not result.get("success"):
                break

            data = result.get("json", {})
            items = data.get("data", data.get("items", data.get("results", [])))

            if not items:
                break

            all_items.extend(items)

            # Проверка на наличие следующей страницы
            if len(items) == 0:
                break

            page += 1

        return all_items


# Глобальный экземпляр сервиса
external_api_service = ExternalAPIService()
