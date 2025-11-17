import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import {
  ShoppingBagIcon,
  KeyIcon,
  Cog6ToothIcon,
  ServerIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';

interface AvitoSettingsData {
  client_id: string;
  client_secret: string;
  access_token: string;
  refresh_token: string;
  token_expires_at?: string;
  webhook_url: string;
  webhook_secret: string;
  auto_reply_enabled: boolean;
  auto_reply_message: string;
  ai_enabled: boolean;
  ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
  notification_email: string;
  sync_interval: number;
  max_concurrent_chats: number;
}

export default function AvitoSettings() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState<AvitoSettingsData>({
    client_id: '',
    client_secret: '',
    access_token: '',
    refresh_token: '',
    webhook_url: '',
    webhook_secret: '',
    auto_reply_enabled: false,
    auto_reply_message: '',
    ai_enabled: true,
    ai_model: 'gpt-4',
    ai_temperature: 0.7,
    ai_max_tokens: 1000,
    notification_email: '',
    sync_interval: 300,
    max_concurrent_chats: 10
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    client_secret: false,
    access_token: false,
    refresh_token: false,
    webhook_secret: false
  });
  const [testResults, setTestResults] = useState<{
    connection?: { success: boolean; message: string };
    webhook?: { success: boolean; message: string };
  }>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settingsData = await apiService.getAvitoSettings();
      setSettings({
        client_id: settingsData.client_id || '',
        client_secret: settingsData.client_secret || '',
        access_token: settingsData.access_token || '',
        refresh_token: settingsData.refresh_token || '',
        token_expires_at: settingsData.token_expires_at || undefined,
        webhook_url: settingsData.webhook_url || '',
        webhook_secret: settingsData.webhook_secret || '',
        auto_reply_enabled: settingsData.auto_reply_enabled || false,
        auto_reply_message: settingsData.auto_reply_message || '',
        ai_enabled: settingsData.ai_enabled !== undefined ? settingsData.ai_enabled : true,
        ai_model: settingsData.ai_model || 'gpt-4',
        ai_temperature: settingsData.ai_temperature || 70,
        ai_max_tokens: settingsData.ai_max_tokens || 1000,
        notification_email: settingsData.notification_email || '',
        sync_interval: settingsData.sync_interval || 300,
        max_concurrent_chats: settingsData.max_concurrent_chats || 10
      });
    } catch (error) {
      console.error('Failed to load Avito settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      await apiService.updateAvitoSettings({
        client_id: settings.client_id,
        client_secret: settings.client_secret,
        access_token: settings.access_token,
        refresh_token: settings.refresh_token,
        webhook_url: settings.webhook_url,
        webhook_secret: settings.webhook_secret,
        auto_reply_enabled: settings.auto_reply_enabled,
        auto_reply_message: settings.auto_reply_message,
        ai_enabled: settings.ai_enabled,
        ai_model: settings.ai_model,
        ai_temperature: settings.ai_temperature,
        ai_max_tokens: settings.ai_max_tokens,
        notification_email: settings.notification_email,
        sync_interval: settings.sync_interval,
        max_concurrent_chats: settings.max_concurrent_chats
      });
      alert('Настройки Avito сохранены успешно!');
    } catch (err: any) {
      console.error('Failed to save Avito settings:', err);
      alert(`Ошибка при сохранении настроек: ${err.response?.data?.detail || err.message || 'Неизвестная ошибка'}`);
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      const result = await apiService.testAvitoConnection();
      setTestResults(prev => ({ ...prev, connection: { success: result.success, message: result.message } }));
    } catch (err: any) {
      console.error('Failed to test Avito connection:', err);
      setTestResults(prev => ({
        ...prev,
        connection: { success: false, message: err.response?.data?.message || 'Ошибка при тестировании подключения' }
      }));
    } finally {
      setTesting(false);
    }
  };

  const testWebhook = async () => {
    try {
      setTesting(true);
      const result = await apiService.testAvitoWebhook();
      setTestResults(prev => ({ ...prev, webhook: { success: result.success, message: result.message } }));
    } catch (err: any) {
      console.error('Failed to test Avito webhook:', err);
      setTestResults(prev => ({
        ...prev,
        webhook: { success: false, message: err.response?.data?.message || 'Ошибка при тестировании webhook' }
      }));
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Настройки Avito</h1>
          <p className="text-gray-600 mt-2">Полная интеграция с Avito API</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={testConnection}
            disabled={testing}
            className="btn-secondary flex items-center"
          >
            <ServerIcon className="w-4 h-4 mr-2" />
            Тест подключения
          </button>
          <button
            onClick={testWebhook}
            disabled={testing}
            className="btn-secondary flex items-center"
          >
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Тест webhook
          </button>
          <button
            onClick={saveSettings}
            disabled={saving}
            className="btn-primary flex items-center"
          >
            {saving ? (
              <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircleIcon className="w-4 h-4 mr-2" />
            )}
            Сохранить
          </button>
        </div>
      </div>

      {/* Test Results */}
      {(testResults.connection || testResults.webhook) && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Результаты тестирования</h3>
          <div className="space-y-2">
            {testResults.connection && (
              <div className="flex items-center space-x-2">
                {testResults.connection.success ? (
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircleIcon className="w-5 h-5 text-red-600" />
                )}
                <span className="text-sm">
                  <strong>Подключение:</strong> {testResults.connection.message}
                </span>
              </div>
            )}
            {testResults.webhook && (
              <div className="flex items-center space-x-2">
                {testResults.webhook.success ? (
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircleIcon className="w-5 h-5 text-red-600" />
                )}
                <span className="text-sm">
                  <strong>Webhook:</strong> {testResults.webhook.message}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* API Credentials */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <KeyIcon className="w-5 h-5 mr-2" />
          API учетные данные
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client ID *
            </label>
            <input
              type="text"
              value={settings.client_id}
              onChange={(e) => setSettings(prev => ({ ...prev, client_id: e.target.value }))}
              className="input-field"
              placeholder="Ваш Avito Client ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client Secret *
            </label>
            <div className="relative">
              <input
                type={showPasswords.client_secret ? "text" : "password"}
                value={settings.client_secret}
                onChange={(e) => setSettings(prev => ({ ...prev, client_secret: e.target.value }))}
                className="input-field pr-10"
                placeholder="Ваш Avito Client Secret"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, client_secret: !prev.client_secret }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.client_secret ? (
                  <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                ) : (
                  <EyeIcon className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Access Token
            </label>
            <div className="relative">
              <input
                type={showPasswords.access_token ? "text" : "password"}
                value={settings.access_token}
                onChange={(e) => setSettings(prev => ({ ...prev, access_token: e.target.value }))}
                className="input-field pr-10"
                placeholder="Токен доступа"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, access_token: !prev.access_token }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.access_token ? (
                  <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                ) : (
                  <EyeIcon className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Refresh Token
            </label>
            <div className="relative">
              <input
                type={showPasswords.refresh_token ? "text" : "password"}
                value={settings.refresh_token}
                onChange={(e) => setSettings(prev => ({ ...prev, refresh_token: e.target.value }))}
                className="input-field pr-10"
                placeholder="Токен обновления"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, refresh_token: !prev.refresh_token }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.refresh_token ? (
                  <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                ) : (
                  <EyeIcon className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        </div>

        {settings.token_expires_at && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p className="text-sm text-blue-800">
              <strong>Токен истекает:</strong> {new Date(settings.token_expires_at).toLocaleString('ru-RU')}
            </p>
          </div>
        )}
      </div>

      {/* Webhook Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <ServerIcon className="w-5 h-5 mr-2" />
          Настройки Webhook
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Webhook URL *
            </label>
            <input
              type="url"
              value={settings.webhook_url}
              onChange={(e) => setSettings(prev => ({ ...prev, webhook_url: e.target.value }))}
              className="input-field"
              placeholder="https://yourdomain.com/webhook/avito"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Webhook Secret
            </label>
            <div className="relative">
              <input
                type={showPasswords.webhook_secret ? "text" : "password"}
                value={settings.webhook_secret}
                onChange={(e) => setSettings(prev => ({ ...prev, webhook_secret: e.target.value }))}
                className="input-field pr-10"
                placeholder="Секрет для подписи webhook"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, webhook_secret: !prev.webhook_secret }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.webhook_secret ? (
                  <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                ) : (
                  <EyeIcon className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* AI Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Cog6ToothIcon className="w-5 h-5 mr-2" />
          Настройки ИИ
        </h3>

        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.ai_enabled}
              onChange={(e) => setSettings(prev => ({ ...prev, ai_enabled: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Включить AI ответы в чатах</span>
          </label>

          {settings.ai_enabled && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 ml-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Модель ИИ
                </label>
                <select
                  value={settings.ai_model}
                  onChange={(e) => setSettings(prev => ({ ...prev, ai_model: e.target.value }))}
                  className="input-field"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3">Claude-3</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Температура
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.ai_temperature}
                  onChange={(e) => setSettings(prev => ({ ...prev, ai_temperature: parseFloat(e.target.value) || 0.7 }))}
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Макс. токенов
                </label>
                <input
                  type="number"
                  min="100"
                  max="4000"
                  value={settings.ai_max_tokens}
                  onChange={(e) => setSettings(prev => ({ ...prev, ai_max_tokens: parseInt(e.target.value) || 1000 }))}
                  className="input-field"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Auto Reply Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Автоответчик</h3>

        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.auto_reply_enabled}
              onChange={(e) => setSettings(prev => ({ ...prev, auto_reply_enabled: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Включить автоответчик</span>
          </label>

          {settings.auto_reply_enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Сообщение автоответчика
              </label>
              <textarea
                value={settings.auto_reply_message}
                onChange={(e) => setSettings(prev => ({ ...prev, auto_reply_message: e.target.value }))}
                className="input-field"
                rows={4}
                placeholder="Спасибо за ваше сообщение. Мы свяжемся с вами в ближайшее время."
              />
            </div>
          )}
        </div>
      </div>

      {/* System Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Cog6ToothIcon className="w-5 h-5 mr-2" />
          Системные настройки
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email для уведомлений
            </label>
            <input
              type="email"
              value={settings.notification_email}
              onChange={(e) => setSettings(prev => ({ ...prev, notification_email: e.target.value }))}
              className="input-field"
              placeholder="admin@yourcompany.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Интервал синхронизации (сек)
            </label>
            <input
              type="number"
              min="60"
              max="3600"
              value={settings.sync_interval}
              onChange={(e) => setSettings(prev => ({ ...prev, sync_interval: parseInt(e.target.value) || 300 }))}
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Макс. одновременных чатов
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={settings.max_concurrent_chats}
              onChange={(e) => setSettings(prev => ({ ...prev, max_concurrent_chats: parseInt(e.target.value) || 10 }))}
              className="input-field"
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/avito')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            Управление чатами
          </button>
          <button
            onClick={() => navigate('/communications')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <ShoppingBagIcon className="w-5 h-5 mr-2" />
            История сообщений
          </button>
          <button
            onClick={() => navigate('/customers')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <Cog6ToothIcon className="w-5 h-5 mr-2" />
            Управление клиентами
          </button>
        </div>
      </div>

      {/* Help Section */}
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
        <h4 className="text-md font-semibold text-orange-900 mb-2">Как настроить интеграцию Avito</h4>
        <div className="text-sm text-orange-800 space-y-1">
          <p><strong>1. Регистрация приложения:</strong> Создайте приложение в личном кабинете Avito для разработчиков</p>
          <p><strong>2. Получение токенов:</strong> Используйте OAuth 2.0 flow для получения access и refresh токенов</p>
          <p><strong>3. Настройка webhook:</strong> Укажите URL для получения уведомлений о новых сообщениях</p>
          <p><strong>4. Тестирование:</strong> Используйте кнопки тестирования для проверки подключения</p>
          <p><strong>5. Запуск:</strong> После успешного тестирования интеграция будет активна</p>
        </div>
      </div>
    </div>
  );
}
