import React from 'react';
import { BellIcon, UserCircleIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext.tsx';

export default function Header() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Панель управления</h2>
            <p className="text-sm text-gray-600">Управление настройками AI CRM системы</p>
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <BellIcon className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2">
              <UserCircleIcon className="w-8 h-8 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                {user?.username || user?.email || 'Пользователь'}
              </span>
            </div>

            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Выйти"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
