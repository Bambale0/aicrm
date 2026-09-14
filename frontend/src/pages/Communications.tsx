import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

interface Conversation {
  id: number;
  integration_id: number;
  provider?: string;
  external_chat_id: string;
  resident_id?: number;
  status: string;
  requires_attention: boolean;
  summary?: string;
  last_message_at?: string;
}

interface OperatorAlert {
  id: number;
  conversation_id?: number | null;
  request_id?: number | null;
  request_number?: string | null;
  provider?: string | null;
  external_chat_id?: string | null;
  kind: string;
  severity: string;
  title: string;
  summary: string;
  status: string;
  created_at: string;
}

interface Message {
  id: number;
  direction: 'inbound' | 'outbound';
  message_type: string;
  text?: string;
  status: string;
  created_at: string;
}

export default function Communications() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [alerts, setAlerts] = useState<OperatorAlert[]>([]);
  const [messageText, setMessageText] = useState('');
  const [filter, setFilter] = useState<'all' | 'attention'>('all');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [creatingRequest, setCreatingRequest] = useState(false);
  const [notice, setNotice] = useState('');

  const loadConversations = async () => {
    setLoading(true);
    try {
      const [conversationResponse, alertResponse] = await Promise.all([
        api.get('/conversations', {
          params: filter === 'attention' ? { requires_attention: true } : {},
        }),
        api.get('/operator-alerts', { params: { status: 'new', limit: 100 } }),
      ]);
      setConversations(conversationResponse.data);
      setAlerts(alertResponse.data);
      if (!selectedId && conversationResponse.data.length) {
        setSelectedId(conversationResponse.data[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId: number) => {
    const response = await api.get('/conversations/' + conversationId + '/messages');
    setMessages(response.data);
  };

  useEffect(() => {
    loadConversations().catch(() => undefined);
    const timer = window.setInterval(() => {
      loadConversations().catch(() => undefined);
    }, 10000);
    return () => window.clearInterval(timer);
  }, [filter]);

  useEffect(() => {
    if (selectedId) {
      loadMessages(selectedId).catch(() => setMessages([]));
    } else {
      setMessages([]);
    }
  }, [selectedId]);

  const selected = useMemo(
    () => conversations.find((item) => item.id === selectedId) || null,
    [conversations, selectedId],
  );

  const sendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedId || !messageText.trim()) return;
    setSending(true);
    setNotice('');
    try {
      await api.post('/conversations/' + selectedId + '/messages', { text: messageText.trim() });
      setMessageText('');
      await loadMessages(selectedId);
      await loadConversations();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось отправить сообщение');
    } finally {
      setSending(false);
    }
  };

  const markAlertRead = async (alert: OperatorAlert) => {
    await api.post('/operator-alerts/' + alert.id + '/read');
    setAlerts((current) => current.filter((item) => item.id !== alert.id));
    await loadConversations();
  };

  const openAlert = (alert: OperatorAlert) => {
    if (alert.conversation_id) {
      setSelectedId(alert.conversation_id);
    }
  };

  const createRequest = async () => {
    if (!selectedId) return;
    setCreatingRequest(true);
    setNotice('');
    try {
      const response = await api.post('/conversations/' + selectedId + '/request', {
        category: 'general',
        priority: 'normal',
      });
      setNotice('Создана заявка ' + response.data.number);
      await loadConversations();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось создать заявку');
    } finally {
      setCreatingRequest(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="page-title">Диспетчерская</h1>
          <p className="page-subtitle">Единый приватный поток сообщений из подключенных мессенджеров</p>
        </div>
        <button onClick={() => loadConversations()} className="btn-secondary" disabled={loading}>
          <ArrowPathIcon className={'mr-2 h-4 w-4 ' + (loading ? 'animate-spin' : '')} />
          Обновить
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-900">
              Alerts оператора · {alerts.length}
            </h2>
            <span className="text-xs text-slate-400">Обновление каждые 10 сек.</span>
          </div>

          <div className="grid gap-3 xl:grid-cols-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={
                  'rounded-2xl border p-4 shadow-sm ' +
                  (alert.severity === 'critical'
                    ? 'border-red-200 bg-red-50'
                    : alert.severity === 'high'
                      ? 'border-amber-200 bg-amber-50'
                      : 'border-blue-100 bg-blue-50')
                }
              >
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-white/80 px-2.5 py-1 text-[11px] font-bold uppercase text-slate-600">
                        {alert.severity}
                      </span>
                      {alert.provider && (
                        <span className="text-xs font-medium text-slate-500">
                          {alert.provider.toUpperCase()}
                        </span>
                      )}
                      {alert.request_number && (
                        <span className="text-xs font-medium text-slate-500">
                          {alert.request_number}
                        </span>
                      )}
                    </div>
                    <div className="mt-2 font-semibold text-slate-900">{alert.title}</div>
                    <div className="mt-1 text-sm leading-6 text-slate-700">{alert.summary}</div>
                    <div className="mt-2 text-xs text-slate-400">
                      {new Date(alert.created_at).toLocaleString('ru-RU')}
                    </div>
                  </div>

                  <div className="flex shrink-0 gap-2">
                    {alert.conversation_id && (
                      <button className="btn-secondary px-3 py-2 text-xs" onClick={() => openAlert(alert)}>
                        Открыть чат
                      </button>
                    )}
                    <button className="btn-primary px-3 py-2 text-xs" onClick={() => markAlertRead(alert)}>
                      Принято
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid min-h-[650px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:grid-cols-[360px_1fr]">
        <aside className="border-b border-slate-200 lg:border-b-0 lg:border-r">
          <div className="flex gap-2 border-b border-slate-200 p-3">
            <button
              onClick={() => setFilter('all')}
              className={'rounded-lg px-3 py-2 text-sm font-medium ' + (filter === 'all' ? 'bg-blue-50 text-blue-700' : 'text-slate-500 hover:bg-slate-50')}
            >
              Все
            </button>
            <button
              onClick={() => setFilter('attention')}
              className={'rounded-lg px-3 py-2 text-sm font-medium ' + (filter === 'attention' ? 'bg-amber-50 text-amber-700' : 'text-slate-500 hover:bg-slate-50')}
            >
              Требуют внимания
            </button>
          </div>

          <div className="max-h-[590px] overflow-y-auto">
            {!loading && conversations.length === 0 && (
              <div className="p-8 text-center text-sm text-slate-400">Сообщений пока нет</div>
            )}

            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => setSelectedId(conversation.id)}
                className={'w-full border-b border-slate-100 px-4 py-4 text-left transition hover:bg-slate-50 ' + (selectedId === conversation.id ? 'bg-blue-50/60' : '')}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-2">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100">
                      <ChatBubbleLeftRightIcon className="h-5 w-5 text-slate-500" />
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-slate-900">
                        {conversation.provider || 'Мессенджер'} · {conversation.external_chat_id}
                      </div>
                      <div className="mt-0.5 truncate text-xs text-slate-500">
                        {conversation.summary || 'Диалог с жителем'}
                      </div>
                    </div>
                  </div>
                  {conversation.requires_attention && <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-amber-500" title="Требует внимания" />}
                </div>
                {conversation.last_message_at && (
                  <div className="mt-2 text-xs text-slate-400">
                    {new Date(conversation.last_message_at).toLocaleString('ru-RU')}
                  </div>
                )}
              </button>
            ))}
          </div>
        </aside>

        <section className="flex min-h-[650px] flex-col">
          {!selected ? (
            <div className="flex flex-1 items-center justify-center p-10 text-center text-sm text-slate-400">
              Выберите диалог слева
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
                <div>
                  <div className="font-semibold text-slate-900">
                    {selected.provider || 'Мессенджер'} · чат {selected.external_chat_id}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {selected.requires_attention ? 'Требует внимания диспетчера' : 'Обработан'}
                  </div>
                </div>
                <button onClick={createRequest} disabled={creatingRequest} className="btn-primary">
                  <ClipboardDocumentListIcon className="mr-2 h-4 w-4" />
                  {creatingRequest ? 'Создаем…' : 'Создать заявку'}
                </button>
              </div>

              {notice && (
                <div className="mx-5 mt-4 rounded-xl bg-blue-50 px-4 py-3 text-sm text-blue-700">{notice}</div>
              )}

              <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50/60 p-5">
                {messages.length === 0 && (
                  <div className="py-12 text-center text-sm text-slate-400">В диалоге пока нет сообщений</div>
                )}
                {messages.map((message) => (
                  <div key={message.id} className={'flex ' + (message.direction === 'outbound' ? 'justify-end' : 'justify-start')}>
                    <div className={'max-w-[82%] rounded-2xl px-4 py-3 text-sm shadow-sm ' + (message.direction === 'outbound' ? 'bg-blue-600 text-white' : 'border border-slate-200 bg-white text-slate-800')}>
                      <div className="whitespace-pre-wrap">{message.text || '[' + message.message_type + ']'}</div>
                      <div className={'mt-1 text-[11px] ' + (message.direction === 'outbound' ? 'text-blue-100' : 'text-slate-400')}>
                        {new Date(message.created_at).toLocaleString('ru-RU')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <form onSubmit={sendMessage} className="flex gap-3 border-t border-slate-200 bg-white p-4">
                <input
                  className="input-field"
                  placeholder="Ответить жителю…"
                  value={messageText}
                  onChange={(event) => setMessageText(event.target.value)}
                />
                <button type="submit" disabled={sending || !messageText.trim()} className="btn-primary shrink-0">
                  <PaperAirplaneIcon className="h-5 w-5" />
                  <span className="ml-2 hidden sm:inline">Отправить</span>
                </button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
