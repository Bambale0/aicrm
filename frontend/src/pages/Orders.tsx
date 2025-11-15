import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api.ts';
import {
  ClipboardDocumentListIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TruckIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Order {
  id: number;
  customer_id: number;
  customer_name?: string;
  status: string;
  total_amount: number;
  created_at: string;
  updated_at: string;
  production_steps?: ProductionStep[];
}

interface ProductionStep {
  id: number;
  order_id: number;
  step_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  estimated_duration?: number;
}

const statusConfig = {
  pending: { label: 'Ожидает', color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
  in_progress: { label: 'В работе', color: 'bg-blue-100 text-blue-800', icon: Cog6ToothIcon },
  completed: { label: 'Завершен', color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
  cancelled: { label: 'Отменен', color: 'bg-red-100 text-red-800', icon: XCircleIcon },
  shipped: { label: 'Отправлен', color: 'bg-purple-100 text-purple-800', icon: TruckIcon }
};

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [deletingOrder, setDeletingOrder] = useState<Order | null>(null);
  const [overdueOrders, setOverdueOrders] = useState<Order[]>([]);
  const [formData, setFormData] = useState({
    customer_id: '',
    total_amount: '',
    description: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadOrders();
    loadOverdueOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await apiService.getOrders();
      setOrders(data);
    } catch (error) {
      console.error('Failed to load orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOverdueOrders = async () => {
    try {
      const data = await apiService.getOverdueProduction();
      setOverdueOrders(data);
    } catch (error) {
      console.error('Failed to load overdue orders:', error);
    }
  };

  const handleSearch = () => {
    // Client-side filtering for now
    // In production, this should be server-side search
  };

  const filteredOrders = (Array.isArray(orders) ? orders : []).filter(order =>
    order.id.toString().includes(searchQuery) ||
    order.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    order.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusInfo = (status: string) => {
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      total_amount: '',
      description: ''
    });
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.customer_id || !formData.total_amount) return;

    setSubmitting(true);
    try {
      await apiService.createOrder({
        customer_id: parseInt(formData.customer_id),
        total_amount: parseFloat(formData.total_amount),
        description: formData.description
      });
      setShowCreateModal(false);
      resetForm();
      loadOrders();
    } catch (error) {
      console.error('Failed to create order:', error);
      alert('Ошибка при создании заказа');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditOrder = (order: Order) => {
    setEditingOrder(order);
    setFormData({
      customer_id: order.customer_id.toString(),
      total_amount: order.total_amount.toString(),
      description: '' // Assuming description is not stored in order model
    });
    setShowEditModal(true);
    setSelectedOrder(null);
  };

  const handleUpdateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingOrder || !formData.customer_id || !formData.total_amount) return;

    setSubmitting(true);
    try {
      await apiService.updateOrder(editingOrder.id, {
        customer_id: parseInt(formData.customer_id),
        total_amount: parseFloat(formData.total_amount),
        description: formData.description
      });
      setShowEditModal(false);
      setEditingOrder(null);
      resetForm();
      loadOrders();
    } catch (error) {
      console.error('Failed to update order:', error);
      alert('Ошибка при обновлении заказа');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteOrder = (order: Order) => {
    setDeletingOrder(order);
    setShowDeleteModal(true);
    setSelectedOrder(null);
  };

  const confirmDeleteOrder = async () => {
    if (!deletingOrder) return;

    setSubmitting(true);
    try {
      await apiService.deleteOrder(deletingOrder.id);
      setShowDeleteModal(false);
      setDeletingOrder(null);
      loadOrders();
    } catch (error) {
      console.error('Failed to delete order:', error);
      alert('Ошибка при удалении заказа');
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
    setSelectedOrder(null);
    setEditingOrder(null);
    setDeletingOrder(null);
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
          <h1 className="text-3xl font-bold text-gray-900">Заказы</h1>
          <p className="text-gray-600 mt-2">Управление заказами и производством</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Создать заказ
        </button>
      </div>

      {/* Overdue Orders Alert */}
      {(Array.isArray(overdueOrders) && overdueOrders.length > 0) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="w-5 h-5 text-red-600 mr-2" />
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Просроченные заказы ({overdueOrders.length})
              </h3>
              <p className="text-sm text-red-700 mt-1">
                Есть заказы, требующие внимания
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="card">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Поиск заказов по ID, клиенту или статусу..."
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

      {/* Orders List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Заказы ({filteredOrders.length})
          </h3>
        </div>

        {filteredOrders.length > 0 ? (
          <div className="space-y-4">
            {filteredOrders.map((order) => {
              const statusInfo = getStatusInfo(order.status);
              const StatusIcon = statusInfo.icon;

              return (
                <div key={order.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <StatusIcon className="w-5 h-5 text-gray-600" />
                        <span className={`px-2 py-1 text-xs rounded-full ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900">Заказ #{order.id}</h4>
                        <p className="text-sm text-gray-600">
                          Клиент: {order.customer_name || `ID ${order.customer_id}`}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="font-medium text-gray-900">₽{order.total_amount}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(order.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>

                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Production Progress */}
                  {order.production_steps && Array.isArray(order.production_steps) && order.production_steps.length > 0 && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Производство</span>
                        <span className="text-sm text-gray-600">
                          {order.production_steps.filter(step => step.status === 'completed').length} / {order.production_steps.length}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${(order.production_steps.filter(step => step.status === 'completed').length / order.production_steps.length) * 100}%`
                          }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <ClipboardDocumentListIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Заказы не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Создайте первый заказ'}
            </p>
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Заказ #{selectedOrder.id}
              </h3>
              <button
                onClick={() => setSelectedOrder(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Order Info */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <div className="flex items-center mt-1">
                    {React.createElement(getStatusInfo(selectedOrder.status).icon, {
                      className: "w-5 h-5 mr-2 text-gray-600"
                    })}
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusInfo(selectedOrder.status).color}`}>
                      {getStatusInfo(selectedOrder.status).label}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Клиент</label>
                  <p className="text-gray-900">
                    {selectedOrder.customer_name || `ID ${selectedOrder.customer_id}`}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Сумма</label>
                  <p className="text-gray-900 text-lg font-semibold">₽{selectedOrder.total_amount}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Создан</label>
                    <p className="text-xs text-gray-600">
                      {new Date(selectedOrder.created_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Обновлен</label>
                    <p className="text-xs text-gray-600">
                      {new Date(selectedOrder.updated_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Production Steps */}
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-4">Этапы производства</h4>
                {selectedOrder.production_steps && Array.isArray(selectedOrder.production_steps) && selectedOrder.production_steps.length > 0 ? (
                  <div className="space-y-3">
                    {selectedOrder.production_steps.map((step, index) => (
                      <div key={step.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <div className="flex-shrink-0">
                          {step.status === 'completed' ? (
                            <CheckCircleIcon className="w-5 h-5 text-green-600" />
                          ) : step.status === 'in_progress' ? (
                            <Cog6ToothIcon className="w-5 h-5 text-blue-600 animate-spin" />
                          ) : (
                            <ClockIcon className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{step.step_name}</p>
                          <p className="text-xs text-gray-600">
                            {step.status === 'completed' && step.completed_at
                              ? `Завершено: ${new Date(step.completed_at).toLocaleString('ru-RU')}`
                              : step.status === 'in_progress' && step.started_at
                              ? `Начато: ${new Date(step.started_at).toLocaleString('ru-RU')}`
                              : 'Ожидает'
                            }
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">Этапы производства не определены</p>
                )}
              </div>
            </div>

            <div className="flex justify-between mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => handleDeleteOrder(selectedOrder)}
                className="btn-danger"
              >
                Удалить
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="btn-secondary"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => handleEditOrder(selectedOrder)}
                  className="btn-primary"
                >
                  Редактировать заказ
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Создать заказ</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateOrder} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID клиента *
                </label>
                <input
                  type="number"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="input-field"
                  placeholder="Введите ID клиента"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Сумма заказа *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                  className="input-field"
                  placeholder="0.00"
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
                  placeholder="Описание заказа"
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
                onClick={handleCreateOrder}
                disabled={submitting || !formData.customer_id || !formData.total_amount}
                className="btn-primary"
              >
                {submitting ? 'Создание...' : 'Создать заказ'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Order Modal */}
      {showEditModal && editingOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Редактировать заказ</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateOrder} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID клиента *
                </label>
                <input
                  type="number"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="input-field"
                  placeholder="Введите ID клиента"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Сумма заказа *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                  className="input-field"
                  placeholder="0.00"
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
                  placeholder="Описание заказа"
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
                onClick={handleUpdateOrder}
                disabled={submitting || !formData.customer_id || !formData.total_amount}
                className="btn-primary"
              >
                {submitting ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingOrder && (
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
                <p className="text-gray-900 font-medium">Удалить заказ?</p>
                <p className="text-sm text-gray-600 mt-1">
                  Вы уверены, что хотите удалить заказ #{deletingOrder.id}?
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
                onClick={confirmDeleteOrder}
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
