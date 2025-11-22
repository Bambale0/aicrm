import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Play, Pause, Zap } from 'lucide-react';
import { apiService } from '../services/api';

interface Trigger {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  event_type: string;
  conditions?: any;
  target_stage_id?: number;
  is_active: boolean;
  created_at: string;
}

const Triggers: React.FC = () => {
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [stages, setStages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    entity_type: 'order',
    event_type: 'created',
    conditions: '{}',
    target_stage_id: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [triggersResponse, stagesResponse] = await Promise.all([
        apiService.getAutomationTriggers(),
        apiService.getAutomationStages()
      ]);
      setTriggers(triggersResponse);
      setStages(stagesResponse);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let conditions;
      try {
        conditions = JSON.parse(formData.conditions);
      } catch {
        conditions = {};
      }

      const triggerData = {
        ...formData,
        conditions,
        target_stage_id: formData.target_stage_id ? parseInt(formData.target_stage_id) : undefined
      };

      if (editingTrigger) {
        await apiService.updateAutomationTrigger(editingTrigger.id, triggerData);
        alert('Триггер обновлен');
      } else {
        await apiService.createAutomationTrigger(triggerData);
        alert('Триггер создан');
      }
      setShowModal(false);
      setEditingTrigger(null);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error('Error saving trigger:', error);
      alert(error.response?.data?.detail || 'Ошибка при сохранении триггера');
    }
  };

  const handleEdit = (trigger: Trigger) => {
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
    setShowModal(true);
  };

  const handleDelete = async (triggerId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот триггер?')) return;

    try {
      await apiService.deleteAutomationTrigger(triggerId);
      alert('Триггер удален');
      loadData();
    } catch (error: any) {
      console.error('Error deleting trigger:', error);
      alert(error.response?.data?.detail || 'Ошибка при удалении триггера');
    }
  };

  const toggleTrigger = async (trigger: Trigger) => {
    try {
      await apiService.updateAutomationTrigger(trigger.id, {
        is_active: !trigger.is_active
      });
      alert(`Триггер ${!trigger.is_active ? 'активирован' : 'деактивирован'}`);
      loadData();
    } catch (error: any) {
      console.error('Error toggling trigger:', error);
      alert('Ошибка при изменении статуса триггера');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      entity_type: 'order',
      event_type: 'created',
      conditions: '{}',
      target_stage_id: '',
      is_active: true
    });
  };

  const openCreateModal = () => {
    setEditingTrigger(null);
    resetForm();
    setShowModal(true);
  };

  const getEntityTypeLabel = (entityType: string) => {
    switch (entityType) {
      case 'order': return 'Заказы';
      case 'customer': return 'Клиенты';
      case 'task': return 'Задачи';
      default: return entityType;
    }
  };

  const getEventTypeLabel = (eventType: string) => {
    switch (eventType) {
      case 'created': return 'Создан';
      case 'updated': return 'Обновлен';
      case 'status_changed': return 'Статус изменен';
      case 'completed': return 'Завершен';
      case 'deadline_approaching': return 'Дедлайн приближается';
      default: return eventType;
    }
  };

  const getStageName = (stageId: number) => {
    const stage = stages.find((s: any) => s.id === stageId);
    return stage ? stage.name : 'Неизвестная стадия';
  };

  const getEventOptions = (entityType: string) => {
    switch (entityType) {
      case 'order':
        return [
          { value: 'created', label: 'Создан' },
          { value: 'updated', label: 'Обновлен' },
          { value: 'status_changed', label: 'Статус изменен' },
          { value: 'completed', label: 'Завершен' },
          { value: 'payment_received', label: 'Получена оплата' }
        ];
      case 'customer':
        return [
          { value: 'created', label: 'Создан' },
          { value: 'updated', label: 'Обновлен' }
        ];
      case 'task':
        return [
          { value: 'created', label: 'Создана' },
          { value: 'updated', label: 'Обновлена' },
          { value: 'status_changed', label: 'Статус изменен' },
          { value: 'completed', label: 'Завершена' },
          { value: 'deadline_approaching', label: 'Дедлайн приближается' }
        ];
      default:
        return [{ value: 'created', label: 'Создан' }];
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Триггеры автоматизации</h1>
          <p className="text-gray-600">Управление триггерами событий для автоматического перемещения по стадиям</p>
        </div>
        <button onClick={openCreateModal} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Добавить триггер
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Триггеры событий</h3>
          <p className="text-sm text-gray-600 mt-1">Настройка автоматических переходов между стадиями</p>
        </div>

        <div className="divide-y divide-gray-200">
          {triggers.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              Нет созданных триггеров. Создайте первый триггер для настройки автоматизации.
            </div>
          ) : (
            triggers.map((trigger) => (
              <div key={trigger.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Zap className={`w-5 h-5 ${trigger.is_active ? 'text-yellow-500' : 'text-gray-400'}`} />
                      <div className={`w-3 h-3 rounded-full ${trigger.is_active ? 'bg-green-400' : 'bg-gray-400'}`} />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-sm font-medium text-gray-900">{trigger.name}</h4>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          trigger.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {trigger.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {getEntityTypeLabel(trigger.entity_type)}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          {getEventTypeLabel(trigger.event_type)}
                        </span>
                      </div>
                      {trigger.description && (
                        <p className="text-sm text-gray-500 mt-1">{trigger.description}</p>
                      )}
                      {trigger.target_stage_id && (
                        <p className="text-xs text-gray-600 mt-1">
                          Переход в стадию: <span className="font-medium">{getStageName(trigger.target_stage_id)}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleTrigger(trigger)}
                      className={`p-1 rounded-md ${
                        trigger.is_active
                          ? 'text-green-600 hover:text-green-800 hover:bg-green-50'
                          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                      }`}
                      title={trigger.is_active ? 'Деактивировать' : 'Активировать'}
                    >
                      {trigger.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => handleEdit(trigger)}
                      className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                      title="Редактировать"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(trigger.id)}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md"
                      title="Удалить"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingTrigger ? 'Редактировать триггер' : 'Создать триггер'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Название триггера *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Описание
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Тип сущности *
                    </label>
                    <select
                      value={formData.entity_type}
                      onChange={(e) => setFormData({ ...formData, entity_type: e.target.value, event_type: 'created' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="order">Заказы</option>
                      <option value="customer">Клиенты</option>
                      <option value="task">Задачи</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Тип события *
                    </label>
                    <select
                      value={formData.event_type}
                      onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {getEventOptions(formData.entity_type).map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Целевая стадия
                  </label>
                  <select
                    value={formData.target_stage_id}
                    onChange={(e) => setFormData({ ...formData, target_stage_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Не указана</option>
                    {stages
                      .filter((stage: any) => stage.entity_type === formData.entity_type)
                      .map((stage: any) => (
                        <option key={stage.id} value={stage.id}>
                          {stage.name}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Дополнительные условия (JSON)
                  </label>
                  <textarea
                    value={formData.conditions}
                    onChange={(e) => setFormData({ ...formData, conditions: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    rows={4}
                    placeholder='{"field": "value"}'
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    JSON объект с дополнительными условиями для срабатывания триггера
                  </p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Активен</label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingTrigger(null);
                      resetForm();
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    {editingTrigger ? 'Сохранить' : 'Создать'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Triggers;
