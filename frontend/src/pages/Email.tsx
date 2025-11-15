import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api.ts';
import {
  EnvelopeIcon,
  PaperAirplaneIcon,
  Cog6ToothIcon,
  EyeIcon,
  PlusIcon,
  MagnifyingGlassIcon
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

export default function Email() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [stats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showCreateTemplateModal, setShowCreateTemplateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);

  useEffect(() => {
    loadEmailData();
  }, []);

  const loadEmailData = async () => {
    try {
      const [templatesData] = await Promise.all([
        apiService.getEmailTemplates(),
        // apiService.getEmailStats() // TODO: Add when backend implements
      ]);

      setTemplates(templatesData);
      // setStats(statsData);
    } catch (error) {
      console.error('Failed to load email data:', error);
    } finally {
      setLoading(false);
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
            onClick={() => navigate('/settings/system')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <Cog6ToothIcon className="w-5 h-5 mr-2" />
            Настройки SMTP
          </button>
          <button
            onClick={() => navigate('/settings/avito')}
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
