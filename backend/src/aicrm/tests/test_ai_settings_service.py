"""
Тесты для AISettingsService
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ..services.ai_settings_service import AISettingsService
from ..models.ai_settings import AISettings


class TestAISettingsService:
    """Тесты для сервиса настроек AI"""

    @pytest.fixture
    def db_session(self):
        """Мок для сессии базы данных"""
        session = MagicMock()
        session.query = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def ai_settings_service(self):
        """Фикстура для AISettingsService"""
        return AISettingsService

    @pytest.fixture
    def sample_ai_settings(self):
        """Пример настроек AI"""
        settings = MagicMock(spec=AISettings)
        settings.id = 1
        settings.user_id = 100
        settings.provider = "openai"
        settings.model = "gpt-4"
        settings.api_key = "sk-test123"
        settings.temperature = 0.7
        settings.max_tokens = 2000
        settings.system_prompt = "You are a helpful assistant"
        settings.is_active = True
        settings.created_at = datetime(2023, 1, 1, 10, 0, 0)
        settings.updated_at = datetime(2023, 1, 1, 10, 0, 0)
        return settings

    @pytest.mark.asyncio
    async def test_get_user_ai_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного получения настроек AI пользователя"""
        # Мокаем запрос к БД
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        result = await ai_settings_service.get_user_ai_settings(100)

        assert result is not None
        assert result["id"] == 1
        assert result["user_id"] == 100
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4"
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_user_ai_settings_not_found(self, ai_settings_service):
        """Тест получения настроек AI для пользователя без настроек"""
        # Мокаем запрос к БД (ничего не найдено)
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = None

        result = await ai_settings_service.get_user_ai_settings(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_ai_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного создания настроек AI"""
        # Мокаем создание объекта
        ai_settings_service.db.add.return_value = None
        ai_settings_service.db.refresh.return_value = None

        # Мокаем созданный объект
        created_settings = MagicMock(spec=AISettings)
        created_settings.id = 2
        created_settings.user_id = 200
        created_settings.provider = "anthropic"
        created_settings.model = "claude-3"
        created_settings.is_active = True
        ai_settings_service.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 2)

        settings_data = {
            "user_id": 200,
            "provider": "anthropic",
            "model": "claude-3",
            "api_key": "sk-ant-test456",
            "temperature": 0.8,
            "max_tokens": 3000,
            "system_prompt": "You are Claude, a helpful AI assistant"
        }

        result = await ai_settings_service.create_ai_settings(settings_data)

        assert result is not None
        assert result["user_id"] == 200
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-3"
        assert result["is_active"] is True

        # Проверяем что объект добавлен в БД
        ai_settings_service.db.add.assert_called_once()
        ai_settings_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ai_settings_duplicate_user(self, ai_settings_service, sample_ai_settings):
        """Тест создания настроек AI для пользователя, у которого они уже есть"""
        # Мокаем проверку существования настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        settings_data = {
            "user_id": 100,  # Тот же пользователь
            "provider": "anthropic",
            "model": "claude-3"
        }

        with pytest.raises(ValueError, match="AI settings already exist for this user"):
            await ai_settings_service.create_ai_settings(settings_data)

    @pytest.mark.asyncio
    async def test_update_ai_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного обновления настроек AI"""
        # Мокаем получение существующих настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        update_data = {
            "model": "gpt-4-turbo",
            "temperature": 0.9,
            "max_tokens": 4000,
            "system_prompt": "Updated system prompt"
        }

        result = await ai_settings_service.update_ai_settings(100, update_data)

        assert result is not None
        assert result["model"] == "gpt-4-turbo"
        assert result["temperature"] == 0.9
        assert result["max_tokens"] == 4000

        # Проверяем что изменения сохранены
        ai_settings_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_ai_settings_not_found(self, ai_settings_service):
        """Тест обновления настроек AI для несуществующего пользователя"""
        # Мокаем отсутствие настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = None

        update_data = {"model": "gpt-4-turbo"}

        with pytest.raises(ValueError, match="AI settings not found for user"):
            await ai_settings_service.update_ai_settings(999, update_data)

    @pytest.mark.asyncio
    async def test_delete_ai_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного удаления настроек AI"""
        # Мокаем получение настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        result = await ai_settings_service.delete_ai_settings(100)

        assert result is True

        # Проверяем что объект удален из БД
        ai_settings_service.db.delete.assert_called_once_with(sample_ai_settings)
        ai_settings_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_ai_settings_not_found(self, ai_settings_service):
        """Тест удаления настроек AI для несуществующего пользователя"""
        # Мокаем отсутствие настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = None

        result = await ai_settings_service.delete_ai_settings(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_toggle_ai_settings_active(self, ai_settings_service, sample_ai_settings):
        """Тест переключения активности настроек AI"""
        # Мокаем получение настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        # Сначала настройки активны
        assert sample_ai_settings.is_active is True

        # Деактивируем
        result = await ai_settings_service.toggle_ai_settings(100, False)

        assert result is not None
        assert result["is_active"] is False
        ai_settings_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_ai_settings(self, ai_settings_service, sample_ai_settings):
        """Тест получения активных настроек AI"""
        # Мокаем запрос активных настроек
        ai_settings_service.db.query.return_value.filter.return_value.all.return_value = [sample_ai_settings]

        result = await ai_settings_service.get_active_ai_settings()

        assert len(result) == 1
        assert result[0]["user_id"] == 100
        assert result[0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_validate_ai_settings_valid_openai(self, ai_settings_service):
        """Тест валидации корректных настроек OpenAI"""
        settings_data = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-test123456789",
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_ai_settings_valid_anthropic(self, ai_settings_service):
        """Тест валидации корректных настроек Anthropic"""
        settings_data = {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "api_key": "sk-ant-test123456789",
            "temperature": 0.8,
            "max_tokens": 3000
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_ai_settings_invalid_provider(self, ai_settings_service):
        """Тест валидации настроек с некорректным провайдером"""
        settings_data = {
            "provider": "invalid_provider",
            "model": "some-model",
            "api_key": "test-key"
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is False
        assert "Unsupported AI provider" in str(result["errors"])

    @pytest.mark.asyncio
    async def test_validate_ai_settings_missing_api_key(self, ai_settings_service):
        """Тест валидации настроек без API ключа"""
        settings_data = {
            "provider": "openai",
            "model": "gpt-4"
            # Отсутствует api_key
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is False
        assert any("API key is required" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_ai_settings_invalid_temperature(self, ai_settings_service):
        """Тест валидации настроек с некорректной температурой"""
        settings_data = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-test123",
            "temperature": 2.5  # Должно быть 0-2
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is False
        assert any("Temperature must be between 0 and 2" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_ai_settings_invalid_max_tokens(self, ai_settings_service):
        """Тест валидации настроек с некорректным максимальным количеством токенов"""
        settings_data = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-test123",
            "max_tokens": 100000  # Слишком много для GPT-4
        }

        result = await ai_settings_service.validate_ai_settings(settings_data)

        assert result["valid"] is False
        assert any("Max tokens exceeds model limit" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_get_default_settings_by_provider(self, ai_settings_service):
        """Тест получения настроек по умолчанию для провайдера"""
        # OpenAI
        defaults = ai_settings_service.get_default_settings("openai")
        assert defaults["provider"] == "openai"
        assert defaults["model"] == "gpt-3.5-turbo"
        assert defaults["temperature"] == 0.7
        assert defaults["max_tokens"] == 2000

        # Anthropic
        defaults = ai_settings_service.get_default_settings("anthropic")
        assert defaults["provider"] == "anthropic"
        assert defaults["model"] == "claude-3-haiku-20240307"
        assert defaults["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_get_available_models_by_provider(self, ai_settings_service):
        """Тест получения доступных моделей для провайдера"""
        # OpenAI
        models = ai_settings_service.get_available_models("openai")
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models

        # Anthropic
        models = ai_settings_service.get_available_models("anthropic")
        assert "claude-3-opus-20240229" in models
        assert "claude-3-sonnet-20240229" in models

    @pytest.mark.asyncio
    async def test_backup_user_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного резервного копирования настроек"""
        # Мокаем получение настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        result = await ai_settings_service.backup_user_settings(100)

        assert result is not None
        assert result["user_id"] == 100
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4"
        assert "backup_timestamp" in result

    @pytest.mark.asyncio
    async def test_backup_user_settings_not_found(self, ai_settings_service):
        """Тест резервного копирования для пользователя без настроек"""
        # Мокаем отсутствие настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = None

        result = await ai_settings_service.backup_user_settings(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_restore_user_settings_success(self, ai_settings_service, sample_ai_settings):
        """Тест успешного восстановления настроек из резервной копии"""
        backup_data = {
            "user_id": 100,
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-backup123",
            "temperature": 0.8,
            "max_tokens": 2500,
            "backup_timestamp": datetime.now().isoformat()
        }

        # Мокаем получение существующих настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        result = await ai_settings_service.restore_user_settings(100, backup_data)

        assert result is not None
        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.8
        assert result["max_tokens"] == 2500

        # Проверяем что изменения сохранены
        ai_settings_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_user_settings_no_existing(self, ai_settings_service):
        """Тест восстановления настроек для пользователя без существующих настроек"""
        backup_data = {
            "user_id": 999,
            "provider": "anthropic",
            "model": "claude-3",
            "api_key": "sk-restore456",
            "backup_timestamp": datetime.now().isoformat()
        }

        # Мокаем отсутствие настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = None

        result = await ai_settings_service.restore_user_settings(999, backup_data)

        assert result is not None
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-3"

        # Проверяем что новые настройки созданы
        ai_settings_service.db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_settings_summary(self, ai_settings_service, sample_ai_settings):
        """Тест получения сводки настроек пользователя"""
        # Мокаем получение настроек
        ai_settings_service.db.query.return_value.filter.return_value.first.return_value = sample_ai_settings

        summary = await ai_settings_service.get_user_settings_summary(100)

        assert summary is not None
        assert summary["user_id"] == 100
        assert summary["provider"] == "openai"
        assert summary["model"] == "gpt-4"
        assert summary["is_active"] is True
        assert "last_updated" in summary

    @pytest.mark.asyncio
    async def test_bulk_update_settings_success(self, ai_settings_service):
        """Тест массового обновления настроек"""
        settings_list = [
            {"user_id": 1, "model": "gpt-4"},
            {"user_id": 2, "temperature": 0.9},
            {"user_id": 3, "max_tokens": 3000}
        ]

        # Мокаем получение настроек для каждого пользователя
        mock_settings = []
        for i, settings_data in enumerate(settings_list):
            mock_setting = MagicMock(spec=AISettings)
            mock_setting.user_id = settings_data["user_id"]
            mock_setting.model = "gpt-3.5-turbo"  # Исходная модель
            mock_setting.temperature = 0.7
            mock_setting.max_tokens = 2000
            mock_settings.append(mock_setting)

        # Настраиваем последовательные возвраты
        ai_settings_service.db.query.return_value.filter.return_value.first.side_effect = mock_settings

        results = await ai_settings_service.bulk_update_settings(settings_list)

        assert len(results) == 3
        assert all(r["success"] for r in results)

        # Проверяем что commit вызван для каждого обновления
        assert ai_settings_service.db.commit.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_update_settings_partial_failure(self, ai_settings_service):
        """Тест массового обновления с частичными неудачами"""
        settings_list = [
            {"user_id": 1, "model": "gpt-4"},
            {"user_id": 999, "temperature": 0.9},  # Пользователь не найден
            {"user_id": 3, "max_tokens": 3000}
        ]

        # Мокаем: первый и третий пользователи найдены, второй - нет
        mock_setting1 = MagicMock(spec=AISettings)
        mock_setting1.user_id = 1

        mock_setting3 = MagicMock(spec=AISettings)
        mock_setting3.user_id = 3

        ai_settings_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_setting1,  # user 1
            None,           # user 999 (не найден)
            mock_setting3   # user 3
        ]

        results = await ai_settings_service.bulk_update_settings(settings_list)

        assert len(results) == 3
        assert results[0]["success"] is True   # user 1 - успех
        assert results[1]["success"] is False  # user 999 - неудача
        assert results[2]["success"] is True   # user 3 - успех

    def test_get_provider_limits(self, ai_settings_service):
        """Тест получения лимитов провайдера"""
        # OpenAI
        limits = ai_settings_service._get_provider_limits("openai")
        assert limits["max_tokens"] == 128000  # GPT-4 Turbo
        assert limits["max_temperature"] == 2.0

        # Anthropic
        limits = ai_settings_service._get_provider_limits("anthropic")
        assert limits["max_tokens"] == 200000  # Claude 3
        assert limits["max_temperature"] == 1.0

    def test_sanitize_api_key(self, ai_settings_service):
        """Тест очистки API ключа"""
        # Нормальный ключ
        clean_key = ai_settings_service._sanitize_api_key("sk-test123456789")
        assert clean_key == "sk-test123456789"

        # Ключ с пробелами
        clean_key = ai_settings_service._sanitize_api_key("  sk-test123456789  ")
        assert clean_key == "sk-test123456789"

        # Пустой ключ
        clean_key = ai_settings_service._sanitize_api_key("")
        assert clean_key == ""

        # None
        clean_key = ai_settings_service._sanitize_api_key(None)
        assert clean_key == ""

    def test_format_settings_for_display(self, ai_settings_service, sample_ai_settings):
        """Тест форматирования настроек для отображения"""
        formatted = ai_settings_service._format_settings_for_display(sample_ai_settings)

        assert formatted["id"] == 1
        assert formatted["user_id"] == 100
        assert formatted["provider"] == "openai"
        assert formatted["model"] == "gpt-4"
        assert formatted["is_active"] is True
        # API ключ не должен отображаться
        assert "api_key" not in formatted or formatted["api_key"] == "***"

    def test_calculate_settings_hash(self, ai_settings_service):
        """Тест вычисления хэша настроек"""
        settings_data = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }

        hash1 = ai_settings_service._calculate_settings_hash(settings_data)
        hash2 = ai_settings_service._calculate_settings_hash(settings_data)

        # Хэши должны быть одинаковыми для одинаковых данных
        assert hash1 == hash2

        # Хэши должны быть разными для разных данных
        settings_data["temperature"] = 0.8
        hash3 = ai_settings_service._calculate_settings_hash(settings_data)
        assert hash1 != hash3

    def test_is_settings_changed(self, ai_settings_service, sample_ai_settings):
        """Тест проверки изменения настроек"""
        # Без изменений
        assert not ai_settings_service._is_settings_changed(sample_ai_settings, {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        })

        # С изменениями
        assert ai_settings_service._is_settings_changed(sample_ai_settings, {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "max_tokens": 2000
        })

    def test_get_settings_audit_trail(self, ai_settings_service):
        """Тест получения журнала аудита настроек"""
        # Мокаем запрос к audit логу
        mock_audit_entries = [
            {"timestamp": datetime(2023, 1, 1, 10, 0), "action": "created", "user_id": 100},
            {"timestamp": datetime(2023, 1, 2, 11, 0), "action": "updated", "user_id": 100}
        ]

        # Предполагаем что есть отдельная таблица аудита
        with patch.object(ai_settings_service, '_get_audit_entries', return_value=mock_audit_entries):
            audit_trail = ai_settings_service.get_settings_audit_trail(100)

            assert len(audit_trail) == 2
            assert audit_trail[0]["action"] == "created"
            assert audit_trail[1]["action"] == "updated"
