"""
Сервис rate limiting с Redis
"""

import time
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from ..core.config import settings
from ..services.metrics_service import metrics_service
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitService:
    """Сервис ограничения частоты запросов"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis_client: Optional[redis.Redis] = None

        # Настройки по умолчанию
        self.default_limits = {
            "global": {"requests": 1000, "window": 60},  # 1000 запросов в минуту
            "ai": {"requests": 60, "window": 60},  # 60 AI запросов в минуту
            "auth": {"requests": 10, "window": 60},  # 10 попыток входа в минуту
            "api": {"requests": 100, "window": 60},  # 100 API запросов в минуту
        }

    async def __aenter__(self):
        """Async context manager entry"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.redis_client:
            await self.redis_client.close()

    async def _get_client(self) -> redis.Redis:
        """Получение Redis клиента"""
        if not self.redis_client:
            await self.__aenter__()
        return self.redis_client

    async def check_rate_limit(
        self,
        key: str,
        limit_type: str = "api",
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Проверка rate limit

        Args:
            key: Уникальный ключ (обычно IP + user_id)
            limit_type: Тип лимита (global, ai, auth, api)
            custom_limit: Кастомный лимит запросов
            custom_window: Кастомное окно времени (секунды)

        Returns:
            Tuple[bool, Dict]: (разрешено ли, информация о лимите)
        """
        client = await self._get_client()

        # Получаем настройки лимита
        limit_config = self.default_limits.get(limit_type, self.default_limits["api"])
        max_requests = custom_limit or limit_config["requests"]
        window_seconds = custom_window or limit_config["window"]

        # Создаем ключ для Redis
        redis_key = f"ratelimit:{limit_type}:{key}"

        try:
            # Используем Redis sorted set для sliding window
            current_time = time.time()
            window_start = current_time - window_seconds

            # Удаляем старые записи вне окна
            await client.zremrangebyscore(redis_key, 0, window_start)

            # Получаем количество запросов в окне
            request_count = await client.zcard(redis_key)

            # Информация о лимите
            limit_info = {
                "limit": max_requests,
                "remaining": max(max_requests - request_count, 0),
                "reset": int(current_time + window_seconds),
                "window_seconds": window_seconds,
            }

            if request_count >= max_requests:
                # Лимит превышен
                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    limit_type=limit_type,
                    count=request_count,
                    limit=max_requests,
                )
                metrics_service.record_error(
                    "rate_limit_exceeded", f"{limit_type}_endpoint"
                )
                return False, limit_info

            # Добавляем текущий запрос
            await client.zadd(redis_key, {str(current_time): current_time})

            # Устанавливаем TTL на ключ (чуть больше окна для безопасности)
            await client.expire(redis_key, window_seconds * 2)

            limit_info["remaining"] -= 1  # Уменьшаем на текущий запрос
            return True, limit_info

        except Exception as e:
            logger.error(
                "Rate limit check error", key=key, limit_type=limit_type, error=str(e)
            )
            # В случае ошибки Redis разрешаем запрос (fail-open)
            return True, {
                "limit": max_requests,
                "remaining": max_requests - 1,
                "reset": int(time.time() + window_seconds),
                "window_seconds": window_seconds,
                "error": "Redis unavailable",
            }

    async def get_rate_limit_info(
        self, key: str, limit_type: str = "api"
    ) -> Dict[str, Any]:
        """Получение информации о текущем состоянии rate limit"""
        client = await self._get_client()

        limit_config = self.default_limits.get(limit_type, self.default_limits["api"])
        window_seconds = limit_config["window"]
        max_requests = limit_config["requests"]

        redis_key = f"ratelimit:{limit_type}:{key}"

        try:
            current_time = time.time()
            window_start = current_time - window_seconds

            # Удаляем старые записи
            await client.zremrangebyscore(redis_key, 0, window_start)

            # Получаем количество запросов
            request_count = await client.zcard(redis_key)

            return {
                "limit": max_requests,
                "remaining": max(max_requests - request_count, 0),
                "reset": int(current_time + window_seconds),
                "window_seconds": window_seconds,
                "current_requests": request_count,
            }

        except Exception as e:
            logger.error(
                "Rate limit info error", key=key, limit_type=limit_type, error=str(e)
            )
            return {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": int(time.time() + window_seconds),
                "window_seconds": window_seconds,
                "error": "Redis unavailable",
            }

    def get_client_identifier(
        self, request: Request, user_id: Optional[int] = None
    ) -> str:
        """Получение идентификатора клиента для rate limiting"""
        # Используем комбинацию IP и user_id (если есть)
        client_ip = self._get_client_ip(request)

        if user_id:
            # Для аутентифицированных пользователей используем user_id
            return f"user:{user_id}"
        else:
            # Для неаутентифицированных - IP адрес
            return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Получение IP адреса клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Берем первый IP из списка
            return forwarded_for.split(",")[0].strip()

        # Проверяем другие заголовки прокси
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Используем client.host
        return request.client.host if request.client else "unknown"

    async def reset_rate_limit(self, key: str, limit_type: str = "api") -> bool:
        """Сброс rate limit для ключа"""
        client = await self._get_client()
        redis_key = f"ratelimit:{limit_type}:{key}"

        try:
            result = await client.delete(redis_key)
            logger.info("Rate limit reset", key=key, limit_type=limit_type)
            return bool(result)
        except Exception as e:
            logger.error(
                "Rate limit reset error", key=key, limit_type=limit_type, error=str(e)
            )
            return False

    async def cleanup_expired_limits(self) -> int:
        """Очистка истекших rate limit записей"""
        # Redis автоматически удаляет ключи с TTL, но можем сделать дополнительную очистку
        logger.info("Rate limit cleanup completed")
        return 0

    # Специализированные методы для разных типов запросов

    async def check_ai_rate_limit(
        self, request: Request, user_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Проверка rate limit для AI запросов"""
        key = self.get_client_identifier(request, user_id)
        return await self.check_rate_limit(key, "ai")

    async def check_auth_rate_limit(
        self, request: Request
    ) -> Tuple[bool, Dict[str, Any]]:
        """Проверка rate limit для запросов аутентификации"""
        key = self._get_client_ip(request)
        return await self.check_rate_limit(key, "auth")

    async def check_api_rate_limit(
        self, request: Request, user_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Проверка rate limit для общих API запросов"""
        key = self.get_client_identifier(request, user_id)
        return await self.check_rate_limit(key, "api")

    async def check_global_rate_limit(
        self, request: Request
    ) -> Tuple[bool, Dict[str, Any]]:
        """Проверка глобального rate limit"""
        key = self._get_client_ip(request)
        return await self.check_rate_limit(key, "global")


# FastAPI dependency для rate limiting
async def rate_limit_dependency(
    request: Request, limit_type: str = "api"
) -> Dict[str, Any]:
    """
    Dependency для FastAPI rate limiting

    Использование:
    @app.get("/api/endpoint")
    async def endpoint(rate_limit: dict = Depends(rate_limit_dependency)):
        return {"message": "OK"}
    """
    service = RateLimitService()

    async with service:
        allowed, limit_info = await service.check_rate_limit(
            service._get_client_ip(request), limit_type
        )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(limit_info["reset"]),
                "Retry-After": str(limit_info["reset"] - int(time.time())),
            },
        )

    return limit_info


# Middleware для автоматического rate limiting
class RateLimitMiddleware:
    """Middleware для автоматического применения rate limiting"""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.rate_limiter = RateLimitService()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Создаем ASGI приложение для обработки
        from starlette.requests import Request
        from starlette.responses import Response

        request = Request(scope, receive)

        # Пропускаем исключенные пути
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Определяем тип лимита на основе пути
        limit_type = "api"
        if request.url.path.startswith("/api/ai"):
            limit_type = "ai"
        elif request.url.path.startswith("/api/auth"):
            limit_type = "auth"

        # Проверяем rate limit
        async with self.rate_limiter:
            allowed, limit_info = await self.rate_limiter.check_api_rate_limit(request)

        if not allowed:
            # Создаем ответ с rate limit headers
            response = Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )
            response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
            response.headers["Retry-After"] = str(
                limit_info["reset"] - int(time.time())
            )

            await response(scope, receive, send)
            return

        # Продолжаем обработку запроса
        await self.app(scope, receive, send)


# Глобальный экземпляр сервиса
rate_limit_service = RateLimitService()
