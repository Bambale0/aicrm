"""
Сервис для работы с настройками AI
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.ai_settings import AISettings


class AISettingsService:
    """Сервис для управления настройками AI"""

    @staticmethod
    async def get_settings(db: AsyncSession) -> Optional[AISettings]:
        """Получить текущие настройки AI"""
        result = await db.execute(select(AISettings).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_default_settings(db: AsyncSession) -> AISettings:
        """Создать настройки по умолчанию"""
        settings = AISettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def get_or_create_settings(db: AsyncSession) -> AISettings:
        """Получить настройки или создать по умолчанию"""
        settings = await AISettingsService.get_settings(db)
        if not settings:
            settings = await AISettingsService.create_default_settings(db)
        return settings

    @staticmethod
    async def update_settings(
        db: AsyncSession,
        settings_id: int,
        updates: Dict[str, Any]
    ) -> Optional[AISettings]:
        """Обновить настройки AI"""
        # Фильтруем только допустимые поля
        allowed_fields = {
            'default_model', 'temperature', 'max_tokens',
            'openrouter_api_key', 'openai_api_key', 'huggingface_api_key',
            'provider', 'auto_reply_enabled', 'auto_reply_temperature',
            'auto_reply_max_tokens', 'rate_limit_per_minute',
            'cache_enabled', 'log_level', 'fallback_model', 'premium_model'
        }

        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return None

        await db.execute(
            update(AISettings)
            .where(AISettings.id == settings_id)
            .values(**filtered_updates)
        )
        await db.commit()

        # Возвращаем обновленные настройки
        result = await db.execute(select(AISettings).where(AISettings.id == settings_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_api_key(db: AsyncSession, provider: str) -> Optional[str]:
        """Получить API ключ для указанного провайдера"""
        settings = await AISettingsService.get_settings(db)
        if not settings:
            return None

        provider_key_map = {
            'openrouter': settings.openrouter_api_key,
            'openai': settings.openai_api_key,
            'huggingface': settings.huggingface_api_key
        }

        return provider_key_map.get(provider)

    @staticmethod
    async def get_current_model_config(db: AsyncSession) -> Dict[str, Any]:
        """Получить конфигурацию текущей модели"""
        settings = await AISettingsService.get_settings(db)
        if not settings:
            # Возвращаем настройки по умолчанию
            return {
                'model': 'deepseek/deepseek-chat-v3.1',
                'temperature': 0.7,
                'max_tokens': 1000,
                'provider': 'openrouter'
            }

        return {
            'model': settings.default_model,
            'temperature': settings.temperature,
            'max_tokens': settings.max_tokens,
            'provider': settings.provider
        }

    @staticmethod
    async def get_auto_reply_config(db: AsyncSession) -> Dict[str, Any]:
        """Получить конфигурацию для автоответов"""
        settings = await AISettingsService.get_settings(db)
        if not settings:
            return {
                'enabled': True,
                'temperature': 0.5,
                'max_tokens': 500
            }

        return {
            'enabled': settings.auto_reply_enabled,
            'temperature': settings.auto_reply_temperature,
            'max_tokens': settings.auto_reply_max_tokens
        }

    @staticmethod
    async def is_cache_enabled(db: AsyncSession) -> bool:
        """Проверить, включено ли кеширование"""
        settings = await AISettingsService.get_settings(db)
        return settings.cache_enabled if settings else True

    @staticmethod
    async def get_rate_limit(db: AsyncSession) -> int:
        """Получить лимит запросов в минуту"""
        settings = await AISettingsService.get_settings(db)
        return settings.rate_limit_per_minute if settings else 60
