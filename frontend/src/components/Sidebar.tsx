import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link, useLocation } from 'react-router-dom';
import {
  BuildingOffice2Icon, ChatBubbleLeftRightIcon, ClipboardDocumentListIcon,
  CpuChipIcon, HomeIcon, LinkIcon, RectangleStackIcon,
  UserGroupIcon, UsersIcon, WrenchScrewdriverIcon,
  ChevronLeftIcon, ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  onClose?: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const navigation = [
  { name: 'Главная', href: '/dashboard', icon: HomeIcon },
  { name: 'Заявки', href: '/requests', icon: ClipboardDocumentListIcon },
  { name: 'Диспетчерская', href: '/communications', icon: ChatBubbleLeftRightIcon },
  { name: 'Жители', href: '/residents', icon: UsersIcon },
  { name: 'Дома и помещения', href: '/buildings', icon: BuildingOffice2Icon },
  { name: 'Сотрудники', href: '/users', icon: UserGroupIcon, adminOnly: true },
  { name: 'Подрядчики', href: '/contractors', icon: WrenchScrewdriverIcon },
  { name: 'Каналы связи', href: '/messengers', icon: LinkIcon, adminOnly: true },
  { name: 'Автоматизация', href: '/automation/board', icon: RectangleStackIcon },
  { name: 'ИИ API', href: '/ai', icon: CpuChipIcon, adminOnly: true },
];

export default function Sidebar({ onClose, collapsed = false, onToggleCollapse }: SidebarProps) {
  const location = useLocation();
  const { isAdmin } = useAuth();
  const visibleNavigation = navigation.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside className={(collapsed ? 'w-20' : 'w-64') + ' flex h-full min-h-screen flex-col border-r border-slate-200 bg-white transition-all duration-200'} aria-label="Основная навигация">
      <div className={'flex min-h-16 items-center border-b border-slate-200 ' + (collapsed ? 'justify-center px-2' : 'justify-between px-4')}>
        <Link to="/dashboard" onClick={onClose} className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <BuildingOffice2Icon className="h-6 w-6" />
          </div>
          {!collapsed && <div className="min-w-0"><div className="truncate text-sm font-bold text-slate-900">ЖКХ CRM</div><div className="truncate text-xs text-slate-500">Управление заявками</div></div>}
        </Link>
        {onToggleCollapse && !collapsed && (
          <button onClick={onToggleCollapse} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Свернуть меню">
            <ChevronLeftIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        {collapsed && onToggleCollapse && (
          <button onClick={onToggleCollapse} className="mb-2 flex w-full justify-center rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Развернуть меню">
            <ChevronRightIcon className="h-4 w-4" />
          </button>
        )}
        <ul className="space-y-1">
          {visibleNavigation.map((item) => {
            const active = location.pathname === item.href || (item.href !== '/dashboard' && location.pathname.startsWith(item.href + '/'));
            return (
              <li key={item.href}>
                <Link to={item.href} onClick={onClose} className={'sidebar-link ' + (active ? 'active ' : '') + (collapsed ? 'justify-center px-2' : '')} title={collapsed ? item.name : undefined}>
                  <item.icon className={'h-5 w-5 shrink-0 ' + (collapsed ? '' : 'mr-3')} />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className={'border-t border-slate-200 p-3 text-xs text-slate-400 ' + (collapsed ? 'text-center' : '')}>{collapsed ? 'CRM' : 'ЖКХ CRM · v1.3'}</div>
    </aside>
  );
}
