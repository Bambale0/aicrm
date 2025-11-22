import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import {
  EnvelopeIcon,
  PaperAirplaneIcon,
  Cog6ToothIcon,
  EyeIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ServerIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  variables: string[];
}

interface EmailStats {
  sent_today: number;
  sent_month: number;
  delivered: number;
  opened: number;
  bounced: number;
}

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

export default function Email() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [emailSettings, setEmailSettings] = useState<EmailSettingsData>({
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
  const [emailSaving, setEmailSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    smtp: false,
    imap: false
  });
  const [testResults, setTestResults] = useState<{
    smtp?: { success: boolean; message: string; details?: any };
    imap?: { success: boolean; message: string; details?: any };
  }>({});
  const [loading, setLoading] = useState(true);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showCreateTemplateModal, setShowCreateTemplateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);

  useEffect(() => {
    loadEmailData();
  }, []);

  const loadEmailData = async () => {
    try {
      const [templatesData, settingsData, statsData] = await Promise.all([
        apiService.getEmailTemplates(),
        apiService.getEmailSettings(),
        apiService.getEmailStats()
      ]);

      setTemplates(templatesData);
      setStats(statsData);
      // Объединяем загруженные данные с дефолтными значениями, чтобы избежать undefined
      setEmailSettings(prev => ({
        smtp_host: settingsData?.smtp_host || prev.smtp_host,
        smtp_port: settingsData?.smtp_port || prev.smtp_port,
        smtp_username: settingsData?.smtp_username || prev.smtp_username,
        smtp_password: settingsData?.smtp_password || prev.smtp_password,
        smtp_use_tls: settingsData?.smtp_use_tls ?? prev.smtp_use_tls,
        smtp_use_ssl: settingsData?.smtp_use_ssl ?? prev.smtp_use_ssl,
        imap_host: settingsData?.imap_host || prev.imap_host,
        imap_port: settingsData?.imap_port || prev.imap_port,
        imap_username: settingsData?.imap_username || prev.imap_username,
        imap_password: settingsData?.imap_password || prev.imap_password,
        imap_use_ssl: settingsData?.imap_use_ssl ?? prev.imap_use_ssl,
        default_from_email: settingsData?.default_from_email || prev.default_from_email,
        default_from_name: settingsData?.default_from_name || prev.default_from_name,
        signature: settingsData?.signature || prev.signature,
        auto_reply_enabled: settingsData?.auto_reply_enabled ?? prev.auto_reply_enabled,
        auto_reply_message: settingsData?.auto_reply_message || prev.auto_reply_message
      }));
    } catch (error) {
      console.error('Failed to load email data:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveEmailSettings = async () => {
    try {
      setEmailSaving(true);
      await apiService.saveEmailSettings(emailSettings);
      // Показать успех
      alert('Настройки email сохранены успешно');
    } catch (err: any) {
      console.error('Failed to save email settings:', err);
      alert(`Ошибка при сохранении настроек email: ${err.response?.data?.detail || err.message || 'Неизвестная ошибка'}`);
    } finally {
      setEmailSaving(false);
    }
  };

  const testSMTPConnection = async () => {
    try {
      const result = await apiService.testSMTPConnection(emailSettings);
      setTestResults(prev => ({ ...prev, smtp: result }));
    } catch (err) {
      console.error('Failed to test SMTP:', err);
      setTestResults(prev => ({
        ...prev,
        smtp: { success: false, message: 'Ошибка при тестировании SMTP' }
      }));
    }
  };

  const testIMAPConnection = async () => {
    try {
      const result = await apiService.testIMAPConnection(emailSettings);
      setTestResults(prev => ({ ...prev, imap: result }));
    } catch (err) {
      console.error('Failed to test IMAP:', err);
      setTestResults(prev => ({
        ...prev,
        imap: { success: false, message: 'Ошибка при тестировании IMAP' }
      }));
    }
  };

  const handleSendEmail = async (emailData: {
    to: string;
    subject: string;
    body: string;
    template?: string;
  }) => {
    try {
      await apiService.sendEmail(emailData);
      alert('Email отправлен успешно!');
      setShowSendModal(false);
    } catch (error) {
      console.error('Failed to send email:', error);
      alert('Ошибка при отправке email');
    }
  };

  const handleTestEmail = async (email: string) => {
    try {
      await apiService.testEmail({ to: email });
      alert('Тестовый email отправлен!');
    } catch (error) {
      console.error('Failed to send test email:', error);
      alert('Ошибка при отправке тестового email');
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
          <h1 className="text-3xl font-bold text-gray-900">Email</h1>
          <p className="text-gray-600 mt-2">Управление email рассылками и шаблонами</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowCreateTemplateModal(true)}
            className="btn-secondary flex items-center"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            Создать шаблон
          </button>
          <button
            onClick={() => setShowSendModal(true)}
            className="btn-primary flex items-center"
          >
            <PaperAirplaneIcon className="w-5 h-5 mr-2" />
            Отправить email
          </button>
        </div>
      </div>

      {/* Email Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.sent_today}</div>
            <div className="text-sm text-gray-600">Отправлено сегодня</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">{stats.sent_month}</div>
            <div className="text-sm text-gray-600">Отправлено за месяц</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600">{stats.delivered}</div>
            <div className="text-sm text-gray-600">Доставлено</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-600">{stats.opened}</div>
            <div className="text-sm text-gray-600">Открыто</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-red-600">{stats.bounced}</div>
            <div className="text-sm text-gray-600">Возвращено</div>
          </div>
        </div>
      )}

      {/* Email Templates */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Шаблоны email ({templates.length})
          </h3>
        </div>

        {templates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{template.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{template.subject}</p>
                  </div>
                  <button
                    onClick={() => setSelectedTemplate(template)}
                    className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                </div>

                <div className="text-xs text-gray-500">
                  Переменные: {template.variables.join(', ') || 'нет'}
                </div>

                <div className="flex space-x-2 mt-3">
                  <button
                    onClick={() => handleSendEmail({
                      to: '',
                      subject: template.subject,
                      body: template.body,
                      template: template.id
                    })}
                    className="flex-1 btn-primary text-xs py-1"
                  >
                    Использовать
                  </button>
                  <button className="btn-secondary text-xs py-1 px-2">
                    <Cog6ToothIcon className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <EnvelopeIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Шаблоны email не найдены</p>
            <p className="text-sm text-gray-500 mt-1">Создайте первый шаблон</p>
          </div>
        )}
      </div>

      {/* Email Settings */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Настройки Email</h3>
          <div className="flex space-x-2">
            <button
              onClick={testSMTPConnection}
              disabled={false}
              className="btn-secondary flex items-center"
            >
              <ServerIcon className="w-4 h-4 mr-2" />
              Тест SMTP
            </button>
            <button
              onClick={testIMAPConnection}
              disabled={false}
              className="btn-secondary flex items-center"
            >
              <EnvelopeIcon className="w-4 h-4 mr-2" />
              Тест IMAP
            </button>
            <button
              onClick={saveEmailSettings}
              disabled={emailSaving}
              className="btn-primary flex items-center"
            >
              {emailSaving ? (
                <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircleIcon className="w-4 h-4 mr-2" />
              )}
              Сохранить
            </button>
          </div>
        </div>

        {/* Test Results */}
        {(testResults.smtp || testResults.imap) && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Результаты тестирования:</h4>
            <div className="space-y-2">
              {testResults.smtp && (
                <div className="flex items-center space-x-2">
                  {testResults.smtp.success ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-red-600" />
                  )}
                  <span className="text-sm">
                    <strong>SMTP:</strong> {testResults.smtp.message}
                  </span>
                </div>
              )}
              {testResults.imap && (
                <div className="flex items-center space-x-2">
                  {testResults.imap.success ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-red-600" />
                  )}
                  <span className="text-sm">
                    <strong>IMAP:</strong> {testResults.imap.message}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* SMTP Settings */}
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
              <ServerIcon className="w-5 h-5 mr-2" />
              Настройки SMTP (Отправка)
            </h4>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SMTP сервер *
                  </label>
                  <input
                    type="text"
                    value={emailSettings.smtp_host}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_host: e.target.value }))}
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
                    value={emailSettings.smtp_port}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_port: parseInt(e.target.value) || 587 }))}
                    className="input-field"
                    placeholder="587"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Логин (email) *
                </label>
                <input
                  type="email"
                  value={emailSettings.smtp_username}
                  onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_username: e.target.value }))}
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
                    type={showPasswords.smtp ? "text" : "password"}
                    value={emailSettings.smtp_password}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_password: e.target.value }))}
                    className="input-field pr-10"
                    placeholder="Пароль от почты"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords(prev => ({ ...prev, smtp: !prev.smtp }))}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.smtp ? (
                      <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                    ) : (
                      <EyeIcon className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailSettings.smtp_use_tls}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_use_tls: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Использовать TLS</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailSettings.smtp_use_ssl}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_use_ssl: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Использовать SSL</span>
                </label>
              </div>
            </div>
          </div>

          {/* IMAP Settings */}
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
              <EnvelopeIcon className="w-5 h-5 mr-2" />
              Настройки IMAP (Получение)
            </h4>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IMAP сервер
                  </label>
                  <input
                    type="text"
                    value={emailSettings.imap_host}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, imap_host: e.target.value }))}
                    className="input-field"
                    placeholder="imap.gmail.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Порт
                  </label>
                  <input
                    type="number"
                    value={emailSettings.imap_port}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, imap_port: parseInt(e.target.value) || 993 }))}
                    className="input-field"
                    placeholder="993"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Логин (email)
                </label>
                <input
                  type="email"
                  value={emailSettings.imap_username}
                  onChange={(e) => setEmailSettings(prev => ({ ...prev, imap_username: e.target.value }))}
                  className="input-field"
                  placeholder="your-email@gmail.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Пароль
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.imap ? "text" : "password"}
                    value={emailSettings.imap_password}
                    onChange={(e) => setEmailSettings(prev => ({ ...prev, imap_password: e.target.value }))}
                    className="input-field pr-10"
                    placeholder="Пароль от почты"
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

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={emailSettings.imap_use_ssl}
                  onChange={(e) => setEmailSettings(prev => ({ ...prev, imap_use_ssl: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Использовать SSL</span>
              </label>
            </div>
          </div>
        </div>

        {/* General Email Settings */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
            <Cog6ToothIcon className="w-5 h-5 mr-2" />
            Общие настройки
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email отправителя по умолчанию *
              </label>
              <input
                type="email"
                value={emailSettings.default_from_email}
                onChange={(e) => setEmailSettings(prev => ({ ...prev, default_from_email: e.target.value }))}
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
                value={emailSettings.default_from_name}
                onChange={(e) => setEmailSettings(prev => ({ ...prev, default_from_name: e.target.value }))}
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
              value={emailSettings.signature}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, signature: e.target.value }))}
              className="input-field"
              rows={3}
              placeholder="С уважением,&#10;Ваша Компания"
            />
          </div>

          <div className="mt-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={emailSettings.auto_reply_enabled}
                onChange={(e) => setEmailSettings(prev => ({ ...prev, auto_reply_enabled: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Включить автоответчик</span>
            </label>
            {emailSettings.auto_reply_enabled && (
              <div className="mt-2">
                <textarea
                  value={emailSettings.auto_reply_message}
                  onChange={(e) => setEmailSettings(prev => ({ ...prev, auto_reply_message: e.target.value }))}
                  className="input-field"
                  rows={3}
                  placeholder="Спасибо за ваше сообщение. Мы свяжемся с вами в ближайшее время."
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => handleTestEmail('test@example.com')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <PaperAirplaneIcon className="w-5 h-5 mr-2" />
            Отправить тестовый email
          </button>
          <button
            onClick={() => navigate('/email')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
            История отправок
          </button>
        </div>
      </div>

      {/* Send Email Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Отправить email</h3>
              <button
                onClick={() => setShowSendModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form className="space-y-4" onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              handleSendEmail({
                to: formData.get('to') as string,
                subject: formData.get('subject') as string,
                body: formData.get('body') as string,
                template: formData.get('template') as string || undefined
              });
            }}>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Получатель *
                </label>
                <input
                  type="email"
                  name="to"
                  className="input-field"
                  placeholder="email@example.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тема *
                </label>
                <input
                  type="text"
                  name="subject"
                  className="input-field"
                  placeholder="Тема письма"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Шаблон (опционально)
                </label>
                <select name="template" className="input-field">
                  <option value="">Без шаблона</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Содержание *
                </label>
                <textarea
                  name="body"
                  className="input-field"
                  rows={6}
                  placeholder="Текст письма"
                  required
                />
              </div>
            </form>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowSendModal(false)}
                className="btn-secondary"
              >
                Отмена
              </button>
              <button
                onClick={(e) => {
                  const form = (e.target as HTMLElement).closest('form');
                  if (form) form.requestSubmit();
                }}
                className="btn-primary flex items-center"
              >
                <PaperAirplaneIcon className="w-4 h-4 mr-2" />
                Отправить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Template Modal */}
      {showCreateTemplateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Создать шаблон</h3>
              <button
                onClick={() => setShowCreateTemplateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название шаблона *
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Например: Приветственное письмо"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тема письма *
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Тема письма"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Содержание *
                </label>
                <textarea
                  className="input-field"
                  rows={8}
                  placeholder="Текст шаблона. Используйте {{variable}} для переменных."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Переменные (через запятую)
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="name, email, company"
                />
              </div>
            </form>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateTemplateModal(false)}
                className="btn-secondary"
              >
                Отмена
              </button>
              <button className="btn-primary">
                Создать шаблон
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Template Details Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Шаблон: {selectedTemplate.name}
              </h3>
              <button
                onClick={() => setSelectedTemplate(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Тема</label>
                <p className="text-gray-900 mt-1">{selectedTemplate.subject}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Содержание</label>
                <div className="mt-1 p-3 bg-gray-50 rounded border text-sm whitespace-pre-wrap">
                  {selectedTemplate.body}
                </div>
              </div>

              {selectedTemplate.variables.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Переменные</label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedTemplate.variables.map((variable, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {variable}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => setSelectedTemplate(null)}
                className="btn-secondary"
              >
                Закрыть
              </button>
              <button className="btn-primary">
                Редактировать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
