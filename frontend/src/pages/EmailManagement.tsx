import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import {
  PaperAirplaneIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  ChartBarIcon,
  InboxIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  TrashIcon,
  FlagIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface EmailMessage {
  id: string;
  uid: string;
  subject: string;
  from_addr: string;
  from_name: string;
  to: string[];
  cc: string[];
  date: string;
  body_text: string;
  body_html?: string;
  attachments: Array<{
    filename: string;
    content_type: string;
    size: number;
  }>;
  flags: string[];
  size: number;
  message_id?: string;
  folder: string;
  is_read: boolean;
  is_flagged: boolean;
  is_deleted: boolean;
}

interface EmailTemplate {
  name: string;
  subject_template: string;
  html_template: string;
  text_template: string;
  variables: string[];
  category: string;
  created_at: string;
  updated_at: string;
}

interface EmailSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  imap_use_ssl: boolean;
  default_from_email: string;
  default_from_name: string;
  signature: string;
  auto_reply_enabled: boolean;
  auto_reply_message: string;
}

interface EmailStats {
  total_sent: number;
  total_received: number;
  unread_count: number;
  folders_count: number;
  contacts_count: number;
  templates_count: number;
}

export default function EmailManagement() {
  const [activeTab, setActiveTab] = useState('inbox');
  const [loading, setLoading] = useState(false);

  // Inbox state
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [currentFolder, setCurrentFolder] = useState('INBOX');
  const [searchQuery, setSearchQuery] = useState('');

  // Compose state
  const [composeData, setComposeData] = useState({
    to: '',
    subject: '',
    body: '',
    template: ''
  });

  // Templates state
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  // Settings state
  const [settings, setSettings] = useState<EmailSettings | null>(null);

  // Stats state
  const [stats, setStats] = useState<EmailStats | null>(null);

  const loadEmails = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getEmailMessages(currentFolder, 50, 0);
      setEmails(data);
    } catch (error) {
      console.error('Failed to load emails:', error);
    } finally {
      setLoading(false);
    }
  }, [currentFolder]);

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getEmailTemplates();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getEmailSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getEmailStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data based on active tab
  useEffect(() => {
    switch (activeTab) {
      case 'inbox':
        loadEmails();
        break;
      case 'templates':
        loadTemplates();
        break;
      case 'settings':
        loadSettings();
        break;
      case 'stats':
        loadStats();
        break;
    }
  }, [activeTab, currentFolder, loadEmails, loadSettings, loadStats, loadTemplates]);

  const handleSendEmail = async () => {
    try {
      setLoading(true);
      await apiService.sendEmail({
        to: composeData.to,
        subject: composeData.subject,
        body: composeData.body
      });
      setComposeData({ to: '', subject: '', body: '', template: '' });
      alert('Email отправлен успешно!');
    } catch (error) {
      console.error('Failed to send email:', error);
      alert('Ошибка при отправке email');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (emailId: string) => {
    try {
      await apiService.markEmailsAsRead({ message_ids: [emailId], folder: currentFolder });
      loadEmails();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleDeleteEmail = async (emailId: string) => {
    try {
      await apiService.deleteEmails({ message_ids: [emailId], folder: currentFolder });
      loadEmails();
    } catch (error) {
      console.error('Failed to delete email:', error);
    }
  };

  const handleTestEmail = async () => {
    if (!settings) return;

    try {
      setLoading(true);
      await apiService.testSMTPConnection(settings);
      alert('Тестовый email отправлен!');
    } catch (error) {
      console.error('Failed to test email:', error);
      alert('Ошибка при тестировании email');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'inbox', name: 'Входящие', icon: InboxIcon },
    { id: 'compose', name: 'Отправить', icon: PaperAirplaneIcon },
    { id: 'templates', name: 'Шаблоны', icon: DocumentTextIcon },
    { id: 'settings', name: 'Настройки', icon: Cog6ToothIcon },
    { id: 'stats', name: 'Статистика', icon: ChartBarIcon }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Управление Email</h1>
        <p className="text-gray-600 mt-2">Отправка, получение и управление email сообщениями</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {activeTab === 'inbox' && (
          <div className="space-y-4">
            {/* Search and folder selector */}
            <div className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Поиск по email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input-field"
                />
              </div>
              <select
                value={currentFolder}
                onChange={(e) => setCurrentFolder(e.target.value)}
                className="input-field"
              >
                <option value="INBOX">Входящие</option>
                <option value="Sent">Отправленные</option>
                <option value="Drafts">Черновики</option>
                <option value="Trash">Корзина</option>
              </select>
              <button
                onClick={loadEmails}
                className="btn-secondary flex items-center"
              >
                <ArrowPathIcon className="w-5 h-5 mr-2" />
                Обновить
              </button>
            </div>

            {/* Email list */}
            <div className="card">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : emails.length > 0 ? (
                <div className="space-y-2">
                  {emails.map((email) => (
                    <div
                      key={email.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                        !email.is_read ? 'bg-blue-50 border-blue-200' : 'border-gray-200'
                      }`}
                      onClick={() => setSelectedEmail(email)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            {!email.is_read && (
                              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                            )}
                            <span className="font-medium text-gray-900">
                              {email.from_name || email.from_addr}
                            </span>
                            {email.is_flagged && (
                              <FlagIcon className="w-4 h-4 text-yellow-600" />
                            )}
                          </div>
                          <p className="text-sm font-medium text-gray-900 mt-1">
                            {email.subject}
                          </p>
                          <p className="text-sm text-gray-600 truncate">
                            {email.body_text.substring(0, 100)}...
                          </p>
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(email.date).toLocaleString('ru-RU')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <InboxIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Нет сообщений</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'compose' && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Отправить Email</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Кому
                </label>
                <input
                  type="email"
                  value={composeData.to}
                  onChange={(e) => setComposeData({ ...composeData, to: e.target.value })}
                  className="input-field"
                  placeholder="email@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тема
                </label>
                <input
                  type="text"
                  value={composeData.subject}
                  onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                  className="input-field"
                  placeholder="Тема сообщения"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Сообщение
                </label>
                <textarea
                  value={composeData.body}
                  onChange={(e) => setComposeData({ ...composeData, body: e.target.value })}
                  className="input-field"
                  rows={10}
                  placeholder="Текст сообщения..."
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setComposeData({ to: '', subject: '', body: '', template: '' })}
                  className="btn-secondary"
                >
                  Очистить
                </button>
                <button
                  onClick={handleSendEmail}
                  disabled={loading || !composeData.to || !composeData.subject}
                  className="btn-primary flex items-center"
                >
                  {loading && <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />}
                  <PaperAirplaneIcon className="w-5 h-5 mr-2" />
                  Отправить
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Email Шаблоны</h3>
              <button
                onClick={() => alert('Функция создания шаблонов пока не реализована')}
                className="btn-primary flex items-center"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Создать шаблон
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : templates.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((template) => (
                  <div key={template.name} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {template.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Переменные: {template.variables.join(', ')}
                    </p>
                    <div className="flex space-x-2">
                      <button className="btn-secondary text-xs">
                        <EyeIcon className="w-4 h-4 mr-1" />
                        Просмотр
                      </button>
                      <button className="btn-secondary text-xs">
                        <PencilIcon className="w-4 h-4 mr-1" />
                        Редактировать
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Нет шаблонов</p>
                <p className="text-sm text-gray-500 mt-1">
                  Создайте первый email шаблон
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Настройки Email</h3>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : settings ? (
              <div className="space-y-6">
                {/* SMTP Settings */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">SMTP Настройки</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        SMTP Хост
                      </label>
                      <input
                        type="text"
                        value={settings.smtp_host}
                        onChange={(e) => setSettings({ ...settings, smtp_host: e.target.value })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        SMTP Порт
                      </label>
                      <input
                        type="number"
                        value={settings.smtp_port}
                        onChange={(e) => setSettings({ ...settings, smtp_port: parseInt(e.target.value) })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        SMTP Логин
                      </label>
                      <input
                        type="text"
                        value={settings.smtp_username}
                        onChange={(e) => setSettings({ ...settings, smtp_username: e.target.value })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        SMTP Пароль
                      </label>
                      <input
                        type="password"
                        value={settings.smtp_username ? '••••••••' : ''}
                        onChange={(e) => setSettings({ ...settings, smtp_username: e.target.value })}
                        className="input-field"
                      />
                    </div>
                  </div>
                </div>

                {/* Test buttons */}
                <div className="flex space-x-3">
                  <button
                    onClick={handleTestEmail}
                    disabled={loading}
                    className="btn-secondary flex items-center"
                  >
                    {loading && <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />}
                    <PaperAirplaneIcon className="w-5 h-5 mr-2" />
                    Тестировать SMTP
                  </button>
                  <button
                    onClick={() => alert('IMAP тест пока не реализован')}
                    className="btn-secondary"
                  >
                    Тестировать IMAP
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Cog6ToothIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Не удалось загрузить настройки</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика Email</h3>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : stats ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{stats.total_sent || 0}</div>
                  <div className="text-sm text-gray-600">Отправлено</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{stats.total_received || 0}</div>
                  <div className="text-sm text-gray-600">Получено</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">{stats.unread_count || 0}</div>
                  <div className="text-sm text-gray-600">Непрочитанных</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Статистика недоступна</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Email Detail Modal */}
      {selectedEmail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Просмотр Email</h3>
              <button
                onClick={() => setSelectedEmail(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedEmail.subject}</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    От: {selectedEmail.from_name || selectedEmail.from_addr}
                  </div>
                  <div className="text-sm text-gray-600">
                    Кому: {selectedEmail.to.join(', ')}
                  </div>
                  <div className="text-sm text-gray-600">
                    Дата: {new Date(selectedEmail.date).toLocaleString('ru-RU')}
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  {selectedEmail.body_html ? (
                    <div dangerouslySetInnerHTML={{ __html: selectedEmail.body_html }} />
                  ) : (
                    <pre className="whitespace-pre-wrap text-gray-900">{selectedEmail.body_text}</pre>
                  )}
                </div>

                {selectedEmail.attachments.length > 0 && (
                  <div className="border-t border-gray-200 pt-4">
                    <h5 className="font-medium text-gray-900 mb-2">Вложения:</h5>
                    <div className="space-y-2">
                      {selectedEmail.attachments.map((att, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm text-gray-600">
                          <DocumentTextIcon className="w-4 h-4" />
                          <span>{att.filename} ({Math.round(att.size / 1024)} KB)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between p-6 border-t border-gray-200">
              <div className="flex space-x-3">
                {!selectedEmail.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(selectedEmail.id)}
                    className="btn-secondary"
                  >
                    Отметить как прочитанное
                  </button>
                )}
                <button
                  onClick={() => handleDeleteEmail(selectedEmail.id)}
                  className="btn-danger"
                >
                  <TrashIcon className="w-4 h-4 mr-2" />
                  Удалить
                </button>
              </div>
              <button
                onClick={() => setSelectedEmail(null)}
                className="btn-secondary"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
