"""
Сервис управления сессиями с Redis
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SessionService:
    """Сервис для управления пользовательскими сессиями в Redis"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.session_ttl = settings.access_token_expire_minutes * 60  # в секундах

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

    async def create_session(self, user_id: int, user_data: Dict[str, Any]) -> str:
        """Создание новой сессии"""
        session_id = str(uuid.uuid4())
        client = await self._get_client()

        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "ip_address": user_data.get("ip_address"),
            "user_agent": user_data.get("user_agent"),
        }

        try:
            await client.setex(
                f"session:{session_id}", self.session_ttl, json.dumps(session_data)
            )

            # Также сохраняем сессию пользователя для быстрого поиска
            await client.sadd(f"user_sessions:{user_id}", session_id)
            await client.expire(f"user_sessions:{user_id}", self.session_ttl)

            logger.info("Session created", session_id=session_id, user_id=user_id)
            return session_id

        except Exception as e:
            logger.error("Failed to create session", error=str(e), user_id=user_id)
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных сессии"""
        client = await self._get_client()

        try:
            session_data = await client.get(f"session:{session_id}")
            if not session_data:
                return None

            session = json.loads(session_data)

            # Обновляем время последней активности
            session["last_activity"] = datetime.utcnow().isoformat()
            await client.setex(
                f"session:{session_id}", self.session_ttl, json.dumps(session)
            )

            return session

        except Exception as e:
            logger.error("Failed to get session", error=str(e), session_id=session_id)
            return None

    async def update_session_activity(self, session_id: str) -> bool:
        """Обновление времени активности сессии"""
        client = await self._get_client()

        try:
            session_data = await client.get(f"session:{session_id}")
            if not session_data:
                return False

            session = json.loads(session_data)
            session["last_activity"] = datetime.utcnow().isoformat()

            await client.setex(
                f"session:{session_id}", self.session_ttl, json.dumps(session)
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to update session activity", error=str(e), session_id=session_id
            )
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Удаление сессии"""
        client = await self._get_client()

        try:
            session_data = await client.get(f"session:{session_id}")
            if not session_data:
                return False

            session = json.loads(session_data)
            user_id = session["user_id"]

            # Удаляем сессию
            await client.delete(f"session:{session_id}")

            # Удаляем из списка сессий пользователя
            await client.srem(f"user_sessions:{user_id}", session_id)

            logger.info("Session deleted", session_id=session_id, user_id=user_id)
            return True

        except Exception as e:
            logger.error(
                "Failed to delete session", error=str(e), session_id=session_id
            )
            return False

    async def delete_user_sessions(self, user_id: int) -> int:
        """Удаление всех сессий пользователя"""
        client = await self._get_client()

        try:
            # Получаем все сессии пользователя
            session_ids = await client.smembers(f"user_sessions:{user_id}")
            if not session_ids:
                return 0

            # Удаляем все сессии
            session_keys = [f"session:{sid}" for sid in session_ids]
            if session_keys:
                await client.delete(*session_keys)

            # Удаляем множество сессий пользователя
            await client.delete(f"user_sessions:{user_id}")

            logger.info(
                "User sessions deleted", user_id=user_id, count=len(session_ids)
            )
            return len(session_ids)

        except Exception as e:
            logger.error(
                "Failed to delete user sessions", error=str(e), user_id=user_id
            )
            return 0

    async def get_active_sessions_count(self, user_id: int) -> int:
        """Получение количества активных сессий пользователя"""
        async with session_service:
            client = await self._get_client()

            try:
                count = await client.scard(f"user_sessions:{user_id}")
                return count or 0

            except Exception as e:
                logger.error(
                    "Failed to get active sessions count", error=str(e), user_id=user_id
                )
                return 0

    async def cleanup_expired_sessions(self) -> int:
        """Очистка истекших сессий (вызывается периодически)"""
        # Redis автоматически удаляет ключи с TTL, но можем реализовать дополнительную логику
        logger.info("Session cleanup completed")
        return 0


# Глобальный экземпляр сервиса
session_service = SessionService()
