import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService, AIStatus, AIUsageStats, SystemSettings } from '../services/api';
import Button from '../components/ui/Button';
import { usePullToRefresh } from '../hooks/usePullToRefresh';
import {
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

function Dashboard() {
  const navigate = useNavigate();
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = async () => {
    try {
      setRefreshing(true);
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
      setRefreshing(false);
    }
  };

  // Pull-to-refresh functionality
  const { isRefreshing: pullRefreshing, pullDistance, canRefresh } = usePullToRefresh({
    onRefresh: loadDashboardData,
    threshold: 80,
    disabled: loading
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-van-gogh-ultramarine"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 relative">
      {/* Pull-to-refresh indicator */}
      {pullDistance > 0 && (
        <div
          className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-purple-600 to-cyan-600 text-white py-2 px-4 text-center transform transition-transform duration-200"
          style={{
            transform: `translateY(${Math.min(pullDistance - 80, 0)}px)`,
            opacity: canRefresh ? 1 : 0.7
          }}
        >
          <div className="flex items-center justify-center space-x-2">
            {canRefresh ? (
              <>
                <ArrowDownIcon className="w-5 h-5 animate-bounce" />
                <span className="font-medium">Отпустите для обновления</span>
              </>
            ) : (
              <>
                <ArrowDownIcon className="w-5 h-5" />
                <span>Потяните для обновления</span>
              </>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Главная панель</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">Обзор состояния системы AI CRM</p>
        </div>
        <Button
          onClick={loadDashboardData}
          loading={refreshing || pullRefreshing}
          variant="secondary"
          size="sm"
        >
          <ArrowPathIcon className="w-4 h-4 mr-2" />
          Обновить
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* AI Status */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">ИИ Система</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">
                {aiStatus?.status === 'active' ? 'Активна' : 'Неактивна'}
              </p>
            </div>
            <CpuChipIcon className="w-8 h-8 text-van-gogh-ultramarine" />
          </div>
          <div className="mt-4 flex items-center">
            {getStatusIcon(aiStatus?.status || 'inactive')}
            <span className="ml-2 text-sm text-van-gogh-chrome-green">
              {aiStatus?.available_models?.length || 0} моделей доступно
            </span>
          </div>
        </div>

        {/* Avito Integration */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">Avito</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">Интеграция</p>
            </div>
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-van-gogh-chrome-green" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-van-gogh-chrome-green">Работает</span>
          </div>
        </div>

        {/* Automation */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">Автоматизация</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">Активна</p>
            </div>
            <WrenchScrewdriverIcon className="w-8 h-8 text-van-gogh-vermilion" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-van-gogh-chrome-green">Процессы запущены</span>
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">Система</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">Здорова</p>
            </div>
            <ServerIcon className="w-8 h-8 text-van-gogh-ultramarine" />
          </div>
          <div className="mt-4 space-y-1">
            <div className="flex items-center">
              {getStatusIcon(systemHealth?.status === 'healthy' ? 'connected' : 'disconnected')}
              <span className="ml-2 text-xs text-van-gogh-chrome-green">Система</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Usage Stats */}
      {aiUsage && (
        <div className="card">
          <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">Использование ИИ</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-van-gogh-chrome-green">Всего токенов</p>
              <p className="text-2xl font-bold text-van-gogh-ultramarine">{(aiUsage.total_tokens || 0).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-van-gogh-chrome-green">Запросов</p>
              <p className="text-2xl font-bold text-van-gogh-chrome-green">{(aiUsage.total_requests || 0).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-van-gogh-chrome-green">Уникальных моделей</p>
              <p className="text-2xl font-bold text-van-gogh-vermilion">{(aiUsage.unique_models || 0).toLocaleString()}</p>
            </div>
          </div>
          {aiUsage.model_breakdown && aiUsage.model_breakdown.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-van-gogh-chrome-green mb-2">Статистика по моделям:</p>
              <div className="space-y-2">
                {aiUsage.model_breakdown.slice(0, 3).map((modelData, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-van-gogh-wheat-field/20 rounded">
                    <span className="text-sm font-medium text-van-gogh-starry-night-blue">{modelData.model}</span>
                    <div className="flex space-x-4 text-xs text-van-gogh-chrome-green">
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
        <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button
            onClick={() => navigate('/settings/ai')}
            variant="secondary"
            fullWidth
          >
            <CpuChipIcon className="w-5 h-5 mr-2" />
            Настроить ИИ
          </Button>
          <Button
            onClick={() => navigate('/settings/avito')}
            variant="secondary"
            fullWidth
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            Avito чаты
          </Button>
          <Button
            onClick={() => navigate('/settings/automation')}
            variant="secondary"
            fullWidth
          >
            <WrenchScrewdriverIcon className="w-5 h-5 mr-2" />
            Автоматизация
          </Button>
          <Button
            onClick={() => navigate('/settings/system')}
            variant="secondary"
            fullWidth
          >
            <ServerIcon className="w-5 h-5 mr-2" />
            Система
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
