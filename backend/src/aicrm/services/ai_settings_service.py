"""
Сервис для работы с настройками AI
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from ..models.ai_settings import AISettings


class AISettingsService:
    """Сервис для управления настройками AI"""

    @staticmethod
    def get_settings(db: Session) -> Optional[AISettings]:
        """Получить текущие настройки AI"""
        result = db.execute(select(AISettings).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    def create_default_settings(db: Session) -> AISettings:
        """Создать настройки по умолчанию"""
        settings = AISettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def get_or_create_settings(db: Session) -> AISettings:
        """Получить настройки или создать по умолчанию"""
        settings = AISettingsService.get_settings(db)
        if not settings:
            settings = AISettingsService.create_default_settings(db)
        return settings

    @staticmethod
    def update_settings(
        db: Session,
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

        db.execute(
            update(AISettings)
            .where(AISettings.id == settings_id)
            .values(**filtered_updates)
        )
        db.commit()

        # Возвращаем обновленные настройки
        result = db.execute(select(AISettings).where(AISettings.id == settings_id))
        return result.scalar_one_or_none()

    @staticmethod
    def get_api_key(db: Session, provider: str) -> Optional[str]:
        """Получить API ключ для указанного провайдера"""
        settings = AISettingsService.get_settings(db)
        if not settings:
            return None

        provider_key_map = {
            'openrouter': getattr(settings, 'openrouter_api_key', None),
            'openai': getattr(settings, 'openai_api_key', None),
            'huggingface': getattr(settings, 'huggingface_api_key', None)
        }

        return provider_key_map.get(provider)

    @staticmethod
    def get_current_model_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию текущей модели"""
        settings = AISettingsService.get_settings(db)
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
    def get_auto_reply_config(db: Session) -> Dict[str, Any]:
        """Получить конфигурацию для автоответов"""
        settings = AISettingsService.get_settings(db)
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
    def is_cache_enabled(db: Session) -> bool:
        """Проверить, включено ли кеширование"""
        settings = AISettingsService.get_settings(db)
        return bool(getattr(settings, 'cache_enabled', True)) if settings else True

    @staticmethod
    def get_rate_limit(db: Session) -> int:
        """Получить лимит запросов в минуту"""
        settings = AISettingsService.get_settings(db)
        return int(getattr(settings, 'rate_limit_per_minute', 60)) if settings else 60

    @staticmethod
    def save_ai_settings(db: Session, settings_data: Dict[str, Any]) -> AISettings:
        """
        Сохранить настройки AI (создать или обновить)

        Args:
            db: Сессия базы данных
            settings_data: Данные настроек

        Returns:
            AISettings: Сохраненные настройки
        """
        # Получаем существующие настройки
        existing_settings = AISettingsService.get_settings(db)

        if existing_settings:
            # Обновляем существующие
            updated_settings = AISettingsService.update_settings(
                db, existing_settings.id, settings_data
            )
            if updated_settings:
                return updated_settings
            else:
                # Если обновление не удалось (нет разрешенных полей), возвращаем существующие
                return existing_settings
        else:
            # Создаем новые настройки
            new_settings = AISettings()

            # Фильтруем только допустимые поля
            allowed_fields = {
                'default_model', 'temperature', 'max_tokens',
                'openrouter_api_key', 'openai_api_key', 'huggingface_api_key',
                'provider', 'auto_reply_enabled', 'auto_reply_temperature',
                'auto_reply_max_tokens', 'rate_limit_per_minute',
                'cache_enabled', 'log_level', 'fallback_model', 'premium_model'
            }

            # Применяем значения
            for field, value in settings_data.items():
                if field in allowed_fields and hasattr(new_settings, field):
                    setattr(new_settings, field, value)

            db.add(new_settings)
            db.commit()
            db.refresh(new_settings)
            return new_settings

    @staticmethod
    def validate_api_keys(db: Session) -> Dict[str, bool]:
        """
        Проверить валидность API ключей

        Returns:
            Dict с результатами проверки для каждого провайдера
        """
        settings = AISettingsService.get_settings(db)
        if not settings:
            return {
                'openrouter': False,
                'openai': False,
                'huggingface': False
            }

        results = {}
        providers = ['openrouter', 'openai', 'huggingface']

        for provider in providers:
            api_key = AISettingsService.get_api_key(db, provider)
            # Простая проверка - ключ существует и не пустой
            results[provider] = bool(api_key and api_key.strip())

        return results

    @staticmethod
    def get_model_list(db: Session) -> Dict[str, Any]:
        """
        Получить список доступных моделей по провайдерам

        Returns:
            Dict с моделями для каждого провайдера
        """
        return {
            'openrouter': [
                'anthropic/claude-3-haiku',
                'anthropic/claude-3-sonnet',
                'openai/gpt-4o-mini',
                'openai/gpt-4o',
                'deepseek/deepseek-chat-v3.1',
                'google/gemini-pro',
                'meta-llama/llama-3.1-8b-instruct',
                'meta-llama/llama-3.1-70b-instruct'
            ],
            'openai': [
                'gpt-4o-mini',
                'gpt-4o',
                'gpt-4-turbo',
                'gpt-3.5-turbo'
            ],
            'huggingface': [
                'microsoft/DialoGPT-medium',
                'facebook/blenderbot-400M-distill',
                'google/flan-t5-base'
            ]
        }

    @staticmethod
    def reset_to_defaults(db: Session) -> AISettings:
        """
        Сбросить настройки к значениям по умолчанию

        Returns:
            AISettings: Настройки по умолчанию
        """
        default_settings = {
            'default_model': 'deepseek/deepseek-chat-v3.1',
            'temperature': 0.7,
            'max_tokens': 1000,
            'provider': 'openrouter',
            'auto_reply_enabled': True,
            'auto_reply_temperature': 0.5,
            'auto_reply_max_tokens': 500,
            'rate_limit_per_minute': 60,
            'cache_enabled': True,
            'log_level': 'INFO',
            'fallback_model': 'openai/gpt-3.5-turbo'
        }

        return AISettingsService.save_ai_settings(db, default_settings)
