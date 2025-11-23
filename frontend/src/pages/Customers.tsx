
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Button from '../components/ui/Button';
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
    <div className="space-y-4 sm:space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Клиенты</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">Управление базой клиентов</p>
        </div>
        <Button
          onClick={openCreateModal}
          variant="primary"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Добавить клиента
        </Button>
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
          <Button
            onClick={handleSearch}
            variant="secondary"
          >
            <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
            Поиск
          </Button>
        </div>
      </div>

      {/* Customers List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
            Клиенты ({filteredCustomers.length})
          </h3>
        </div>

        {filteredCustomers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCustomers.map((customer) => (
              <div key={customer.id} className="card">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-van-gogh-ultramarine/20 rounded-full flex items-center justify-center">
                      <UsersIcon className="w-5 h-5 text-van-gogh-ultramarine" />
                    </div>
                    <div className="ml-3">
                      <h4 className="font-medium text-van-gogh-starry-night-blue">{customer.name}</h4>
                      <p className="text-sm text-van-gogh-chrome-green">ID: {customer.id}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCustomer(customer)}
                    className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                    aria-label={`Просмотреть детали клиента ${customer.name}`}
                  >
                    <EyeIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center text-sm text-van-gogh-chrome-green">
                    <EnvelopeIcon className="w-4 h-4 mr-2 text-van-gogh-vermilion" />
                    {customer.email}
                  </div>

                  {customer.phone && (
                    <div className="flex items-center text-sm text-van-gogh-chrome-green">
                      <PhoneIcon className="w-4 h-4 mr-2 text-van-gogh-vermilion" />
                      {customer.phone}
                    </div>
                  )}

                  {customer.address && (
                    <div className="flex items-center text-sm text-van-gogh-chrome-green">
                      <MapPinIcon className="w-4 h-4 mr-2 text-van-gogh-vermilion" />
                      {customer.address}
                    </div>
                  )}
                </div>

                <div className="mt-3 pt-3 border-t border-gray-700/50">
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>Заказов: {customer.orders_count || 0}</span>
                    <span>Потрачено: ₽{customer.total_spent || 0}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Создан: {new Date(customer.created_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <UsersIcon className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-van-gogh-chrome-green">Клиенты не найдены</p>
            <p className="text-sm text-gray-400 mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первого клиента'}
            </p>
          </div>
        )}
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Детали клиента</h3>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Имя</label>
                <p className="text-van-gogh-starry-night-blue font-medium">{selectedCustomer.name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Email</label>
                <p className="text-van-gogh-chrome-green">{selectedCustomer.email}</p>
              </div>

              {selectedCustomer.phone && (
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Телефон</label>
                  <p className="text-van-gogh-chrome-green">{selectedCustomer.phone}</p>
                </div>
              )}

              {selectedCustomer.address && (
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Адрес</label>
                  <p className="text-van-gogh-chrome-green">{selectedCustomer.address}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700/50">
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Заказов</label>
                  <p className="text-van-gogh-starry-night-blue font-medium">{selectedCustomer.orders_count || 0}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Потрачено</label>
                  <p className="text-van-gogh-vermilion font-medium">₽{selectedCustomer.total_spent || 0}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Создан</label>
                  <p className="text-xs text-gray-400">
                    {new Date(selectedCustomer.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">Обновлен</label>
                  <p className="text-xs text-gray-400">
                    {new Date(selectedCustomer.updated_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-6 pt-6 border-t border-gray-700/50">
              <Button
                onClick={() => handleDeleteCustomer(selectedCustomer)}
                variant="danger"
              >
                Удалить
              </Button>
              <div className="flex space-x-3">
                <Button
                  onClick={() => setSelectedCustomer(null)}
                  variant="secondary"
                >
                  Закрыть
                </Button>
                <Button
                  onClick={() => handleEditCustomer(selectedCustomer)}
                  variant="primary"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Редактировать
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Customer Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Добавить клиента</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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

            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-700/50">
              <Button
                onClick={closeModals}
                variant="secondary"
                disabled={submitting}
              >
                Отмена
              </Button>
              <Button
                onClick={handleCreateCustomer}
                variant="primary"
                loading={submitting}
                disabled={!formData.name || !formData.email}
              >
                Создать клиента
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {showEditModal && editingCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Редактировать клиента</h3>
              <button
                onClick={closeModals}
                className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateCustomer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-2">
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

            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-700/50">
              <Button
                onClick={closeModals}
                variant="secondary"
                disabled={submitting}
              >
                Отмена
              </Button>
              <Button
                onClick={handleUpdateCustomer}
                variant="primary"
                loading={submitting}
                disabled={!formData.name || !formData.email}
              >
                Сохранить изменения
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card max-w-sm w-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Подтверждение удаления</h3>
              <button
                onClick={closeModals}
                className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>

            <div className="flex items-center mb-6">
              <ExclamationTriangleIcon className="w-12 h-12 text-van-gogh-vermilion mr-4 flex-shrink-0" />
              <div>
                <p className="text-van-gogh-starry-night-blue font-medium">Удалить клиента?</p>
                <p className="text-sm text-van-gogh-chrome-green mt-1">
                  Вы уверены, что хотите удалить клиента "{deletingCustomer.name}"?
                  Это действие нельзя отменить.
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700/50">
              <Button
                onClick={closeModals}
                variant="secondary"
                disabled={submitting}
              >
                Отмена
              </Button>
              <Button
                onClick={confirmDeleteCustomer}
                variant="danger"
                loading={submitting}
              >
                Удалить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
