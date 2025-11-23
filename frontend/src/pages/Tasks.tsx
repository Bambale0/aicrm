import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  UserIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

interface Task {
  id: number;
  title: string;
  description?: string;
  status: string;
  priority: string;
  assigned_to?: number;
  assigned_user_name?: string;
  customer_id?: number;
  customer_name?: string;
  order_id?: number;
  due_date?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

const statusConfig = {
  pending: { label: 'Ожидает', color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
  in_progress: { label: 'В работе', color: 'bg-blue-100 text-blue-800', icon: ExclamationTriangleIcon },
  completed: { label: 'Завершена', color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
  cancelled: { label: 'Отменена', color: 'bg-red-100 text-red-800', icon: ExclamationTriangleIcon }
};

const priorityConfig = {
  low: { label: 'Низкий', color: 'bg-gray-100 text-gray-800' },
  medium: { label: 'Средний', color: 'bg-yellow-100 text-yellow-800' },
  high: { label: 'Высокий', color: 'bg-orange-100 text-orange-800' },
  urgent: { label: 'Срочный', color: 'bg-red-100 text-red-800' }
};

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingTask, setDeletingTask] = useState<Task | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    customer_id: '',
    order_id: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const data = await apiService.getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId: number) => {
    try {
      await apiService.completeTask(taskId);
      await loadTasks(); // Reload tasks
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (task.description && task.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
                         (task.assigned_user_name && task.assigned_user_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = !statusFilter || task.status === statusFilter;
    const matchesPriority = !priorityFilter || task.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  const getStatusInfo = (status: string) => {
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  };

  const getPriorityInfo = (priority: string) => {
    return priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.medium;
  };

  const isOverdue = (task: Task) => {
    if (!task.due_date || task.status === 'completed') return false;
    return new Date(task.due_date) < new Date();
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      due_date: '',
      customer_id: '',
      order_id: ''
    });
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title) return;

    setSubmitting(true);
    try {
      const taskData: any = {
        title: formData.title,
        description: formData.description,
        priority: formData.priority
      };

      if (formData.due_date) taskData.due_date = formData.due_date;
      if (formData.customer_id) taskData.customer_id = parseInt(formData.customer_id);
      if (formData.order_id) taskData.order_id = parseInt(formData.order_id);

      await apiService.createTask(taskData);
      setShowCreateModal(false);
      resetForm();
      loadTasks();
    } catch (error) {
      console.error('Failed to create task:', error);
      alert('Ошибка при создании задачи');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description || '',
      priority: task.priority,
      due_date: task.due_date ? task.due_date.split('T')[0] : '',
      customer_id: task.customer_id?.toString() || '',
      order_id: task.order_id?.toString() || ''
    });
    setShowEditModal(true);
    setSelectedTask(null);
  };

