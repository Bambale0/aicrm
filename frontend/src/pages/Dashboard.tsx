import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService, AIStatus, AIUsageStats, SystemSettings } from '../services/api.ts';
import {
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function Dashboard() {
  const navigate = useNavigate();
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [aiStatusData, aiUsageData, systemData] = await Promise.all([
        apiService.getAIStatus(),
        apiService.getAIUsage(),
        apiService.getSystemHealth()
      ]);

      setAiStatus(aiStatusData);
      setAiUsage(aiUsageData);
      setSystemHealth(systemData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'connected':
      case 'running':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'inactive':
      case 'disconnected':
      case 'stopped':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Главная панель</h1>
        <p className="text-gray-600 mt-2">Обзор состояния системы AI CRM</p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* AI Status */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">ИИ Система</p>
              <p className="text-2xl font-bold text-gray-900">
                {aiStatus?.status === 'active' ? 'Активна' : 'Неактивна'}
              </p>
            </div>
            <CpuChipIcon className="w-8 h-8 text-blue-600" />
          </div>
          <div className="mt-4 flex items-center">
            {getStatusIcon(aiStatus?.status || 'inactive')}
            <span className="ml-2 text-sm text-gray-600">
              {aiStatus?.available_models?.length || 0} моделей доступно
            </span>
          </div>
        </div>

        {/* Avito Integration */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avito</p>
              <p className="text-2xl font-bold text-gray-900">Интеграция</p>
            </div>
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-gray-600">Работает</span>
          </div>
        </div>

        {/* Automation */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Автоматизация</p>
              <p className="text-2xl font-bold text-gray-900">Активна</p>
            </div>
            <WrenchScrewdriverIcon className="w-8 h-8 text-purple-600" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-gray-600">Процессы запущены</span>
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Система</p>
              <p className="text-2xl font-bold text-gray-900">Здорова</p>
            </div>
            <ServerIcon className="w-8 h-8 text-gray-600" />
          </div>
          <div className="mt-4 space-y-1">
            <div className="flex items-center">
              {getStatusIcon(systemHealth?.status === 'healthy' ? 'connected' : 'disconnected')}
              <span className="ml-2 text-xs text-gray-600">Система</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Usage Stats */}
      {aiUsage && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Использование ИИ</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Всего токенов</p>
              <p className="text-2xl font-bold text-blue-600">{(aiUsage.total_tokens || 0).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Запросов</p>
              <p className="text-2xl font-bold text-green-600">{(aiUsage.total_requests || 0).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Уникальных моделей</p>
              <p className="text-2xl font-bold text-purple-600">{(aiUsage.unique_models || 0).toLocaleString()}</p>
            </div>
          </div>
          {aiUsage.model_breakdown && aiUsage.model_breakdown.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Статистика по моделям:</p>
              <div className="space-y-2">
                {aiUsage.model_breakdown.slice(0, 3).map((modelData, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium text-gray-900">{modelData.model}</span>
                    <div className="flex space-x-4 text-xs text-gray-600">
                      <span>{modelData.tokens.toLocaleString()} токенов</span>
                      <span>{modelData.requests} запросов</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/settings/ai')}
            className="btn-secondary flex items-center justify-center"
          >
            <CpuChipIcon className="w-5 h-5 mr-2" />
            Настроить ИИ
          </button>
          <button
            onClick={() => navigate('/settings/avito')}
            className="btn-secondary flex items-center justify-center"
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            Avito чаты
          </button>
          <button
            onClick={() => navigate('/settings/automation')}
            className="btn-secondary flex items-center justify-center"
          >
            <WrenchScrewdriverIcon className="w-5 h-5 mr-2" />
            Автоматизация
          </button>
          <button
            onClick={() => navigate('/settings/system')}
            className="btn-secondary flex items-center justify-center"
          >
            <ServerIcon className="w-5 h-5 mr-2" />
            Система
          </button>
        </div>
      </div>
    </div>
  );
}
