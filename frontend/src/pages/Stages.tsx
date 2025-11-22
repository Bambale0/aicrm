import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, GripVertical } from 'lucide-react';
import { apiService } from '../services/api';

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

const Stages: React.FC = () => {
  const [stages, setStages] = useState<Stage[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingStage, setEditingStage] = useState<Stage | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    entity_type: 'order',
    process_id: '',
    color: '#3B82F6',
    is_active: true
  });

  useEffect(() => {
    loadStages();
  }, []);

  const loadStages = async () => {
    try {
      const response = await apiService.getAutomationStages();
      setStages(response);
    } catch (error) {
      console.error('Error loading stages:', error);
      alert('Ошибка при загрузке стадий');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const stageData = {
        ...formData,
        process_id: formData.process_id ? parseInt(formData.process_id) : undefined,
        order_index: editingStage ? editingStage.order_index : stages.length
      };

      if (editingStage) {
        await apiService.updateAutomationStage(editingStage.id, stageData);
        alert('Стадия обновлена');
      } else {
        await apiService.createAutomationStage(stageData);
        alert('Стадия создана');
      }
      setShowModal(false);
      setEditingStage(null);
      resetForm();
      loadStages();
    } catch (error: any) {
      console.error('Error saving stage:', error);
      alert(error.response?.data?.detail || 'Ошибка при сохранении стадии');
    }
  };

  const handleEdit = (stage: Stage) => {
    setEditingStage(stage);
    setFormData({
      name: stage.name,
      description: stage.description || '',
      entity_type: stage.entity_type,
      process_id: stage.process_id?.toString() || '',
      color: stage.color || '#3B82F6',
      is_active: stage.is_active
    });
    setShowModal(true);
  };

  const handleDelete = async (stageId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту стадию?')) return;

    try {
      await apiService.deleteAutomationStage(stageId);
      alert('Стадия удалена');
      loadStages();
    } catch (error: any) {
      console.error('Error deleting stage:', error);
      alert(error.response?.data?.detail || 'Ошибка при удалении стадии');
    }
  };

  const handleDragStart = (e: React.DragEvent, stage: Stage) => {
    e.dataTransfer.setData('text/plain', stage.id.toString());
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent, targetStage: Stage) => {
    e.preventDefault();
    const draggedStageId = parseInt(e.dataTransfer.getData('text/plain'));

    if (draggedStageId === targetStage.id) return;

    const draggedStage = stages.find(s => s.id === draggedStageId);
    if (!draggedStage) return;

    // Пересчитываем order_index для всех стадий
    const newStages = [...stages];
    const draggedIndex = newStages.findIndex(s => s.id === draggedStageId);
    const targetIndex = newStages.findIndex(s => s.id === targetStage.id);

    // Удаляем dragged элемент
    newStages.splice(draggedIndex, 1);

    // Вставляем на новую позицию
    newStages.splice(targetIndex, 0, draggedStage);

    // Обновляем order_index
    const updatedStages = newStages.map((stage, index) => ({
      ...stage,
      order_index: index
    }));

    setStages(updatedStages);

    // Сохраняем изменения на сервере
    try {
      for (const stage of updatedStages) {
        await apiService.updateAutomationStage(stage.id, {
          order_index: stage.order_index
        });
      }
    } catch (error) {
      console.error('Error updating stage order:', error);
      alert('Ошибка при обновлении порядка стадий');
      loadStages(); // Перезагружаем в случае ошибки
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      entity_type: 'order',
      process_id: '',
      color: '#3B82F6',
      is_active: true
    });
  };

  const openCreateModal = () => {
    setEditingStage(null);
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
          <h1 className="text-2xl font-bold text-gray-900">Стадии автоматизации</h1>
          <p className="text-gray-600">Управление стадиями бизнес-процессов</p>
        </div>
        <button onClick={openCreateModal} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Добавить стадию
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Стадии процессов</h3>
          <p className="text-sm text-gray-600 mt-1">Перетаскивайте стадии для изменения порядка</p>
        </div>

        <div className="divide-y divide-gray-200">
          {stages.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              Нет созданных стадий. Создайте первую стадию для начала работы с автоматизацией.
            </div>
          ) : (
            stages
              .sort((a, b) => a.order_index - b.order_index)
              .map((stage) => (
                <div
                  key={stage.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, stage)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, stage)}
                  className="px-6 py-4 hover:bg-gray-50 cursor-move group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <GripVertical className="w-5 h-5 text-gray-400" />
                        <div
                          className="w-4 h-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: stage.color || '#3B82F6' }}
                        />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="text-sm font-medium text-gray-900">{stage.name}</h4>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            stage.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {stage.is_active ? 'Активна' : 'Неактивна'}
                          </span>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {getEntityTypeLabel(stage.entity_type)}
                          </span>
                        </div>
                        {stage.description && (
                          <p className="text-sm text-gray-500 mt-1">{stage.description}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleEdit(stage)}
                        className="p-1 text-gray-400 hover:text-blue-600"
                        title="Редактировать"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(stage.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
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
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingStage ? 'Редактировать стадию' : 'Создать стадию'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Название стадии *
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
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип сущности *
                  </label>
                  <select
                    value={formData.entity_type}
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="order">Заказы</option>
                    <option value="customer">Клиенты</option>
                    <option value="task">Задачи</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Цвет стадии
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="color"
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="w-12 h-8 border border-gray-300 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="#3B82F6"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Активна</label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingStage(null);
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
                    {editingStage ? 'Сохранить' : 'Создать'}
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
