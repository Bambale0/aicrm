import React, { useEffect, useState } from 'react';
import { LinkIcon, PlusIcon } from '@heroicons/react/24/outline';
import api from '../services/api';

export default function Messengers() {
  const [providers, setProviders] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([api.get('/messengers/providers'), api.get('/messengers')])
      .then(([providersResponse, integrationsResponse]) => {
        setProviders(providersResponse.data);
        setItems(integrationsResponse.data);
      })
      .catch(() => undefined);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Каналы связи</h1>
          <p className="page-subtitle">Единый слой подключения Telegram, MAX, VK и новых мессенджеров</p>
        </div>
        <button className="btn-primary"><PlusIcon className="mr-2 h-4 w-4" />Подключить</button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {providers.map((provider) => (
          <div key={provider.provider} className="card">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
              <LinkIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div className="font-semibold text-slate-900">{provider.name}</div>
            <div className="mt-1 text-xs text-slate-500">{provider.capabilities.join(' · ')}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Подключенные интеграции</h2>
        <div className="mt-4 divide-y divide-slate-100">
          {items.length === 0 && <div className="py-10 text-center text-sm text-slate-400">Интеграций пока нет</div>}
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-4 py-4">
              <div><div className="font-medium text-slate-900">{item.name}</div><div className="mt-1 text-xs text-slate-500">{item.provider}</div></div>
              <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (item.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600')}>{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
