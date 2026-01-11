#!/usr/bin/env python3
"""
Скрипт для тестирования Telegram webhook
"""
import asyncio

import httpx


async def test_webhook():
    """Тестирование webhook с данными из getUpdates"""

    # Данные из getUpdates (сообщение "Добрый день")
    webhook_data = {
        "update_id": 880965053,
        "message": {
            "message_id": 18,
            "from": {
                "id": 339795159,
                "is_bot": False,
                "first_name": "ам",
                "last_name": "ням",
                "username": "Chillcreative",
                "language_code": "ru",
            },
            "chat": {
                "id": 339795159,
                "first_name": "ам",
                "last_name": "ням",
                "username": "Chillcreative",
                "type": "private",
            },
            "date": 1763112440,
            "text": "Добрый день",
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/telegram/webhook",
                json=webhook_data,
                headers={"Content-Type": "application/json"},
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_webhook())
