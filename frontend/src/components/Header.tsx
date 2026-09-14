import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  BellIcon,
  BuildingOffice2Icon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps { onMenuClick?: () => void; }

export default function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="navbar sticky top-0 z-20">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button onClick={onMenuClick} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" aria-label="Открыть меню">
            <Bars3Icon className="h-6 w-6" />
          </button>
          <div className="hidden h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white sm:flex">
            <BuildingOffice2Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold text-slate-900 sm:text-base">CRM управляющей компании ЖКХ</h2>
            <p className="hidden text-xs text-slate-500 sm:block">Заявки, жители, исполнители и подрядчики</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button className="relative rounded-xl p-2.5 text-slate-500 hover:bg-slate-100" aria-label="Уведомления">
            <BellIcon className="h-5 w-5" />
          </button>
          <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 sm:flex">
            <UserCircleIcon className="h-6 w-6 text-slate-400" />
            <span className="max-w-44 truncate text-sm font-medium text-slate-700">{user?.full_name || user?.email || 'Сотрудник'}</span>
          </div>
          {user ? (
            <button onClick={logout} className="rounded-xl p-2.5 text-slate-500 hover:bg-red-50 hover:text-red-600" title="Выйти" aria-label="Выйти">
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
            </button>
          ) : (
            <Link to="/login" className="rounded-xl px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50">
              Админ
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
