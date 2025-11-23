import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import Button from '../components/ui/Button';
import {
  PlusIcon,
  Cog6ToothIcon,
  CheckCircleIcon,
  XMarkIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

interface Organization {
  id: number;
  name: string;
  slug: string;
  email: string;
  phone?: string;
  website?: string;
  plan: string;
  is_active: boolean;
  is_verified: boolean;
  max_users: number;
  max_storage_mb: number;
  created_at: string;
}

function Organizations() {
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Organization | null>(null);
  const [checkingSlug, setCheckingSlug] = useState<string | null>(null);
  const [slugCheckResult, setSlugCheckResult] = useState<{
    slug: string;
    available: boolean;
    message: string;
  } | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    website: '',
    plan: 'free' as const
  });

  const queryClient = useQueryClient();

  // React Query hooks
  const { data: organizations, isLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => apiService.getOrganizations(),
  });

  const deleteMutation = useMutation({
    mutationFn: (orgId: number) => apiService.deleteOrganization(orgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      alert('Организация успешно удалена');
    },
    onError: () => {
      alert('Ошибка при удалении организации');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      apiService.updateOrganization(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      setEditing(null);
      setFormData({ name: '', email: '', phone: '', website: '', plan: 'free' });
      alert('Организация успешно обновлена');
    },
    onError: () => {
      alert('Ошибка при обновлении организации');
    },
  });

  const handleDelete = (org: Organization) => {
    if (window.confirm(`Вы уверены, что хотите удалить организацию "${org.name}"?`)) {
      deleteMutation.mutate(org.id);
    }
  };

  const handleEdit = (org: Organization) => {
    setEditing(org);
    setFormData({
      name: org.name,
      email: org.email,
      phone: org.phone || '',
      website: org.website || '',
      plan: org.plan as any
    });
  };

  const handleUpdate = () => {
    if (!editing || !formData.name.trim() || !formData.email.trim()) return;
    updateMutation.mutate({ id: editing.id, data: formData });
  };

  const cancelEdit = () => {
    setEditing(null);
    setFormData({ name: '', email: '', phone: '', website: '', plan: 'free' });
  };

  const handleCreate = async () => {
    if (!formData.name.trim() || !formData.email.trim()) return;

    try {
      setCreating(true);
      const response = await apiService.createOrganization(formData);
      alert(`Организация "${formData.name}" успешно создана!`);
      // Reset form and refresh list
      setFormData({
        name: '',
        email: '',
        phone: '',
        website: '',
        plan: 'free'
      });
      setSlugCheckResult(null);
      setCreating(false);
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    } catch (error) {
      console.error('Failed to create organization:', error);
      alert('Ошибка создания организации');
      setCreating(false);
    }
  };

  const checkSlugAvailability = async (name: string) => {
    if (!name.trim()) return;

    // Generate slug from name
    const slug = name.toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');

    if (!slug || slug.length < 2) return;

    setCheckingSlug(slug);
    try {
      const response = await apiService.checkOrganizationSlug(slug);
      setSlugCheckResult(response);
    } catch (error) {
      console.error('Failed to check slug:', error);
    } finally {
      setCheckingSlug(null);
    }
  };

  // Auto-check slug when name changes
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (formData.name.trim().length >= 3) {
        checkSlugAvailability(formData.name);
      } else {
        setSlugCheckResult(null);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [formData.name]);

  if (creating || editing) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-van-gogh-starry-night-blue">
              {editing ? 'Редактирование организации' : 'Регистрация новой организации'}
            </h1>
            <button
              onClick={() => {
                if (editing) cancelEdit();
                else setCreating(false);
                setSlugCheckResult(null);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Basic Information */}
            <div className="border-b border-gray-200 pb-6">
              <h2 className="text-lg font-semibold text-van-gogh-chrome-green mb-4">
                Основная информация
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                    Название организации *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                    placeholder="ООО Компания"
                    required
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                    Slug (короткое имя)
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <div className="flex items-center bg-gray-50 border border-gray-300 rounded-lg">
                        <span className="px-3 py-3 text-gray-500 text-sm">app.aicrm.dev/</span>
                        <input
                          type="text"
                          value={
                            formData.name.toLowerCase()
                              .replace(/[^a-z0-9]/g, '-')
                              .replace(/-+/g, '-')
                              .replace(/^-|-$/g, '')
                          }
                          readOnly
                          className="flex-1 bg-transparent border-0 focus:ring-0 text-sm py-3"
                        />
                      </div>
                    </div>
                    {slugCheckResult && (
                      <div className="flex items-center">
                        {slugCheckResult.available ? (
                          <CheckCircleIcon className="w-5 h-5 text-green-500" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                    )}
                  </div>
                  {slugCheckResult && (
                    <p className={`text-xs mt-1 ${
                      slugCheckResult.available ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {slugCheckResult.message}
                    </p>
                  )}
                  {checkingSlug && (
                    <div className="flex items-center gap-2 mt-1">
                      <div className="animate-spin rounded-full h-3 w-3 border-b border-van-gogh-ultramarine"></div>
                      <span className="text-xs text-gray-500">Проверка...</span>
                    </div>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                    Email адрес *
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                    placeholder="admin@company.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                    Телефон
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                    placeholder="+7 (999) 123-45-67"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                    Website
                  </label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                    placeholder="https://company.com"
                  />
                </div>
              </div>
            </div>

            {/* Plan Selection */}
            <div className="border-b border-gray-200 pb-6">
              <h2 className="text-lg font-semibold text-van-gogh-chrome-green mb-4">
                Тарифный план
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    name: 'Free',
                    value: 'free',
                    description: 'До 50 пользователей',
                    features: ['CRM основы', 'Email рассылки', 'Базовая аналитика']
                  },
                  {
                    name: 'Pro',
                    value: 'pro',
                    description: 'До 500 пользователей',
                    features: ['Все функции Free', 'AI помощник', 'Расширенная аналитика']
                  },
                  {
                    name: 'Enterprise',
                    value: 'enterprise',
                    description: 'Неограниченное',
                    features: ['Все функции Pro', 'Кастомизация', 'Приоритетная поддержка']
                  }
                ].map(plan => (
                  <div
                    key={plan.value}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      formData.plan === plan.value
                        ? 'border-van-gogh-ultramarine bg-van-gogh-ultramarine/5'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                    onClick={() => setFormData({ ...formData, plan: plan.value as any })}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-van-gogh-starry-night-blue">
                        {plan.name}
                      </h3>
                      {formData.plan === plan.value && (
                        <CheckCircleIcon className="w-5 h-5 text-van-gogh-ultramarine" />
                      )}
                    </div>
                    <p className="text-sm text-van-gogh-chrome-green mb-2">
                      {plan.description}
                    </p>
                    <ul className="space-y-1">
                      {plan.features.map(feature => (
                        <li key={feature} className="text-xs text-gray-600 flex items-center">
                          <div className="w-1 h-1 bg-gray-400 rounded-full mr-2"></div>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            {/* Warnings */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-medium text-yellow-800 mb-2">Важная информация</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• При регистрации будет создана отдельная база данных для организации</li>
                <li>• Первый администратор организации получит учетные данные по email</li>
                <li>• Домены вида app.aicrm.dev/company-slug становятся доступными после верификации</li>
                <li>• Время создания: 5-10 минут</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <Button
                onClick={editing ? handleUpdate : handleCreate}
                variant="primary"
                loading={editing ? updateMutation.isPending : creating}
                disabled={!slugCheckResult?.available || !formData.name.trim() || !formData.email.trim()}
              >
                {editing ? 'Сохранить изменения' : creating ? 'Создание...' : 'Создать организацию'}
              </Button>
              <Button
                onClick={() => {
                  if (editing) cancelEdit();
                  else setCreating(false);
                  setSlugCheckResult(null);
                }}
                variant="secondary"
              >
                Отмена
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Организации</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">
            Управление мультитенантными организациями в системе
          </p>
        </div>
        <Button
          onClick={() => setCreating(true)}
          variant="primary"
          className="flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Создать организацию
        </Button>
      </div>

      {/* Organizations List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-van-gogh-ultramarine"></div>
        </div>
      ) : organizations && organizations.length > 0 ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-6">
          {organizations.map((org: Organization) => (
            <div key={org.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-van-gogh-starry-night-blue mb-1">
                    {org.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{org.slug}</p>
                  <div className="space-y-1 text-sm">
                    <p className="text-gray-700">{org.email}</p>
                    {org.phone && <p className="text-gray-600">{org.phone}</p>}
                    {org.website && (
                      <a
                        href={org.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-van-gogh-ultramarine hover:underline"
                      >
                        {org.website}
                      </a>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(org)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="Редактировать"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(org)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Удалить"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  org.is_verified
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {org.is_verified ? 'Верифицирована' : 'Не верифицирована'}
                </span>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  org.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {org.is_active ? 'Активна' : 'Неактивна'}
                </span>
              </div>

              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Тариф:</span>
                  <span className="font-medium capitalize">{org.plan}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-600">Лимит пользователей:</span>
                  <span className="font-medium">{org.max_users}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-600">Хранилище:</span>
                  <span className="font-medium">{org.max_storage_mb} MB</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* Empty State */}
          <div className="text-center py-12">
            <Cog6ToothIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-van-gogh-chrome-green">
              Создайте первую организацию
            </h3>
            <p className="mt-1 text-sm text-gray-500 max-w-md mx-auto">
              Регистрация организации создаст отдельную базу данных и предоставит доступ
              к CRM системе под доменом организации.
            </p>
            <div className="mt-6">
              <Button onClick={() => setCreating(true)} variant="primary">
                <PlusIcon className="w-5 h-5 mr-2" />
                Начать регистрацию
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Organizations;
