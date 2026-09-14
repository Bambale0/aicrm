import React, { useEffect, useState } from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import api from '../services/api';

export default function Requests() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/housing/requests')
      .then(({ data }) => setItems(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Заявки</h1>
          <p className="page-subtitle">Единый реестр обращений жителей и работ по ним</p>
        </div>
        <button className="btn-primary"><PlusIcon className="mr-2 h-4 w-4" />Новая заявка</button>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">№</th>
                <th className="px-5 py-3">Проблема</th>
                <th className="px-5 py-3">Категория</th>
                <th className="px-5 py-3">Приоритет</th>
                <th className="px-5 py-3">Статус</th>
                <th className="px-5 py-3">SLA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {!loading && items.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-12 text-center text-slate-400">Заявок пока нет</td></tr>
              )}
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50">
                  <td className="px-5 py-4 font-medium text-slate-700">{item.number}</td>
                  <td className="max-w-md px-5 py-4">
                    <div className="font-medium text-slate-900">{item.title}</div>
                    <div className="mt-1 truncate text-slate-500">{item.description}</div>
                  </td>
                  <td className="px-5 py-4 text-slate-600">{item.category}</td>
                  <td className="px-5 py-4 text-slate-600">{item.priority}</td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">{item.status}</span>
                  </td>
                  <td className={'px-5 py-4 text-sm ' + (item.overdue ? 'font-semibold text-red-600' : 'text-slate-500')}>
                    {item.overdue ? 'Просрочено' : item.sla_deadline ? new Date(item.sla_deadline).toLocaleString('ru-RU') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
