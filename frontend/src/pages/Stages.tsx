/* eslint-disable no-restricted-globals */

import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import api from '../services/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';

interface Stage {
  id: string;
  name: string;
  description?: string;
  entity_type: string;
  process_id: string;
  order_index: number;
  color: string;
  is_active: boolean;
  entry_conditions?: any[];
  exit_conditions?: any[];
  actions?: any[];
  created_at: string;
  updated_at: string;
}

interface Process {
  id: string | number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
}

const Stages: React.FC = () => {
  const [stages, setStages] = useState<Stage[]>([]);
  const [processes, setProcesses] = useState<Process[]>([]);
  const [filteredStages, setFilteredStages] = useState<Stage[]>([]);
  const [selectedProcess, setSelectedProcess] = useState<string>('all');
  const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [draggedStage, setDraggedStage] = useState<Stage | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    process_id: '',
    color: '#3B82F6',
    is_active: true,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterStages();
  }, [stages, selectedProcess]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      const stagesResponse = await apiService.getAutomationStages();
      const processesResponse = await apiService.getAutomationProcesses();

      setStages(stagesResponse);
      setProcesses(processesResponse);
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const filterStages = () => {
    if (selectedProcess === 'all') {
      setFilteredStages(stages);
    } else {
      setFilteredStages(stages.filter(stage => stage.process_id === selectedProcess));
    }

    // Sort by order_index within each process
    const sorted = [...filteredStages].sort((a, b) => a.order_index - b.order_index);
    setFilteredStages(sorted);
  };

  const handleDragStart = (e: React.DragEvent, stage: Stage) => {
    setDraggedStage(stage);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', stage.id);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedStage(null);
    setDragOverIndex(null);
  };

  const handleDrop = async (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();

    if (!draggedStage) return;

    const currentProcessStages = filteredStages.filter(s => s.process_id === draggedStage.process_id);
    const draggedIndex = currentProcessStages.findIndex(s => s.id === draggedStage.id);

    if (draggedIndex === -1 || draggedIndex === dropIndex) return;

    // Reorder stages within the same process
    const reorderedStages = [...currentProcessStages];
    const [removed] = reorderedStages.splice(draggedIndex, 1);
    reorderedStages.splice(dropIndex, 0, removed);

    // Update order_index for all stages in the process
    const updatedStages = reorderedStages.map((stage, index) => ({
      ...stage,
      order_index: index
    }));

    // Update local state
    const newStages = stages.map(stage => {
      const updated = updatedStages.find(us => us.id === stage.id);
      return updated || stage;
    });
    setStages(newStages);

    // Save changes to backend
    try {
      for (const stage of updatedStages) {
        await apiService.updateAutomationStage(parseInt(stage.id), {
          order_index: stage.order_index
        });
      }
    } catch (err: any) {
      console.error('Error updating stage order:', err);
      // Revert on error
      loadData();
    }

    setDraggedStage(null);
    setDragOverIndex(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem('auth_token');
      if (selectedStage) {
        // Update existing stage
        await api.put(`/automation/stages/${selectedStage.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        // Create new stage
        await api.post('/automation/stages', formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      setShowForm(false);
      setSelectedStage(null);
      resetForm();
      loadData();
    } catch (err: any) {
      console.error('Error saving stage:', err);
      setError(err.response?.data?.detail || 'Ошибка сохранения стадии');
    }
  };

  const handleEdit = (stage: Stage) => {
    setSelectedStage(stage);
    setFormData({
      name: stage.name,
      description: stage.description || '',
      process_id: stage.process_id,
      color: stage.color,
      is_active: stage.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = async (stageId: string) => {
    if (!confirm('Вы уверены, что хотите удалить эту стадию?')) return;

    try {
      const token = localStorage.getItem('auth_token');
      await api.delete(`/automation/stages/${stageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
    } catch (err: any) {
      console.error('Error deleting stage:', err);
      setError(err.response?.data?.detail || 'Ошибка удаления стадии');
    }
  };

  const handleToggleActive = async (stage: Stage) => {
    try {
      const token = localStorage.getItem('auth_token');
      await api.put(`/automation/stages/${stage.id}`, {
        is_active: !stage.is_active
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
    } catch (err: any) {
      console.error('Error toggling stage active state:', err);
      setError(err.response?.data?.detail || 'Ошибка изменения статуса стадии');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      process_id: '',
      color: '#3B82F6',
      is_active: true,
    });
    setSelectedStage(null);
  };

  const getProcessName = (processId: string) => {
    const process = processes.find(p => p.id === processId);
    return process?.name || 'Неизвестный процесс';
  };

  const groupedStages = filteredStages.reduce((acc, stage) => {
    const processId = stage.process_id;
    if (!acc[processId]) {
      acc[processId] = [];
    }
    acc[processId].push(stage);
    return acc;
  }, {} as Record<string, Stage[]>);

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
          <h1 className="text-2xl font-semibold text-gray-900">Управление стадиями автоматизации</h1>
          <p className="mt-2 text-sm text-gray-700">
            Настройте стадии процессов автоматизации с помощью drag & drop интерфейса
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
            Добавить стадию
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

      {/* Stages by Process */}
      <div className="mt-8 space-y-8">
        {Object.entries(groupedStages).map(([processId, processStages]) => (
          <div key={processId} className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-medium text-gray-900">
                  {getProcessName(processId)}
                </h3>
                <span className="text-sm text-gray-500">
                  {processStages.length} стадий
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {processStages.map((stage, index) => (
                  <div
                    key={stage.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, stage)}
                    onDragEnd={handleDragEnd}
                    onDragOver={(e) => handleDragOver(e, index)}
                    onDrop={(e) => handleDrop(e, index)}
                    className={`
                      relative p-4 rounded-lg border-2 transition-all cursor-move
                      ${stage.is_active ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-300 opacity-60'}
                      ${dragOverIndex === index ? 'border-blue-400 bg-blue-50' : ''}
                      ${draggedStage?.id === stage.id ? 'opacity-50' : ''}
                    `}
                    style={{
                      borderLeftColor: stage.color,
                      borderLeftWidth: '4px'
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {stage.name}
                          </h4>
                          <span
                            className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                            style={{ backgroundColor: `${stage.color}20`, color: stage.color }}
                          >
                            #{stage.order_index + 1}
                          </span>
                        </div>
                        {stage.description && (
                          <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                            {stage.description}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center space-x-1 ml-2">
                        <button
                          onClick={() => handleToggleActive(stage)}
                          className={`p-1 rounded-full ${stage.is_active ? 'text-green-600 hover:bg-green-50' : 'text-gray-400 hover:bg-gray-50'}`}
                          title={stage.is_active ? 'Деактивировать' : 'Активировать'}
                        >
                          {stage.is_active ? (
                            <EyeIcon className="h-4 w-4" />
                          ) : (
                            <EyeSlashIcon className="h-4 w-4" />
                          )}
                        </button>

                        <button
                          onClick={() => handleEdit(stage)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded-full"
                          title="Редактировать"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>

                        <button
                          onClick={() => handleDelete(stage.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded-full"
                          title="Удалить"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>

                        <Cog6ToothIcon className="h-4 w-4 text-gray-400 cursor-move" />
                      </div>
                    </div>

                    {((stage.entry_conditions && stage.entry_conditions.length > 0) ||
                      (stage.actions && stage.actions.length > 0)) && (
                      <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
                        {stage.entry_conditions && stage.entry_conditions.length > 0 && (
                          <span>Условий: {stage.entry_conditions.length}</span>
                        )}
                        {stage.actions && stage.actions.length > 0 && (
                          <span>Действий: {stage.actions.length}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {processStages.length === 0 && (
                <div className="text-center py-12">
                  <Cog6ToothIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Нет стадий</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Создайте первую стадию для этого процесса автоматизации
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {Object.keys(groupedStages).length === 0 && selectedProcess !== 'all' && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              <p>В выбранном процессе нет стадий</p>
              <button
                onClick={() => {
                  resetForm();
                  setFormData(prev => ({ ...prev, process_id: selectedProcess }));
                  setShowForm(true);
                }}
                className="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100"
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Создать первую стадию
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleSubmit}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                        {selectedStage ? 'Редактировать стадию' : 'Создать новую стадию'}
                      </h3>

                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Название стадии *
                          </label>
                          <input
                            type="text"
                            required
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Например: Обработка заказа"
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
                            placeholder="Описание стадии и ее назначения"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Процесс *
                          </label>
                          <select
                            required
                            value={formData.process_id}
                            onChange={(e) => setFormData(prev => ({ ...prev, process_id: e.target.value }))}
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

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Цвет стадии
                          </label>
                          <input
                            type="color"
                            value={formData.color}
                            onChange={(e) => setFormData(prev => ({ ...prev, color: e.target.value }))}
                            className="w-full h-10 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>

                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id="is_active"
                            checked={formData.is_active}
                            onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                            Активная стадия
                          </label>
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
                    {selectedStage ? 'Сохранить изменения' : 'Создать стадию'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setSelectedStage(null);
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

export default Stages;
