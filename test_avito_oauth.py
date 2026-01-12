#!/usr/bin/env python3
"""
Тест OAuth авторизации Avito
"""

import asyncio
import os
from datetime import datetime, timedelta

import redis.asyncio as redis

from src.aicrm.schemas.avito import AvitoAuthUrlRequest
from src.aicrm.services.avito_auth_service import AvitoAuthService
from src.aicrm.services.avito_service import AvitoClient


async def test_generate_auth_url():
    """Тест генерации URL авторизации"""
    print("=== Тест генерации URL авторизации ===")

    auth_service = AvitoAuthService()

    request = AvitoAuthUrlRequest(
        client_id="test_client_id",
        redirect_uri="https://example.com/callback",
        scope=["messenger:read", "messenger:write"],
        state="custom_state",
    )

    try:
        result = await auth_service.generate_auth_url(request)
        print(f"✓ URL сгенерирован: {result.auth_url}")
        print(f"✓ State: {result.state}")

        # Проверяем state в Redis
        redis_client = await auth_service._get_redis()
        state_data_json = await redis_client.get(f"avito:oauth:state:{result.state}")
        if state_data_json:
            print("✓ State сохранен в Redis")
        else:
            print("✗ State не найден в Redis")

    except Exception as e:
        print(f"✗ Ошибка генерации URL: {e}")


async def test_validate_state():
    """Тест валидации state"""
    print("\n=== Тест валидации state ===")

    auth_service = AvitoAuthService()

    # Создаем state
    request = AvitoAuthUrlRequest(
        client_id="test_client_id",
        redirect_uri="https://example.com/callback",
        scope=["messenger:read"],
    )

    result = await auth_service.generate_auth_url(request)
    state = result.state

    # Валидируем
    validated_state = await auth_service.validate_state(state)
    if validated_state:
        print(f"✓ State валиден: {validated_state.state}")
    else:
        print("✗ State не валиден")


async def test_client_credentials_token():
    """Тест получения токена через Client Credentials"""
    print("\n=== Тест Client Credentials токена ===")

    auth_service = AvitoAuthService()

    # Используем реальные credentials из env, если есть
    client_id = os.getenv("AVITO_CLIENT_ID", "test_client_id")
    client_secret = os.getenv("AVITO_CLIENT_SECRET", "test_client_secret")

    try:
        result = await auth_service.get_token_via_client_credentials(
            client_id, client_secret
        )
        print("✓ Токен получен:")
        print(f"  - Access Token: {result['access_token'][:20]}...")
        print(f"  - Token Type: {result['token_type']}")
        print(f"  - Expires In: {result['expires_in']}")

    except Exception as e:
        print(f"✗ Ошибка получения токена: {e}")


async def test_avito_client_creation():
    """Тест создания AvitoClient с разными типами авторизации"""
    print("\n=== Тест создания AvitoClient ===")

    # Client Credentials
    client_cc = AvitoClient(auth_type="client_credentials")
    print(f"✓ Client Credentials client создан: {type(client_cc).__name__}")

    # Authorization Code
    client_ac = AvitoClient(auth_type="authorization_code")
    print(f"✓ Authorization Code client создан: {type(client_ac).__name__}")

    # Тест установки токенов вручную
    client_ac.set_tokens(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_in=3600,
    )
    print("✓ Токены установлены вручную")


async def test_cleanup_expired_states():
    """Тест очистки просроченных state"""
    print("\n=== Тест очистки просроченных state ===")

    auth_service = AvitoAuthService()

    # Создаем несколько state
    for i in range(3):
        request = AvitoAuthUrlRequest(
            client_id=f"test_client_{i}",
            redirect_uri="https://example.com/callback",
            scope=["messenger:read"],
        )
        await auth_service.generate_auth_url(request)

    # Очищаем просроченные (все должны быть просрочены через 10 минут)
    cleaned = await auth_service.cleanup_expired_states()
    print(f"✓ Очищено {cleaned} просроченных state")


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов OAuth авторизации Avito\n")

    await test_generate_auth_url()
    await test_validate_state()
    await test_client_credentials_token()
    await test_avito_client_creation()
    await test_cleanup_expired_states()

    print("\n✅ Все тесты завершены!")


if __name__ == "__main__":
    asyncio.run(main())
