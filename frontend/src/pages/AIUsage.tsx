import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  ChartBarIcon,
  CpuChipIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface AIUsageStats {
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
  date: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_requests: number;
  cost_usd?: number;
}

export default function AIUsage() {
  const [monthlyStats, setMonthlyStats] = useState<AIUsageStats | null>(null);
  const [usageHistory, setUsageHistory] = useState<UsageHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('current');

  useEffect(() => {
    loadData();
  }, [selectedPeriod]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load monthly stats
      const stats = await apiService.getAIUsage();
      setMonthlyStats(stats);

      // Load usage history
      const history = await apiService.getUsageHistory();
      setUsageHistory(history || []);
    } catch (error) {
      console.error('Failed to load AI usage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    }
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return 'N/A';
    return `$${amount.toFixed(2)}`;
  };

  const getModelColor = (index: number) => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500',
      'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500'
    ];
    return colors[index % colors.length];
  };

  const calculateCost = (tokens: number, model: string) => {
    // Rough estimation - in real app this would come from API
    const rates: { [key: string]: { input: number; output: number } } = {
      'gpt-4': { input: 0.03, output: 0.06 },
      'gpt-3.5-turbo': { input: 0.0015, output: 0.002 },
      'claude-3': { input: 0.015, output: 0.075 },
      'default': { input: 0.002, output: 0.002 }
    };

    const rate = rates[model] || rates.default;
    // Assuming 70% completion tokens, 30% prompt tokens
    const promptCost = (tokens * 0.3) * rate.input / 1000;
    const completionCost = (tokens * 0.7) * rate.output / 1000;
    return promptCost + completionCost;
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
          <h1 className="text-3xl font-bold text-gray-900">Статистика AI</h1>
          <p className="text-gray-600 mt-2">Мониторинг использования ИИ и расходов</p>
        </div>
        <button
          onClick={loadData}
          className="btn-secondary flex items-center"
        >
          <ArrowPathIcon className="w-5 h-5 mr-2" />
          Обновить
        </button>
      </div>

      {/* Period Selector */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Период</h3>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="input-field w-48"
          >
            <option value="current">Текущий месяц</option>
            <option value="last">Прошлый месяц</option>
            <option value="last3">Последние 3 месяца</option>
            <option value="year">За год</option>
          </select>
        </div>
      </div>

      {/* Monthly Stats Cards */}
      {monthlyStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center">
              <ChartBarIcon className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Всего токенов</p>
                <p className="text-2xl font-bold text-gray-900">{formatTokens(monthlyStats.total_tokens)}</p>
                <p className="text-xs text-gray-500">
                  {monthlyStats.period.month_year}
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <CpuChipIcon className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Запросов</p>
                <p className="text-2xl font-bold text-gray-900">{monthlyStats.total_requests}</p>
                <p className="text-xs text-gray-500">
                  {monthlyStats.unique_models} моделей
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Входящие токены</p>
                <p className="text-2xl font-bold text-gray-900">{formatTokens(monthlyStats.prompt_tokens)}</p>
                <p className="text-xs text-gray-500">
                  {((monthlyStats.prompt_tokens / monthlyStats.total_tokens) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <CurrencyDollarIcon className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Расходы (примерно)</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(monthlyStats.model_breakdown.reduce((sum, model) =>
                    sum + calculateCost(model.tokens, model.model), 0
                  ))}
                </p>
                <p className="text-xs text-gray-500">
                  На основе тарифов
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Breakdown */}
      {monthlyStats && monthlyStats.model_breakdown.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Использование по моделям</h3>
          <div className="space-y-3">
            {monthlyStats.model_breakdown.map((model, index) => {
              const percentage = (model.tokens / monthlyStats.total_tokens) * 100;
              return (
                <div key={model.model} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded ${getModelColor(index)}`}></div>
                    <div>
                      <p className="font-medium text-gray-900">{model.model}</p>
                      <p className="text-sm text-gray-600">
                        {model.requests} запросов • {formatTokens(model.tokens)} токенов
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">{percentage.toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">
                      ~{formatCurrency(calculateCost(model.tokens, model.model))}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Usage History Chart Placeholder */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">История использования</h3>
        {usageHistory.length > 0 ? (
          <div className="space-y-4">
            <div className="text-sm text-gray-600 mb-4">
              График использования токенов по дням (плейсхолдер - требуется интеграция с Chart.js или Recharts)
            </div>
            <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Здесь будет график использования AI</p>
              <p className="text-sm text-gray-500 mt-2">
                Требуется добавить библиотеку для графиков (Chart.js, Recharts, или D3.js)
              </p>
            </div>

            {/* History Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Токены
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Запросы
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Расходы
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {usageHistory.slice(0, 10).map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(item.date).toLocaleDateString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatTokens(item.total_tokens)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.total_requests}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(item.cost_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">История использования недоступна</p>
            <p className="text-sm text-gray-500 mt-1">
              Данные по истории использования AI не найдены
            </p>
          </div>
        )}
      </div>

      {/* Cost Analysis */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Анализ расходов</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Рекомендации по оптимизации</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Используйте GPT-3.5-turbo для простых задач</li>
              <li>• Кешируйте частые запросы</li>
              <li>• Оптимизируйте промпты для меньшего количества токенов</li>
              <li>• Мониторьте использование по пользователям</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Прогноз на следующий месяц</h4>
            <div className="space-y-2 text-sm">
              <p className="text-gray-600">
                На основе текущего использования:
              </p>
              <p className="font-medium text-gray-900">
                ~{formatCurrency(
                  monthlyStats ?
                  monthlyStats.model_breakdown.reduce((sum, model) =>
                    sum + calculateCost(model.tokens, model.model), 0
                  ) : 0
                )}
              </p>
              <p className="text-xs text-gray-500">
                Расчет основан на средних тарифах провайдеров
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
