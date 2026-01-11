#!/usr/bin/env python3
"""
Создание таблиц для кампаний с AI настройками
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from aicrm.core.database import engine
from aicrm.main import create_application
from aicrm.models.campaign import Campaign, CampaignAISettings

app = create_application()


async def create_tables():
    """Создание таблиц в базе данных"""
    try:
        # Создаем таблицы асинхронно
        async with engine.begin() as conn:
            await conn.run_sync(Campaign.metadata.create_all)
            await conn.run_sync(CampaignAISettings.metadata.create_all)

        print("✅ Таблицы campaigns и campaign_ai_settings успешно созданы!")

    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_tables())
