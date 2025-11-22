"""
Сервис кеширования с Redis
"""
import json
from typing import Any, Optional, Dict, List
import redis.asyncio as redis

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Сервис кеширования с Redis"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1 час по умолчанию

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

    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кеша"""
        client = await self._get_client()
        try:
            value = await client.get(key)
            if value:
                # Попытка распарсить JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.warning("Cache get error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установка значения в кеш"""
        client = await self._get_client()
        try:
            # Сериализация значения
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            ttl_value = ttl or self.default_ttl
            result = await client.setex(key, ttl_value, serialized_value)
            return bool(result)
        except Exception as e:
            logger.warning("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Удаление значения из кеша"""
        client = await self._get_client()
        try:
            result = await client.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning("Cache delete error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        client = await self._get_client()
        try:
            result = await client.exists(key)
            return bool(result)
        except Exception as e:
            logger.warning("Cache exists error", key=key, error=str(e))
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Установка TTL для ключа"""
        client = await self._get_client()
        try:
            result = await client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.warning("Cache expire error", key=key, error=str(e))
            return False

    async def ttl(self, key: str) -> int:
        """Получение TTL ключа"""
        client = await self._get_client()
        try:
            result = await client.ttl(key)
            return result
        except Exception as e:
            logger.warning("Cache ttl error", key=key, error=str(e))
            return -1

    # Специализированные методы кеширования

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение кешированных данных пользователя"""
        key = f"user:{user_id}"
        return await self.get(key)

    async def set_user_data(self, user_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Кеширование данных пользователя"""
        key = f"user:{user_id}"
        return await self.set(key, data, ttl or 1800)  # 30 минут

    async def get_order_data(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получение кешированных данных заказа"""
        key = f"order:{order_id}"
        return await self.get(key)

    async def set_order_data(self, order_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Кеширование данных заказа"""
        key = f"order:{order_id}"
        return await self.set(key, data, ttl or 3600)  # 1 час

    async def get_customer_orders(self, customer_id: int) -> Optional[List[Dict[str, Any]]]:
        """Получение кешированного списка заказов клиента"""
        key = f"customer_orders:{customer_id}"
        return await self.get(key)

    async def set_customer_orders(self, customer_id: int, orders: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Кеширование списка заказов клиента"""
        key = f"customer_orders:{customer_id}"
        return await self.set(key, orders, ttl or 1800)  # 30 минут

    async def invalidate_user_cache(self, user_id: int) -> bool:
        """Инвалидация кеша пользователя"""
        key = f"user:{user_id}"
        return await self.delete(key)

    async def invalidate_order_cache(self, order_id: int) -> bool:
        """Инвалидация кеша заказа"""
        key = f"order:{order_id}"
        return await self.delete(key)

    async def invalidate_customer_orders_cache(self, customer_id: int) -> bool:
        """Инвалидация кеша заказов клиента"""
        key = f"customer_orders:{customer_id}"
        return await self.delete(key)

    async def get_ai_response(self, query_hash: str) -> Optional[str]:
        """Получение кешированного AI ответа"""
        key = f"ai_response:{query_hash}"
        return await self.get(key)

    async def set_ai_response(self, query_hash: str, response: str, ttl: Optional[int] = None) -> bool:
        """Кеширование AI ответа"""
        key = f"ai_response:{query_hash}"
        return await self.set(key, response, ttl or 7200)  # 2 часа

    async def clear_pattern(self, pattern: str) -> int:
        """Очистка кеша по паттерну"""
        client = await self._get_client()
        try:
            # Получаем все ключи по паттерну
            keys = await client.keys(pattern)
            if keys:
                # Удаляем ключи
                await client.delete(*keys)
                logger.info("Cache cleared by pattern", pattern=pattern, keys_deleted=len(keys))
                return len(keys)
            return 0
        except Exception as e:
            logger.warning("Cache clear pattern error", pattern=pattern, error=str(e))
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кеша"""
        client = await self._get_client()
        try:
            info = await client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_keys": await client.dbsize(),
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except Exception as e:
            logger.warning("Cache stats error", error=str(e))
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Redis"""
        try:
            client = await self._get_client()
            await client.ping()
            return {"status": "healthy", "message": "Redis is responding"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Глобальный экземпляр сервиса
cache_service = CacheService()
