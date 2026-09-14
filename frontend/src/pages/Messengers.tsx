import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  ArchiveBoxIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  KeyIcon,
  LinkIcon,
  PencilSquareIcon,
  PlusIcon,
  ShieldCheckIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

interface CredentialField {
  name: string;
  label?: string;
  type: string;
  required?: boolean;
}

interface Provider {
  provider: string;
  name: string;
  primary?: boolean;
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
  credential_status?: Record<string, boolean>;
  webhook_secret_configured?: boolean;
}

interface ChannelPurpose {
  value: string;
  label: string;
  description: string;
}

interface MessengerChannel {
  id: number;
  integration_id: number;
  external_chat_id: string;
  name?: string | null;
  purpose: string;
  channel_type?: string | null;
  status: string;
  provider_data: Record<string, any>;
  last_health_at?: string | null;
  last_error?: string | null;
  is_active: boolean;
}

const AUTH_REQUIRED = process.env.REACT_APP_AUTH_REQUIRED !== 'false';

const statusClass = (status: string) => {
  if (['active', 'verified'].includes(status)) {
    return 'bg-emerald-50 text-emerald-700';
  }
  if (['error', 'removed'].includes(status)) {
    return 'bg-red-50 text-red-700';
  }
  return 'bg-amber-50 text-amber-700';
};

