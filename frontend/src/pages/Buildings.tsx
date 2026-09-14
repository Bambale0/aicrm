import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Buildings() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api.get('/housing/buildings').then(({ data }) => setItems(data)).catch(() => setItems([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Дома и помещения</h1>
        <p className="page-subtitle">Объекты управления и адресная структура</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.length === 0 && <div className="card col-span-full py-12 text-center text-slate-400">Объекты пока не добавлены</div>}
        {items.map((item) => (
          <div key={item.id} className="card">
            <div className="text-base font-semibold text-slate-900">{item.address}</div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-500">
              <div>Подъездов<br/><span className="font-semibold text-slate-800">{item.entrances || '—'}</span></div>
              <div>Помещений<br/><span className="font-semibold text-slate-800">{item.apartments_count || '—'}</span></div>
            </div>
            {item.management_area && <div className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">{item.management_area}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
