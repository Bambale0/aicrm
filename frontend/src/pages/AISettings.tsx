import React, { useState, useEffect, useCallback } from 'react';
import { apiService, AIStatus, AIUsageStats } from '../services/api';
import {
  CpuChipIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  KeyIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface AIModel {
  id: string;
  name: string;
  context_length: number;
  pricing?: {
    input: number;
    output: number;
  };
}

export default function AISettings() {
  const [models, setModels] = useState<AIModel[]>([]);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Settings state
  const [settings, setSettings] = useState({
    default_model: '',
    temperature: 0.7,
    max_tokens: 2000,
    api_key: ''
  });

  const loadAIData = useCallback(async () => {
    try {
      const [modelsResponse, statusData, usageData] = await Promise.all([
        apiService.getAIModels(),
        apiService.getAIStatus(),
        apiService.getAIUsage()
      ]);

      setModels(Array.isArray(modelsResponse) ? modelsResponse : []);
      setAiStatus(statusData);
      setAiUsage(usageData);

      // Set default model if available
      if (Array.isArray(modelsResponse) && modelsResponse.length > 0 && !settings.default_model) {
        setSettings(prev => ({ ...prev, default_model: modelsResponse[0].id }));
      }
    } catch (error) {
      console.error('Failed to load AI data:', error);
      setModels([]);
    } finally {
      setLoading(false);
    }
  }, [settings.default_model]);

  useEffect(() => {
    loadAIData();
  }, [loadAIData]);

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await apiService.updateAISettings(settings);
      // Reload status to reflect changes
      const statusData = await apiService.getAIStatus();
      setAiStatus(statusData);
      alert('Настройки ИИ успешно сохранены');
    } catch (error) {
      console.error('Failed to save AI settings:', error);
      alert('Ошибка при сохранении настроек');
    } finally {
      setSaving(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'inactive':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Активен';
      case 'inactive':
        return 'Неактивен';
      default:
        return 'Ошибка';
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
        <h1 className="text-3xl font-bold text-gray-900">Настройки ИИ</h1>
        <p className="text-gray-600 mt-2">Управление настройками искусственного интеллекта</p>
      </div>

      {/* AI Status Overview */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Статус системы ИИ</h3>
          <button
            onClick={loadAIData}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <ArrowPathIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon(aiStatus?.status || 'inactive')}
            <div>
              <p className="font-medium text-gray-900">Статус</p>
              <p className="text-sm text-gray-600">{getStatusText(aiStatus?.status || 'inactive')}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <CpuChipIcon className="w-5 h-5 text-blue-500" />
            <div>
              <p className="font-medium text-gray-900">Моделей</p>
              <p className="text-sm text-gray-600">{aiStatus?.available_models?.length || 0} доступно</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <ChartBarIcon className="w-5 h-5 text-green-500" />
            <div>
              <p className="font-medium text-gray-900">Провайдер</p>
              <p className="text-sm text-gray-600">{aiStatus?.provider || 'Неизвестно'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Models */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Доступные модели ИИ</h3>

        {models.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model) => (
              <div key={model.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{model.name}</h4>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    openrouter
                  </span>
                </div>

                <div className="space-y-1 text-sm text-gray-600">
                  <p>Контекст: {model.context_length.toLocaleString()} токенов</p>
                  {model.pricing && (
                    <p>
                      Цена: ${model.pricing.input}/1K вход • ${model.pricing.output}/1K выход
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">Модели не найдены</p>
        )}
      </div>

      {/* AI Settings Form */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Настройки ИИ</h3>

        <div className="space-y-6">
          {/* Default Model */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Модель по умолчанию
            </label>
            <select
              value={settings.default_model}
              onChange={(e) => setSettings(prev => ({ ...prev, default_model: e.target.value }))}
              className="input-field"
            >
              <option value="">Выберите модель</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} (openrouter)
                </option>
              ))}
            </select>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Температура: {settings.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Детерминированный (0)</span>
              <span>Креативный (2)</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Максимальное количество токенов
            </label>
            <input
              type="number"
              value={settings.max_tokens}
              onChange={(e) => setSettings(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
              className="input-field"
              min="1"
              max="8000"
            />
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API ключ
            </label>
            <div className="relative">
              <input
                type="password"
                value={settings.api_key}
                onChange={(e) => setSettings(prev => ({ ...prev, api_key: e.target.value }))}
                className="input-field pr-10"
                placeholder="Введите API ключ..."
              />
              <KeyIcon className="absolute right-3 top-3 w-5 h-5 text-gray-400" />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              API ключ для доступа к сервисам ИИ (OpenRouter, OpenAI и т.д.)
            </p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="btn-primary flex items-center"
            >
              {saving && <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />}
              <Cog6ToothIcon className="w-5 h-5 mr-2" />
              {saving ? 'Сохранение...' : 'Сохранить настройки'}
            </button>
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      {aiUsage && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика использования</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{(aiUsage.total_tokens || 0).toLocaleString()}</div>
              <div className="text-sm text-gray-600">Всего токенов</div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{(aiUsage.total_requests || 0).toLocaleString()}</div>
              <div className="text-sm text-gray-600">Всего запросов</div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{(aiUsage.unique_models || 0).toLocaleString()}</div>
              <div className="text-sm text-gray-600">Уникальных моделей</div>
            </div>
          </div>

          {aiUsage.model_breakdown && aiUsage.model_breakdown.length > 0 && (
            <div className="mt-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">Статистика по моделям</h4>
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
    </div>
  );
}
