import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  LinkIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

interface CredentialField {
  name: string;
  type: string;
  required?: boolean;
}

interface Provider {
  provider: string;
  name: string;
  credential_fields: CredentialField[];
  capabilities: string[];
  verification: string;
}

interface Integration {
  id: number;
  provider: string;
  name: string;
  status: string;
  settings: Record<string, any>;
  webhook_url?: string | null;
  external_account_id?: string | null;
  last_health_at?: string | null;
  last_error?: string | null;
  is_active: boolean;
  has_credentials: boolean;
}

export default function Messengers() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [items, setItems] = useState<Integration[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [providerKey, setProviderKey] = useState('max');
  const [name, setName] = useState('MAX УК');
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [operatorChatId, setOperatorChatId] = useState('');
  const [aiMonitoring, setAiMonitoring] = useState(true);
  const [privateAck, setPrivateAck] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState('');

  const selectedProvider = useMemo(
    () => providers.find((item) => item.provider === providerKey) || null,
    [providers, providerKey],
  );

  const load = async () => {
    const [providersResponse, integrationsResponse] = await Promise.all([
      api.get('/messengers/providers'),
      api.get('/messengers'),
    ]);
    setProviders(providersResponse.data);
    setItems(integrationsResponse.data);
  };

  useEffect(() => {
    load().catch(() => setNotice('Не удалось загрузить подключения'));
  }, []);

  const createIntegration = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProvider) return;
    setSaving(true);
    setNotice('');
    try {
      await api.post('/messengers', {
        provider: providerKey,
        name: name.trim(),
        credentials,
        settings: {
          ai_monitoring_enabled: aiMonitoring,
          send_private_ack: privateAck,
          ...(operatorChatId.trim() ? { operator_chat_id: operatorChatId.trim() } : {}),
        },
      });
      setModalOpen(false);
      setCredentials({});
      setOperatorChatId('');
      setNotice('Подключение создано. Теперь проверьте токен и включите webhook.');
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось создать подключение');
    } finally {
      setSaving(false);
    }
  };

  const runAction = async (
    item: Integration,
    action: 'verify' | 'webhook' | 'activate' | 'deactivate',
  ) => {
    setBusyId(item.id);
    setNotice('');
    try {
      const path =
        action === 'webhook'
          ? '/messengers/' + item.id + '/webhook/register'
          : '/messengers/' + item.id + '/' + action;
      const response = await api.post(path, action === 'webhook' ? {} : undefined);

      if (action === 'verify' && response.data.verified === false) {
        setNotice(response.data.detail || 'Токен не прошёл проверку');
      } else {
        const labels: Record<string, string> = {
          verify: 'Токен проверен',
          webhook: 'Webhook зарегистрирован',
          activate: 'Подключение включено',
          deactivate: 'Подключение выключено',
        };
        setNotice(labels[action]);
      }
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Операция не выполнена');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Каналы связи</h1>
          <p className="page-subtitle">
            Бот принимает личные заявки и может работать администратором общего чата, где ИИ отделяет трёп от реальных проблем.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setModalOpen(true)}>
          <PlusIcon className="mr-2 h-4 w-4" />
          Подключить
        </button>
      </div>

      {notice && (
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {typeof notice === 'string' ? notice : JSON.stringify(notice)}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {providers.map((provider) => (
          <div key={provider.provider} className="card">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
              <LinkIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div className="font-semibold text-slate-900">{provider.name}</div>
            <div className="mt-1 text-xs text-slate-500">
              {provider.capabilities.join(' · ')}
            </div>
          </div>
        ))}
      </div>

      <div className="card overflow-hidden p-0">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-lg font-semibold text-slate-900">Подключенные интеграции</h2>
        </div>

        <div className="divide-y divide-slate-100">
          {items.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-400">
              Интеграций пока нет
            </div>
          )}

          {items.map((item) => (
            <div key={item.id} className="p-5">
              <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="font-semibold text-slate-900">{item.name}</div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                      {item.provider.toUpperCase()}
                    </span>
                    <span
                      className={
                        'rounded-full px-2.5 py-1 text-xs font-semibold ' +
                        (item.is_active
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-amber-50 text-amber-700')
                      }
                    >
                      {item.is_active ? 'Активен' : item.status}
                    </span>
                  </div>

                  <div className="mt-2 space-y-1 text-xs text-slate-500">
                    {item.external_account_id && <div>Bot ID: {item.external_account_id}</div>}
                    {item.webhook_url && <div className="break-all">Webhook: {item.webhook_url}</div>}
                    {item.settings?.ai_monitoring_enabled && (
                      <div>ИИ-мониторинг включён</div>
                    )}
                    {(item.settings?.monitor_chat_ids || []).length > 0 && (
                      <div className="space-y-1">
                        <div>Чатов под наблюдением: {item.settings.monitor_chat_ids.length}</div>
                        {(item.settings.monitor_chat_ids || []).slice(0, 5).map((chatId: any) => {
                          const chatStatus = item.settings?.monitor_chat_status?.[String(chatId)];
                          return (
                            <div key={String(chatId)} className="flex flex-wrap items-center gap-2">
                              <span>chat {String(chatId)}</span>
                              {chatStatus ? (
                                <span
                                  className={
                                    'rounded-full px-2 py-0.5 text-[10px] font-semibold ' +
                                    (chatStatus.is_admin && chatStatus.read_all_messages
                                      ? 'bg-emerald-50 text-emerald-700'
                                      : 'bg-red-50 text-red-700')
                                  }
                                >
                                  {chatStatus.is_admin && chatStatus.read_all_messages
                                    ? 'Админ · читает все сообщения'
                                    : 'Нет read_all_messages'}
                                </span>
                              ) : (
                                <span className="text-[10px] text-slate-400">проверяем права…</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {item.settings?.operator_chat_id && (
                      <div>MAX alert-чат оператора: {item.settings.operator_chat_id}</div>
                    )}
                    {item.last_error && <div className="text-red-600">{item.last_error}</div>}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    className="btn-secondary"
                    disabled={busyId === item.id}
                    onClick={() => runAction(item, 'verify')}
                  >
                    <CheckCircleIcon className="mr-2 h-4 w-4" />
                    Проверить
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={busyId === item.id}
                    onClick={() => runAction(item, 'webhook')}
                  >
                    <ArrowPathIcon className="mr-2 h-4 w-4" />
                    Webhook
                  </button>
                  <button
                    className={item.is_active ? 'btn-danger' : 'btn-primary'}
                    disabled={busyId === item.id}
                    onClick={() => runAction(item, item.is_active ? 'deactivate' : 'activate')}
                  >
                    {item.is_active ? 'Выключить' : 'Включить'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4 backdrop-blur-sm">
          <form onSubmit={createIntegration} className="card w-full max-w-xl space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Подключить мессенджер</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Для теста MAX достаточно токена бота. Webhook на HTTPS будет зарегистрирован отдельной кнопкой.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Мессенджер</label>
              <select
                className="input-field"
                value={providerKey}
                onChange={(event) => {
                  setProviderKey(event.target.value);
                  setCredentials({});
                }}
              >
                {providers.map((provider) => (
                  <option key={provider.provider} value={provider.provider}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Название подключения</label>
              <input
                className="input-field"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </div>

            {(selectedProvider?.credential_fields || []).map((field) => (
              <div key={field.name}>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  {field.name === 'access_token'
                    ? 'Access token'
                    : field.name === 'bot_token'
                      ? 'Bot token'
                      : field.name}
                </label>
                <input
                  className="input-field"
                  type={field.type === 'secret' ? 'password' : 'text'}
                  value={credentials[field.name] || ''}
                  onChange={(event) =>
                    setCredentials({
                      ...credentials,
                      [field.name]: event.target.value,
                    })
                  }
                  required={field.required}
                  autoComplete="off"
                />
              </div>
            ))}

            {providerKey === 'max' && (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-800">Контур MAX</div>
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={aiMonitoring}
                    onChange={(event) => setAiMonitoring(event.target.checked)}
                  />
                  ИИ анализирует контекст и отделяет трёп от проблем
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={privateAck}
                    onChange={(event) => setPrivateAck(event.target.checked)}
                  />
                  Подтверждать жителю регистрацию заявки в личном диалоге
                </label>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-500">
                    MAX chat_id оператора для дублирования alert, необязательно
                  </label>
                  <input
                    className="input-field"
                    value={operatorChatId}
                    onChange={(event) => setOperatorChatId(event.target.value)}
                    placeholder="Оставьте пустым — alerts останутся в диспетчерской CRM"
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">
                Отмена
              </button>
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Сохраняю…' : 'Создать подключение'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
