import React, { FormEvent, useEffect, useState } from 'react';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  CpuChipIcon,
  KeyIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

interface AISettings {
  api_key_configured: boolean;
  selected_model: string | null;
}

interface AIModel {
  id: string;
  name: string;
  owned_by?: string | null;
}

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  prompt_cache_hit_tokens: number;
  prompt_cache_miss_tokens: number;
  reasoning_tokens: number;
}

interface TestResult {
  ok: boolean;
  model: string;
  duration_ms: number;
  response?: string | null;
  usage?: TokenUsage | null;
}

interface AIUsageSummary extends TokenUsage {
  api_key_configured: boolean;
  tracked_since?: string | null;
  last_usage_at?: string | null;
  calls: number;
}

interface ProviderBalance {
  supported: boolean;
  provider?: string | null;
  status: string;
  is_available?: boolean;
  balances?: Array<{
    currency: string;
    total_balance: string;
    granted_balance: string;
    topped_up_balance: string;
  }>;
  remaining_tokens?: number | null;
  note?: string;
  error?: string;
}

interface AIUsageResponse {
  usage: AIUsageSummary;
  balance: ProviderBalance;
}

export default function AIConnection() {
  const [settings, setSettings] = useState<AISettings>({
    api_key_configured: false,
    selected_model: null,
  });
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [notice, setNotice] = useState('');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [usage, setUsage] = useState<AIUsageResponse | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);

  const loadUsage = async () => {
    setUsageLoading(true);
    try {
      const response = await api.get('/ai/usage');
      setUsage(response.data as AIUsageResponse);
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить расход AI key');
    } finally {
      setUsageLoading(false);
    }
  };

  const loadModels = async () => {
    setModelsLoading(true);
    setNotice('');
    try {
      const response = await api.get('/ai/models');
      const nextModels = (response.data.data || []) as AIModel[];
      setModels(nextModels);

      setSelectedModel((current) => {
        if (current && nextModels.some((model) => model.id === current)) {
          return current;
        }
        if (settings.selected_model && nextModels.some((model) => model.id === settings.selected_model)) {
          return settings.selected_model;
        }
        return nextModels[0]?.id || '';
      });

      if (nextModels.length === 0) {
        setNotice('API не вернул доступных моделей');
      }
    } catch (error: any) {
      setModels([]);
      setNotice(error?.response?.data?.detail || 'Не удалось получить список моделей');
    } finally {
      setModelsLoading(false);
    }
  };

  const load = async () => {
    setLoading(true);
    setNotice('');
    try {
      const [settingsResponse, usageResponse] = await Promise.all([
        api.get('/ai/settings'),
        api.get('/ai/usage'),
      ]);
      const nextSettings = settingsResponse.data as AISettings;
      setSettings(nextSettings);
      setUsage(usageResponse.data as AIUsageResponse);
      setSelectedModel(nextSettings.selected_model || '');

      if (nextSettings.api_key_configured) {
        try {
          const modelsResponse = await api.get('/ai/models');
          const nextModels = (modelsResponse.data.data || []) as AIModel[];
          setModels(nextModels);
          if (!nextSettings.selected_model && nextModels.length) {
            setSelectedModel(nextModels[0].id);
          }
        } catch (error: any) {
          setNotice(error?.response?.data?.detail || 'Ключ сохранён, но список моделей получить не удалось');
        }
      }
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить настройки ИИ');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  const saveKey = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = apiKey.trim();
    if (!trimmed) {
      setNotice('Введите API key');
      return;
    }

    setSaving(true);
    setNotice('');
    setTestResult(null);
    try {
      const response = await api.put('/ai/settings', { api_key: trimmed });
      setSettings(response.data);
      setApiKey('');
      setNotice('API key сохранён. Загружаю модели и баланс…');
      await Promise.all([loadModels(), loadUsage()]);
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось сохранить API key');
    } finally {
      setSaving(false);
    }
  };

  const saveModel = async () => {
    if (!selectedModel) {
      setNotice('Выберите модель');
      return;
    }

    setSaving(true);
    setNotice('');
    setTestResult(null);
    try {
      const response = await api.put('/ai/settings', {
        selected_model: selectedModel,
      });
      setSettings(response.data);
      setNotice('Модель сохранена');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось сохранить модель');
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    if (!selectedModel) {
      setNotice('Выберите модель');
      return;
    }

    setTesting(true);
    setNotice('');
    setTestResult(null);
    try {
      const response = await api.post('/ai/test', { model: selectedModel });
      setTestResult(response.data);
      await loadUsage();
      setNotice('Соединение с ИИ API работает, фактический расход обновлён');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Тест ИИ API не прошёл');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="page-title">ИИ API</h1>
        <p className="page-subtitle">
          CRM использует внешний OpenAI-compatible API. В интерфейсе настраиваются только ключ и рабочая модель.
        </p>
      </div>

      {notice && (
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {notice}
        </div>
      )}

      <section className="card">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <KeyIcon className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-slate-900">API key</h2>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Ключ хранится в зашифрованном виде и обратно в браузер не возвращается.
            </p>
          </div>
          <span
            className={
              'rounded-full px-3 py-1 text-xs font-semibold ' +
              (settings.api_key_configured
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-600')
            }
          >
            {settings.api_key_configured ? 'Ключ настроен' : 'Ключ не задан'}
          </span>
        </div>

        <form onSubmit={saveKey} className="flex flex-col gap-3 sm:flex-row">
          <input
            className="input-field"
            type="password"
            autoComplete="new-password"
            placeholder={settings.api_key_configured ? 'Введите новый ключ, чтобы заменить текущий' : 'Введите API key'}
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
          />
          <button className="btn-primary shrink-0" type="submit" disabled={saving}>
            {saving ? 'Сохраняю…' : settings.api_key_configured ? 'Заменить ключ' : 'Сохранить ключ'}
          </button>
        </form>
      </section>

      <section className="card">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Расход ключа</h2>
            <p className="mt-1 text-sm text-slate-500">
              Токены считаются только по фактическому <code>usage</code> в ответах AI API.
            </p>
          </div>
          <button
            className="btn-secondary shrink-0"
            type="button"
            disabled={!settings.api_key_configured || usageLoading}
            onClick={() => loadUsage()}
          >
            <ArrowPathIcon className={'mr-2 h-4 w-4 ' + (usageLoading ? 'animate-spin' : '')} />
            Обновить
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card-soft">
            <div className="text-xs text-slate-400">Всего израсходовано</div>
            <div className="mt-1 text-xl font-semibold text-slate-900">
              {(usage?.usage.total_tokens || 0).toLocaleString('ru-RU')} токенов
            </div>
          </div>
          <div className="card-soft">
            <div className="text-xs text-slate-400">Вход / выход</div>
            <div className="mt-1 font-medium text-slate-800">
              {(usage?.usage.prompt_tokens || 0).toLocaleString('ru-RU')} /{' '}
              {(usage?.usage.completion_tokens || 0).toLocaleString('ru-RU')}
            </div>
          </div>
          <div className="card-soft">
            <div className="text-xs text-slate-400">Cache hit / miss</div>
            <div className="mt-1 font-medium text-slate-800">
              {(usage?.usage.prompt_cache_hit_tokens || 0).toLocaleString('ru-RU')} /{' '}
              {(usage?.usage.prompt_cache_miss_tokens || 0).toLocaleString('ru-RU')}
            </div>
          </div>
          <div className="card-soft">
            <div className="text-xs text-slate-400">Вызовов / reasoning</div>
            <div className="mt-1 font-medium text-slate-800">
              {(usage?.usage.calls || 0).toLocaleString('ru-RU')} /{' '}
              {(usage?.usage.reasoning_tokens || 0).toLocaleString('ru-RU')} ток.
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <div className="text-sm font-semibold text-slate-800">Остаток у провайдера</div>
              {usage?.balance.supported && usage.balance.status === 'ok' ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {(usage.balance.balances || []).map((balance) => (
                    <span
                      key={balance.currency}
                      className="rounded-lg bg-white px-3 py-2 text-sm font-semibold text-slate-800"
                    >
                      {balance.total_balance} {balance.currency}
                    </span>
                  ))}
                  <span
                    className={
                      'rounded-lg px-3 py-2 text-sm font-medium ' +
                      (usage.balance.is_available
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-red-50 text-red-700')
                    }
                  >
                    {usage.balance.is_available ? 'API доступен' : 'Баланс недостаточен'}
                  </span>
                </div>
              ) : (
                <div className="mt-2 text-sm text-slate-500">
                  {usage?.balance.error ||
                    (usage?.balance.status === 'key_not_configured'
                      ? 'Сначала сохраните API key'
                      : 'Провайдер не отдаёт баланс через поддерживаемый API')}
                </div>
              )}
            </div>

            <div className="sm:text-right">
              <div className="text-xs text-slate-400">Осталось токенов</div>
              <div className="mt-1 font-semibold text-slate-700">
                {usage?.balance.remaining_tokens != null
                  ? usage.balance.remaining_tokens.toLocaleString('ru-RU')
                  : 'Нет точного значения'}
              </div>
            </div>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            {usage?.balance.note ||
              'Точный остаток токенов показывается только если его отдаёт API провайдера.'}
          </p>
          <p className="mt-2 text-xs text-slate-400">
            {usage?.usage.tracked_since
              ? 'Учёт текущего ключа с ' +
                new Date(usage.usage.tracked_since).toLocaleString('ru-RU')
              : 'Исторический расход до включения этого учёта восстановить из DeepSeek API нельзя.'}
          </p>
        </div>
      </section>

      <section className="card">
        <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div className="flex items-center gap-2">
              <CpuChipIcon className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-slate-900">Модель</h2>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Список загружается напрямую из подключённого API через <code>/models</code>.
            </p>
          </div>
          <button
            className="btn-secondary shrink-0"
            type="button"
            disabled={!settings.api_key_configured || modelsLoading}
            onClick={() => loadModels()}
          >
            <ArrowPathIcon className={'mr-2 h-4 w-4 ' + (modelsLoading ? 'animate-spin' : '')} />
            Обновить модели
          </button>
        </div>

        <div className="space-y-3">
          <select
            className="input-field"
            disabled={!settings.api_key_configured || modelsLoading || models.length === 0}
            value={selectedModel}
            onChange={(event) => setSelectedModel(event.target.value)}
          >
            <option value="">
              {!settings.api_key_configured
                ? 'Сначала сохраните API key'
                : modelsLoading
                  ? 'Загрузка моделей…'
                  : 'Выберите модель'}
            </option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>

          <div className="flex flex-wrap gap-2">
            <button
              className="btn-primary"
              type="button"
              disabled={!selectedModel || saving}
              onClick={saveModel}
            >
              <CheckCircleIcon className="mr-2 h-4 w-4" />
              Сохранить модель
            </button>
            <button
              className="btn-secondary"
              type="button"
              disabled={!selectedModel || testing}
              onClick={testConnection}
            >
              <PlayIcon className="mr-2 h-4 w-4" />
              {testing ? 'Проверяю…' : 'Тест API'}
            </button>
          </div>
        </div>
      </section>

      {testResult && (
        <section className="card border-emerald-100">
          <div className="flex items-center gap-2 text-emerald-700">
            <CheckCircleIcon className="h-5 w-5" />
            <div className="font-semibold">Тест успешен</div>
          </div>
          <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
            <div className="card-soft">
              <div className="text-xs text-slate-400">Модель</div>
              <div className="mt-1 font-medium text-slate-800">{testResult.model}</div>
            </div>
            <div className="card-soft">
              <div className="text-xs text-slate-400">Задержка</div>
              <div className="mt-1 font-medium text-slate-800">{testResult.duration_ms} ms</div>
            </div>
            <div className="card-soft">
              <div className="text-xs text-slate-400">Ответ</div>
              <div className="mt-1 font-medium text-slate-800">{testResult.response || '—'}</div>
            </div>
            <div className="card-soft sm:col-span-3">
              <div className="text-xs text-slate-400">Фактический расход теста</div>
              <div className="mt-1 font-medium text-slate-800">
                {testResult.usage
                  ? testResult.usage.total_tokens.toLocaleString('ru-RU') +
                    ' токенов (' +
                    testResult.usage.prompt_tokens.toLocaleString('ru-RU') +
                    ' вход / ' +
                    testResult.usage.completion_tokens.toLocaleString('ru-RU') +
                    ' выход)'
                  : 'Провайдер не вернул usage'}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
