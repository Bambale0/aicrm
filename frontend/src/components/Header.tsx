import React from 'react';
import { BellIcon, UserCircleIcon, ArrowRightOnRectangleIcon, Bars3Icon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps {
  onMenuClick?: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="navbar">
      <div className="px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Mobile menu button */}
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/20 transition-all duration-300"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>

            <img
              src="/лого.png"
              alt="AI CRM Logo"
              className="w-10 h-10 sm:w-12 sm:h-12 drop-shadow-lg"
            />
            <div className="hidden sm:block">
              <h2 className="text-lg sm:text-xl font-semibold text-gradient">Панель управления</h2>
              <p className="text-xs sm:text-sm text-gray-400">Управление настройками AI CRM системы</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-4">
            <button className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/20 transition-all duration-300">
              <BellIcon className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2">
              <UserCircleIcon className="w-8 h-8 text-gray-400" />
              <span className="text-sm font-medium text-van-gogh-chrome-green">
                {user?.username || user?.email || 'Пользователь'}
              </span>
            </div>

            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-van-gogh-vermilion rounded-lg hover:bg-van-gogh-vermilion/20 transition-all duration-300"
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
