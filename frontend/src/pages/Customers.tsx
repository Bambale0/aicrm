
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api.ts';
import {
  UsersIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  PhoneIcon,
  EnvelopeIcon,
  MapPinIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Customer {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
  orders_count?: number;
  total_spent?: number;
}

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [deletingCustomer, setDeletingCustomer] = useState<Customer | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const data = await apiService.getCustomers();
      setCustomers(data);
    } catch (error) {
      console.error('Failed to load customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadCustomers();
      return;
    }

    try {
      const data = await apiService.searchCustomers(searchQuery);
      setCustomers(data);
    } catch (error) {
      console.error('Failed to search customers:', error);
    }
  };

  const filteredCustomers = customers.filter(customer =>
    customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    customer.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (customer.phone && customer.phone.includes(searchQuery))
  );

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      phone: '',
      address: ''
    });
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email) return;

    setSubmitting(true);
    try {
      await apiService.createCustomer(formData);
      setShowCreateModal(false);
      resetForm();
      loadCustomers();
    } catch (error) {
      console.error('Failed to create customer:', error);
      alert('Ошибка при создании клиента');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditCustomer = (customer: Customer) => {
    setEditingCustomer(customer);
    setFormData({
      name: customer.name,
      email: customer.email,
      phone: customer.phone || '',
      address: customer.address || ''
    });
    setShowEditModal(true);
    setSelectedCustomer(null);
  };

  const handleUpdateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCustomer || !formData.name || !formData.email) return;

    setSubmitting(true);
    try {
      await apiService.updateCustomer(editingCustomer.id, formData);
      setShowEditModal(false);
      setEditingCustomer(null);
      resetForm();
      loadCustomers();
    } catch (error) {
      console.error('Failed to update customer:', error);
      alert('Ошибка при обновлении клиента');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCustomer = (customer: Customer) => {
    setDeletingCustomer(customer);
    setShowDeleteModal(true);
    setSelectedCustomer(null);
  };

  const confirmDeleteCustomer = async () => {
    if (!deletingCustomer) return;

    setSubmitting(true);
    try {
      await apiService.deleteCustomer(deletingCustomer.id);
      setShowDeleteModal(false);
      setDeletingCustomer(null);
      loadCustomers();
    } catch (error) {
      console.error('Failed to delete customer:', error);
      alert('Ошибка при удалении клиента');
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
    setSelectedCustomer(null);
    setEditingCustomer(null);
    setDeletingCustomer(null);
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
          <h1 className="text-3xl font-bold text-gray-900">Клиенты</h1>
          <p className="text-gray-600 mt-2">Управление базой клиентов</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Добавить клиента
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Поиск клиентов по имени, email или телефону..."
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

      {/* Customers List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Клиенты ({filteredCustomers.length})
          </h3>
        </div>

        {filteredCustomers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCustomers.map((customer) => (
              <div key={customer.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <UsersIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900">{customer.name}</h4>
                      <p className="text-sm text-gray-600">ID: {customer.id}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCustomer(customer)}
                    className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <EnvelopeIcon className="w-4 h-4 mr-2" />
                    {customer.email}
                  </div>

                  {customer.phone && (
                    <div className="flex items-center text-sm text-gray-600">
                      <PhoneIcon className="w-4 h-4 mr-2" />
                      {customer.phone}
                    </div>
                  )}

                  {customer.address && (
                    <div className="flex items-center text-sm text-gray-600">
                      <MapPinIcon className="w-4 h-4 mr-2" />
                      {customer.address}
                    </div>
                  )}
                </div>

                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Заказов: {customer.orders_count || 0}</span>
                    <span>Потрачено: ₽{customer.total_spent || 0}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Создан: {new Date(customer.created_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <UsersIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Клиенты не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первого клиента'}
            </p>
          </div>
        )}
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Детали клиента</h3>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Имя</label>
                <p className="text-gray-900">{selectedCustomer.name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <p className="text-gray-900">{selectedCustomer.email}</p>
              </div>

              {selectedCustomer.phone && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Телефон</label>
                  <p className="text-gray-900">{selectedCustomer.phone}</p>
                </div>
              )}

              {selectedCustomer.address && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Адрес</label>
                  <p className="text-gray-900">{selectedCustomer.address}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Заказов</label>
                  <p className="text-gray-900">{selectedCustomer.orders_count || 0}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Потрачено</label>
                  <p className="text-gray-900">₽{selectedCustomer.total_spent || 0}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Создан</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedCustomer.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Обновлен</label>
                  <p className="text-xs text-gray-600">
                    {new Date(selectedCustomer.updated_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-6">
              <button
                onClick={() => handleDeleteCustomer(selectedCustomer)}
                className="btn-danger"
              >
                Удалить
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="btn-secondary"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => handleEditCustomer(selectedCustomer)}
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

      {/* Create Customer Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Добавить клиента</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Имя *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Введите имя клиента"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="client@example.com"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Телефон
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input-field"
                  placeholder="+7 (999) 123-45-67"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Адрес
                </label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input-field"
                  rows={3}
                  placeholder="Введите адрес клиента"
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
                onClick={handleCreateCustomer}
                disabled={submitting || !formData.name || !formData.email}
                className="btn-primary"
              >
                {submitting ? 'Создание...' : 'Создать клиента'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {showEditModal && editingCustomer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Редактировать клиента</h3>
              <button
                onClick={closeModals}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateCustomer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Имя *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="Введите имя клиента"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="client@example.com"
                  required
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Телефон
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input-field"
                  placeholder="+7 (999) 123-45-67"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Адрес
                </label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input-field"
                  rows={3}
                  placeholder="Введите адрес клиента"
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
                onClick={handleUpdateCustomer}
                disabled={submitting || !formData.name || !formData.email}
                className="btn-primary"
              >
                {submitting ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingCustomer && (
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
                <p className="text-gray-900 font-medium">Удалить клиента?</p>
                <p className="text-sm text-gray-600 mt-1">
                  Вы уверены, что хотите удалить клиента "{deletingCustomer.name}"?
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
                onClick={confirmDeleteCustomer}
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