  const handleUpdateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTask || !formData.title) return;

    setSubmitting(true);
    try {
      const taskData: any = {
        title: formData.title,
        description: formData.description,
        priority: formData.priority
      };

      if (formData.due_date) taskData.due_date = formData.due_date;
      if (formData.customer_id) taskData.customer_id = parseInt(formData.customer_id);
      if (formData.order_id) taskData.order_id = parseInt(formData.order_id);

      await apiService.updateTask(editingTask.id, taskData);
      setShowEditModal(false);
      setEditingTask(null);
      resetForm();
      loadTasks();
    } catch (error) {
      console.error('Failed to update task:', error);
      alert('Ошибка при обновлении задачи');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTask = (task: Task) => {
    setDeletingTask(task);
    setShowDeleteModal(true);
    setSelectedTask(null);
  };

  const confirmDeleteTask = async () => {
    if (!deletingTask) return;

    setSubmitting(true);
    try {
      await apiService.deleteTask(deletingTask.id);
      setShowDeleteModal(false);
      setDeletingTask(null);
      loadTasks();
    } catch (error) {
      console.error('Failed to delete task:', error);
      alert('Ошибка при удалении задачи');
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
    setSelectedTask(null);
    setEditingTask(null);
    setDeletingTask(null);
    resetForm();
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
          <h1 className="text-3xl font-bold text-gray-900">Задачи</h1>
          <p className="text-gray-600 mt-2">Управление задачами и поручениями</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Создать задачу
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <input
              type="text"
              placeholder="Поиск задач..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="">Все статусы</option>
              <option value="pending">Ожидает</option>
              <option value="in_progress">В работе</option>
              <option value="completed">Завершена</option>
              <option value="cancelled">Отменена</option>
            </select>
          </div>

          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="input-field"
            >
              <option value="">Все приоритеты</option>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
              <option value="urgent">Срочный</option>
            </select>
          </div>

          <button
            onClick={() => {
              setSearchQuery('');
              setStatusFilter('');
              setPriorityFilter('');
            }}
            className="btn-secondary"
          >
            Сбросить фильтры
          </button>
        </div>
      </div>

      {/* Tasks List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Задачи ({filteredTasks.length})
          </h3>
        </div>

        {filteredTasks.length > 0 ? (
          <div className="space-y-4">
            {filteredTasks.map((task) => {
              const statusInfo = getStatusInfo(task.status);
              const priorityInfo = getPriorityInfo(task.priority);
              const StatusIcon = statusInfo.icon;
              const overdue = isOverdue(task);

              return (
                <div key={task.id} className={`border rounded-lg p-4 transition-colors ${
                  overdue ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-blue-300'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="flex items-center space-x-2">
                        <StatusIcon className={`w-5 h-5 ${overdue ? 'text-red-600' : 'text-gray-600'}`} />
                        <span className={`px-2 py-1 text-xs rounded-full ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded-full ${priorityInfo.color}`}>
                          {priorityInfo.label}
                        </span>
                        {overdue && (
                          <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                            Просрочена
                          </span>
                        )}
                      </div>

                      <div className="flex-1">
                        <h4 className={`font-medium ${overdue ? 'text-red-900' : 'text-gray-900'}`}>
                          {task.title}
                        </h4>
                        {task.description && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {task.description}
                          </p>
                        )}

                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          {task.assigned_user_name && (
                            <div className="flex items-center">
                              <UserIcon className="w-4 h-4 mr-1" />
                              {task.assigned_user_name}
                            </div>
                          )}

                          {task.customer_name && (
                            <div className="flex items-center">
                              <UserIcon className="w-4 h-4 mr-1" />
                              Клиент: {task.customer_name}
                            </div>
                          )}

                          {task.order_id && (
                            <span>Заказ #{task.order_id}</span>
                          )}

                          {task.due_date && (
                            <div className="flex items-center">
                              <CalendarIcon className="w-4 h-4 mr-1" />
                              {new Date(task.due_date).toLocaleDateString('ru-RU')}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedTask(task)}
                        className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>

                      {task.status !== 'completed' && (
                        <button
                          onClick={() => handleCompleteTask(task.id)}
                          className="p-2 text-green-600 hover:text-green-700 rounded-lg hover:bg-green-50"
                          title="Отметить как выполненную"
                        >
                          <CheckCircleIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <CheckCircleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Задачи не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery || statusFilter || priorityFilter
                ? 'Попробуйте изменить фильтры'
                : 'Создайте первую задачу'
              }
            </p>
          </div>
        )}
      </div>

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Задача #{selectedTask.id}
              </h3>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Название</label>
                <p className="text-gray-900 text-lg">{selectedTask.title}</p>
              </div>

              {selectedTask.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Описание</label>
                  <p className="text-gray-900 whitespace-pre-wrap">{selectedTask.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <div className="flex items-center mt-1">
                    {React.createElement(getStatusInfo(selectedTask.status).icon, {
                      className: "w-5 h-5 mr-2 text-gray-600"
                    })}
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusInfo(selectedTask.status).color}`}>
                      {getStatusInfo(selectedTask.status).label}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Приоритет</label>
                  <span className={`px-2 py-1 text-xs rounded-full ${getPriorityInfo(selectedTask.priority).color} mt-1 inline-block`}>
                    {getPriorityInfo(selectedTask.priority).label}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {selectedTask.assigned_user_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Исполнитель</label>
                    <p className="text-gray-900">{selectedTask.assigned_user_name}</p>
                  </div>
                )}

                {selectedTask.customer_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Клиент</label>
                    <p className="text-gray-900">{selectedTask.customer_name}</p>
                  </div>
                )}

                {selectedTask.order_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Заказ</label>
                    <p className="text-gray-900">#{selectedTask.order_id}</p>
                  </div>
                )}

                {selectedTask.due_date && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Срок выполнения</label>
                    <p className={`text-gray-900 ${isOverdue(selectedTask) ? 'text-red-600 font-medium' : ''}`}>
                      {new Date(selectedTask.due_date).toLocaleDateString('ru-RU')}
                      {isOverdue(selectedTask) && ' (Просрочена)'}
                    </p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Создана</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedTask.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Обновлена</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedTask.updated_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              </div>

              {selectedTask.completed_at && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Завершена</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedTask.completed_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-between mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => handleDeleteTask(selectedTask)}
                className="btn-danger"
              >
                Удалить
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedTask(null)}
                  className="btn-secondary"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => handleEditTask(selectedTask)}
                  className="btn-primary flex items-center"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Редактировать
                </button>
                {selectedTask.status !== 'completed' && (
                  <button
                    onClick={() => {
                      handleCompleteTask(selectedTask.id);
                      setSelectedTask(null);
                    }}
                    className="btn-success flex items-center"
                  >
                    <CheckCircleIcon className="w-4 h-4 mr-2" />
                    Завершить
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Создать задачу</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="input-field"
                  placeholder="Введите название задачи"
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
                  placeholder="Описание задачи"
                  disabled={submitting}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Приоритет
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="input-field"
                    disabled={submitting}
                  >
                    <option value="medium">Средний</option>
                    <option value="low">Низкий</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Срок выполнения
                  </label>
                  <input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="input-field"
                    disabled={submitting}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID клиента (опционально)
                </label>
                <input
                  type="number"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="input-field"
                  placeholder="ID клиента"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID заказа (опционально)
                </label>
                <input
                  type="number"
                  value={formData.order_id}
                  onChange={(e) => setFormData({ ...formData, order_id: e.target.value })}
                  className="input-field"
                  placeholder="ID заказа"
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
                onClick={handleCreateTask}
                disabled={submitting || !formData.title}
                className="btn-primary"
              >
                {submitting ? 'Создание...' : 'Создать задачу'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Task Modal */}
      {showEditModal && editingTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Редактировать задачу</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="input-field"
                  placeholder="Введите название задачи"
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
                  placeholder="Описание задачи"
                  disabled={submitting}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Приоритет
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="input-field"
                    disabled={submitting}
                  >
                    <option value="medium">Средний</option>
                    <option value="low">Низкий</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Срок выполнения
                  </label>
                  <input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="input-field"
                    disabled={submitting}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID клиента (опционально)
                </label>
                <input
                  type="number"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="input-field"
                  placeholder="ID клиента"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID заказа (опционально)
                </label>
                <input
                  type="number"
                  value={formData.order_id}
                  onChange={(e) => setFormData({ ...formData, order_id: e.target.value })}
                  className="input-field"
                  placeholder="ID заказа"
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
                onClick={handleUpdateTask}
                disabled={submitting || !formData.title}
                className="btn-primary"
              >
                {submitting ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingTask && (
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
                <p className="text-gray-900 font-medium">Удалить задачу?</p>
                <p className="text-sm text-gray-600 mt-1">
                  Вы уверены, что хотите удалить задачу "{deletingTask.title}"?
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
                onClick={confirmDeleteTask}
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
