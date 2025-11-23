/* eslint-disable no-restricted-globals */

import {
  DocumentTextIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { useCallback, useEffect, useState } from 'react';
import Button from '../components/ui/Button';
import { apiService } from '../services/api';

interface EmailTemplate {
  id: number;
  name: string;
  display_name: string;
  description: string;
  category: string;
  subject_template: string;
  html_template: string;
  text_template: string;
  variables: string[];
  required_variables: string[];
  is_active: boolean;
  is_default: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

function EmailTemplates() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<EmailTemplate | null>(null);
  const [previewing, setPreviewing] = useState<EmailTemplate | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [renderedTemplate, setRenderedTemplate] = useState<any>(null);

  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: 'general',
    subject_template: '',
    html_template: '',
    text_template: '',
    variables: [] as string[],
    required_variables: [] as string[],
    is_active: true
  });

  const [renderForm, setRenderForm] = useState<Record<string, string>>({});

  const loadTemplates = useCallback(async () => {
    try {
      const response = await apiService.getEmailTemplates({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        is_active: true,
        search: searchQuery || undefined,
        limit: 50
      });
      setTemplates(response.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleCreate = async () => {
    if (!formData.name.trim() || !formData.display_name.trim()) return;

    try {
      await apiService.createEmailTemplate(formData);
      await loadTemplates();
      setFormData({
        name: '',
        display_name: '',
        description: '',
        category: 'general',
        subject_template: '',
        html_template: '',
        text_template: '',
        variables: [],
        required_variables: [],
        is_active: true
      });
      setCreating(false);
    } catch (error) {
      console.error('Failed to create template:', error);
    }
  };

  const handleUpdate = async () => {
    if (!editing) return;

    try {
      await apiService.updateEmailTemplate(editing.id, formData);
      await loadTemplates();
      setEditing(null);
    } catch (error) {
      console.error('Failed to update template:', error);
    }
  };

  const handleDelete = async (templateId: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот шаблон?')) return;

    try {
      await apiService.deleteEmailTemplate(templateId);
      await loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
    }
  };

  const handleDuplicate = async (template: EmailTemplate) => {
    try {
      const newName = `${template.name}_copy`;
      await apiService.duplicateEmailTemplate(template.id, {
        new_name: newName,
        new_display_name: `${template.display_name} (Копия)`
      });
      await loadTemplates();
    } catch (error) {
      console.error('Failed to duplicate template:', error);
    }
  };

  const handleRender = async () => {
    if (!previewing) return;

    try {
      const rendered = await apiService.renderEmailTemplate(previewing.id, renderForm);
      setRenderedTemplate(rendered.rendered);
    } catch (error) {
      console.error('Failed to render template:', error);
    }
  };

  const startEdit = (template: EmailTemplate) => {
    setEditing(template);
    setFormData({
      name: template.name,
      display_name: template.display_name,
      description: template.description,
      category: template.category,
      subject_template: template.subject_template,
      html_template: template.html_template,
      text_template: template.text_template,
      variables: template.variables,
      required_variables: template.required_variables,
      is_active: template.is_active
    });
  };

  const startPreview = (template: EmailTemplate) => {
    setPreviewing(template);
    setRenderedTemplate(null);
    // Initialize render form with template variables
    const initialRenderForm: Record<string, string> = {};
    template.required_variables.forEach(variable => {
      initialRenderForm[variable] = '';
    });
    template.variables.forEach(variable => {
      if (!initialRenderForm[variable]) {
        initialRenderForm[variable] = '';
      }
    });
    setRenderForm(initialRenderForm);
  };

  const cancelEdit = () => {
    setEditing(null);
    resetForm();
  };

  const cancelPreview = () => {
    setPreviewing(null);
    setRenderedTemplate(null);
    setRenderForm({});
  };

  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      category: 'general',
      subject_template: '',
      html_template: '',
      text_template: '',
      variables: [],
      required_variables: [],
      is_active: true
    });
  };

  const categories = [
    { value: 'all', label: 'Все категории' },
    { value: 'orders', label: 'Заказы' },
    { value: 'tasks', label: 'Задачи' },
    { value: 'welcome', label: 'Приветственные' },
    { value: 'payments', label: 'Оплаты' },
    { value: 'general', label: 'Общие' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-van-gogh-ultramarine"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Email шаблоны</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">Управление шаблонами email рассылок</p>
        </div>
        <Button
          onClick={() => setCreating(true)}
          variant="primary"
          className="flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Создать шаблон
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Поиск шаблонов..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
            />
          </div>
        </div>
        <div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
          >
            {categories.map(category => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Create/Edit Form */}
      {(creating || editing) && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-van-gogh-starry-night-blue">
              {editing ? 'Редактировать шаблон' : 'Создать новый шаблон'}
            </h2>
            <button
              onClick={editing ? cancelEdit : () => { setCreating(false); resetForm(); }}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Системное имя
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="order_confirmation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Отображаемое название
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="Подтверждение заказа"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Категория
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                >
                  {categories.filter(cat => cat.value !== 'all').map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Переменные (через запятую)
                </label>
                <input
                  type="text"
                  value={formData.variables.join(', ')}
                  onChange={(e) => setFormData({
                    ...formData,
                    variables: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                  })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="customer_name, order_number, total_amount"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Обязательные переменные (через запятую)
                </label>
                <input
                  type="text"
                  value={formData.required_variables.join(', ')}
                  onChange={(e) => setFormData({
                    ...formData,
                    required_variables: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                  })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="customer_email, order_number"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Шаблон темы
                </label>
                <input
                  type="text"
                  value={formData.subject_template}
                  onChange={(e) => setFormData({ ...formData, subject_template: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="Подтверждение заказа #{{ order_number }}"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  HTML шаблон
                </label>
                <textarea
                  value={formData.html_template}
                  onChange={(e) => setFormData({ ...formData, html_template: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent font-mono"
                  rows={6}
                  placeholder="<h1>Спасибо за заказ, {{ customer_name }}!</h1><p>Номер заказа: {{ order_number }}</p>"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Текстовый шаблон
                </label>
                <textarea
                  value={formData.text_template}
                  onChange={(e) => setFormData({ ...formData, text_template: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent font-mono"
                  rows={4}
                  placeholder="Спасибо за заказ, {{ customer_name }}! Номер заказа: {{ order_number }}"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <Button
              onClick={editing ? handleUpdate : handleCreate}
              variant="primary"
            >
              {editing ? 'Сохранить изменения' : 'Создать шаблон'}
            </Button>
            <Button
              onClick={editing ? cancelEdit : () => { setCreating(false); resetForm(); }}
              variant="secondary"
            >
              Отмена
            </Button>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-screen overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-semibold text-van-gogh-starry-night-blue">
                Предпросмотр: {previewing.display_name}
              </h2>
              <button
                onClick={cancelPreview}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Variable Input Form */}
              {previewing.variables.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-van-gogh-chrome-green mb-3">
                    Значения переменных
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {previewing.variables.map(variable => (
                      <div key={variable}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {variable} {previewing.required_variables.includes(variable) && '*'}
                        </label>
                        <input
                          type="text"
                          value={renderForm[variable] || ''}
                          onChange={(e) => setRenderForm({
                            ...renderForm,
                            [variable]: e.target.value
                          })}
                          className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                        />
                      </div>
                    ))}
                  </div>
                  <div className="mt-4">
                    <Button onClick={handleRender} variant="secondary">
                      Рендерить шаблон
                    </Button>
                  </div>
                </div>
              )}

              {/* Rendered Result */}
              {renderedTemplate && (
                <div className="space-y-4">
                  <h3 className="font-medium text-van-gogh-chrome-green">Результат:</h3>

                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-medium mb-2">Тема:</h4>
                    <div className="bg-white p-2 rounded border">
                      {renderedTemplate.subject || previewing.subject_template}
                    </div>
                  </div>

                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-medium mb-2">HTML версия:</h4>
                    <div className="bg-white p-4 rounded border max-h-96 overflow-y-auto">
                      <div dangerouslySetInnerHTML={{__html: renderedTemplate.html || previewing.html_template}} />
                    </div>
                  </div>

                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-medium mb-2">Текстовая версия:</h4>
                    <div className="bg-white p-4 rounded border font-mono whitespace-pre-wrap">
                      {renderedTemplate.text || previewing.text_template}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-van-gogh-starry-night-blue">
                    {template.display_name}
                  </h3>
                  {template.is_default && (
                    <span className="px-2 py-1 bg-van-gogh-ultramarine/20 text-van-gogh-ultramarine text-xs rounded">
                      По умолчанию
                    </span>
                  )}
                </div>
                <p className="text-sm text-van-gogh-chrome-green mb-2">
                  {template.description}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="capitalize">{template.category}</span>
                  <span>•</span>
                  <span>Использован {template.usage_count || 0} раз</span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  {template.variables.length > 0 && (
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      Переменных: {template.variables.length}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex space-x-1">
                <button
                  onClick={() => startPreview(template)}
                  className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                  title="Предпросмотр"
                >
                  <EyeIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDuplicate(template)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  title="Дублировать"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => startEdit(template)}
                  className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                  title="Редактировать"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(template.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Удалить"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {templates.length === 0 && !loading && (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-van-gogh-chrome-green">Нет шаблонов</h3>
          <p className="mt-1 text-sm text-gray-500">
            Создайте свой первый email шаблон.
          </p>
          <div className="mt-6">
            <Button onClick={() => setCreating(true)} variant="primary">
              <PlusIcon className="w-5 h-5 mr-2" />
              Создать шаблон
            </Button>
          </div>
        </div>
      )}

      {/* Initialize Defaults Button */}
      <div className="text-center">
        <Button
          onClick={async () => {
            try {
              await apiService.initializeDefaultEmailTemplates();
              await loadTemplates();
              alert('Стандартные шаблоны успешно инициализированы');
            } catch (error) {
              console.error('Failed to initialize defaults:', error);
              alert('Ошибка инициализации стандартных шаблонов');
            }
          }}
          variant="secondary"
        >
          Инициализировать стандартные шаблоны
        </Button>
      </div>
    </div>
  );
}

export default EmailTemplates;
