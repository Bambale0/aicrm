/* eslint-disable no-restricted-globals */

import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  BoltIcon,
  ArrowPathIcon,
  ClockIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';

interface Trigger {
  id: string;
  name: string;
  description?: string;
  event_type: string;
  entity_type: string;
  process_id: string;
  target_stage_id: string;
  conditions: TriggerCondition[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TriggerCondition {
  id: string;
  field: string;
  operator: string;
  value: any;
  logical_operator?: 'AND' | 'OR';
}

interface Process {
  id: string;
  name: string;
  entity_type: string;
  stages: Stage[];
}

interface Stage {
  id: string;
  name: string;
  color: string;
}

interface AvailableTriggerType {
  type: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  available_fields: Array<{
    field: string;
    type: 'text' | 'number' | 'boolean' | 'select' | 'date';
    label: string;
    options?: string[];
  }>;
}

const TRIGGER_TYPES: AvailableTriggerType[] = [
  {
    type: 'status_changed',
    name: 'Изменение статуса',
    description: 'Когда изменяется статус сущности',
    icon: <BoltIcon className="h-5 w-5" />,
    available_fields: [
      {
        field: 'status',
        type: 'select',
        label: 'Новый статус',
        options: ['pending', 'paid', 'in_progress', 'completed', 'cancelled']
      },
      {
        field: 'old_status',
        type: 'select',
        label: 'Предыдущий статус',
        options: ['pending', 'paid', 'in_progress', 'completed', 'cancelled']
      }
    ]
  },
  {
    type: 'time_elapsed',
    name: 'Время прошло',
    description: 'Когда прошло определенное время с момента создания',
    icon: <ClockIcon className="h-5 w-5" />,
    available_fields: [
      {
        field: 'hours',
        type: 'number',
        label: 'Количество часов'
      },
      {
        field: 'days',
        type: 'number',
        label: 'Количество дней'
      }
    ]
  },
  {
    type: 'field_updated',
    name: 'Поле изменено',
    description: 'Когда изменяется значение поля',
    icon: <DocumentTextIcon className="h-5 w-5" />,
    available_fields: [
      {
        field: 'field_name',
        type: 'select',
        label: 'Поле',
        options: ['name', 'email', 'phone', 'company', 'status', 'total_amount', 'deadline']
      },
      {
        field: 'old_value',
        type: 'text',
        label: 'Предыдущее значение'
      },
      {
        field: 'new_value',
        type: 'text',
        label: 'Новое значение'
      }
    ]
  },
  {
    type: 'message_received',
    name: 'Сообщение получено',
    description: 'Когда поступает новое сообщение (Telegram, Avito)',
    icon: <ChatBubbleLeftRightIcon className="h-5 w-5" />,
    available_fields: [
      {
        field: 'channel',
        type: 'select',
        label: 'Канал',
        options: ['telegram', 'avito', 'email', 'phone']
      },
      {
        field: 'sender_name',
        type: 'text',
        label: 'Имя отправителя'
      }
    ]
  },
  {
    type: 'payment_received',
    name: 'Оплата получена',
    description: 'Когда поступает оплата',
    icon: <Cog6ToothIcon className="h-5 w-5" />,
    available_fields: [
      {
        field: 'amount',
        type: 'number',
        label: 'Сумма оплаты'
      },
      {
        field: 'payment_method',
        type: 'select',
        label: 'Метод оплаты',
        options: ['card', 'cash', 'bank_transfer', 'yandex_money', 'qiwi']
      }
    ]
  }
];

const Triggers: React.FC = () => {
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [processes, setProcesses] = useState<Process[]>([]);
  const [selectedProcess, setSelectedProcess] = useState<string>('all');
  const [selectedTrigger, setSelectedTrigger] = useState<Trigger | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showConditionBuilder, setShowConditionBuilder] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    process_id: '',
    target_stage_id: '',
    event_type: '',
    conditions: [] as TriggerCondition[],
    is_active: true,
  });

  // Condition builder state
  const [currentConditions, setCurrentConditions] = useState<TriggerCondition[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('auth_token');

      const [triggersRes, processesRes] = await Promise.all([
        api.get('/automation/triggers', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/automation/processes', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      const processesData = processesRes.data || [];
      // Load stages for each process
      for (let process of processesData) {
        const stagesRes = await api.get(`/automation/processes/${process.id}/stages`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        process.stages = stagesRes.data || [];
      }

      setTriggers(triggersRes.data || []);
      setProcesses(processesData);
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem('auth_token');
      const submitData = {
        ...formData,
        conditions: currentConditions.filter(c => c.field && c.operator && c.value !== undefined)
      };

      if (selectedTrigger) {
        await api.put(`/automation/triggers/${selectedTrigger.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/automation/triggers', submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      setShowForm(false);
      setSelectedTrigger(null);
      resetForm();
      loadData();
    } catch (err: any) {
      console.error('Error saving trigger:', err);
      setError(err.response?.data?.detail || 'Ошибка сохранения триггера');
    }
  };

  const handleEdit = (trigger: Trigger) => {
    setSelectedTrigger(trigger);
    setFormData({
      name: trigger.name,
      description: trigger.description || '',
      process_id: trigger.process_id,
      target_stage_id: trigger.target_stage_id,
      event_type: trigger.event_type,
      conditions: trigger.conditions || [],
      is_active: trigger.is_active,
    });
    setCurrentConditions(trigger.conditions || []);
    setShowForm(true);
  };

  const handleDelete = async (triggerId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот триггер?')) return;

    try {
      const token = localStorage.getItem('auth_token');
      await api.delete(`/automation/triggers/${triggerId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
    } catch (err: any) {
      console.error('Error deleting trigger:', err);
      setError(err.response?.data?.detail || 'Ошибка удаления триггера');
    }
  };

  const handleToggleActive = async (trigger: Trigger) => {
    try {
      const token = localStorage.getItem('auth_token');
      await api.put(`/automation/triggers/${trigger.id}`, {
        is_active: !trigger.is_active
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
    } catch (err: any) {
      console.error('Error toggling trigger active state:', err);
      setError(err.response?.data?.detail || 'Ошибка изменения статуса триггера');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      process_id: '',
      target_stage_id: '',
      event_type: '',
      conditions: [],
      is_active: true,
    });
    setCurrentConditions([]);
    setSelectedTrigger(null);
  };

  const selectedTriggerType = TRIGGER_TYPES.find(t => t.type === formData.event_type);
  const selectedProcessStages = processes.find(p => p.id === formData.process_id)?.stages || [];

  const getTriggerTypeInfo = (type: string) => {
    return TRIGGER_TYPES.find(t => t.type === type);
  };

  const getStageName = (stageId: string) => {
    const allStages = processes.flatMap(p => p.stages);
    return allStages.find(s => s.id === stageId)?.name || 'Неизвестная стадия';
  };

  const getProcessName = (processId: string) => {
    return processes.find(p => p.id === processId)?.name || 'Неизвестный процесс';
  };

  const addCondition = () => {
    const newCondition: TriggerCondition = {
      id: `temp_${Date.now()}`,
      field: '',
      operator: 'equals',
      value: ''
    };
    setCurrentConditions([...currentConditions, newCondition]);
  };

  const updateCondition = (index: number, updates: Partial<TriggerCondition>) => {
    const updatedConditions = [...currentConditions];
    updatedConditions[index] = { ...updatedConditions[index], ...updates };
    setCurrentConditions(updatedConditions);
  };

  const removeCondition = (index: number) => {
    const updatedConditions = currentConditions.filter((_, i) => i !== index);
    setCurrentConditions(updatedConditions);
  };

  const filteredTriggers = selectedProcess === 'all'
    ? triggers
    : triggers.filter(t => t.process_id === selectedProcess);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Управление триггерами автоматизации</h1>
          <p className="mt-2 text-sm text-gray-700">
            Создавайте условия для автоматических переходов между стадиями
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
            className="inline-flex items-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Добавить триггер
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      {/* Filter */}
      <div className="mt-6">
        <select
          value={selectedProcess}
          onChange={(e) => setSelectedProcess(e.target.value)}
          className="rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 sm:text-sm sm:leading-6"
        >
          <option value="all">Все процессы</option>
          {processes.map((process) => (
            <option key={process.id} value={process.id}>
              {process.name} ({process.entity_type})
            </option>
          ))}
        </select>
      </div>

      {/* Triggers Grid */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTriggers.map((trigger) => (
          <div
            key={trigger.id}
            className={`
              bg-white shadow rounded-lg overflow-hidden border-l-4 transition-all
              ${trigger.is_active ? 'border-blue-500 bg-white' : 'border-gray-300 bg-gray-50 opacity-60'}
            `}
            style={{
              borderLeftColor: trigger.is_active ? '#3B82F6' : '#D1D5DB'
            }}
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center">
                    <div className="text-blue-600 mr-2">
                      {getTriggerTypeInfo(trigger.event_type)?.icon || <BoltIcon className="h-5 w-5" />}
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {trigger.name}
                    </h3>
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      trigger.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {trigger.is_active ? 'Активный' : 'Неактивный'}
                    </span>
                  </div>

                  {trigger.description && (
                    <p className="mt-2 text-sm text-gray-600">
                      {trigger.description}
                    </p>
                  )}

                  <div className="mt-4 space-y-2">
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium">Процесс:</span>
                      <span className="ml-1">{getProcessName(trigger.process_id)}</span>
                    </div>

                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium">Тип события:</span>
                      <span className="ml-1">{getTriggerTypeInfo(trigger.event_type)?.name || trigger.event_type}</span>
                    </div>

                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium">Целевая стадия:</span>
                      <span className="ml-1">{getStageName(trigger.target_stage_id)}</span>
                    </div>

                    {(trigger.conditions && trigger.conditions.length > 0) && (
                      <div className="text-sm text-gray-500">
                        <span className="font-medium">Условий: {trigger.conditions.length}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-1 ml-2">
                  <button
                    onClick={() => handleToggleActive(trigger)}
                    className={`p-1 rounded-full ${trigger.is_active ? 'text-green-600 hover:bg-green-50' : 'text-gray-400 hover:bg-gray-50'}`}
                    title={trigger.is_active ? 'Деактивировать' : 'Активировать'}
                  >
                    {trigger.is_active ? (
                      <EyeIcon className="h-4 w-4" />
                    ) : (
                      <EyeSlashIcon className="h-4 w-4" />
                    )}
                  </button>

                  <button
                    onClick={() => handleEdit(trigger)}
                    className="p-1 text-blue-600 hover:bg-blue-50 rounded-full"
                    title="Редактировать"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => handleDelete(trigger.id)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded-full"
                    title="Удалить"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredTriggers.length === 0 && (
        <div className="text-center py-12">
          <BoltIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Нет триггеров</h3>
          <p className="mt-1 text-sm text-gray-500">
            Создайте первый триггер для автоматизации процессов
          </p>
          <div className="mt-6">
            <button
              onClick={() => {
                resetForm();
                setShowForm(true);
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Создать триггер
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <form onSubmit={handleSubmit}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
                        {selectedTrigger ? 'Редактировать триггер' : 'Создать новый триггер'}
                      </h3>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Basic Info */}
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Название триггера *
                            </label>
                            <input
                              type="text"
                              required
                              value={formData.name}
                              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                              placeholder="Например: Переход при оплате"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Описание
                            </label>
                            <textarea
                              value={formData.description}
                              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                              rows={3}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                              placeholder="Описание триггера и его назначения"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Процесс автоматизации *
                            </label>
                            <select
                              required
                              value={formData.process_id}
                              onChange={(e) => {
                                setFormData(prev => ({
                                  ...prev,
                                  process_id: e.target.value,
                                  target_stage_id: '' // Reset target stage when process changes
                                }));
                                setCurrentConditions([]);
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            >
                              <option value="">Выберите процесс</option>
                              {processes.map((process) => (
                                <option key={process.id} value={process.id}>
                                  {process.name} ({process.entity_type})
                                </option>
                              ))}
                            </select>
                          </div>

                          {selectedProcessStages.length > 0 && (
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Целевая стадия *
                              </label>
                              <select
                                required
                                value={formData.target_stage_id}
                                onChange={(e) => setFormData(prev => ({ ...prev, target_stage_id: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                              >
                                <option value="">Выберите целевую стадию</option>
                                {selectedProcessStages.map((stage) => (
                                  <div key={stage.id} className="flex items-center">
                                    <div
                                      className="w-3 h-3 rounded-full mr-2"
                                      style={{ backgroundColor: stage.color }}
                                    />
                                    <span>{stage.name}</span>
                                  </div>
                                ))}
                              </select>
                            </div>
                          )}

                          <div className="flex items-center">
                            <input
                              type="checkbox"
                              id="is_active"
                              checked={formData.is_active}
                              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                              Активный триггер
                            </label>
                          </div>
                        </div>

                        {/* Trigger Type & Conditions */}
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-3">
                              Тип события *
                            </label>
                            <div className="space-y-2">
                              {TRIGGER_TYPES.map((triggerType) => (
                                <label
                                  key={triggerType.type}
                                  className={`
                                    flex items-center p-3 rounded-lg border cursor-pointer transition-all
                                    ${formData.event_type === triggerType.type ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
                                  `}
                                >
                                  <input
                                    type="radio"
                                    name="event_type"
                                    value={triggerType.type}
                                    checked={formData.event_type === triggerType.type}
                                    onChange={(e) => setFormData(prev => ({ ...prev, event_type: e.target.value }))}
                                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                                  />
                                  <div className="ml-3 flex items-center">
                                    <div className="text-blue-600 mr-3">
                                      {triggerType.icon}
                                    </div>
                                    <div>
                                      <div className="text-sm font-medium text-gray-900">
                                        {triggerType.name}
                                      </div>
                                      <div className="text-xs text-gray-500">
                                        {triggerType.description}
                                      </div>
                                    </div>
                                  </div>
                                </label>
                              ))}
                            </div>
                          </div>

                          {selectedTriggerType && (
                            <div>
                              <div className="flex items-center justify-between mb-3">
                                <label className="block text-sm font-medium text-gray-700">
                                  Условия срабатывания
                                </label>
                                <button
                                  type="button"
                                  onClick={addCondition}
                                  className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-600 bg-blue-50 hover:bg-blue-100"
                                >
                                  <PlusIcon className="h-3 w-3 mr-1" />
                                  Добавить условие
                                </button>
                              </div>

                              <div className="space-y-3">
                                {currentConditions.map((condition, index) => (
                                  <div key={condition.id} className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                                    <select
                                      value={condition.field}
                                      onChange={(e) => updateCondition(index, { field: e.target.value })}
                                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                                    >
                                      <option value="">Выберите поле</option>
                                      {selectedTriggerType.available_fields.map((field) => (
                                        <option key={field.field} value={field.field}>
                                          {field.label}
                                        </option>
                                      ))}
                                    </select>

                                    <select
                                      value={condition.operator}
                                      onChange={(e) => updateCondition(index, { operator: e.target.value })}
                                      className="px-2 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm w-20"
                                    >
                                      <option value="equals">=</option>
                                      <option value="not_equals">≠</option>
                                      <option value="greater">&gt;</option>
                                      <option value="less">&lt;</option>
                                      <option value="contains">содержит</option>
                                    </select>

                                    <input
                                      type="text"
                                      value={condition.value || ''}
                                      onChange={(e) => updateCondition(index, { value: e.target.value })}
                                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                                      placeholder="Значение"
                                    />

                                    <button
                                      type="button"
                                      onClick={() => removeCondition(index)}
                                      className="p-1 text-red-600 hover:bg-red-50 rounded-full"
                                    >
                                      <XCircleIcon className="h-4 w-4" />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    {selectedTrigger ? 'Сохранить изменения' : 'Создать триггер'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setSelectedTrigger(null);
                      resetForm();
                    }}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Отменить
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
