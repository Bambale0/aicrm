import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  Cog6ToothIcon,
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  WrenchScrewdriverIcon,
  UsersIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon,
  EnvelopeIcon,
  PaperAirplaneIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Главная', href: '/dashboard', icon: HomeIcon },
  { name: 'Клиенты', href: '/customers', icon: UsersIcon },
  { name: 'Заказы', href: '/orders', icon: ClipboardDocumentListIcon },
  { name: 'Задачи', href: '/tasks', icon: CheckCircleIcon },
  { name: 'Email', href: '/email', icon: EnvelopeIcon },
  { name: 'Telegram', href: '/telegram', icon: PaperAirplaneIcon },
  {
    name: 'Настройки ИИ',
    icon: CpuChipIcon,
    submenu: [
      { name: 'Основные настройки', href: '/settings/ai' },
      { name: 'Настройки ИИ Менеджера', href: '/settings/ai-manager' }
    ]
  },
  { name: 'Avito', href: '/settings/avito', icon: ChatBubbleLeftRightIcon },
  { name: 'Автоматизация', href: '/settings/automation', icon: WrenchScrewdriverIcon },
  { name: 'Система', href: '/settings/system', icon: Cog6ToothIcon },
];

export default function Sidebar() {
  const location = useLocation();
  const [expandedMenus, setExpandedMenus] = useState<{ [key: string]: boolean }>({
    'Настройки ИИ': true
  });

  const toggleMenu = (menuName: string) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuName]: !prev[menuName]
    }));
  };

  const isMenuActive = (item: any) => {
    if (item.href) {
      return location.pathname === item.href;
    }
    if (item.submenu) {
      return item.submenu.some((subItem: any) => location.pathname === subItem.href);
    }
    return false;
  };

  return (
    <div className="w-64 bg-white shadow-lg">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900">AI CRM</h1>
        <p className="text-sm text-gray-600 mt-1">Панель управления</p>
      </div>

      <nav className="px-4 pb-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = isMenuActive(item);
            const hasSubmenu = item.submenu && item.submenu.length > 0;

            return (
              <li key={item.name}>
                {hasSubmenu ? (
                  <div>
                    <button
                      onClick={() => toggleMenu(item.name)}
                      className={`sidebar-link w-full text-left ${isActive ? 'active' : ''}`}
                    >
                      <item.icon className="w-5 h-5 mr-3" />
                      {item.name}
                      {expandedMenus[item.name] ? (
                        <ChevronDownIcon className="w-4 h-4 ml-auto" />
                      ) : (
                        <ChevronRightIcon className="w-4 h-4 ml-auto" />
                      )}
                    </button>
                    {expandedMenus[item.name] && (
                      <ul className="ml-8 mt-2 space-y-1">
                        {item.submenu.map((subItem: any) => {
                          const isSubActive = location.pathname === subItem.href;
                          return (
                            <li key={subItem.name}>
                              <Link
                                to={subItem.href}
                                className={`sidebar-link text-sm ${isSubActive ? 'active' : ''}`}
                              >
                                {subItem.name}
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                ) : item.href ? (
                  <Link
                    to={item.href}
                    className={`sidebar-link ${isActive ? 'active' : ''}`}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                ) : null}
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="px-6 py-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Версия 0.1.0
        </div>
      </div>
    </div>
  );
}
