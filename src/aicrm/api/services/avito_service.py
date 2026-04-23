"""
Сервис интеграции с Avito API
"""

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import redis.asyncio as redis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.config import settings
from ..utils.logging import get_logger
from .rate_limiter import get_avito_rate_limiter

logger = get_logger(__name__)


class AvitoAuthError(Exception):
    """Ошибка авторизации Avito"""

    def __init__(self, message: str = "Ошибка авторизации Avito", details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_type = "auth"


class AvitoAPIError(Exception):
    """Ошибка API Avito"""

    def __init__(
        self,
        message: str = "Ошибка API Avito",
        status_code: int = None,
        response_data: dict = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.error_type = "api"

        # Классификация ошибок по статус кодам
        if status_code:
            if status_code == 400:
                self.error_subtype = "bad_request"
            elif status_code == 401:
                self.error_subtype = "unauthorized"
            elif status_code == 403:
                self.error_subtype = "forbidden"
            elif status_code == 404:
                self.error_subtype = "not_found"
            elif status_code == 422:
                self.error_subtype = "validation_error"
            elif status_code == 429:
                self.error_subtype = "rate_limit"
            elif status_code >= 500:
                self.error_subtype = "server_error"
            else:
                self.error_subtype = "unknown"
        else:
            self.error_subtype = "unknown"


class AvitoRateLimitError(Exception):
    """Превышен лимит запросов Avito"""

    def __init__(
        self, message: str = "Превышен лимит запросов Avito", retry_after: int = None
    ):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after  # секунды до следующего запроса
        self.error_type = "rate_limit"


class AvitoNetworkError(Exception):
    """Сетевая ошибка при работе с Avito API"""

    def __init__(
        self,
        message: str = "Сетевая ошибка Avito API",
        original_error: Exception = None,
    ):
        super().__init__(message)
        self.message = message
        self.original_error = original_error
        self.error_type = "network"


class AvitoTimeoutError(Exception):
    """Таймаут при работе с Avito API"""

    def __init__(self, message: str = "Таймаут Avito API", timeout_seconds: int = None):
        super().__init__(message)
        self.message = message
        self.timeout_seconds = timeout_seconds
        self.error_type = "timeout"


class AvitoValidationError(Exception):
    """Ошибка валидации данных Avito"""

    def __init__(
        self, message: str = "Ошибка валидации данных Avito", field_errors: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.field_errors = field_errors or {}
        self.error_type = "validation"


class AvitoCircuitBreakerError(Exception):
    """Ошибка Circuit Breaker - сервис временно недоступен"""

    def __init__(
        self,
        message: str = "Avito API временно недоступен (Circuit Breaker)",
        service_name: str = "avito_api",
    ):
        super().__init__(message)
        self.message = message
        self.service_name = service_name
        self.error_type = "circuit_breaker"


class AvitoServiceUnavailableError(Exception):
    """Сервис Avito временно недоступен"""

    def __init__(
        self, message: str = "Avito API временно недоступен", retry_after: int = None
    ):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after
        self.error_type = "service_unavailable"


class AvitoQuotaExceededError(Exception):
    """Превышена квота API Avito"""

    def __init__(
        self,
        message: str = "Превышена квота API Avito",
        quota_type: str = None,
        reset_time: str = None,
    ):
        super().__init__(message)
        self.message = message
        self.quota_type = quota_type
        self.reset_time = reset_time
        self.error_type = "quota_exceeded"


class AvitoClient:
    """
    HTTP клиент для работы с Avito API
    """

    def __init__(self):
        self.base_url = "https://api.avito.ru"
        self.client_id = settings.avito_client_id
        self.client_secret = settings.avito_client_secret
        self.access_token = None
        self.token_expires_at = None
        self.user_id = settings.avito_user_id

        # HTTP клиент с настройками
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Content-Type": "application/json", "User-Agent": "AI-CRM/1.0"},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    async def _ensure_token(self) -> str:
        """Обеспечение валидного access token"""
        if not self._is_token_valid():
            await self._refresh_token()
        return self.access_token

    def _is_token_valid(self) -> bool:
        """Проверка валидности токена"""
        if not self.access_token or not self.token_expires_at:
            return False
        # Добавляем 5 минут буфера
        return datetime.utcnow() < (self.token_expires_at - timedelta(minutes=5))

    async def _refresh_token(self):
        """Обновление access token через Client Credentials"""
        try:
            response = await self.http_client.post(
                "/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            token_data = await response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info("Avito access token обновлен")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AvitoAuthError("Неверные учетные данные Avito")
            raise AvitoAPIError(f"Ошибка авторизации: {e.response.text}")
        except Exception as e:
            raise AvitoAPIError(f"Ошибка получения токена: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def _make_request(
        self, method: str, endpoint: str, operation_type: str = "read", **kwargs
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса с обработкой ошибок и rate limiting"""
        # Проверка rate limit перед запросом
        rate_limiter = await get_avito_rate_limiter()
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            operation_type, str(self.user_id)
        )

        if not allowed:
            raise AvitoRateLimitError(
                f"Превышен лимит запросов Avito для операции {operation_type}. "
                f"Осталось {remaining} запросов, сброс через {reset_time:.0f} сек."
            )

        token = await self._ensure_token()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        try:
            response = await self.http_client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            # Проверка на rate limit со стороны Avito
            if response.status_code == 429:
                raise AvitoRateLimitError("Превышен лимит запросов Avito")

            return response.json() if response.content else {}

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Токен истек, попробуем обновить
                self.access_token = None
                token = await self._ensure_token()
                headers["Authorization"] = f"Bearer {token}"
                kwargs["headers"] = headers
                response = await self.http_client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
            elif e.response.status_code == 429:
                # Извлекаем информацию о rate limit из заголовков
                retry_after = e.response.headers.get("Retry-After")
                raise AvitoRateLimitError(
                    f"Превышен лимит запросов Avito для {endpoint}",
                    retry_after=int(retry_after) if retry_after else None,
                )
            elif e.response.status_code == 422:
                # Ошибка валидации данных
                try:
                    error_data = e.response.json()
                    raise AvitoValidationError(
                        f"Ошибка валидации данных: {error_data.get('message', 'Неверный формат данных')}",
                        field_errors=error_data.get("errors", {}),
                    )
                except:
                    raise AvitoValidationError(
                        f"Ошибка валидации данных: {e.response.text}"
                    )
            elif e.response.status_code >= 500:
                # Серверная ошибка Avito
                raise AvitoAPIError(
                    f"Серверная ошибка Avito: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response_data={"error": "server_error"},
                )
            else:
                # Другие ошибки API
                try:
                    error_data = e.response.json()
                    raise AvitoAPIError(
                        f"API ошибка {e.response.status_code}: {error_data.get('message', e.response.text)}",
                        status_code=e.response.status_code,
                        response_data=error_data,
                    )
                except:
                    raise AvitoAPIError(
                        f"API ошибка {e.response.status_code}: {e.response.text}",
                        status_code=e.response.status_code,
                    )
        except httpx.TimeoutException:
            raise AvitoTimeoutError(
                f"Таймаут запроса к Avito API: {endpoint}", timeout_seconds=30
            )
        except httpx.ConnectError as e:
            raise AvitoNetworkError(
                f"Ошибка подключения к Avito API: {endpoint}", original_error=e
            )
        except httpx.RequestError as e:
            raise AvitoNetworkError(
                f"Ошибка сети при запросе к Avito API: {endpoint}", original_error=e
            )
        except Exception as e:
            raise AvitoAPIError(
                f"Неизвестная ошибка при запросе к {endpoint}: {str(e)}"
            )

    # Методы API

    async def get_items(self, **params) -> List[Dict[str, Any]]:
        """Получение списка объявлений"""
        response = await self._make_request(
            "GET", "/core/v1/items", operation_type="read", params=params
        )
        return response.get("resources", [])

    async def get_item_info(self, item_id: int) -> Dict[str, Any]:
        """Получение информации об объявлении"""
        return await self._make_request(
            "GET",
            f"/core/v1/accounts/{self.user_id}/items/{item_id}/",
            operation_type="read",
        )

    async def get_item_stats(
        self,
        item_ids: List[int],
        date_from: date,
        date_to: date,
        fields: List[str] = None,
        period_grouping: str = "day",
    ) -> Dict[str, Any]:
        """Получение статистики объявлений"""
        if fields is None:
            fields = ["uniqViews", "uniqContacts", "uniqFavorites"]

        data = {
            "itemIds": item_ids,
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "fields": fields,
            "periodGrouping": period_grouping,
        }

        return await self._make_request(
            "POST",
            f"/stats/v1/accounts/{self.user_id}/items",
            operation_type="read",
            json=data,
        )

    async def get_analytics(
        self,
        date_from: date,
        date_to: date,
        metrics: List[str],
        grouping: str = "item",
        **filters,
    ) -> Dict[str, Any]:
        """Получение аналитики по профилю"""
        data = {
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "metrics": metrics,
            "grouping": grouping,
            "limit": 1000,
            "offset": 0,
        }

        if filters:
            data["filter"] = filters

        return await self._make_request(
            "POST",
            f"/stats/v2/accounts/{self.user_id}/items",
            operation_type="read",
            json=data,
        )

    async def get_vas_prices(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Получение цен на услуги продвижения"""
        return await self._make_request(
            "POST",
            f"/core/v1/accounts/{self.user_id}/vas/prices",
            operation_type="read",
            json={"itemIds": item_ids},
        )

    async def apply_vas(
        self, item_id: int, slugs: List[str], stickers: List[int] = None
    ) -> Dict[str, Any]:
        """Применение услуг продвижения"""
        data = {"slugs": slugs}
        if stickers:
            data["stickers"] = stickers

        return await self._make_request(
            "PUT", f"/core/v2/items/{item_id}/vas/", operation_type="write", json=data
        )

    async def update_price(self, item_id: int, price: int) -> Dict[str, Any]:
        """Обновление цены объявления"""
        return await self._make_request(
            "POST",
            f"/core/v1/items/{item_id}/update_price",
            operation_type="write",
            json={"price": price},
        )

    async def get_calls_stats(
        self, date_from: date, date_to: date, item_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Получение статистики звонков"""
        data = {"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat()}
        if item_ids:
            data["itemIds"] = item_ids

        return await self._make_request(
            "POST",
            f"/core/v1/accounts/{self.user_id}/calls/stats/",
            operation_type="read",
            json=data,
        )

    # Messenger API методы

    async def get_chats(
        self,
        item_ids: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Получение списка чатов"""
        params = {"limit": limit, "offset": offset}
        if item_ids:
            params["itemIds"] = item_ids
        if unread_only is not None:
            params["unreadOnly"] = str(unread_only).lower()

        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats",
            operation_type="read",
            params=params,
        )

    async def get_chat_by_id(self, chat_id: str) -> Dict[str, Any]:
        """Получение информации по чату"""
        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}",
            operation_type="read",
        )

    async def get_messages(
        self, chat_id: str, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка сообщений (v1)"""
        params = {"limit": limit, "offset": offset}

        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages/",
            operation_type="read",
            params=params,
        )

    async def get_messages_v2(
        self, chat_id: str, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка сообщений (v2)"""
        params = {"limit": limit, "offset": offset}

        return await self._make_request(
            "GET",
            f"/messenger/v2/accounts/{self.user_id}/chats/{chat_id}/messages/",
            operation_type="read",
            params=params,
        )

    async def send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Отправка сообщения"""
        data = {"message": {"text": message}}

        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages",
            operation_type="write",
            json=data,
        )

    async def mark_chat_read(self, chat_id: str) -> Dict[str, Any]:
        """Отметка чата как прочитанного"""
        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/read",
            operation_type="write",
        )

    async def delete_message(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        """Удаление сообщения"""
        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages/{message_id}",
            operation_type="write",
        )

    async def add_to_blacklist(
        self, user_id: str, reason: Optional[str] = None
    ) -> None:
        """Добавление пользователя в черный список"""
        data = {"userId": user_id}
        if reason:
            data["reason"] = reason

        await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/blacklist",
            operation_type="write",
            json=data,
        )

    async def subscribe_webhook(
        self, url: str, events: List[str] = None
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления"""
        if events is None:
            events = ["message"]

        data = {"url": url, "events": events}

        return await self._make_request(
            "POST", "/messenger/v1/webhook", operation_type="write", json=data
        )

    async def unsubscribe_webhook(self, url: str) -> Dict[str, Any]:
        """Отписка от webhook уведомлений"""
        data = {"url": url}

        return await self._make_request(
            "POST",
            "/messenger/v1/webhook/unsubscribe",
            operation_type="write",
            json=data,
        )

    async def subscribe_webhook_v2(
        self, url: str, events: List[str] = None
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления (v2)"""
        if events is None:
            events = ["message"]

        data = {"url": url, "events": events}

        return await self._make_request(
            "POST", "/messenger/v2/webhook", operation_type="write", json=data
        )


class AvitoCache:
    """
    Кэширование данных Avito API в Redis
    """

    def __init__(self):
        self.redis_url = settings.redis_url or "redis://localhost:6379"
        self.redis_client = None

    async def _get_redis(self) -> redis.Redis:
        """Получение Redis клиента"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Получение данных из кэша"""
        try:
            redis_client = await self._get_redis()
            cached_data = await redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.warning(f"Ошибка чтения из кэша {key}: {e}")
            return None

    async def set_cached(
        self, key: str, data: Dict[str, Any], ttl_seconds: int
    ) -> None:
        """Сохранение данных в кэш"""
        try:
            redis_client = await self._get_redis()
            await redis_client.setex(key, ttl_seconds, json.dumps(data))
            logger.debug(f"Cached data for key: {key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"Ошибка записи в кэш {key}: {e}")

    async def invalidate_pattern(self, pattern: str) -> None:
        """Инвалидация кэша по паттерну"""
        try:
            redis_client = await self._get_redis()
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(
                    f"Invalidated {len(keys)} cache keys matching pattern: {pattern}"
                )
        except Exception as e:
            logger.warning(f"Ошибка инвалидации кэша {pattern}: {e}")


class AvitoService:
    """
    Бизнес-логика интеграции с Avito
    """

    def __init__(self):
        self.client = AvitoClient()
        self.cache = AvitoCache()

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_active_items(
        self, use_cache_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """Получение активных объявлений с кэшированием и graceful degradation"""
        cache_key = f"avito:active_items:{self.client.user_id}"

        # Проверяем кэш
        cached_data = await self.cache.get_cached(cache_key)
        if cached_data:
            logger.info(
                f"Возвращены активные объявления из кэша ({len(cached_data)} шт.)"
            )
            return cached_data

        try:
            items = await self.client.get_items(status="active", per_page=100)
            logger.info(f"Получено {len(items)} активных объявлений из API")

            # Кэшируем на 5 минут
            await self.cache.set_cached(cache_key, items, ttl_seconds=300)
            return items
        except (AvitoNetworkError, AvitoTimeoutError, AvitoAPIError) as e:
            if (
                use_cache_fallback
                and isinstance(e, (AvitoNetworkError, AvitoTimeoutError))
                or (isinstance(e, AvitoAPIError) and e.error_subtype == "server_error")
            ):
                # Graceful degradation: возвращаем пустой список с предупреждением
                logger.warning(
                    f"Avito API недоступен ({e.error_type}), возвращаем пустой список для graceful degradation"
                )
                return []
            else:
                logger.error(f"Ошибка получения объявлений: {e}")
                raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка получения объявлений: {e}")
            if use_cache_fallback:
                logger.warning("Возвращаем пустой список из-за неожиданной ошибки")
                return []
            raise

    async def get_item_performance(
        self, item_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Получение производительности объявления с кэшированием"""
        cache_key = f"avito:item_performance:{item_id}:{days}"

        # Проверяем кэш
        cached_data = await self.cache.get_cached(cache_key)
        if cached_data:
            logger.info(f"Возвращена производительность объявления {item_id} из кэша")
            return cached_data

        try:
            date_to = date.today()
            date_from = date_to - timedelta(days=days)

            # Статистика просмотров
            stats = await self.client.get_item_stats(
                item_ids=[item_id], date_from=date_from, date_to=date_to
            )

            # Статистика звонков
            calls_stats = await self.client.get_calls_stats(
                date_from=date_from, date_to=date_to, item_ids=[item_id]
            )

            # Информация об объявлении
            item_info = await self.client.get_item_info(item_id)

            result = {
                "item_id": item_id,
                "title": item_info.get("title"),
                "status": item_info.get("status"),
                "url": item_info.get("url"),
                "stats": stats.get("result", {}),
                "calls": calls_stats.get("result", {}),
                "vas_active": item_info.get("vas", []),
            }

            # Кэшируем на 10 минут
            await self.cache.set_cached(cache_key, result, ttl_seconds=600)
            logger.info(f"Производительность объявления {item_id} сохранена в кэш")

            return result

        except Exception as e:
            logger.error(f"Ошибка получения статистики объявления {item_id}: {e}")
            raise

    async def optimize_ad_pricing(self, item_id: int) -> Dict[str, Any]:
        """Оптимизация цены объявления на основе статистики"""
        try:
            # Получаем статистику за последние 30 дней
            performance = await self.get_item_performance(item_id, days=30)

            # Анализируем эффективность
            stats = performance.get("stats", {}).get("items", [])
            if not stats:
                return {"recommendation": "Недостаточно данных для анализа"}

            total_views = sum(
                day.get("uniqViews", 0) for day in stats[0].get("stats", [])
            )
            total_contacts = sum(
                day.get("uniqContacts", 0) for day in stats[0].get("stats", [])
            )

            if total_views == 0:
                conversion_rate = 0
            else:
                conversion_rate = total_contacts / total_views

            # Простая логика оптимизации
            if conversion_rate < 0.01:  # Менее 1% конверсии
                recommendation = (
                    "Увеличить цену на 5-10% для повышения качества трафика"
                )
            elif conversion_rate > 0.05:  # Более 5% конверсии
                recommendation = "Цена оптимальна, рассмотреть применение VAS услуг"
            else:
                recommendation = "Цена в оптимальном диапазоне"

            return {
                "item_id": item_id,
                "current_conversion": conversion_rate,
                "total_views": total_views,
                "total_contacts": total_contacts,
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Ошибка оптимизации цены для {item_id}: {e}")
            raise

    async def apply_promotion_service(
        self, item_id: int, service_slug: str, stickers: List[int] = None
    ) -> Dict[str, Any]:
        """Применение услуги продвижения с инвалидацией кэша"""
        try:
            result = await self.client.apply_vas(
                item_id=item_id, slugs=[service_slug], stickers=stickers
            )

            logger.info(f"Применена услуга {service_slug} к объявлению {item_id}")

            # Инвалидируем кэш производительности объявления
            await self.cache.invalidate_pattern(f"avito:item_performance:{item_id}:*")
            logger.info(f"Кэш производительности объявления {item_id} инвалидирован")

            return result

        except Exception as e:
            logger.error(f"Ошибка применения услуги {service_slug} к {item_id}: {e}")
            raise

    async def get_promotion_options(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Получение доступных услуг продвижения с кэшированием"""
        # Создаем ключ на основе отсортированных item_ids для консистентности
        sorted_ids = sorted(item_ids)
        cache_key = f"avito:vas_prices:{':'.join(map(str, sorted_ids))}"

        # Проверяем кэш
        cached_data = await self.cache.get_cached(cache_key)
        if cached_data:
            logger.info(f"Возвращены цены VAS из кэша для {len(item_ids)} объявлений")
            return cached_data

        try:
            prices = await self.client.get_vas_prices(item_ids)
            logger.info(f"Получены цены VAS из API для {len(item_ids)} объявлений")

            # Кэшируем на 30 минут
            await self.cache.set_cached(cache_key, prices, ttl_seconds=1800)
            return prices
        except Exception as e:
            logger.error(f"Ошибка получения цен VAS для {item_ids}: {e}")
            raise

    async def update_item_price(self, item_id: int, new_price: int) -> Dict[str, Any]:
        """Обновление цены объявления с инвалидацией кэша"""
        try:
            result = await self.client.update_price(item_id, new_price)
            logger.info(f"Цена объявления {item_id} обновлена на {new_price}")

            # Инвалидируем кэш производительности объявления
            await self.cache.invalidate_pattern(f"avito:item_performance:{item_id}:*")
            logger.info(f"Кэш производительности объявления {item_id} инвалидирован")

            return result
        except Exception as e:
            logger.error(f"Ошибка обновления цены для {item_id}: {e}")
            raise

    # Messenger API бизнес-методы

    async def get_avito_chats(
        self,
        item_ids: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Получение списка чатов из Avito"""
        try:
            return await self.client.get_chats(item_ids, unread_only, limit, offset)
        except Exception as e:
            logger.error(f"Ошибка получения списка чатов: {e}")
            raise

    async def get_avito_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Получение информации о чате из Avito"""
        try:
            return await self.client.get_chat_by_id(chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения информации о чате {chat_id}: {e}")
            raise

    async def get_avito_messages(
        self, chat_id: str, limit: int = 100, offset: int = 0, use_v2: bool = True
    ) -> Dict[str, Any]:
        """Получение сообщений из чата Avito"""
        try:
            if use_v2:
                return await self.client.get_messages_v2(chat_id, limit, offset)
            else:
                return await self.client.get_messages(chat_id, limit, offset)
        except Exception as e:
            logger.error(f"Ошибка получения сообщений чата {chat_id}: {e}")
            raise

    async def send_avito_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Отправка сообщения в чат Avito"""
        try:
            result = await self.client.send_message(chat_id, message)
            logger.info(f"Сообщение отправлено в чат {chat_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
            raise

    async def mark_avito_chat_read(self, chat_id: str) -> Dict[str, Any]:
        """Отметка чата как прочитанного в Avito"""
        try:
            result = await self.client.mark_chat_read(chat_id)
            logger.info(f"Чат {chat_id} отмечен как прочитанный")
            return result
        except Exception as e:
            logger.error(f"Ошибка отметки чата {chat_id} как прочитанного: {e}")
            raise

    async def delete_avito_message(
        self, chat_id: str, message_id: str
    ) -> Dict[str, Any]:
        """Удаление сообщения в Avito"""
        try:
            result = await self.client.delete_message(chat_id, message_id)
            logger.info(f"Сообщение {message_id} удалено из чата {chat_id}")
            return result
        except Exception as e:
            logger.error(
                f"Ошибка удаления сообщения {message_id} из чата {chat_id}: {e}"
            )
            raise

    async def subscribe_avito_webhook(
        self, webhook_url: str, events: List[str] = None, use_v2: bool = False
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления Avito"""
        try:
            if use_v2:
                result = await self.client.subscribe_webhook_v2(webhook_url, events)
            else:
                result = await self.client.subscribe_webhook(webhook_url, events)

            logger.info(f"Подписка на webhook создана: {webhook_url}")
            return result
        except Exception as e:
            logger.error(f"Ошибка создания подписки на webhook {webhook_url}: {e}")
            raise

    async def unsubscribe_avito_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Отписка от webhook уведомлений Avito"""
        try:
            result = await self.client.unsubscribe_webhook(webhook_url)
            logger.info(f"Подписка на webhook отменена: {webhook_url}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отмены подписки на webhook {webhook_url}: {e}")
            raise

    async def add_user_to_blacklist(
        self, user_id: str, reason: Optional[str] = None
    ) -> None:
        """Добавление пользователя в черный список Avito"""
        try:
            await self.client.add_to_blacklist(user_id, reason)
            logger.info(f"Пользователь {user_id} добавлен в черный список")
        except Exception as e:
            logger.error(
                f"Ошибка добавления пользователя {user_id} в черный список: {e}"
            )
            raise

    async def sync_avito_chats_with_db(
        self, db_session, limit: int = 100
    ) -> Dict[str, Any]:
        """Синхронизация чатов из Avito с базой данных"""
        try:
            from ..models.avito_chat import AvitoChatSettings

            # Получаем чаты из Avito
            avito_chats = await self.get_avito_chats(limit=limit)
            synced_count = 0
            created_count = 0

            if "chats" in avito_chats:
                for chat_data in avito_chats["chats"]:
                    chat_id = chat_data.get("id")
                    if not chat_id:
                        continue

                    # Проверяем существование чата в базе
                    existing_chat = (
                        db_session.query(AvitoChatSettings)
                        .filter(AvitoChatSettings.chat_id == chat_id)
                        .first()
                    )

                    if not existing_chat:
                        # Создаем новый чат
                        chat_settings = AvitoChatSettings(
                            chat_id=chat_id, ai_enabled=True, notifications_enabled=True
                        )
                        db_session.add(chat_settings)
                        created_count += 1

                    synced_count += 1

                db_session.commit()
                logger.info(
                    f"Синхронизировано {synced_count} чатов, создано {created_count} новых"
                )

            return {
                "synced_chats": synced_count,
                "created_chats": created_count,
                "total_chats": len(avito_chats.get("chats", [])),
            }

        except Exception as e:
            logger.error(f"Ошибка синхронизации чатов: {e}")
            raise
