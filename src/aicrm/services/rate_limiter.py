"""
Rate limiter для Avito API
"""

import time
from typing import Optional

import redis.asyncio as redis

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AvitoRateLimiter:
    """
    Rate limiter для Avito API запросов

    Ограничения Avito:
    - Чтение: 500 запросов в минуту
    - Запись: 150 запросов в минуту
    """

    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis_client: Optional[redis.Redis] = None

        # Ограничения по типам операций
        self.limits = {
            "read": 500,  # запросов в минуту
            "write": 150,  # запросов в минуту
        }

        # Ключи для Redis
        self.key_prefix = "avito_rate_limit"

    async def __aenter__(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self, operation_type: str, user_id: str
    ) -> tuple[bool, int, float]:
        """
        Проверка rate limit для операции

        Args:
            operation_type: Тип операции ("read" или "write")
            user_id: ID пользователя Avito

        Returns:
            tuple: (разрешено ли, количество оставшихся запросов, время до сброса в секундах)
        """
        if operation_type not in self.limits:
            logger.warning(f"Неизвестный тип операции: {operation_type}")
            return True, 999, 0

        if not self.redis_client:
            await self.__aenter__()

        # Ключ для Redis: avito_rate_limit:{user_id}:{operation_type}:{timestamp_минуты}
        current_minute = int(time.time() // 60)
        redis_key = f"{self.key_prefix}:{user_id}:{operation_type}:{current_minute}"

        try:
            # Получаем текущее количество запросов
            current_count = await self.redis_client.get(redis_key)
            current_count = int(current_count) if current_count else 0

            limit = self.limits[operation_type]
            remaining = max(0, limit - current_count)
            time_to_reset = (current_minute + 1) * 60 - time.time()

            if current_count >= limit:
                logger.warning(
                    f"Rate limit exceeded для {operation_type} операции пользователя {user_id}"
                )
                return False, remaining, time_to_reset

            # Увеличиваем счетчик
            await self.redis_client.incr(redis_key)
            # Устанавливаем TTL на 2 минуты (текущая + следующая)
            await self.redis_client.expire(redis_key, 120)

            return True, remaining - 1, time_to_reset

        except Exception as e:
            logger.error(f"Ошибка проверки rate limit: {e}")
            # В случае ошибки Redis разрешаем запрос, но логируем
            return True, 999, 0

    async def get_rate_limit_status(self, operation_type: str, user_id: str) -> dict:
        """
        Получение статуса rate limit для операции

        Returns:
            dict: {
                "limit": int,
                "remaining": int,
                "reset_time": float,
                "current_count": int
            }
        """
        if operation_type not in self.limits:
            return {"error": f"Неизвестный тип операции: {operation_type}"}

        if not self.redis_client:
            await self.__aenter__()

        current_minute = int(time.time() // 60)
        redis_key = f"{self.key_prefix}:{user_id}:{operation_type}:{current_minute}"

        try:
            current_count = await self.redis_client.get(redis_key)
            current_count = int(current_count) if current_count else 0

            limit = self.limits[operation_type]
            remaining = max(0, limit - current_count)
            time_to_reset = (current_minute + 1) * 60 - time.time()

            return {
                "limit": limit,
                "remaining": remaining,
                "reset_time": time_to_reset,
                "current_count": current_count,
            }

        except Exception as e:
            logger.error(f"Ошибка получения статуса rate limit: {e}")
            return {"error": str(e)}

    async def reset_rate_limit(self, operation_type: str, user_id: str) -> bool:
        """
        Сброс rate limit для операции (для тестирования или админских нужд)
        """
        if operation_type not in self.limits:
            return False

        if not self.redis_client:
            await self.__aenter__()

        try:
            # Удаляем все ключи для данного пользователя и типа операции
            current_minute = int(time.time() // 60)
            pattern = f"{self.key_prefix}:{user_id}:{operation_type}:*"

            # Получаем все ключи по паттерну
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)

            logger.info(
                f"Сброшен rate limit для {operation_type} операций пользователя {user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Ошибка сброса rate limit: {e}")
            return False


# Глобальный экземпляр rate limiter
_rate_limiter_instance: Optional[AvitoRateLimiter] = None


async def get_avito_rate_limiter() -> AvitoRateLimiter:
    """Получение глобального экземпляра rate limiter"""
    global _rate_limiter_instance
    if not _rate_limiter_instance:
        _rate_limiter_instance = AvitoRateLimiter()
        await _rate_limiter_instance.__aenter__()
    return _rate_limiter_instance


# Глобальный экземпляр для импорта
rate_limiter = AvitoRateLimiter()