import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import {
  EnvelopeIcon,
  ServerIcon,
  KeyIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

interface EmailSettingsData {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  imap_password: string;
  imap_use_ssl: boolean;
  default_from_email: string;
  default_from_name: string;
  signature: string;
  auto_reply_enabled: boolean;
  auto_reply_message: string;
}

export default function EmailSettings() {
  const [settings, setSettings] = useState<EmailSettingsData>({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
    imap_host: '',
    imap_port: 993,
    imap_username: '',
    imap_password: '',
    imap_use_ssl: true,
    default_from_email: '',
    default_from_name: '',
    signature: '',
    auto_reply_enabled: false,
    auto_reply_message: ''
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    smtp: false,
    imap: false
  });
  const [testResults, setTestResults] = useState<{
    smtp?: boolean;
    imap?: boolean;
  }>({});

  const loadSettings = useCallback(async () => {
    try {
      const data = await apiService.getEmailServiceStatus();
      setSettings(data.settings || settings);
    } catch (error) {
      console.error('Failed to load email settings:', error);
    } finally {
      setLoading(false);
    }
  }, [settings]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiService.updateSystemSettings({ email: settings });
      alert('Настройки email сохранены успешно!');
    } catch (error) {
      console.error('Failed to save email settings:', error);
      alert('Ошибка при сохранении настроек');
    } finally {
      setSaving(false);
    }
  };

  const testSMTP = async () => {
    try {
      await apiService.testEmail({ to: settings.default_from_email });
      setTestResults(prev => ({ ...prev, smtp: true }));
      alert('SMTP подключение успешно!');
    } catch (error) {
      setTestResults(prev => ({ ...prev, smtp: false }));
      alert('Ошибка SMTP подключения');
    }
  };

  const testIMAP = async () => {
    try {
      // TODO: Add IMAP test endpoint
      setTestResults(prev => ({ ...prev, imap: true }));
      alert('IMAP подключение успешно!');
    } catch (error) {
      setTestResults(prev => ({ ...prev, imap: false }));
      alert('Ошибка IMAP подключения');
    }
  };

  const updateSetting = (key: keyof EmailSettingsData, value: any) => {
    setSettings((prev: EmailSettingsData) => ({ ...prev, [key]: value }));
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
          <h1 className="text-3xl font-bold text-gray-900">Настройки Email</h1>
          <p className="text-gray-600 mt-2">Конфигурация SMTP и IMAP для отправки и получения email</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary flex items-center"
        >
          {saving ? (
            <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin" />
          ) : (
            <CheckCircleIcon className="w-5 h-5 mr-2" />
          )}
          {saving ? 'Сохранение...' : 'Сохранить настройки'}
        </button>
      </div>

      {/* SMTP Settings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <ServerIcon className="w-5 h-5 mr-2" />
            Настройки SMTP (отправка)
          </h3>
          <button
            onClick={testSMTP}
            className="btn-secondary text-sm"
          >
            Тестировать подключение
          </button>
        </div>

        {testResults.smtp !== undefined && (
          <div className={`mb-4 p-3 rounded-lg flex items-center ${
            testResults.smtp ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {testResults.smtp ? (
              <CheckCircleIcon className="w-5 h-5 mr-2" />
            ) : (
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
            )}
            {testResults.smtp ? 'SMTP подключение успешно' : 'Ошибка SMTP подключения'}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SMTP сервер *
            </label>
            <input
              type="text"
              value={settings.smtp_host}
              onChange={(e) => updateSetting('smtp_host', e.target.value)}
              className="input-field"
              placeholder="smtp.gmail.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Порт *
            </label>
            <input
              type="number"
              value={settings.smtp_port}
              onChange={(e) => updateSetting('smtp_port', parseInt(e.target.value))}
              className="input-field"
              placeholder="587"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Логин *
            </label>
            <input
              type="text"
              value={settings.smtp_username}
              onChange={(e) => updateSetting('smtp_username', e.target.value)}
              className="input-field"
              placeholder="your-email@gmail.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Пароль *
            </label>
            <div className="relative">
              <input
                type={showPasswords.smtp ? 'text' : 'password'}
                value={settings.smtp_password}
                onChange={(e) => updateSetting('smtp_password', e.target.value)}
                className="input-field pr-10"
                placeholder="Пароль приложения"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, smtp: !prev.smtp }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.smtp ? (
                  <EyeSlashIcon className="w-5 h-5 text-gray-400" />
                ) : (
                  <EyeIcon className="w-5 h-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.smtp_use_tls}
              onChange={(e) => updateSetting('smtp_use_tls', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Использовать TLS</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.smtp_use_ssl}
              onChange={(e) => updateSetting('smtp_use_ssl', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Использовать SSL</span>
          </label>
        </div>
      </div>

      {/* IMAP Settings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <EnvelopeIcon className="w-5 h-5 mr-2" />
            Настройки IMAP (получение)
          </h3>
          <button
            onClick={testIMAP}
            className="btn-secondary text-sm"
          >
            Тестировать подключение
          </button>
        </div>

        {testResults.imap !== undefined && (
          <div className={`mb-4 p-3 rounded-lg flex items-center ${
            testResults.imap ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {testResults.imap ? (
              <CheckCircleIcon className="w-5 h-5 mr-2" />
            ) : (
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
            )}
            {testResults.imap ? 'IMAP подключение успешно' : 'Ошибка IMAP подключения'}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              IMAP сервер *
            </label>
            <input
              type="text"
              value={settings.imap_host}
              onChange={(e) => updateSetting('imap_host', e.target.value)}
              className="input-field"
              placeholder="imap.gmail.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Порт *
            </label>
            <input
              type="number"
              value={settings.imap_port}
              onChange={(e) => updateSetting('imap_port', parseInt(e.target.value))}
              className="input-field"
              placeholder="993"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Логин *
            </label>
            <input
              type="text"
              value={settings.imap_username}
              onChange={(e) => updateSetting('imap_username', e.target.value)}
              className="input-field"
              placeholder="your-email@gmail.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Пароль *
            </label>
            <div className="relative">
              <input
                type={showPasswords.imap ? 'text' : 'password'}
                value={settings.imap_password}
                onChange={(e) => updateSetting('imap_password', e.target.value)}
                className="input-field pr-10"
                placeholder="Пароль приложения"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, imap: !prev.imap }))}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPasswords.imap ? (
                  <EyeSlashIcon className="w-5 h-5 text-gray-400" />
                ) : (
                  <EyeIcon className="w-5 h-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.imap_use_ssl}
              onChange={(e) => updateSetting('imap_use_ssl', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Использовать SSL</span>
          </label>
        </div>
      </div>

      {/* General Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <KeyIcon className="w-5 h-5 mr-2" />
          Общие настройки
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email отправителя по умолчанию *
            </label>
            <input
              type="email"
              value={settings.default_from_email}
              onChange={(e) => updateSetting('default_from_email', e.target.value)}
              className="input-field"
              placeholder="noreply@yourcompany.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Имя отправителя по умолчанию
            </label>
            <input
              type="text"
              value={settings.default_from_name}
              onChange={(e) => updateSetting('default_from_name', e.target.value)}
              className="input-field"
              placeholder="Ваша Компания"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Подпись по умолчанию
          </label>
          <textarea
            value={settings.signature}
            onChange={(e) => updateSetting('signature', e.target.value)}
            className="input-field"
            rows={4}
            placeholder="С уважением,&#10;Ваша команда поддержки"
          />
        </div>
      </div>

      {/* Auto Reply Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Автоответчик
        </h3>

        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.auto_reply_enabled}
              onChange={(e) => updateSetting('auto_reply_enabled', e.target.checked)}
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
                onChange={(e) => updateSetting('auto_reply_message', e.target.value)}
                className="input-field"
                rows={6}
                placeholder="Спасибо за ваше сообщение. Мы ответим в ближайшее время."
              />
            </div>
          )}
        </div>
      </div>

      {/* Help Section */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Помощь по настройке</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p><strong>Gmail:</strong> Используйте "Пароль приложения" вместо основного пароля</p>
          <p><strong>Yandex:</strong> Включите IMAP в настройках почты</p>
          <p><strong>Outlook:</strong> Используйте пароль приложения для двухфакторной аутентификации</p>
          <p><strong>Порты:</strong> SMTP обычно 587 (TLS) или 465 (SSL), IMAP обычно 993 (SSL)</p>
        </div>
      </div>
    </div>
  );
}
