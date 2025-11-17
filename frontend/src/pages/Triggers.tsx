import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  BoltIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Trigger {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  event_type: string;
  conditions?: any;
  target_stage_id?: number;
  target_stage?: {
    id: number;
    name: string;
  };
  is_active: boolean;
  created_at: string;
}

interface Stage {
  id: number;
  name: string;
  entity_type: string;
}

export default function Triggers() {
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [stages, setStages] = useState<Stage[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTrigger, setSelectedTrigger] = useState<Trigger | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null);
  const [deletingTrigger, setDeletingTrigger] = useState<Trigger | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    entity_type: 'ORDER',
    event_type: 'ORDER_CREATED',
    conditions: '{}',
    target_stage_id: '',
    is_active: true
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [triggersData, stagesData] = await Promise.all([
        apiService.getAutomationTriggers(),
        apiService.getAutomationStages()
      ]);
      setTriggers(triggersData);
      setStages(stagesData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadData();
      return;
    }

    try {
      // Фильтрация на клиенте
      const filtered = triggers.filter(trigger =>
        trigger.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (trigger.description && trigger.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
        trigger.entity_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        trigger.event_type.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setTriggers(filtered);
    } catch (error) {
      console.error('Failed to search triggers:', error);
    }
  };

  const filteredTriggers = triggers.filter(trigger =>
    trigger.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (trigger.description && trigger.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
    trigger.entity_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    trigger.event_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      entity_type: 'ORDER',
      event_type: 'ORDER_CREATED',
      conditions: '{}',
      target_stage_id: '',
      is_active: true
    });
  };

  const handleCreateTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name) return;

    setSubmitting(true);
    try {
      const triggerData = {
        ...formData,
        conditions: JSON.parse(formData.conditions || '{}'),
        target_stage_id: formData.target_stage_id ? parseInt(formData.target_stage_id) : null
      };

      await apiService.createAutomationTrigger(triggerData);
      setShowCreateModal(false);
      resetForm();
      loadData();
    } catch (error) {
      console.error('Failed to create trigger:', error);
      alert('Ошибка при создании триггера');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditTrigger = (trigger: Trigger) => {
    setEditingTrigger(trigger);
    setFormData({
      name: trigger.name,
      description: trigger.description || '',
      entity_type: trigger.entity_type,
      event_type: trigger.event_type,
      conditions: JSON.stringify(trigger.conditions || {}, null, 2),
      target_stage_id: trigger.target_stage_id?.toString() || '',
      is_active: trigger.is_active
    });
    setShowEditModal(true);
    setSelectedTrigger(null);
  };

  const handleUpdateTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTrigger || !formData.name) return;

    setSubmitting(true);
    try {
      const triggerData = {
        ...formData,
        conditions: JSON.parse(formData.conditions || '{}'),
        target_stage_id: formData.target_stage_id ? parseInt(formData.target_stage_id) : null
      };

      await apiService.updateAutomationTrigger(editingTrigger.id, triggerData);
      setShowEditModal(false);
      setEditingTrigger(null);
      resetForm();
      loadData();
    } catch (error) {
      console.error('Failed to update trigger:', error);
      alert('Ошибка при обновлении триггера');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTrigger = (trigger: Trigger) => {
    setDeletingTrigger(trigger);
    setShowDeleteModal(true);
    setSelectedTrigger(null);
  };

  const confirmDeleteTrigger = async () => {
    if (!deletingTrigger) return;

    setSubmitting(true);
    try {
      await apiService.deleteAutomationTrigger(deletingTrigger.id);
      setShowDeleteModal(false);
      setDeletingTrigger(null);
      loadData();
    } catch (error) {
      console.error('Failed to delete trigger:', error);
      alert('Ошибка при удалении триггера');
    } finally {
      setSubmitting(false);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const closeModals = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowDeleteModal(false);
    setSelectedTrigger(null);
    setEditingTrigger(null);
    setDeletingTrigger(null);
    resetForm();
  };

  const getEntityTypeLabel = (entityType: string) => {
    switch (entityType) {
      case 'CUSTOMER': return 'Клиент';
      case 'ORDER': return 'Заказ';
      case 'TASK': return 'Задача';
      case 'PRODUCTION_STEP': return 'Производство';
      case 'COMMUNICATION': return 'Коммуникация';
      default: return entityType;
    }
  };

  const getEventTypeLabel = (eventType: string) => {
    const labels: { [key: string]: string } = {
      // Заказы
      'ORDER_CREATED': 'Заказ создан',
      'ORDER_STATUS_CHANGED': 'Статус заказа изменен',
      'ORDER_COMPLETED': 'Заказ завершен',
      'PAYMENT_RECEIVED': 'Получена оплата',

      // Задачи
      'TASK_CREATED': 'Задача создана',
      'TASK_STATUS_CHANGED': 'Статус задачи изменен',
      'TASK_COMPLETED': 'Задача завершена',
      'TASK_ASSIGNED': 'Задача назначена',
      'DEADLINE_APPROACHING': 'Приближается дедлайн',

      // Производство
      'PRODUCTION_STARTED': 'Производство начато',
      'PRODUCTION_STEP_COMPLETED': 'Этап производства завершен',
      'PRODUCTION_COMPLETED': 'Производство завершено',
      'PRODUCTION_OVERDUE': 'Производство просрочено',
      'PRINT_COMPLETED': 'Печать завершена',

      // Клиенты
      'CUSTOMER_CREATED': 'Клиент создан',
      'CUSTOMER_UPDATED': 'Клиент обновлен',
      'CUSTOMER_LOYALTY_CHANGED': 'Лояльность клиента изменена',

      // Коммуникации
      'MESSAGE_RECEIVED': 'Получено сообщение',
      'MESSAGE_SENT': 'Отправлено сообщение',
      'EMAIL_OPENED': 'Email открыт',

      // Бизнес-процессы
      'MANAGER_APPROVAL': 'Утверждение менеджером',
      'DESIGN_COMPLETED': 'Дизайн завершен',
      'CLIENT_APPROVED': 'Утверждено клиентом',
      'QUALITY_APPROVED': 'Утверждено качеством',
      'DESIGNER_ASSIGNED': 'Дизайнер назначен',
      'PRINTING_COMPLETED': 'Печать завершена',
      'STAGE_ENTERED': 'Вход в стадию',
      'APPROVAL_GRANTED': 'Утверждение получено',
      'ASSIGNEE_ASSIGNED': 'Исполнитель назначен',
      'ORDER_APPROVED': 'Заказ утвержден',
      'CUSTOMER_APPROVED': 'Утверждено клиентом',
      'DESIGN_APPROVED': 'Дизайн утвержден',
      'STAGE_COMPLETED': 'Стадия завершена',
      'ORDER_UPDATED': 'Заказ обновлен',
      'APPROVAL_COMPLETED': 'Утверждение завершено',

      // Avito интеграция
      'AVITO_MESSAGE_RECEIVED': 'Получено сообщение Avito',
      'AVITO_CHAT_CREATED': 'Чат Avito создан',
      'AVITO_CHAT_CLOSED': 'Чат Avito закрыт'
    };
    return labels[eventType] || eventType;
  };

  const getFilteredStages = (entityType: string) => {
    return stages.filter(stage => stage.entity_type === entityType);
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
          <h1 className="text-3xl font-bold text-gray-900">Триггеры автоматизации</h1>
          <p className="text-gray-600 mt-2">Управление триггерами событий для автоматизации</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Добавить триггер
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Поиск триггеров по названию, описанию или типу..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="input-field"
            />
          </div>
          <button
            onClick={handleSearch}
            className="btn-secondary flex items-center"
          >
            <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
            Поиск
          </button>
        </div>
      </div>

      {/* Triggers List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Триггеры ({filteredTriggers.length})
          </h3>
        </div>

        {filteredTriggers.length > 0 ? (
          <div className="space-y-3">
            {filteredTriggers.map((trigger) => (
              <div key={trigger.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <BoltIcon className="w-5 h-5 text-yellow-600" />
                      <h4 className="font-medium text-gray-900">{trigger.name}</h4>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        trigger.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trigger.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <span>{getEntityTypeLabel(trigger.entity_type)}</span>
                      <span className="text-blue-600">→</span>
                      <span>{getEventTypeLabel(trigger.event_type)}</span>
                      {trigger.target_stage && (
                        <>
                          <span className="text-blue-600">→</span>
                          <span className="text-green-600">{trigger.target_stage.name}</span>
                        </>
                      )}
                    </div>

                    {trigger.description && (
                      <p className="text-sm text-gray-500 mb-2">{trigger.description}</p>
                    )}

                    {trigger.conditions && Object.keys(trigger.conditions).length > 0 && (
                      <div className="text-xs text-gray-500">
                        Условия: {JSON.stringify(trigger.conditions)}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => setSelectedTrigger(trigger)}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      title="Просмотр деталей"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleEditTrigger(trigger)}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      title="Редактировать"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <BoltIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Триггеры не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первый триггер'}
            </p>
          </div>
        )}
      </div>

      {/* Trigger Details Modal */}
      {selectedTrigger && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Детали триггера</h3>
              <button
                onClick={() => setSelectedTrigger(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <BoltIcon className="w-6 h-6 text-yellow-600" />
                <div>
                  <h4 className="font-medium text-gray-900">{selectedTrigger.name}</h4>
                  <p className="text-sm text-gray-600">ID: {selectedTrigger.id}</p>
                </div>
              </div>

              {selectedTrigger.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Описание</label>
                  <p className="text-gray-900">{selectedTrigger.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Тип сущности</label>
                  <p className="text-gray-900">{getEntityTypeLabel(selectedTrigger.entity_type)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Событие</label>
                  <p className="text-gray-900">{getEventTypeLabel(selectedTrigger.event_type)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Целевая стадия</label>
                  <p className="text-green-600">
                    {selectedTrigger.target_stage ? selectedTrigger.target_stage.name : 'Не указана'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <p className={`text-sm ${selectedTrigger.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedTrigger.is_active ? 'Активен' : 'Неактивен'}
                  </p>
                </div>
              </div>

              {selectedTrigger.conditions && Object.keys(selectedTrigger.conditions).length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Условия</label>
                  <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
                    {JSON.stringify(selectedTrigger.conditions, null, 2)}
                  </pre>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Создан</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedTrigger.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">ID</label>
                  <p className="text-xs text-gray-600">{selectedTrigger.id}</p>
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-6">
              <button
                onClick={() => handleDeleteTrigger(selectedTrigger)}
                className="btn-danger"
              >
                Удалить
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedTrigger(null)}
                  className="btn-secondary"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => handleEditTrigger(selectedTrigger)}
                  className="btn-primary flex items-center"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Редактировать
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Trigger Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Добавить триггер</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTrigger} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Название триггера"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Описание
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input-field"
                  rows={3}
                  placeholder="Описание триггера"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип сущности
                </label>
                <select
                  value={formData.entity_type}
                  onChange={(e) => setFormData({ ...formData, entity_type: e.target.value, event_type: 'ORDER_CREATED', target_stage_id: '' })}
                  className="input-field"
                  disabled={submitting}
                >
                  <option value="CUSTOMER">Клиент</option>
                  <option value="ORDER">Заказ</option>
                  <option value="TASK">Задача</option>
                  <option value="PRODUCTION_STEP">Производство</option>
                  <option value="COMMUNICATION">Коммуникация</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип события
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                  className="input-field"
                  disabled={submitting}
                >
                  {/* Заказы */}
                  {formData.entity_type === 'ORDER' && (
                    <>
                      <option value="ORDER_CREATED">Заказ создан</option>
                      <option value="ORDER_STATUS_CHANGED">Статус заказа изменен</option>
                      <option value="ORDER_COMPLETED">Заказ завершен</option>
                      <option value="PAYMENT_RECEIVED">Получена оплата</option>
                    </>
                  )}

                  {/* Задачи */}
                  {formData.entity_type === 'TASK' && (
                    <>
                      <option value="TASK_CREATED">Задача создана</option>
                      <option value="TASK_STATUS_CHANGED">Статус задачи изменен</option>
                      <option value="TASK_COMPLETED">Задача завершена</option>
                      <option value="TASK_ASSIGNED">Задача назначена</option>
                      <option value="DEADLINE_APPROACHING">Приближается дедлайн</option>
                    </>
                  )}

                  {/* Клиенты */}
                  {formData.entity_type === 'CUSTOMER' && (
                    <>
                      <option value="CUSTOMER_CREATED">Клиент создан</option>
                      <option value="CUSTOMER_UPDATED">Клиент обновлен</option>
                      <option value="CUSTOMER_LOYALTY_CHANGED">Лояльность клиента изменена</option>
                    </>
                  )}

                  {/* Производство */}
                  {formData.entity_type === 'PRODUCTION_STEP' && (
                    <>
                      <option value="PRODUCTION_STARTED">Производство начато</option>
                      <option value="PRODUCTION_STEP_COMPLETED">Этап производства завершен</option>
                      <option value="PRODUCTION_COMPLETED">Производство завершено</option>
                      <option value="PRODUCTION_OVERDUE">Производство просрочено</option>
                      <option value="PRINT_COMPLETED">Печать завершена</option>
                    </>
                  )}

                  {/* Коммуникации */}
                  {formData.entity_type === 'COMMUNICATION' && (
                    <>
                      <option value="MESSAGE_RECEIVED">Получено сообщение</option>
                      <option value="MESSAGE_SENT">Отправлено сообщение</option>
                      <option value="EMAIL_OPENED">Email открыт</option>
                    </>
                  )}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Целевая стадия
                </label>
                <select
                  value={formData.target_stage_id}
                  onChange={(e) => setFormData({ ...formData, target_stage_id: e.target.value })}
                  className="input-field"
                  disabled={submitting}
                >
                  <option value="">Не указана</option>
                  {getFilteredStages(formData.entity_type).map(stage => (
                    <option key={stage.id} value={stage.id}>
                      {stage.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Условия (JSON)
                </label>
                <textarea
                  value={formData.conditions}
                  onChange={(e) => setFormData({ ...formData, conditions: e.target.value })}
                  className="input-field font-mono text-xs"
                  rows={4}
                  placeholder='{"field": "value", "operator": "equals"}'
                  disabled={submitting}
                />
              </div>
            </form>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={closeModals}
                className="btn-secondary"
                disabled={submitting}
              >
                Отмена
              </button>
              <button
                onClick={handleCreateTrigger}
                disabled={submitting || !formData.name}
                className="btn-primary"
              >
                {submitting ? 'Создание...' : 'Создать триггер'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Trigger Modal */}
      {showEditModal && editingTrigger && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Редактировать триггер</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateTrigger} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Название триггера"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Описание
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input-field"
                  rows={3}
                  placeholder="Описание триггера"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип сущности
                </label>
                <select
                  value={formData.entity_type}
                  onChange={(e) => setFormData({ ...formData, entity_type: e.target.value, event_type: 'ORDER_CREATED', target_stage_id: '' })}
                  className="input-field"
                  disabled={submitting}
                >
                  <option value="CUSTOMER">Клиент</option>
                  <option value="ORDER">Заказ</option>
                  <option value="TASK">Задача</option>
                  <option value="PRODUCTION_STEP">Производство</option>
                  <option value="COMMUNICATION">Коммуникация</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип события
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                  className="input-field"
                  disabled={submitting}
                >
                  {/* Заказы */}
                  {formData.entity_type === 'ORDER' && (
                    <>
                      <option value="ORDER_CREATED">Заказ создан</option>
                      <option value="ORDER_STATUS_CHANGED">Статус заказа изменен</option>
                      <option value="ORDER_COMPLETED">Заказ завершен</option>
                      <option value="PAYMENT_RECEIVED">Получена оплата</option>
                    </>
                  )}

                  {/* Задачи */}
                  {formData.entity_type === 'TASK' && (
                    <>
                      <option value="TASK_CREATED">Задача создана</option>
                      <option value="TASK_STATUS_CHANGED">Статус задачи изменен</option>
                      <option value="TASK_COMPLETED">Задача завершена</option>
                      <option value="TASK_ASSIGNED">Задача назначена</option>
                      <option value="DEADLINE_APPROACHING">Приближается дедлайн</option>
                    </>
                  )}

                  {/* Клиенты */}
                  {formData.entity_type === 'CUSTOMER' && (
                    <>
                      <option value="CUSTOMER_CREATED">Клиент создан</option>
                      <option value="CUSTOMER_UPDATED">Клиент обновлен</option>
                      <option value="CUSTOMER_LOYALTY_CHANGED">Лояльность клиента изменена</option>
                    </>
                  )}

                  {/* Производство */}
                  {formData.entity_type === 'PRODUCTION_STEP' && (
                    <>
                      <option value="PRODUCTION_STARTED">Производство начато</option>
                      <option value="PRODUCTION_STEP_COMPLETED">Этап производства завершен</option>
                      <option value="PRODUCTION_COMPLETED">Производство завершено</option>
                      <option value="PRODUCTION_OVERDUE">Производство просрочено</option>
                      <option value="PRINT_COMPLETED">Печать завершена</option>
                    </>
                  )}

                  {/* Коммуникации */}
                  {formData.entity_type === 'COMMUNICATION' && (
                    <>
                      <option value="MESSAGE_RECEIVED">Получено сообщение</option>
                      <option value="MESSAGE_SENT">Отправлено сообщение</option>
                      <option value="EMAIL_OPENED">Email открыт</option>
                    </>
                  )}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Целевая стадия
                </label>
                <select
                  value={formData.target_stage_id}
                  onChange={(e) => setFormData({ ...formData, target_stage_id: e.target.value })}
                  className="input-field"
                  disabled={submitting}
                >
                  <option value="">Не указана</option>
                  {getFilteredStages(formData.entity_type).map(stage => (
                    <option key={stage.id} value={stage.id}>
                      {stage.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Условия (JSON)
                </label>
                <textarea
                  value={formData.conditions}
                  onChange={(e) => setFormData({ ...formData, conditions: e.target.value })}
                  className="input-field font-mono text-xs"
                  rows={4}
                  placeholder='{"field": "value", "operator": "equals"}'
                  disabled={submitting}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  disabled={submitting}
                />
                <label htmlFor="edit_is_active" className="ml-2 block text-sm text-gray-900">
                  Активен
                </label>
              </div>
            </form>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={closeModals}
                className="btn-secondary"
                disabled={submitting}
              >
                Отмена
              </button>
              <button
                onClick={handleUpdateTrigger}
                disabled={submitting || !formData.name}
                className="btn-primary"
              >
                {submitting ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingTrigger && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Подтверждение удаления</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="flex items-center mb-4">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-600 mr-4" />
              <div>
                <p className="text-gray-900 font-medium">Удалить триггер?</p>
                <p className="text-sm text-gray-600 mt-1">
                  Вы уверены, что хотите удалить триггер "{deletingTrigger.name}"?
                  Это действие нельзя отменить.
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={closeModals}
                className="btn-secondary"
                disabled={submitting}
              >
                Отмена
              </button>
              <button
                onClick={confirmDeleteTrigger}
                disabled={submitting}
                className="btn-danger"
              >
                {submitting ? 'Удаление...' : 'Удалить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
