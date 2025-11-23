import {
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  EyeIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { useCallback, useEffect, useState } from 'react';

interface IntentTemplate {
  id: string;
  intent_type: string;
  name: string;
  template: string;
  variables: string[];
  is_active: boolean;
  language: string;
}

const INTENT_TYPES = [
  { id: 'order_request', name: 'Запрос заказа' },
  { id: 'pricing_inquiry', name: 'Вопрос о цене' },
  { id: 'delivery_question', name: 'Вопрос о доставке' },
  { id: 'support_request', name: 'Запрос поддержки' },
  { id: 'complaint', name: 'Жалоба' },
  { id: 'status_check', name: 'Проверка статуса' },
  { id: 'general', name: 'Общее обращение' }
] as const;

export default function AITemplates() {
  const [templates, setTemplates] = useState<IntentTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<IntentTemplate | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [previewContext, setPreviewContext] = useState({
    customer_name: 'Иван Иванов',
    order_id: '12345',
    order_status: 'completed',
    order_date: '2024-01-15',
    due_date: '2024-01-20',
    contact_method: 'свяжитесь с нами',
    dashboard_url: 'https://app.company.com'
  });

  const loadTemplates = useCallback(async () => {
    try {
      // TODO: Create API endpoint for templates
      // For now, use mock data
      const mockTemplates: IntentTemplate[] = INTENT_TYPES.map(type => ({
        id: type.id,
        intent_type: type.id,
        name: type.name,
        template: getDefaultTemplate(type.id),
        variables: getVariablesForIntent(type.id),
        is_active: true,
        language: 'ru'
      }));
      setTemplates(mockTemplates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const getDefaultTemplate = (intentType: string): string => {
    const templates: Record<string, string> = {
      order_request: `Спасибо за ваш интерес к нашим услугам!

Для оформления заказа нам потребуется:
• Описание дизайна или логотипа
• Тип материала и цвет
• Количество изделий
• Срок изготовления

Пожалуйста, {contact_method} с указанными данными, и мы подготовим индивидуальное предложение.

📞 Телефон: +7 (495) 123-45-67
📧 Email: info@company.com`,
      pricing_inquiry: `Здравствуйте!

Стоимость наших услуг зависит от нескольких факторов:
• Тип материала и цвет
• Сложность дизайна
• Размер и количество изделий
• Срочность заказа

Минимальный тираж: 50 штук
Базовая цена: от 150 руб/шт

Для точного расчета отправьте нам:
• Макет или описание дизайна
• Требования к продукции
• Планируемый тираж

Мы свяжемся с вами в течение 1-2 часов!`,
      delivery_question: `Информация о доставке:

🚚 Мы осуществляем доставку по всей России через проверенные транспортные компании
⏱️ Срок доставки: 3-7 рабочих дней (в зависимости от региона)
💰 Стоимость рассчитывается индивидуально после оформления заказа

Доставка осуществляется до двери или до пункта выдачи заказов.

Для точной информации о стоимости доставки для вашего региона, пожалуйста, укажите город доставки.`,
      support_request: `Мы всегда готовы помочь!

Для оперативного решения вашего вопроса опишите ситуацию подробнее:
• Что именно произошло?
• Когда это случилось?
• Есть ли у вас номер заказа?

Наши специалисты свяжутся с вами в течение 30 минут.

📞 Горячая линия: +7 (495) 123-45-67 (работаем 9:00-18:00 МСК)

Или напишите нам на email: support@company.com`,
      complaint: `Нам очень жаль, что вы остались недовольны нашим сервисом.

Ваше мнение очень важно для нас! Для разбора ситуации и компенсации неудобств:

1. Опишите подробно, что произошло
2. Укажите номер заказа или контактные данные
3. Уточните, какую компенсацию вы хотели бы получить

Мы разберемся в ситуации в кратчайшие сроки и обязательно свяжемся с вами!

📞 Директор по качеству: +7 (495) 999-88-77`,
      status_check: `Информация о статусе заказа #{order_id}:

📋 Текущий статус: {order_status}
📅 Дата заказа: {order_date}
⏰ Ориентировочная готовность: {due_date}

Подробную информацию о этапах производства можно посмотреть в личном кабинете: {dashboard_url}

Если есть вопросы - звоните: +7 (495) 123-45-67`,
      general: `Спасибо за ваше обращение!

Мы получили ваше сообщение и ответим в ближайшее время.

Для оперативного решения вопроса уточните:
• Темы обращения
• Контактные данные для связи
• Номер заказа (если есть)

📞 Телефон: +7 (495) 123-45-67
📧 Email: info@company.com`
    };
    return templates[intentType] || templates.general;
  };

  const getVariablesForIntent = (intentType: string): string[] => {
    const variables: Record<string, string[]> = {
      order_request: ['contact_method'],
      pricing_inquiry: [],
      delivery_question: [],
      support_request: [],
      complaint: [],
      status_check: ['order_id', 'order_status', 'order_date', 'due_date', 'dashboard_url'],
      general: []
    };
    return variables[intentType] || [];
  };

  const handleSaveTemplate = async (template: IntentTemplate) => {
    setSaving(true);
    try {
      // TODO: Create API endpoint for saving templates
      // For now, just update local state
      setTemplates(prev =>
        prev.map(t => t.id === template.id ? template : t)
      );
      alert('Шаблон успешно сохранен');
    } catch (error) {
      console.error('Failed to save template:', error);
      alert('Ошибка при сохранении шаблона');
    } finally {
      setSaving(false);
      setIsEditing(false);
    }
  };

  const renderTemplate = (template: string, context: any): string => {
    let result = template;
    Object.keys(context).forEach(key => {
      const placeholder = `{${key}}`;
      result = result.replace(new RegExp(placeholder, 'g'), context[key]);
    });
    return result;
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Шаблоны ответов ИИ</h1>
          <p className="text-gray-600 mt-2">Настройка шаблонов автоматических ответов</p>
        </div>
        <button
          onClick={loadTemplates}
          className="btn-secondary flex items-center"
        >
          <DocumentTextIcon className="w-5 h-5 mr-2" />
          Обновить
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Templates List */}
        <div className="card">
          <div className="flex items-center mb-4">
            <ChatBubbleLeftRightIcon className="w-6 h-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Шаблоны ответов</h3>
          </div>

          <div className="space-y-3">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedTemplate?.id === template.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      template.is_active ? 'bg-green-500' : 'bg-gray-300'
                    }`}></div>
                    <div>
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <p className="text-sm text-gray-600 truncate">
                        {template.template.substring(0, 80)}...
                      </p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedTemplate(template);
                        setIsEditing(true);
                      }}
                      className="p-1 text-gray-400 hover:text-blue-600"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Template Editor */}
        <div className="card">
          {selectedTemplate ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <DocumentTextIcon className="w-6 h-6 text-blue-600 mr-2" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    {isEditing ? 'Редактирование' : 'Просмотр'} шаблона
                  </h3>
                </div>
                <div className="flex space-x-2">
                  {!isEditing && (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="btn-secondary flex items-center"
                    >
                      <PencilIcon className="w-4 h-4 mr-2" />
                      Редактировать
                    </button>
                  )}
                  {isEditing && (
                    <button
                      onClick={() => setIsEditing(false)}
                      className="btn-secondary"
                    >
                      Отмена
                    </button>
                  )}
                </div>
              </div>

              {selectedTemplate && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Тип намерения
                    </label>
                    <select
                      value={selectedTemplate.intent_type}
                      onChange={(e) => setSelectedTemplate(prev => prev ? {
                        ...prev,
                        intent_type: e.target.value,
                        name: INTENT_TYPES.find(t => t.id === e.target.value)?.name || prev.name
                      } : null)}
                      className="input-field"
                      disabled={!isEditing}
                    >
                      {INTENT_TYPES.map((type) => (
                        <option key={type.id} value={type.id}>
                          {type.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {isEditing ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Шаблон ответа
                      </label>
                      <textarea
                        value={selectedTemplate.template}
                        onChange={(e) => setSelectedTemplate(prev => prev ? {
                          ...prev,
                          template: e.target.value
                        } : null)}
                        className="input-field min-h-[300px] font-mono text-sm"
                        placeholder="Введите шаблон ответа..."
                      />
                      <div className="mt-2">
                        <p className="text-xs text-gray-500">
                          Доступные переменные: {selectedTemplate.variables.map(v =>
                            `{${v}}`
                          ).join(', ')}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Шаблон ответа
                      </label>
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 min-h-[300px] whitespace-pre-wrap font-mono text-sm">
                        {renderTemplate(selectedTemplate.template, previewContext)}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedTemplate.is_active}
                        onChange={(e) => setSelectedTemplate(prev => prev ? {
                          ...prev,
                          is_active: e.target.checked
                        } : null)}
                        className="mr-2"
                        disabled={!isEditing}
                      />
                      <span className="text-sm text-gray-700">Активен</span>
                    </label>
                  </div>

                  {isEditing && (
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => handleSaveTemplate(selectedTemplate)}
                        disabled={saving}
                        className="btn-primary flex items-center"
                      >
                        {saving && <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin mr-2"></div>}
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        {saving ? 'Сохранение...' : 'Сохранить'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <DocumentTextIcon className="w-12 h-12 mb-4" />
              <p>Выберите шаблон для просмотра или редактирования</p>
            </div>
          )}
        </div>
      </div>

      {/* Preview Context */}
      <div className="card">
        <div className="flex items-center mb-4">
          <EyeIcon className="w-6 h-6 text-green-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Контекст для предпросмотра</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(previewContext).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {key.replace('_', ' ').toUpperCase()}
              </label>
              <input
                type="text"
                value={value}
                onChange={(e) => setPreviewContext(prev => ({
                  ...prev,
                  [key]: e.target.value
                }))}
                className="input-field text-sm"
              />
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-500 mt-4">
          Эти значения используются для предварительного просмотра шаблонов.
          В реальном использовании они будут заменяться на реальные данные из системы.
        </p>
      </div>
    </div>
  );
}
