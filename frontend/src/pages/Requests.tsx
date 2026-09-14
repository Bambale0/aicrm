import React, { useEffect, useMemo, useState } from 'react';
import { ArrowPathIcon, PlusIcon } from '@heroicons/react/24/outline';
import api from '../services/api';

interface RequestStatus {
  value: string;
  label: string;
  terminal: boolean;
}

interface RequestTransition {
  to: string;
  label: string;
  tone: 'primary' | 'danger' | 'secondary' | string;
}

interface RequestStatusCatalog {
  statuses: RequestStatus[];
  transitions: Record<string, RequestTransition[]>;
}

interface ServiceRequest {
  id: number;
  number: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  sla_deadline?: string | null;
  overdue: boolean;
  extra_data?: Record<string, any> | null;
  source_channel?: string;
}

const buttonClass = (tone: string) => {
  if (tone === 'danger') return 'btn-danger';
  if (tone === 'secondary') return 'btn-secondary';
  return 'btn-primary';
};

export default function Requests() {
  const [items, setItems] = useState<ServiceRequest[]>([]);
  const [catalog, setCatalog] = useState<RequestStatusCatalog>({
    statuses: [],
    transitions: {},
  });
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState('');

  const statusLabels = useMemo(
    () => new Map(catalog.statuses.map((item) => [item.value, item.label])),
    [catalog.statuses],
  );

  const load = async () => {
    setLoading(true);
    try {
      const [requestsResponse, catalogResponse] = await Promise.all([
        api.get('/housing/requests'),
        api.get('/housing/request-statuses/catalog'),
      ]);
      setItems(requestsResponse.data);
      setCatalog(catalogResponse.data);
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить заявки');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  const changeStatus = async (
    item: ServiceRequest,
    transition: RequestTransition,
  ) => {
    if (
      transition.tone === 'danger' &&
      !window.confirm('Отменить заявку ' + item.number + '?')
    ) {
      return;
    }

    setBusyId(item.id);
    setNotice('');
    try {
      await api.patch('/housing/requests/' + item.id, {
        status: transition.to,
      });
      setNotice(
        transition.to === 'accepted'
          ? 'Заявка принята. Жителю отправлено уведомление.'
          : 'Статус заявки обновлён.',
      );
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось изменить статус заявки');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Заявки</h1>
          <p className="page-subtitle">
            Единый реестр обращений жителей и работ по ним
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => load()}>
            <ArrowPathIcon className="mr-2 h-4 w-4" />
            Обновить
          </button>
          <button className="btn-primary">
            <PlusIcon className="mr-2 h-4 w-4" />
            Новая заявка
          </button>
        </div>
      </div>

      {notice && (
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {notice}
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">№</th>
                <th className="px-5 py-3">Заявитель</th>
                <th className="px-5 py-3">Проблема</th>
                <th className="px-5 py-3">Статус</th>
                <th className="px-5 py-3">SLA</th>
                <th className="px-5 py-3 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-400">
                    Заявок пока нет
                  </td>
                </tr>
              )}

              {items.map((item) => {
                const transitions = catalog.transitions[item.status] || [];
                const intake = item.extra_data || {};

                return (
                  <tr key={item.id} className="align-top hover:bg-slate-50">
                    <td className="px-5 py-4">
                      <div className="font-medium text-slate-700">{item.number}</div>
                      <div className="mt-1 text-xs text-slate-400">
                        {item.source_channel || 'CRM'}
                      </div>
                    </td>

                    <td className="min-w-[220px] px-5 py-4">
                      <div className="font-medium text-slate-900">
                        {intake.applicant_name || '—'}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {intake.address || 'Адрес не указан'}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {intake.phone || 'Телефон не указан'}
                      </div>
                    </td>

                    <td className="max-w-md px-5 py-4">
                      <div className="font-medium text-slate-900">{item.title}</div>
                      <div className="mt-1 line-clamp-2 text-slate-500">
                        {item.description}
                      </div>
                      <div className="mt-2 text-xs text-slate-400">
                        {item.category} · {item.priority}
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                        {statusLabels.get(item.status) || item.status}
                      </span>
                    </td>

                    <td
                      className={
                        'px-5 py-4 text-sm ' +
                        (item.overdue
                          ? 'font-semibold text-red-600'
                          : 'text-slate-500')
                      }
                    >
                      {item.overdue
                        ? 'Просрочено'
                        : item.sla_deadline
                          ? new Date(item.sla_deadline).toLocaleString('ru-RU')
                          : '—'}
                    </td>

                    <td className="px-5 py-4">
                      <div className="flex min-w-[220px] flex-wrap justify-end gap-2">
                        {transitions.map((transition) => (
                          <button
                            key={transition.to}
                            className={buttonClass(transition.tone) + ' px-3 py-2'}
                            disabled={busyId === item.id}
                            onClick={() => changeStatus(item, transition)}
                          >
                            {transition.label}
                          </button>
                        ))}
                        {transitions.length === 0 && (
                          <span className="text-xs text-slate-400">Действий нет</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
