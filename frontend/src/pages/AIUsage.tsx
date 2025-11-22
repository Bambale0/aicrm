import React, { useState, useEffect } from 'react';
import { ChartBarIcon, CpuChipIcon, ClockIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';

interface MonthlyUsage {
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

interface UsageHistoryItem {
  id: number;
  model_used: string;
  endpoint: string;
  total_tokens: number;
  created_at: string;
  request_id: string;
}

const AIUsage: React.FC = () => {
  const [monthlyUsage, setMonthlyUsage] = useState<MonthlyUsage | null>(null);
  const [usageHistory, setUsageHistory] = useState<UsageHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('current');

  useEffect(() => {
    loadUsageData();
  }, [selectedPeriod]);

  const loadUsageData = async () => {
    try {
      const [monthlyResponse, historyResponse] = await Promise.all([
        apiService.getAIMonthlyUsage(),
        apiService.getAIUsageHistory(30)
      ]);
      setMonthlyUsage(monthlyResponse);
      setUsageHistory(historyResponse.history || []);
    } catch (error) {
      console.error('Error loading usage data:', error);
      alert('Ошибка при загрузке данных использования AI');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getModelColor = (model: string) => {
    const colors: { [key: string]: string } = {
      'deepseek/deepseek-chat-v3.1': 'bg-blue-500',
      'moonshotai/kimi-k2': 'bg-green-500',
      'openai/gpt-5-nano': 'bg-purple-500',
      'default': 'bg-gray-500'
    };
    return colors[model] || colors.default;
  };

  const getEndpointLabel = (endpoint: string) => {
    switch (endpoint) {
      case 'analyze-intent': return 'Анализ намерений';
      case 'chat': return 'Чат';
      case 'generate-response': return 'Генерация ответа';
      default: return endpoint;
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
          <h1 className="text-2xl font-bold text-gray-900">Статистика использования ИИ</h1>
          <p className="text-gray-600">Мониторинг использования токенов и запросов к AI</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="current">Текущий месяц</option>
            <option value="previous">Предыдущий месяц</option>
          </select>
          <button
            onClick={loadUsageData}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 flex items-center"
          >
            <ArrowTrendingUpIcon className="w-4 h-4 mr-2" />
            Обновить
          </button>
        </div>
      </div>

      {/* Monthly Statistics Cards */}
      {monthlyUsage && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="w-8 h-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Всего токенов</p>
                <p className="text-2xl font-bold text-gray-900">{formatNumber(monthlyUsage.total_tokens)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CpuChipIcon className="w-8 h-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Запросов</p>
                <p className="text-2xl font-bold text-gray-900">{formatNumber(monthlyUsage.total_requests)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ArrowTrendingUpIcon className="w-8 h-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Уникальных моделей</p>
                <p className="text-2xl font-bold text-gray-900">{monthlyUsage.unique_models}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="w-8 h-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Среднее на запрос</p>
                <p className="text-2xl font-bold text-gray-900">
                  {monthlyUsage.total_requests > 0
                    ? formatNumber(Math.round(monthlyUsage.total_tokens / monthlyUsage.total_requests))
                    : 0
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Token Distribution */}
      {monthlyUsage && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Распределение токенов</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{formatNumber(monthlyUsage.prompt_tokens)}</div>
              <div className="text-sm text-gray-600">Токенов запроса</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: monthlyUsage.total_tokens > 0
                      ? `${(monthlyUsage.prompt_tokens / monthlyUsage.total_tokens) * 100}%`
                      : '0%'
                  }}
                ></div>
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{formatNumber(monthlyUsage.completion_tokens)}</div>
              <div className="text-sm text-gray-600">Токенов ответа</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{
                    width: monthlyUsage.total_tokens > 0
                      ? `${(monthlyUsage.completion_tokens / monthlyUsage.total_tokens) * 100}%`
                      : '0%'
                  }}
                ></div>
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(monthlyUsage.total_tokens)}</div>
              <div className="text-sm text-gray-600">Всего токенов</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div className="bg-gray-900 h-2 rounded-full w-full"></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Usage History */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">История использования</h3>
          <p className="text-sm text-gray-600 mt-1">Последние 30 дней</p>
        </div>

        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {usageHistory.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              История использования пуста
            </div>
          ) : (
            usageHistory.map((item) => (
              <div key={item.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${getModelColor(item.model_used)}`}></div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-1">
                        <span className="text-sm font-medium text-gray-900">{item.model_used}</span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {getEndpointLabel(item.endpoint)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{formatDate(item.created_at)}</span>
                        <span>{formatNumber(item.total_tokens)} токенов</span>
                        <span>ID: {item.request_id}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatNumber(item.total_tokens)}
                    </div>
                    <div className="text-xs text-gray-500">
                      токенов
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Model Usage Summary */}
      {usageHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Использование по моделям</h3>
          <div className="space-y-3">
            {Object.entries(
              usageHistory.reduce((acc, item) => {
                if (!acc[item.model_used]) {
                  acc[item.model_used] = { tokens: 0, requests: 0 };
                }
                acc[item.model_used].tokens += item.total_tokens;
                acc[item.model_used].requests += 1;
                return acc;
              }, {} as Record<string, { tokens: number; requests: number }>)
            )
              .sort(([, a], [, b]) => b.tokens - a.tokens)
              .map(([model, stats]) => (
                <div key={model} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getModelColor(model)}`}></div>
                    <span className="text-sm font-medium text-gray-900">{model}</span>
                    <span className="text-xs text-gray-500">({stats.requests} запросов)</span>
                  </div>
                  <div className="text-sm font-medium text-gray-900">
                    {formatNumber(stats.tokens)} токенов
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIUsage;
