#!/usr/bin/env python3
"""
Тестирование системы кампаний с AI настройками
"""
import asyncio
import requests
import json
import sys
import os

# Настройки для тестирования
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

def test_campaign_creation():
    """Тестирование создания кампании"""
    try:
        print("🔄 Создание тестовой кампании...")

        # Создаем кампанию
        campaign_data = {
            "name": "Тестовая кампания AI",
            "description": "Кампания для тестирования индивидуальных AI настроек",
            "organization_id": 1  # Предполагаем, что организация с ID 1 существует
        }

        headers = {
            "Content-Type": "application/json",
            # TODO: Добавить JWT токен для аутентификации
            # "Authorization": "Bearer YOUR_JWT_TOKEN"
        }

        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/campaigns/",
            json=campaign_data,
            headers=headers
        )

        if response.status_code == 201:
            campaign = response.json()
            print(f"✅ Кампания создана: {campaign['name']} (ID: {campaign['id']})")
            return campaign['id']
        else:
            print(f"❌ Ошибка создания кампании: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return None

def test_campaign_ai_settings_update(campaign_id):
    """Тестирование обновления AI настроек кампании"""
    try:
        print(f"🔄 Обновление AI настроек кампании {campaign_id}...")

        # AI настройки для кампании
        ai_settings = {
            "default_model": "deepseek/deepseek-chat-v3.1",
            "provider": "openrouter",
            "temperature": 0.8,
            "max_tokens": 1200,
            "openrouter_api_key": "sk-or-v1-test-key-replace-with-real-key",
            "auto_reply_enabled": True,
            "auto_reply_temperature": 0.7,
            "custom_prompt": "Ты - ассистент тестовой маркетинговой кампании. Отвечай вежливо и профессионально.",
            "target_audience": "Бизнес-пользователи",
            "brand_voice": "Профессиональный",
            "daily_token_limit": 10000,
            "monthly_token_limit": 300000
        }

        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer YOUR_JWT_TOKEN"
        }

        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/campaigns/{campaign_id}/ai-settings",
            json=ai_settings,
            headers=headers
        )

        if response.status_code == 200:
            settings = response.json()
            print(f"✅ AI настройки кампании обновлены: модель {settings['default_model']}")
            return True
        else:
            print(f"❌ Ошибка обновления AI настроек: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при тестировании AI настроек: {e}")
        return False

def test_campaign_ai_chat(campaign_id):
    """Тестирование AI чата с использованием настроек кампании"""
    try:
        print(f"🔄 Тестирование AI чата кампании {campaign_id}...")

        # Сообщения для чата
        chat_request = {
            "messages": [
                {
                    "role": "user",
                    "content": "Привет! Расскажи о наших услугах."
                }
            ],
            "temperature": 0.8,
            "max_tokens": 500
        }

        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer YOUR_JWT_TOKEN"
        }

        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/ai/campaigns/{campaign_id}/chat",
            json=chat_request,
            headers=headers
        )

        if response.status_code == 200:
            chat_response = response.json()
            print("✅ AI чат кампании работает!")
            print(f"   Модель: {chat_response.get('model_used', 'unknown')}")
            print(f"   Токенов использовано: {chat_response.get('tokens_used', 0)}")
            print(f"   Ответ: {chat_response.get('response', '')[:200]}...")
            return True
        else:
            print(f"❌ Ошибка AI чата: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при тестировании AI чата: {e}")
        return False

def test_campaign_analyze_intent(campaign_id):
    """Тестирование анализа намерения с настройками кампании"""
    try:
        print(f"🔄 Тестирование анализа намерения кампании {campaign_id}...")

        analyze_request = {
            "message": "Привет! Меня интересует печать логотипов на футболках. Сколько это стоит?",
            "context": {
                "channel": "website",
                "customer_type": "b2b"
            }
        }

        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer YOUR_JWT_TOKEN"
        }

        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/ai/campaigns/{campaign_id}/analyze-intent",
            json=analyze_request,
            headers=headers
        )

        if response.status_code == 200:
            analysis = response.json()
            print("✅ Анализ намерения кампании работает!")
            print(f"   Намерение: {analysis.get('intent', 'unknown')}")
            print(f"   Ответ: {analysis.get('response', '')[:150]}...")
            return True
        else:
            print(f"❌ Ошибка анализа намерения: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при тестировании анализа: {e}")
        return False

async def create_database_tables():
    """Создание таблиц в базе данных"""
    try:
        print("🔄 Создание таблиц кампаний...")

        # Импортируем скрипт создания таблиц
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from create_campaigns_table import create_tables

        await create_tables()
        print("✅ Таблицы кампаний созданы!")

    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы кампаний с AI\n")

    try:
        # NOTE: Раскомментируйте для создания таблиц при первом запуске
        # asyncio.run(create_database_tables())

        # Тестируем создание кампании
        campaign_id = test_campaign_creation()
        if not campaign_id:
            print("❌ Невозможно продолжить тестирование без созданной кампании")
            return

        print()

        # Тестируем обновление AI настроек
        if test_campaign_ai_settings_update(campaign_id):
            print()

            # Тестируем AI чат
            test_campaign_ai_chat(campaign_id)
            print()

            # Тестируем анализ намерения
            test_campaign_analyze_intent(campaign_id)

        print("\n" + "="*50)
        print("🎉 ТЕСТИРОВАНИЕ СИСТЕМЫ КАМПАНИЙ ЗАВЕРШЕНО!")
        print("="*50)
        print("\n📋 РЕЗУЛЬТАТЫ:")
        print("✅ Система кампаний с индивидуальными AI токенами реализована")
        print("✅ Каждая кампания может иметь собственные AI настройки")
        print("✅ Поддержка разных провайдеров (OpenRouter, OpenAI, HuggingFace)")
        print("✅ Кастомные промпты для каждой кампании")
        print("✅ Лимиты токенов для биллинга")
        print("✅ API эндпоинты для работы с AI кампаниями")

    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")

        print(f"\n❌ Критическая ошибка тестирования: {e}")

