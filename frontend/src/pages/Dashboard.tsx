import React, { useEffect, useState } from 'react';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  UserGroupIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

interface DashboardData {
  requests: { total: number; in_progress: number; done: number; overdue: number };
  residents: number;
  contractors: number;
  recent_requests: Array<any>;
}

const emptyData: DashboardData = {
  requests: { total: 0, in_progress: 0, done: 0, overdue: 0 },
  residents: 0,
  contractors: 0,
  recent_requests: [],
};

const priorityLabel: Record<string, string> = {
  emergency: 'Аварийная',
  urgent: 'Срочная',
  high: 'Высокая',
  normal: 'Обычная',
  planned: 'Плановая',
};

const statusLabel: Record<string, string> = {
  new: 'Новая',
  assigned: 'Назначена',
  in_progress: 'В работе',
  waiting: 'Ожидание',
  done: 'Выполнена',
  closed: 'Закрыта',
  cancelled: 'Отменена',
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [intake, setIntake] = useState({
    applicant_name: '',
    phone: '',
    address: '',
    apartment: '',
    problem: '',
    notify_resident: true,
  });
  const [intakeSaving, setIntakeSaving] = useState(false);
  const [intakeNotice, setIntakeNotice] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/housing/dashboard');
      setData(response.data);
    } catch {
      setError('Не удалось загрузить сводку. Проверьте соединение с сервером.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submitIntake = async (event: React.FormEvent) => {
    event.preventDefault();
    setIntakeSaving(true);
    setIntakeNotice('');
    try {
      const response = await api.post('/housing/requests/intake', {
        ...intake,
        apartment: intake.apartment || null,
      });
      setIntakeNotice('Заявка ' + response.data.number + ' создана');
      setIntake({
        applicant_name: '',
        phone: '',
        address: '',
        apartment: '',
        problem: '',
        notify_resident: true,
      });
      await load();
    } catch (requestError: any) {
      setIntakeNotice(requestError?.response?.data?.detail || 'Не удалось создать заявку');
    } finally {
      setIntakeSaving(false);
    }
  };

  const active = data.recent_requests.filter((item) => ['new', 'assigned', 'in_progress', 'waiting'].includes(item.status));
  const completed = data.recent_requests.filter((item) => ['done', 'closed'].includes(item.status));
  const overdue = data.recent_requests.filter((item) => item.overdue);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="page-title">Обзор заявок</h1>
          <p className="page-subtitle">Состояние обращений жителей, исполнителей и подрядчиков</p>
        </div>
        <button onClick={load} className="btn-secondary" disabled={loading}>
          <ArrowPathIcon className={'mr-2 h-4 w-4 ' + (loading ? 'animate-spin' : '')} />
          Обновить
        </button>
      </div>

      {error && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>}

      <form onSubmit={submitIntake} className="card">
        <div className="mb-5 flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Прием заявки от жителя</h2>
            <p className="mt-1 text-sm text-slate-500">Минимум полей. Категория, приоритет и SLA определяются автоматически.</p>
          </div>
          <span className="text-xs font-medium text-slate-400">Быстро · понятно · без лишних полей</span>
        </div>

        <div className="grid gap-4 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <label className="mb-2 block text-sm font-medium text-slate-700">Заявитель</label>
            <input
              className="input-field"
              placeholder="ФИО"
              value={intake.applicant_name}
              onChange={(event) => setIntake({ ...intake, applicant_name: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Телефон</label>
            <input
              className="input-field"
              placeholder="+7 900 000-00-00"
              value={intake.phone}
              onChange={(event) => setIntake({ ...intake, phone: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Квартира</label>
            <input
              className="input-field"
              placeholder="Например, 45"
              value={intake.apartment}
              onChange={(event) => setIntake({ ...intake, apartment: event.target.value })}
            />
          </div>
          <div className="lg:col-span-4">
            <label className="mb-2 block text-sm font-medium text-slate-700">Адрес дома</label>
            <input
              className="input-field"
              placeholder="Улица, дом"
              value={intake.address}
              onChange={(event) => setIntake({ ...intake, address: event.target.value })}
              required
            />
          </div>
          <div className="lg:col-span-4">
            <label className="mb-2 block text-sm font-medium text-slate-700">Проблема</label>
            <textarea
              className="input-field min-h-24 resize-y"
              placeholder="Опишите обращение жителя"
              value={intake.problem}
              onChange={(event) => setIntake({ ...intake, problem: event.target.value })}
              required
            />
          </div>
        </div>

        <div className="mt-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={intake.notify_resident}
              onChange={(event) => setIntake({ ...intake, notify_resident: event.target.checked })}
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Уведомлять заявителя о статусе
          </label>

          <div className="flex flex-wrap items-center justify-end gap-3">
            {intakeNotice && <span className="text-sm font-medium text-blue-700">{intakeNotice}</span>}
            <button type="submit" disabled={intakeSaving} className="btn-primary">
              <PlusIcon className="mr-2 h-4 w-4" />
              {intakeSaving ? 'Создаем…' : 'Создать заявку'}
            </button>
          </div>
        </div>
      </form>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <SummaryCard label="Всего заявок" value={data.requests.total} icon={ClockIcon} tone="blue" />
        <SummaryCard label="В работе" value={data.requests.in_progress} icon={WrenchScrewdriverIcon} tone="indigo" />
        <SummaryCard label="Выполнено" value={data.requests.done} icon={CheckCircleIcon} tone="emerald" />
        <SummaryCard label="Просрочено" value={data.requests.overdue} icon={ExclamationTriangleIcon} tone="red" />
        <SummaryCard label="Жителей" value={data.residents} icon={UserGroupIcon} tone="sky" />
        <SummaryCard label="Подрядчиков" value={data.contractors} icon={WrenchScrewdriverIcon} tone="violet" />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <RequestColumn title="В работе" items={active.filter((item) => !item.overdue)} empty="Активных заявок пока нет" />
        <RequestColumn title="Выполнено" items={completed} empty="Выполненных заявок пока нет" />
        <RequestColumn title="Просроченные" items={overdue} empty="Просроченных заявок нет" danger />
      </div>

      <div className="card">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Автоматическое распределение</h2>
            <p className="mt-1 text-sm text-slate-500">
              Категория + приоритет + дом + смена + загрузка исполнителя + SLA → назначение или очередь диспетчера
            </p>
          </div>
          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">AI assisted</span>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-5">
          {[
            ['Электрика', 'Электрик'],
            ['Сантехника', 'Слесарь'],
            ['Общие вопросы', 'Диспетчер'],
            ['Претензии', 'Директор'],
            ['Пожелания', 'Мастер участка'],
          ].map(([category, assignee]) => (
            <div key={category} className="card-soft">
              <div className="text-sm font-semibold text-slate-800">{category}</div>
              <div className="mt-1 text-xs text-slate-500">Автоназначение</div>
              <div className="mt-3 text-sm font-medium text-blue-700">{assignee}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon, tone }: { label: string; value: number; icon: any; tone: string }) {
  const tones: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    red: 'bg-red-50 text-red-600',
    sky: 'bg-sky-50 text-sky-600',
    violet: 'bg-violet-50 text-violet-600',
  };

  return (
    <div className="card p-4">
      <div className={'mb-3 flex h-10 w-10 items-center justify-center rounded-xl ' + tones[tone]}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="mt-1 text-sm text-slate-500">{label}</div>
    </div>
  );
}

function RequestColumn({ title, items, empty, danger = false }: { title: string; items: any[]; empty: string; danger?: boolean }) {
  return (
    <section className={'rounded-2xl border p-4 ' + (danger ? 'border-red-100 bg-red-50/40' : 'border-slate-200 bg-white')}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900">{title}</h2>
        <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (danger ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600')}>
          {items.length}
        </span>
      </div>

      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white/70 p-6 text-center text-sm text-slate-400">{empty}</div>
        ) : (
          items.slice(0, 6).map((item) => (
            <div key={item.id} className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <span className="text-xs font-semibold text-blue-700">{priorityLabel[item.priority] || item.priority}</span>
                <span className="text-xs text-slate-400">{item.number}</span>
              </div>
              <div className="mt-2 text-sm font-semibold text-slate-900">{item.title}</div>
              <div className="mt-1 line-clamp-2 text-xs text-slate-500">{item.description}</div>
              <div className="mt-3 text-xs font-medium text-slate-600">{statusLabel[item.status] || item.status}</div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
