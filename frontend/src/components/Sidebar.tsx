import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeIcon,
  Cog6ToothIcon,
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  WrenchScrewdriverIcon,
  UsersIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon,
  PaperAirplaneIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ShieldCheckIcon,
  Squares2X2Icon,
  BoltIcon,
  DocumentTextIcon,
  PuzzlePieceIcon,
  ArrowPathIcon,
  EnvelopeIcon,
  ShoppingBagIcon,

} from '@heroicons/react/24/outline';

interface SidebarProps {
  onClose?: () => void;
}

const navigation = [
  { name: 'Главная', href: '/dashboard', icon: HomeIcon },
  { name: 'Клиенты', href: '/customers', icon: UsersIcon },
  { name: 'Заказы', href: '/orders', icon: ClipboardDocumentListIcon },
  { name: 'Задачи', href: '/tasks', icon: CheckCircleIcon },
  { name: 'Пользователи', href: '/users', icon: ShieldCheckIcon },

  {
    name: 'Коммуникации',
    icon: ChatBubbleLeftRightIcon,
    submenu: [
      { name: 'История', href: '/communications', icon: DocumentTextIcon },
      { name: 'Avito', href: '/avito', icon: ShoppingBagIcon },
      { name: 'Telegram', href: '/telegram', icon: PaperAirplaneIcon },
      { name: 'Email', href: '/email/management', icon: EnvelopeIcon },
    ]
  },

  {
    name: 'Автоматизация',
    icon: ArrowPathIcon,
    submenu: [
      { name: 'Доска', href: '/automation/board', icon: PuzzlePieceIcon },
      { name: 'Стадии', href: '/stages', icon: Squares2X2Icon },
      { name: 'Триггеры', href: '/triggers', icon: BoltIcon },
      { name: 'Логи', href: '/automation/logs', icon: DocumentTextIcon },
    ]
  },

  {
    name: 'Настройки',
    icon: Cog6ToothIcon,
    submenu: [
      { name: 'ИИ', href: '/settings/ai', icon: CpuChipIcon },
      { name: 'ИИ Менеджер', href: '/settings/ai-manager', icon: CpuChipIcon },
      { name: 'Статистика ИИ', href: '/ai/usage', icon: CpuChipIcon },
      { name: 'Avito', href: '/settings/avito', icon: ChatBubbleLeftRightIcon },
      { name: 'Telegram', href: '/settings/telegram', icon: PaperAirplaneIcon },
      { name: 'Email', href: '/settings/email', icon: EnvelopeIcon },
      { name: 'Автоматизация', href: '/settings/automation', icon: WrenchScrewdriverIcon },
      { name: 'Система', href: '/settings/system', icon: Cog6ToothIcon },
    ]
  },
];

export default function Sidebar({ onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [expandedMenus, setExpandedMenus] = useState<{ [key: string]: boolean }>({
    'Коммуникации': false,
    'Автоматизация': false,
    'Настройки': false
  });

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + key shortcuts
      if ((event.metaKey || event.ctrlKey) && !event.shiftKey && !event.altKey) {
        const shortcuts: { [key: string]: string } = {
          'd': '/dashboard',
          'c': '/customers',
          'o': '/orders',
          't': '/tasks'
        };

        const path = shortcuts[event.key.toLowerCase()];
        if (path) {
          event.preventDefault();
          navigate(path);
          onClose?.(); // Close mobile sidebar
        }
      }

      // Escape to close mobile sidebar
      if (event.key === 'Escape' && onClose) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate, onClose]);

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
      return item.submenu.some((subItem: any) => {
        if (subItem.href) {
          return location.pathname === subItem.href;
        }
        if (subItem.submenu) {
          return subItem.submenu.some((nestedItem: any) => location.pathname === nestedItem.href);
        }
        return false;
      });
    }
    return false;
  };

  const renderMenuItem = (item: any, level: number = 0) => {
    const isActive = isMenuActive(item);
    const hasSubmenu = item.submenu && item.submenu.length > 0;
    const marginLeft = level * 32; // 8 * level * 4px

    return (
      <li key={item.name}>
        {hasSubmenu ? (
          <div>
            <button
              onClick={() => toggleMenu(item.name)}
              className={`sidebar-link w-full text-left ${isActive ? 'active' : ''}`}
              style={{ marginLeft: `${marginLeft}px` }}
              aria-expanded={expandedMenus[item.name]}
              aria-haspopup="true"
              aria-controls={`submenu-${item.name.replace(/\s+/g, '-').toLowerCase()}`}
              role="menuitem"
              aria-label={`${item.name}, ${expandedMenus[item.name] ? 'свернуто' : 'развернуто'}`}
            >
              {item.icon && <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />}
              {item.name}
              {item.shortcut && (
                <span className="ml-2 text-xs text-gray-500" aria-hidden="true">
                  {item.shortcut}
                </span>
              )}
              {expandedMenus[item.name] ? (
                <ChevronDownIcon className="w-4 h-4 ml-auto" aria-hidden="true" />
              ) : (
                <ChevronRightIcon className="w-4 h-4 ml-auto" aria-hidden="true" />
              )}
            </button>
            {expandedMenus[item.name] && (
              <ul
                className="mt-2 space-y-1"
                role="menu"
                id={`submenu-${item.name.replace(/\s+/g, '-').toLowerCase()}`}
                aria-label={`Подменю ${item.name}`}
              >
                {item.submenu.map((subItem: any) => renderMenuItem(subItem, level + 1))}
              </ul>
            )}
          </div>
        ) : item.href ? (
          <Link
            to={item.href}
            className={`sidebar-link ${isActive ? 'active' : ''}`}
            style={{ marginLeft: `${marginLeft}px` }}
            role="menuitem"
            aria-current={isActive ? 'page' : undefined}
            aria-label={`${item.name}${item.shortcut ? ` (${item.shortcut})` : ''}`}
          >
            {item.icon && <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />}
            {item.name}
            {item.shortcut && (
              <span className="ml-2 text-xs text-gray-500" aria-hidden="true">
                {item.shortcut}
              </span>
            )}
          </Link>
        ) : null}
      </li>
    );
  };

  return (
    <div
      className="w-64 min-w-64 bg-gray-900/95 backdrop-blur-lg shadow-2xl border-r border-gray-700/50 relative overflow-hidden"
      role="navigation"
      aria-label="Основная навигация"
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-transparent to-cyan-900/20"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-purple-600/5 to-cyan-600/5"></div>

      <div className="relative z-10">
        <header className="p-6 border-b border-gray-700/30">
          <h1 className="text-2xl font-bold text-gradient bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-cyan-400">
            AI CRM
          </h1>
          <p className="text-sm text-gray-400 mt-1">Панель управления</p>
        </header>

        <nav className="px-4 py-6" aria-label="Меню навигации">
          <ul className="space-y-1" role="menubar">
            {navigation.map((item) => renderMenuItem(item))}
          </ul>
        </nav>

        <footer className="px-6 py-4 border-t border-gray-700/30 mt-auto">
          <div className="text-xs text-gray-500">
            Версия 0.1.0
          </div>
        </footer>
      </div>
    </div>
  );
}
