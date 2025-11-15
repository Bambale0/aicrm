import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api.ts';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  ChartBarIcon,
  ClockIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

interface SystemHealth {
  status: string;
}

interface AIStatus {
  provider: string;
  status: string;
  default_model: string;
  available_models: string[];
}

interface AIUsage {
  period: {
    year: number;
    month: number;
    month_year: string;
  };
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_requests: number;
  unique_models: number;
  model_breakdown: Array<{
    model: string;
    tokens: number;
    requests: number;
  }>;
}

interface BackgroundTask {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

interface BackgroundTasksResponse {
  running_tasks: BackgroundTask[];
  count: number;
}

export default function SystemSettings() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsage | null>(null);
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTasksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [healthData, aiStatusData, aiUsageData, tasksData] = await Promise.all([
        apiService.getSystemHealth(),
        apiService.getAIStatus(),
        apiService.getAIUsage(),
        apiService.getAvitoBackgroundTasks()
      ]);

      setSystemHealth(healthData);
      setAiStatus(aiStatusData);
      setAiUsage(aiUsageData);
      setBackgroundTasks(tasksData);
    } catch (err) {
      console.error('Failed to load system data:', err);
      setError('Ошибка при загрузке данных системы');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'active':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'unhealthy':
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'unhealthy':
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
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
          <h1 className="text-3xl font-bold text-gray-900">Системные настройки</h1>
          <p className="text-gray-600 mt-2">Мониторинг и управление системой</p>
        </div>
        <button
          onClick={loadSystemData}
          className="btn-secondary flex items-center"
          disabled={loading}
        >
          <Cog6ToothIcon className="w-5 h-5 mr-2" />
          Обновить
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* System Health */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Здоровье системы</h3>
          {systemHealth && getStatusIcon(systemHealth.status)}
        </div>

        {systemHealth ? (
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(systemHealth.status)}`}>
              {systemHealth.status === 'healthy' ? 'Здорова' : systemHealth.status}
            </span>
            <span className="text-sm text-gray-600">
              Система работает нормально
            </span>
          </div>
        ) : (
          <p className="text-gray-600">Не удалось получить данные о здоровье системы</p>
        )}
      </div>

      {/* AI Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Статус ИИ</h3>
          {aiStatus && getStatusIcon(aiStatus.status)}
        </div>

        {aiStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Провайдер</label>
              <p className="text-gray-900 capitalize">{aiStatus.provider}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Статус</label>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(aiStatus.status)}`}>
                {aiStatus.status === 'active' ? 'Активен' : aiStatus.status}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Модель по умолчанию</label>
              <p className="text-gray-900 text-sm font-mono">{aiStatus.default_model}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Доступные модели</label>
              <p className="text-gray-900 text-sm">{aiStatus.available_models.length} моделей</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-600">Не удалось получить статус ИИ</p>
        )}
      </div>

      {/* AI Usage */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Использование ИИ</h3>
          <ChartBarIcon className="w-5 h-5 text-gray-600" />
        </div>

        {aiUsage ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{aiUsage.total_tokens.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Всего токенов</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{aiUsage.total_requests}</div>
              <div className="text-sm text-gray-600">Запросов</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{aiUsage.unique_models}</div>
              <div className="text-sm text-gray-600">Уникальных моделей</div>
            </div>
          </div>
        ) : (
          <p className="text-gray-600">Не удалось получить данные об использовании ИИ</p>
        )}
      </div>

      {/* Background Tasks */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Фоновые задачи</h3>
          <ClockIcon className="w-5 h-5 text-gray-600" />
        </div>

        {backgroundTasks ? (
          <div>
            <div className="mb-4">
              <span className="text-sm text-gray-600">
                Активных задач: {backgroundTasks.count}
              </span>
            </div>

            {backgroundTasks.running_tasks.length > 0 ? (
              <div className="space-y-3">
                {backgroundTasks.running_tasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{task.name}</p>
                      <p className="text-sm text-gray-600">
                        ID: {task.id} • Создана: {new Date(task.created_at).toLocaleString('ru-RU')}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">Нет активных фоновых задач</p>
            )}
          </div>
        ) : (
          <p className="text-gray-600">Не удалось получить данные о фоновых задачах</p>
        )}
      </div>

      {/* System Information */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Информация о системе</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Время сервера</label>
            <p className="text-gray-900">{new Date().toLocaleString('ru-RU')}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Версия API</label>
            <p className="text-gray-900">0.1.0</p>
          </div>
        </div>
      </div>
    </div>
  );
}
