"""
Сервис авторизации Avito API
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis.asyncio as redis
from pydantic import ValidationError

from ..core.config import settings
from ..schemas.avito import (
    AvitoAuthCallbackResponse,
    AvitoAuthUrlRequest,
    AvitoAuthUrlResponse,
    AvitoOAuthState,
)
from ..utils.logging import get_logger
from .avito_service import AvitoClient

logger = get_logger(__name__)


class AvitoAuthService:
    """
    Сервис для управления авторизацией Avito API
    """

    def __init__(self):
        self.redis_url = settings.redis_url or "redis://localhost:6379"
        self.redis_client = None
        self.state_ttl = 600  # 10 минут для state

    async def _get_redis(self) -> redis.Redis:
        """Получение Redis клиента"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def generate_auth_url(
        self, request: AvitoAuthUrlRequest
    ) -> AvitoAuthUrlResponse:
        """Генерация URL для авторизации"""
        try:
            # Генерируем уникальный state
            state = secrets.token_urlsafe(32)

            # Сохраняем state в Redis
            state_data = AvitoOAuthState(
                state=state,
                redirect_uri=request.redirect_uri,
                created_at=datetime.utcnow().isoformat(),
                expires_at=(
                    datetime.utcnow() + timedelta(seconds=self.state_ttl)
                ).isoformat(),
            )

            redis_client = await self._get_redis()
            await redis_client.setex(
                f"avito:oauth:state:{state}", self.state_ttl, state_data.json()
            )

            # Формируем URL авторизации
            base_url = "https://avito.ru/oauth"
            params = [
                f"response_type=code",
                f"client_id={request.client_id}",
                f"scope={'%20'.join(request.scope)}",
                f"state={state}",
            ]

            if request.redirect_uri:
                params.append(f"redirect_uri={request.redirect_uri}")

            auth_url = f"{base_url}?{'&'.join(params)}"

            logger.info(f"Generated Avito auth URL for client {request.client_id}")

            return AvitoAuthUrlResponse(auth_url=auth_url, state=state)

        except Exception as e:
            logger.error(f"Ошибка генерации URL авторизации: {e}")
            raise

    async def handle_auth_callback(
        self,
        code: str,
        state: str,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
    ) -> AvitoAuthCallbackResponse:
        """Обработка callback после авторизации"""
        try:
            # Проверяем ошибки
            if error:
                logger.warning(f"Avito auth error: {error} - {error_description}")
                return AvitoAuthCallbackResponse(
                    success=False,
                    error=(
                        f"{error}: {error_description}" if error_description else error
                    ),
                )

            # Проверяем state
            redis_client = await self._get_redis()
            state_key = f"avito:oauth:state:{state}"
            state_data_json = await redis_client.get(state_key)

            if not state_data_json:
                logger.warning(f"Invalid or expired state: {state}")
                return AvitoAuthCallbackResponse(
                    success=False, error="Invalid or expired state"
                )

            # Парсим state данные
            try:
                state_data = AvitoOAuthState.parse_raw(state_data_json)
            except ValidationError:
                logger.error(f"Invalid state data format: {state_data_json}")
                return AvitoAuthCallbackResponse(
                    success=False, error="Invalid state data"
                )

            # Проверяем срок действия state
            expires_at = datetime.fromisoformat(state_data.expires_at)
            if datetime.utcnow() > expires_at:
                logger.warning(f"Expired state: {state}")
                return AvitoAuthCallbackResponse(success=False, error="Expired state")

            # Обмениваем code на токены
            client = AvitoClient(auth_type="authorization_code")
            token_data = await client.get_token_via_authorization_code(
                code=code, redirect_uri=state_data.redirect_uri
            )

            # Удаляем использованный state
            await redis_client.delete(state_key)

            logger.info("Successfully obtained Avito tokens via authorization code")

            return AvitoAuthCallbackResponse(
                success=True,
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                expires_in=token_data.get("expires_in"),
            )

        except Exception as e:
            logger.error(f"Ошибка обработки auth callback: {e}")
            return AvitoAuthCallbackResponse(success=False, error=str(e))

    async def refresh_access_token(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> Dict[str, Any]:
        """Обновление access token через refresh token"""
        try:
            client = AvitoClient(auth_type="authorization_code")
            client.client_id = client_id
            client.client_secret = client_secret
            client.refresh_token = refresh_token

            # Обновляем токен
            await client._refresh_token_via_refresh_token()

            logger.info("Successfully refreshed Avito access token")

            return {
                "access_token": client.access_token,
                "refresh_token": client.refresh_token,
                "expires_in": int(
                    (client.token_expires_at - datetime.utcnow()).total_seconds()
                ),
            }

        except Exception as e:
            logger.error(f"Ошибка обновления токена: {e}")
            raise

    async def get_token_via_client_credentials(
        self, client_id: str, client_secret: str
    ) -> Dict[str, any]:
        """Получение токена через Client Credentials"""
        try:
            client = AvitoClient(auth_type="client_credentials")
            client.client_id = client_id
            client.client_secret = client_secret

            # Получаем токен
            await client._ensure_token()

            logger.info("Successfully obtained Avito token via client credentials")

            return {
                "access_token": client.access_token,
                "token_type": "Bearer",
                "expires_in": int(
                    (client.token_expires_at - datetime.utcnow()).total_seconds()
                ),
            }

        except Exception as e:
            logger.error(f"Ошибка получения токена через client credentials: {e}")
            raise

    async def validate_state(self, state: str) -> Optional[AvitoOAuthState]:
        """Валидация state"""
        try:
            redis_client = await self._get_redis()
            state_data_json = await redis_client.get(f"avito:oauth:state:{state}")

            if not state_data_json:
                return None

            state_data = AvitoOAuthState.parse_raw(state_data_json)

            # Проверяем срок действия
            expires_at = datetime.fromisoformat(state_data.expires_at)
            if datetime.utcnow() > expires_at:
                # Удаляем просроченный state
                await redis_client.delete(f"avito:oauth:state:{state}")
                return None

            return state_data

        except Exception as e:
            logger.error(f"Ошибка валидации state: {e}")
            return None

    async def cleanup_expired_states(self) -> int:
        """Очистка просроченных state (для cron задач)"""
        try:
            redis_client = await self._get_redis()
            # Получаем все ключи state
            keys = await redis_client.keys("avito:oauth:state:*")

            cleaned_count = 0
            for key in keys:
                try:
                    state_data_json = await redis_client.get(key)
                    if state_data_json:
                        state_data = AvitoOAuthState.parse_raw(state_data_json)
                        expires_at = datetime.fromisoformat(state_data.expires_at)
                        if datetime.utcnow() > expires_at:
                            await redis_client.delete(key)
                            cleaned_count += 1
                except Exception:
                    # Удаляем поврежденные записи
                    await redis_client.delete(key)
                    cleaned_count += 1

            logger.info(f"Cleaned {cleaned_count} expired OAuth states")
            return cleaned_count

        except Exception as e:
            logger.error(f"Ошибка очистки state: {e}")
            return 0
