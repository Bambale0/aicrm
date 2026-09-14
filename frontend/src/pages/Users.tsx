import React, { FormEvent, useEffect, useState } from 'react';
import { PencilIcon, PlusIcon, TrashIcon, XMarkIcon } from '@heroicons/react/24/outline';
import api from '../services/api';

interface UserRole {
  value: string;
  label: string;
}

interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  created_at: string;
}

interface UserForm {
  email: string;
  password: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

const emptyForm: UserForm = {
  email: '',
  password: '',
  full_name: '',
  role: '',
  is_active: true,
};

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [modalOpen, setModalOpen] = useState(false);
  const [notice, setNotice] = useState('');

  const load = async () => {
    setLoading(true);
    setNotice('');
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        api.get('/users/'),
        api.get('/users/roles/catalog'),
      ]);
      setUsers(usersResponse.data);
      setRoles(rolesResponse.data);
      if (!form.role && rolesResponse.data.length) {
        setForm((current) => ({ ...current, role: rolesResponse.data[0].value }));
      }
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить сотрудников');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({
      ...emptyForm,
      role: roles[0]?.value || '',
    });
    setModalOpen(true);
  };

  const openEdit = (user: User) => {
    setEditing(user);
    setForm({
      email: user.email,
      password: '',
      full_name: user.full_name || '',
      role: user.role,
      is_active: user.is_active,
    });
    setModalOpen(true);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    const payload: Record<string, any> = {
      email: form.email,
      full_name: form.full_name || null,
      role: form.role,
      is_active: form.is_active,
    };
    if (form.password) payload.password = form.password;

    if (editing) {
      await api.patch('/users/' + editing.id, payload);
      setNotice('Сотрудник обновлён');
    } else {
      if (!form.password) {
        setNotice('Укажите пароль для нового сотрудника');
        return;
      }
      await api.post('/users/', payload);
      setNotice('Сотрудник создан');
    }

    setModalOpen(false);
    await load();
  };

  const remove = async (user: User) => {
    if (!window.confirm('Удалить сотрудника ' + user.email + '?')) return;
    try {
      await api.delete('/users/' + user.id);
      setNotice('Сотрудник удалён');
      await load();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось удалить сотрудника');
    }
  };

  const roleLabel = (value: string) => roles.find((role) => role.value === value)?.label || value;

  if (loading) {
    return <div className="py-20 text-center text-sm text-slate-400">Загрузка сотрудников…</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Сотрудники</h1>
          <p className="page-subtitle">Учетные записи и роли сотрудников управляющей компании</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <PlusIcon className="mr-2 h-4 w-4" />
          Добавить сотрудника
        </button>
      </div>

      {notice && <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">{notice}</div>}

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">Сотрудник</th>
                <th className="px-5 py-3">Роль</th>
                <th className="px-5 py-3">Статус</th>
                <th className="px-5 py-3">Создан</th>
                <th className="px-5 py-3 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.length === 0 && (
                <tr><td colSpan={5} className="px-5 py-12 text-center text-slate-400">Сотрудников пока нет</td></tr>
              )}
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50">
                  <td className="px-5 py-4">
                    <div className="font-medium text-slate-900">{user.full_name || 'Без имени'}</div>
                    <div className="mt-1 text-xs text-slate-500">{user.email}</div>
                  </td>
                  <td className="px-5 py-4 text-slate-600">{user.is_superuser ? 'Суперадминистратор' : roleLabel(user.role)}</td>
                  <td className="px-5 py-4">
                    <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (user.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600')}>
                      {user.is_active ? 'Активен' : 'Отключён'}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-500">{new Date(user.created_at).toLocaleDateString('ru-RU')}</td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => openEdit(user)} className="btn-secondary px-3 py-2"><PencilIcon className="h-4 w-4" /></button>
                      <button onClick={() => remove(user)} className="btn-danger px-3 py-2"><TrashIcon className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4 backdrop-blur-sm">
          <form onSubmit={save} className="card w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">{editing ? 'Редактировать сотрудника' : 'Новый сотрудник'}</h2>
              <button type="button" onClick={() => setModalOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100">
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">ФИО</label>
              <input className="input-field" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
              <input className="input-field" type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Роль</label>
              <select className="input-field" required value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
                <option value="">Выберите роль</option>
                {roles.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Пароль</label>
              <input className="input-field" type="password" required={!editing} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder={editing ? 'Оставьте пустым, чтобы не менять' : ''} />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
              Активен
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">Отмена</button>
              <button type="submit" className="btn-primary">{editing ? 'Сохранить' : 'Создать'}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
