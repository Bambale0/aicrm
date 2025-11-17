import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  Squares2X2Icon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Stage {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  process_id?: number;
  order_index: number;
  color?: string;
  is_active: boolean;
  created_at: string;
}

export default function Stages() {
  const [stages, setStages] = useState<Stage[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingStage, setEditingStage] = useState<Stage | null>(null);
  const [deletingStage, setDeletingStage] = useState<Stage | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    entity_type: 'ORDER',
    process_id: '',
    color: '#3B82F6',
    is_active: true
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadStages();
  }, []);

  const loadStages = async () => {
    try {
      const data = await apiService.getAutomationStages();
      // Сортируем по order_index
      const sortedData = data.sort((a: Stage, b: Stage) => a.order_index - b.order_index);
      setStages(sortedData);
    } catch (error) {
      console.error('Failed to load stages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadStages();
      return;
    }

    try {
      // Фильтрация на клиенте
      const filtered = stages.filter(stage =>
        stage.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (stage.description && stage.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
        stage.entity_type.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setStages(filtered);
    } catch (error) {
      console.error('Failed to search stages:', error);
    }
  };

  const filteredStages = stages.filter(stage =>
    stage.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (stage.description && stage.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
    stage.entity_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      entity_type: 'ORDER',
      process_id: '',
      color: '#3B82F6',
      is_active: true
    });
  };

  const handleCreateStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name) return;

    setSubmitting(true);
    try {
      // Находим максимальный order_index
      const maxOrder = Math.max(...stages.map(s => s.order_index), 0);
      const stageData = {
        ...formData,
        order_index: maxOrder + 1,
        process_id: formData.process_id ? parseInt(formData.process_id) : null
      };

      await apiService.createAutomationStage(stageData);
      setShowCreateModal(false);
      resetForm();
      loadStages();
    } catch (error) {
      console.error('Failed to create stage:', error);
      alert('Ошибка при создании стадии');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditStage = (stage: Stage) => {
    setEditingStage(stage);
    setFormData({
      name: stage.name,
      description: stage.description || '',
      entity_type: stage.entity_type,
      process_id: stage.process_id?.toString() || '',
      color: stage.color || '#3B82F6',
      is_active: stage.is_active
    });
    setShowEditModal(true);
    setSelectedStage(null);
  };

  const handleUpdateStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStage || !formData.name) return;

    setSubmitting(true);
    try {
      const stageData = {
        ...formData,
        process_id: formData.process_id ? parseInt(formData.process_id) : null
      };

      await apiService.updateAutomationStage(editingStage.id, stageData);
      setShowEditModal(false);
      setEditingStage(null);
      resetForm();
      loadStages();
    } catch (error) {
      console.error('Failed to update stage:', error);
      alert('Ошибка при обновлении стадии');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteStage = (stage: Stage) => {
    setDeletingStage(stage);
    setShowDeleteModal(true);
    setSelectedStage(null);
  };

  const confirmDeleteStage = async () => {
    if (!deletingStage) return;

    setSubmitting(true);
    try {
      await apiService.deleteAutomationStage(deletingStage.id);
      setShowDeleteModal(false);
      setDeletingStage(null);
      loadStages();
    } catch (error) {
      console.error('Failed to delete stage:', error);
      alert('Ошибка при удалении стадии');
    } finally {
      setSubmitting(false);
    }
  };

  const moveStageUp = async (stage: Stage) => {
    if (stage.order_index <= 0) return;

    const prevStage = stages.find(s => s.order_index === stage.order_index - 1);
    if (!prevStage) return;

    try {
      // Меняем order_index местами
      await apiService.updateAutomationStage(stage.id, { order_index: stage.order_index - 1 });
      await apiService.updateAutomationStage(prevStage.id, { order_index: stage.order_index });
      loadStages();
    } catch (error) {
      console.error('Failed to move stage:', error);
      alert('Ошибка при изменении порядка');
    }
  };

  const moveStageDown = async (stage: Stage) => {
    const nextStage = stages.find(s => s.order_index === stage.order_index + 1);
    if (!nextStage) return;

    try {
      // Меняем order_index местами
      await apiService.updateAutomationStage(stage.id, { order_index: stage.order_index + 1 });
      await apiService.updateAutomationStage(nextStage.id, { order_index: stage.order_index });
      loadStages();
    } catch (error) {
      console.error('Failed to move stage:', error);
      alert('Ошибка при изменении порядка');
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
    setSelectedStage(null);
    setEditingStage(null);
    setDeletingStage(null);
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
          <h1 className="text-3xl font-bold text-gray-900">Стадии автоматизации</h1>
          <p className="text-gray-600 mt-2">Управление стадиями бизнес-процессов</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Добавить стадию
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Поиск стадий по названию, описанию или типу..."
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

      {/* Stages List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Стадии ({filteredStages.length})
          </h3>
        </div>

        {filteredStages.length > 0 ? (
          <div className="space-y-3">
            {filteredStages.map((stage) => (
              <div key={stage.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {/* Order controls */}
                    <div className="flex flex-col space-y-1">
                      <button
                        onClick={() => moveStageUp(stage)}
                        disabled={stage.order_index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Переместить вверх"
                      >
                        <ArrowUpIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => moveStageDown(stage)}
                        disabled={stage.order_index === Math.max(...stages.map(s => s.order_index))}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Переместить вниз"
                      >
                        <ArrowDownIcon className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Color indicator */}
                    <div
                      className="w-4 h-4 rounded-full border-2 border-gray-300"
                      style={{ backgroundColor: stage.color || '#3B82F6' }}
                      title="Цвет стадии"
                    />

                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="font-medium text-gray-900">{stage.name}</h4>
                        <span className="text-xs text-gray-500">#{stage.order_index}</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          stage.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {stage.is_active ? 'Активна' : 'Неактивна'}
                        </span>
                      </div>

                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                        <span>{getEntityTypeLabel(stage.entity_type)}</span>
                        {stage.description && (
                          <span className="text-gray-500">{stage.description}</span>
                        )}
                        {stage.process_id && (
                          <span className="text-blue-600">Процесс #{stage.process_id}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedStage(stage)}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      title="Просмотр деталей"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleEditStage(stage)}
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
            <Squares2X2Icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Стадии не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первую стадию'}
            </p>
          </div>
        )}
      </div>

      {/* Stage Details Modal */}
      {selectedStage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Детали стадии</h3>
              <button
                onClick={() => setSelectedStage(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div
                  className="w-6 h-6 rounded-full border-2 border-gray-300"
                  style={{ backgroundColor: selectedStage.color || '#3B82F6' }}
                />
                <div>
                  <h4 className="font-medium text-gray-900">{selectedStage.name}</h4>
                  <p className="text-sm text-gray-600">Порядок: #{selectedStage.order_index}</p>
                </div>
              </div>

              {selectedStage.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Описание</label>
                  <p className="text-gray-900">{selectedStage.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Тип сущности</label>
                  <p className="text-gray-900">{getEntityTypeLabel(selectedStage.entity_type)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <p className={`text-sm ${selectedStage.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedStage.is_active ? 'Активна' : 'Неактивна'}
                  </p>
                </div>
              </div>

              {selectedStage.process_id && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Процесс</label>
                  <p className="text-blue-600">ID: {selectedStage.process_id}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Создан</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedStage.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">ID</label>
                  <p className="text-xs text-gray-600">{selectedStage.id}</p>
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-6">
              <button
                onClick={() => handleDeleteStage(selectedStage)}
                className="btn-danger"
              >
                Удалить
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedStage(null)}
                  className="btn-secondary"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => handleEditStage(selectedStage)}
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

      {/* Create Stage Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Добавить стадию</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateStage} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Название стадии"
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
                  placeholder="Описание стадии"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип сущности
                </label>
                <select
                  value={formData.entity_type}
                  onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
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
                  ID процесса (опционально)
                </label>
                <input
                  type="number"
                  value={formData.process_id}
                  onChange={(e) => setFormData({ ...formData, process_id: e.target.value })}
                  className="input-field"
                  placeholder="ID бизнес-процесса"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Цвет
                </label>
                <input
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="input-field h-10"
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
                onClick={handleCreateStage}
                disabled={submitting || !formData.name}
                className="btn-primary"
              >
                {submitting ? 'Создание...' : 'Создать стадию'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Stage Modal */}
      {showEditModal && editingStage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Редактировать стадию</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateStage} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Название стадии"
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
                  placeholder="Описание стадии"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип сущности
                </label>
                <select
                  value={formData.entity_type}
                  onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
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
                  ID процесса (опционально)
                </label>
                <input
                  type="number"
                  value={formData.process_id}
                  onChange={(e) => setFormData({ ...formData, process_id: e.target.value })}
                  className="input-field"
                  placeholder="ID бизнес-процесса"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Цвет
                </label>
                <input
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="input-field h-10"
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
                  Активна
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
                onClick={handleUpdateStage}
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
      {showDeleteModal && deletingStage && (
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
                <p className="text-gray-900 font-medium">Удалить стадию?</p>
                <p className="text-sm text-gray-600 mt-1">
                  Вы уверены, что хотите удалить стадию "{deletingStage.name}"?
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
                onClick={confirmDeleteStage}
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