export default function Messengers() {
  const { user } = useAuth();
  const isAdmin =
    !AUTH_REQUIRED ||
    Boolean(user?.is_superuser) ||
    ['admin', 'superuser'].includes(String(user?.role || '').toLowerCase());

  const [providers, setProviders] = useState<Provider[]>([]);
  const [items, setItems] = useState<Integration[]>([]);
  const [channels, setChannels] = useState<MessengerChannel[]>([]);
  const [purposes, setPurposes] = useState<ChannelPurpose[]>([]);

  const [integrationModalOpen, setIntegrationModalOpen] = useState(false);
  const [editingIntegration, setEditingIntegration] = useState<Integration | null>(null);
  const [providerKey, setProviderKey] = useState('max');
  const [name, setName] = useState('MAX УК');
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [aiMonitoring, setAiMonitoring] = useState(true);
  const [privateAck, setPrivateAck] = useState(true);
  const [aiContextMessages, setAiContextMessages] = useState(20);

  const [channelModalOpen, setChannelModalOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<MessengerChannel | null>(null);
  const [channelIntegrationId, setChannelIntegrationId] = useState<number | ''>('');
  const [externalChatId, setExternalChatId] = useState('');
  const [channelName, setChannelName] = useState('');
  const [channelPurpose, setChannelPurpose] = useState('');
  const [channelActive, setChannelActive] = useState(true);

  const [saving, setSaving] = useState(false);
  const [busyKey, setBusyKey] = useState('');
  const [notice, setNotice] = useState('');

  const selectedProvider = useMemo(
    () => providers.find((item) => item.provider === providerKey) || null,
    [providers, providerKey],
  );

  const purposeByValue = useMemo(
    () => new Map(purposes.map((item) => [item.value, item])),
    [purposes],
  );

  const load = async () => {
    if (!isAdmin) return;
    const [providersResponse, integrationsResponse, channelsResponse, purposesResponse] =
      await Promise.all([
        api.get('/messengers/providers'),
        api.get('/messengers'),
        api.get('/messenger-channels'),
        api.get('/messenger-channels/catalog'),
      ]);
    setProviders(providersResponse.data);
    setItems(integrationsResponse.data);
    setChannels(channelsResponse.data);
    setPurposes(purposesResponse.data);

    if (!channelPurpose && purposesResponse.data?.length) {
      setChannelPurpose(purposesResponse.data[0].value);
    }
  };

  useEffect(() => {
    load().catch((error: any) =>
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить подключения'),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const resetIntegrationForm = () => {
    setEditingIntegration(null);
    setProviderKey('max');
    setName('MAX УК');
    setCredentials({});
    setAiMonitoring(true);
    setPrivateAck(true);
    setAiContextMessages(20);
  };

  const openCreateIntegration = () => {
    resetIntegrationForm();
    setIntegrationModalOpen(true);
  };

  const openEditIntegration = (item: Integration) => {
    setEditingIntegration(item);
    setProviderKey(item.provider);
    setName(item.name);
    setCredentials({});
    setAiMonitoring(item.settings?.ai_monitoring_enabled !== false);
    setPrivateAck(item.settings?.send_private_ack !== false);
    setAiContextMessages(Number(item.settings?.ai_context_messages || 20));
    setIntegrationModalOpen(true);
  };

  const saveIntegration = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProvider) return;

    const trimmedCredentials = Object.fromEntries(
      Object.entries(credentials)
        .map(([key, value]) => [key, value.trim()])
        .filter(([, value]) => Boolean(value)),
    );

    if (!editingIntegration) {
      const missing = selectedProvider.credential_fields
        .filter((field) => field.required)
        .filter((field) => !trimmedCredentials[field.name])
        .map((field) => field.label || field.name);
      if (missing.length) {
        setNotice('Заполните: ' + missing.join(', '));
        return;
      }
    }

    setSaving(true);
    setNotice('');
    try {
      const settings =
        providerKey === 'max'
          ? {
              ai_monitoring_enabled: aiMonitoring,
              send_private_ack: privateAck,
              ai_context_messages: Math.max(1, Math.min(aiContextMessages, 50)),
            }
          : {};

      if (editingIntegration) {
        const body: Record<string, any> = {
          name: name.trim(),
          settings,
        };
        if (Object.keys(trimmedCredentials).length) {
          body.credentials = trimmedCredentials;
        }
        await api.patch('/messengers/' + editingIntegration.id, body);
        setNotice(
          Object.keys(trimmedCredentials).length
            ? 'Подключение обновлено, секреты ротированы'
            : 'Подключение обновлено',
        );
      } else {
        await api.post('/messengers', {
          provider: providerKey,
          name: name.trim(),
          credentials: trimmedCredentials,
          settings,
        });
        setNotice('Подключение создано. Проверьте токен, зарегистрируйте webhook и включите его.');
      }

      setIntegrationModalOpen(false);
      resetIntegrationForm();
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось сохранить подключение');
    } finally {
      setSaving(false);
    }
  };

  const runIntegrationAction = async (
    item: Integration,
    action: 'verify' | 'webhook' | 'activate' | 'deactivate',
  ) => {
    const key = 'integration:' + item.id + ':' + action;
    setBusyKey(key);
    setNotice('');
    try {
      if (action === 'webhook' && item.webhook_secret_configured) {
        const accepted = window.confirm(
          'Повторная регистрация webhook перевыпустит webhook-secret. Продолжить?',
        );
        if (!accepted) return;
      }

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
          webhook: item.webhook_secret_configured
            ? 'Webhook и секрет перевыпущены'
            : 'Webhook зарегистрирован, секрет создан',
          activate: 'Подключение включено',
          deactivate: 'Подключение выключено',
        };
        setNotice(labels[action]);
      }
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Операция не выполнена');
    } finally {
      setBusyKey('');
    }
  };

  const archiveIntegration = async (item: Integration) => {
    if (
      !window.confirm(
        'Архивировать подключение? Оно будет выключено вместе со всеми его каналами.',
      )
    ) {
      return;
    }
    setBusyKey('archive:' + item.id);
    try {
      await api.delete('/messengers/' + item.id);
      setNotice('Подключение архивировано');
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось архивировать подключение');
    } finally {
      setBusyKey('');
    }
  };

  const resetChannelForm = () => {
    setEditingChannel(null);
    setChannelIntegrationId(items[0]?.id || '');
    setExternalChatId('');
    setChannelName('');
    setChannelPurpose(purposes[0]?.value || '');
    setChannelActive(true);
  };

  const openCreateChannel = (integration?: Integration) => {
    resetChannelForm();
    if (integration) setChannelIntegrationId(integration.id);
    setChannelModalOpen(true);
  };

  const openEditChannel = (channel: MessengerChannel) => {
    setEditingChannel(channel);
    setChannelIntegrationId(channel.integration_id);
    setExternalChatId(String(channel.external_chat_id));
    setChannelName(channel.name || '');
    setChannelPurpose(channel.purpose);
    setChannelActive(channel.is_active);
    setChannelModalOpen(true);
  };

  const saveChannel = async (event: FormEvent) => {
    event.preventDefault();
    if (!channelIntegrationId || !externalChatId.trim() || !channelPurpose) {
      setNotice('Укажите подключение, chat_id и назначение канала');
      return;
    }

    setSaving(true);
    setNotice('');
    try {
      const body = {
        external_chat_id: externalChatId.trim(),
        purpose: channelPurpose,
        name: channelName.trim() || null,
        is_active: channelActive,
      };

      if (editingChannel) {
        await api.patch('/messenger-channels/' + editingChannel.id, body);
        setNotice('Канал обновлён');
      } else {
        await api.post('/messenger-channels', {
          ...body,
          integration_id: channelIntegrationId,
        });
        setNotice('Канал добавлен в CRM');
      }

      setChannelModalOpen(false);
      resetChannelForm();
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось сохранить канал');
    } finally {
      setSaving(false);
    }
  };

  const runChannelAction = async (
    channel: MessengerChannel,
    action: 'verify' | 'toggle' | 'delete' | 'test',
  ) => {
    const key = 'channel:' + channel.id + ':' + action;
    setBusyKey(key);
    setNotice('');

    try {
      if (action === 'verify') {
        await api.post('/messenger-channels/' + channel.id + '/verify');
        setNotice('Права и метаданные канала проверены');
      } else if (action === 'toggle') {
        await api.patch('/messenger-channels/' + channel.id, {
          is_active: !channel.is_active,
        });
        setNotice(channel.is_active ? 'Канал выключен' : 'Канал включён');
      } else if (action === 'delete') {
        if (!window.confirm('Удалить этот канал из CRM?')) return;
        await api.delete('/messenger-channels/' + channel.id);
        setNotice('Канал удалён из CRM');
      } else {
        const message = window.prompt('Текст тестового сообщения', 'Тест MAX из CRM');
        if (!message?.trim()) return;
        await api.post('/messenger-channels/' + channel.id + '/test', {
          text: message.trim(),
        });
        setNotice('Тестовое сообщение отправлено');
      }
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Операция с каналом не выполнена');
    } finally {
      setBusyKey('');
    }
  };

  if (!isAdmin) {
    return (
      <div className="card">
        <h1 className="page-title">Каналы связи</h1>
        <p className="mt-3 text-sm text-slate-600">
          Управление интеграциями, токенами, webhook и channel/chat ID доступно только администратору CRM.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Каналы связи</h1>
          <p className="page-subtitle">
            MAX — основной канал. Telegram и VK подключаются как дополнительные адаптеры.
            Токены и webhook-secret хранятся зашифрованно и обратно в браузер не возвращаются.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={() => openCreateChannel()}>
            <PlusIcon className="mr-2 h-4 w-4" />
            Канал
          </button>
          <button className="btn-primary" onClick={openCreateIntegration}>
            <PlusIcon className="mr-2 h-4 w-4" />
            Подключение
          </button>
        </div>
      </div>

      {notice && (
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {typeof notice === 'string' ? notice : JSON.stringify(notice)}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {providers.map((provider) => (
          <div key={provider.provider} className="card">
            <div className="flex items-start justify-between gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                <LinkIcon className="h-5 w-5 text-blue-600" />
              </div>
              {provider.primary && (
                <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                  Основной
                </span>
              )}
            </div>
            <div className="mt-3 font-semibold text-slate-900">{provider.name}</div>
            <div className="mt-1 text-xs text-slate-500">
              {provider.capabilities.join(' · ')}
            </div>
          </div>
        ))}
      </div>

      <section className="card overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Боты и подключения</h2>
            <p className="mt-1 text-xs text-slate-500">
              Редактирование секрета означает ротацию: старое значение никогда не показывается.
            </p>
          </div>
          <button className="btn-secondary" onClick={() => load()}>
            <ArrowPathIcon className="mr-2 h-4 w-4" />
            Обновить
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {items.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-400">
              Подключений пока нет
            </div>
          )}

          {items.map((item) => {
            const provider = providers.find((candidate) => candidate.provider === item.provider);
            const itemChannels = channels.filter((channel) => channel.integration_id === item.id);

            return (
              <div key={item.id} className="p-5">
                <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="font-semibold text-slate-900">{item.name}</div>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                        {item.provider.toUpperCase()}
                      </span>
                      <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + statusClass(item.status)}>
                        {item.is_active ? 'active' : item.status}
                      </span>
                    </div>

                    <div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
                      <div>Bot ID: {item.external_account_id || 'не проверен'}</div>
                      <div>Каналов в CRM: {itemChannels.length}</div>
                      <div>
                        Секреты:{' '}
                        {item.has_credentials ? (
                          <span className="font-medium text-emerald-700">зашифрованы</span>
                        ) : (
                          <span className="font-medium text-red-600">не настроены</span>
                        )}
                      </div>
                      <div>
                        Webhook secret:{' '}
                        {item.webhook_secret_configured ? 'настроен' : 'ещё не создан'}
                      </div>
                    </div>

                    {item.webhook_url && (
                      <div className="mt-2 break-all text-xs text-slate-500">
                        Webhook: {item.webhook_url}
                      </div>
                    )}

                    {item.provider === 'max' && (
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                        <span>
                          ИИ-мониторинг: {item.settings?.ai_monitoring_enabled !== false ? 'вкл' : 'выкл'}
                        </span>
                        <span>·</span>
                        <span>
                          Подтверждение жителю: {item.settings?.send_private_ack !== false ? 'вкл' : 'выкл'}
                        </span>
                        <span>·</span>
                        <span>
                          Контекст: {item.settings?.ai_context_messages || 20} сообщений
                        </span>
                      </div>
                    )}

                    {item.last_error && (
                      <div className="mt-2 text-xs text-red-600">{item.last_error}</div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary" onClick={() => openEditIntegration(item)}>
                      <PencilSquareIcon className="mr-2 h-4 w-4" />
                      Настроить
                    </button>
                    <button
                      className="btn-secondary"
                      disabled={Boolean(busyKey)}
                      onClick={() => runIntegrationAction(item, 'verify')}
                    >
                      <CheckCircleIcon className="mr-2 h-4 w-4" />
                      Проверить
                    </button>
                    <button
                      className="btn-secondary"
                      disabled={Boolean(busyKey)}
                      onClick={() => runIntegrationAction(item, 'webhook')}
                    >
                      <KeyIcon className="mr-2 h-4 w-4" />
                      {item.webhook_secret_configured ? 'Webhook / rotate' : 'Webhook'}
                    </button>
                    <button
                      className={item.is_active ? 'btn-danger' : 'btn-primary'}
                      disabled={Boolean(busyKey)}
                      onClick={() =>
                        runIntegrationAction(item, item.is_active ? 'deactivate' : 'activate')
                      }
                    >
                      {item.is_active ? 'Выключить' : 'Включить'}
                    </button>
                    <button
                      className="btn-secondary"
                      disabled={Boolean(busyKey)}
                      onClick={() => archiveIntegration(item)}
                    >
                      <ArchiveBoxIcon className="mr-2 h-4 w-4" />
                      Архив
                    </button>
                  </div>
                </div>

                <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-800">Каналы / чаты</div>
                      <div className="text-xs text-slate-500">
                        MAX chat_id хранится строкой — без потери точности int64.
                      </div>
                    </div>
                    <button className="btn-secondary" onClick={() => openCreateChannel(item)}>
                      <PlusIcon className="mr-2 h-4 w-4" />
                      Добавить
                    </button>
                  </div>

                  <div className="mt-3 space-y-2">
                    {itemChannels.length === 0 && (
                      <div className="rounded-lg bg-white px-3 py-4 text-sm text-slate-400">
                        Каналов пока нет. После MAX <code>bot_added</code> чат мониторинга также появится автоматически.
                      </div>
                    )}
                    {itemChannels.map((channel) => {
                      const purpose = purposeByValue.get(channel.purpose);
                      const ready =
                        channel.status === 'verified' ||
                        (channel.purpose !== 'monitor' && channel.status === 'configured');

                      return (
                        <div key={channel.id} className="rounded-lg border border-slate-200 bg-white p-3">
                          <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-start">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="font-medium text-slate-800">
                                  {channel.name || 'chat ' + channel.external_chat_id}
                                </span>
                                <span className={'rounded-full px-2 py-0.5 text-[11px] font-semibold ' + statusClass(channel.status)}>
                                  {channel.status}
                                </span>
                                {!channel.is_active && (
                                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">
                                    выключен
                                  </span>
                                )}
                              </div>
                              <div className="mt-1 text-xs text-slate-500">
                                chat_id: {channel.external_chat_id}
                                {channel.channel_type ? ' · ' + channel.channel_type : ''}
                              </div>
                              <div className="mt-1 text-xs text-slate-600">
                                {purpose?.label || channel.purpose}
                              </div>
                              {channel.purpose === 'monitor' && (
                                <div className="mt-1 text-xs">
                                  <span className={ready ? 'text-emerald-700' : 'text-amber-700'}>
                                    {channel.provider_data?.is_admin &&
                                    channel.provider_data?.read_all_messages
                                      ? 'Админ · read_all_messages есть'
                                      : 'Нужно проверить права администратора/read_all_messages'}
                                  </span>
                                </div>
                              )}
                              {channel.last_error && (
                                <div className="mt-1 text-xs text-red-600">{channel.last_error}</div>
                              )}
                            </div>

                            <div className="flex flex-wrap gap-2">
                              <button className="btn-secondary" onClick={() => openEditChannel(channel)}>
                                <PencilSquareIcon className="mr-1 h-4 w-4" />
                                Изменить
                              </button>
                              {provider?.provider === 'max' && (
                                <>
                                  <button
                                    className="btn-secondary"
                                    disabled={Boolean(busyKey)}
                                    onClick={() => runChannelAction(channel, 'verify')}
                                  >
                                    <ShieldCheckIcon className="mr-1 h-4 w-4" />
                                    Права
                                  </button>
                                  <button
                                    className="btn-secondary"
                                    disabled={Boolean(busyKey)}
                                    onClick={() => runChannelAction(channel, 'test')}
                                  >
                                    Тест
                                  </button>
                                </>
                              )}
                              <button
                                className="btn-secondary"
                                disabled={Boolean(busyKey)}
                                onClick={() => runChannelAction(channel, 'toggle')}
                              >
                                {channel.is_active ? 'Выкл' : 'Вкл'}
                              </button>
                              <button
                                className="btn-secondary"
                                disabled={Boolean(busyKey)}
                                onClick={() => runChannelAction(channel, 'delete')}
                                aria-label="Удалить канал"
                              >
                                <TrashIcon className="h-4 w-4 text-red-600" />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {integrationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4 backdrop-blur-sm">
          <form onSubmit={saveIntegration} className="card max-h-[90vh] w-full max-w-xl space-y-4 overflow-y-auto shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  {editingIntegration ? 'Настроить подключение' : 'Подключить мессенджер'}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {editingIntegration
                    ? 'Секретные поля оставьте пустыми, если менять их не нужно.'
                    : 'Все секреты шифруются до записи в БД.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIntegrationModalOpen(false)}
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
                disabled={Boolean(editingIntegration)}
                onChange={(event) => {
                  setProviderKey(event.target.value);
                  setCredentials({});
                }}
              >
                {providers.map((provider) => (
                  <option key={provider.provider} value={provider.provider}>
                    {provider.name}{provider.primary ? ' · основной' : ''}
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
                maxLength={255}
              />
            </div>

            {(selectedProvider?.credential_fields || []).map((field) => (
              <div key={field.name}>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  {field.label || field.name}
                  {editingIntegration && (
                    <span className="ml-2 font-normal text-slate-400">пусто = не менять</span>
                  )}
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
                  required={!editingIntegration && field.required}
                  autoComplete="new-password"
                />
              </div>
            ))}

            {providerKey === 'max' && (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-800">MAX AI-диспетчер</div>
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={aiMonitoring}
                    onChange={(event) => setAiMonitoring(event.target.checked)}
                  />
                  Анализировать входящие сообщения ИИ
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={privateAck}
                    onChange={(event) => setPrivateAck(event.target.checked)}
                  />
                  Подтверждать жителю создание заявки
                </label>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-500">
                    Контекст сообщений для ИИ
                  </label>
                  <input
                    className="input-field"
                    type="number"
                    min={1}
                    max={50}
                    value={aiContextMessages}
                    onChange={(event) => setAiContextMessages(Number(event.target.value || 1))}
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setIntegrationModalOpen(false)} className="btn-secondary">
                Отмена
              </button>
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Сохраняю…' : 'Сохранить'}
              </button>
            </div>
          </form>
        </div>
      )}

      {channelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4 backdrop-blur-sm">
          <form onSubmit={saveChannel} className="card w-full max-w-xl space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  {editingChannel ? 'Настроить канал' : 'Добавить канал / чат'}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  ID хранится в CRM как строка, поэтому большие MAX int64 не искажаются браузером.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setChannelModalOpen(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Подключение</label>
              <select
                className="input-field"
                value={channelIntegrationId}
                disabled={Boolean(editingChannel)}
                onChange={(event) => setChannelIntegrationId(Number(event.target.value))}
                required
              >
                <option value="">Выберите подключение</option>
                {items
                  .filter((item) => item.status !== 'archived')
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} · {item.provider.toUpperCase()}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                chat_id / channel ID
              </label>
              <input
                className="input-field"
                type="text"
                inputMode="numeric"
                value={externalChatId}
                onChange={(event) => setExternalChatId(event.target.value)}
                required
                maxLength={255}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Название в CRM
              </label>
              <input
                className="input-field"
                value={channelName}
                onChange={(event) => setChannelName(event.target.value)}
                placeholder="Например: Общий чат дома"
                maxLength={255}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Назначение
              </label>
              <select
                className="input-field"
                value={channelPurpose}
                onChange={(event) => setChannelPurpose(event.target.value)}
                required
              >
                {purposes.map((purpose) => (
                  <option key={purpose.value} value={purpose.value}>
                    {purpose.label}
                  </option>
                ))}
              </select>
              {purposeByValue.get(channelPurpose)?.description && (
                <p className="mt-1 text-xs text-slate-500">
                  {purposeByValue.get(channelPurpose)?.description}
                </p>
              )}
            </div>

            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={channelActive}
                onChange={(event) => setChannelActive(event.target.checked)}
              />
              Канал включён
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setChannelModalOpen(false)} className="btn-secondary">
                Отмена
              </button>
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Сохраняю…' : 'Сохранить'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
