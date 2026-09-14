import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Residents() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api.get('/housing/residents').then(({ data }) => setItems(data)).catch(() => setItems([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Жители</h1>
        <p className="page-subtitle">Контакты заявителей и привязка к помещениям</p>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr><th className="px-5 py-3">ФИО</th><th className="px-5 py-3">Телефон</th><th className="px-5 py-3">Email</th><th className="px-5 py-3">Канал</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.length === 0 && <tr><td colSpan={4} className="px-5 py-12 text-center text-slate-400">Жители еще не добавлены</td></tr>}
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="px-5 py-4 font-medium text-slate-900">{item.full_name}</td>
                  <td className="px-5 py-4 text-slate-600">{item.phone || '—'}</td>
                  <td className="px-5 py-4 text-slate-600">{item.email || '—'}</td>
                  <td className="px-5 py-4 text-slate-600">{item.preferred_channel || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
