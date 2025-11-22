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
  ArrowDownIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface DashboardStats {
  totalRobots: number;
  activeAutomations: number;
  processedMessages: number;
  avgResponseTime: number;
}

function Dashboard() {
  const navigate = useNavigate();
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemSettings | null>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [aiStatusError, setAiStatusError] = useState(false);
  const [aiUsageError, setAiUsageError] = useState(false);
  const [systemHealthError, setSystemHealthError] = useState(false);

  const loadDashboardData = async () => {
    try {
      setRefreshing(true);

      // Load data individually to handle errors gracefully for each service
      try {
        const aiStatusData = await apiService.getAIStatus();
        setAiStatus(aiStatusData);
        setAiStatusError(false);
      } catch (error) {
        console.warn('AI status not available:', error);
        setAiStatusError(true);
        setAiStatus({ provider: 'unavailable', status: 'inactive', available_models: [], default_model: '' });
      }

      try {
        const aiUsageData = await apiService.getAIUsage();
        setAiUsage(aiUsageData);
        setAiUsageError(false);
      } catch (error) {
        console.warn('AI usage data not available:', error);
        setAiUsageError(true);
        setAiUsage({
          period: { year: 0, month: 0, month_year: '0000-00' },
          total_tokens: 0,
          prompt_tokens: 0,
          completion_tokens: 0,
          total_requests: 0,
          unique_models: 0,
          model_breakdown: []
        });
      }

      try {
        const systemData = await apiService.getSystemHealth();
        setSystemHealth(systemData);
        setSystemHealthError(false);
      } catch (error) {
        console.warn('System health data not available:', error);
        setSystemHealthError(true);
        setSystemHealth({ status: 'unknown', service: 'unavailable' });
      }

      // Load automation statistics - using mock data for now
      try {
        // TODO: Connect to real dashboard API endpoint
        setDashboardStats({
          totalRobots: 5,
          activeAutomations: 12,
          processedMessages: 147,
          avgResponseTime: 2.3
        });
      } catch (error) {
        console.warn('Dashboard stats not available:', error);
        setDashboardStats(null);
      }

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
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">
            🧠 AI CRM Dashboard
          </h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">
            Интеллектуальная автоматизация бизнеса
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={() => navigate('/ai/templates')}
            variant="secondary"
            size="sm"
          >
            <LightBulbIcon className="w-4 h-4 mr-2" />
            AI Templates
          </Button>
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
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* AI Status */}
        <div className="card bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">🤖 ИИ Система</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">
                {aiStatusError ? 'Недоступна' : (aiStatus?.status === 'active' ? 'Активна' : 'Неактивна')}
              </p>
            </div>
            <CpuChipIcon className="w-8 h-8 text-van-gogh-ultramarine" />
          </div>
          <div className="mt-4 flex items-center">
            {getStatusIcon(aiStatus?.status || 'inactive')}
            <span className="ml-2 text-sm text-van-gogh-chrome-green">
              {aiStatusError ? 'Сервис недоступен' : `${aiStatus?.available_models && Array.isArray(aiStatus.available_models) ? aiStatus.available_models.length : 0} моделей доступно`}
            </span>
          </div>
        </div>

        {/* Automation Stats */}
        <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">⚙️ Автоматизация</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">
                {dashboardStats?.activeAutomations || 0}
              </p>
              <p className="text-xs text-van-gogh-chrome-green mt-1">
                {(dashboardStats?.totalRobots || 0)} роботов
              </p>
            </div>
            <WrenchScrewdriverIcon className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-van-gogh-chrome-green">
              AI-powered процессы
            </span>
          </div>
        </div>

        {/* Message Processing */}
        <div className="card bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">💬 Сообщения</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">
                {dashboardStats?.processedMessages?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-van-gogh-chrome-green mt-1">
                обработано сегодня
              </p>
            </div>
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-600" />
          </div>
          <div className="mt-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="ml-2 text-sm text-van-gogh-chrome-green">
              Автоматическая маршрутизация
            </span>
          </div>
        </div>

        {/* System Health */}
        <div className="card bg-gradient-to-br from-orange-50 to-red-50 border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-van-gogh-chrome-green">🖥️ Система</p>
              <p className="text-2xl font-bold text-van-gogh-starry-night-blue">
                {systemHealthError ? 'Неизвестно' : (systemHealth?.status === 'healthy' ? 'Здорова' : 'Проблемы')}
              </p>
              <p className="text-xs text-van-gogh-chrome-green mt-1">
                {dashboardStats?.avgResponseTime ? `${dashboardStats.avgResponseTime}ms` : 'N/A'} среднее время
              </p>
            </div>
            <ServerIcon className="w-8 h-8 text-orange-600" />
          </div>
          <div className="mt-4 space-y-1">
            <div className="flex items-center">
              {getStatusIcon(systemHealthError ? 'unknown' : (systemHealth?.status === 'healthy' ? 'connected' : 'disconnected'))}
              <span className="ml-2 text-xs text-van-gogh-chrome-green">
                {systemHealthError ? 'БД недоступна' : 'База данных'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Usage Stats */}
      {aiUsage && (
        <div className="card">
          <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">
            📊 Статистика использования ИИ
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-4 rounded-lg">
              <p className="text-sm text-van-gogh-chrome-green">Всего токенов</p>
              <p className="text-2xl font-bold text-van-gogh-ultramarine">
                {(aiUsage.total_tokens || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg">
              <p className="text-sm text-van-gogh-chrome-green">AI Запросов</p>
              <p className="text-2xl font-bold text-van-gogh-chrome-green">
                {(aiUsage.total_requests || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg">
              <p className="text-sm text-van-gogh-chrome-green">Эффективность</p>
              <p className="text-2xl font-bold text-van-gogh-vermilion">
                {aiUsage.total_requests > 0 ? Math.round(aiUsage.total_tokens / aiUsage.total_requests) : 0} ток/запрос
              </p>
            </div>
          </div>

          {/* System Status */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 p-4 rounded-lg text-center">
              <div className="text-3xl mb-2">🚀</div>
              <p className="text-sm font-medium text-emerald-800">Система готова</p>
              <p className="text-xs text-emerald-600">Все сервисы активны</p>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg text-center">
              <div className="text-3xl mb-2">🧠</div>
              <p className="text-sm font-medium text-blue-800">ИИ активен</p>
              <p className="text-xs text-blue-600">Модели загружены</p>
            </div>
            <div className="bg-gradient-to-br from-violet-50 to-purple-50 p-4 rounded-lg text-center">
              <div className="text-3xl mb-2">⚙️</div>
              <p className="text-sm font-medium text-violet-800">Автоматизация</p>
              <p className="text-xs text-violet-600">Процессы запущены</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">
          📈 Последние активности
        </h3>
        <div className="space-y-3">
          <div className="flex items-center p-3 bg-van-gogh-wheat-field/20 rounded-lg">
            <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3" />
            <div className="flex-1">
              <p className="text-sm font-medium text-van-gogh-starry-night-blue">
                AI обработал новое сообщение клиента
              </p>
              <p className="text-xs text-van-gogh-chrome-green">2 минуты назад</p>
            </div>
          </div>
          <div className="flex items-center p-3 bg-van-gogh-wheat-field/20 rounded-lg">
            <CheckCircleIcon className="w-5 h-5 text-blue-500 mr-3" />
            <div className="flex-1">
              <p className="text-sm font-medium text-van-gogh-starry-night-blue">
                Автоматизация создала задачу менеджеру
              </p>
              <p className="text-xs text-van-gogh-chrome-green">5 минут назад</p>
            </div>
          </div>
          <div className="flex items-center p-3 bg-van-gogh-wheat-field/20 rounded-lg">
            <CheckCircleIcon className="w-5 h-5 text-purple-500 mr-3" />
            <div className="flex-1">
              <p className="text-sm font-medium text-van-gogh-starry-night-blue">
                Отправлено персонализированное email уведомление
              </p>
              <p className="text-xs text-van-gogh-chrome-green">12 минут назад</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">
          ⚡ Быстрые действия
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button
            onClick={() => navigate('/settings/ai')}
            variant="secondary"
            fullWidth
            className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
          >
            <CpuChipIcon className="w-5 h-5 mr-2" />
            Настроить ИИ
          </Button>
          <Button
            onClick={() => navigate('/ai/templates')}
            variant="secondary"
            fullWidth
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            <LightBulbIcon className="w-5 h-5 mr-2" />
            AI Шаблоны
          </Button>
          <Button
            onClick={() => navigate('/settings/automation')}
            variant="secondary"
            fullWidth
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
          >
            <WrenchScrewdriverIcon className="w-5 h-5 mr-2" />
            Роботы
          </Button>
          <Button
            onClick={() => navigate('/monitoring')}
            variant="secondary"
            fullWidth
            className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
          >
            <ServerIcon className="w-5 h-5 mr-2" />
            Мониторинг
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
