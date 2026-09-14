import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Contractors() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api.get('/housing/contractors').then(({ data }) => setItems(data)).catch(() => setItems([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Подрядчики</h1>
        <p className="page-subtitle">Компании, договоры, специализации и контакты</p>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr><th className="px-5 py-3">Компания</th><th className="px-5 py-3">ИНН</th><th className="px-5 py-3">Контакт</th><th className="px-5 py-3">Договор</th><th className="px-5 py-3">Специализации</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.length === 0 && <tr><td colSpan={5} className="px-5 py-12 text-center text-slate-400">Подрядчики пока не добавлены</td></tr>}
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="px-5 py-4"><div className="font-medium text-slate-900">{item.name}</div><div className="text-xs text-slate-500">{item.legal_name || ''}</div></td>
                  <td className="px-5 py-4 text-slate-600">{item.inn || '—'}</td>
                  <td className="px-5 py-4 text-slate-600">{item.contact_person || item.phone || '—'}</td>
                  <td className="px-5 py-4 text-slate-600">{item.contract_number || '—'}</td>
                  <td className="px-5 py-4 text-slate-600">{(item.categories || []).join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
