import React, { useState, useEffect, useCallback } from 'react';
import {
  Cog6ToothIcon,
  BoltIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  WrenchScrewdriverIcon,
  PuzzlePieceIcon,
  CpuChipIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

interface Robot {
  id: string;
  name: string;
  description: string;
  entity_type: string;
  stage_id: string;
  is_active: boolean;
  actions_count: number;
  last_execution?: string;
  success_rate: number;
}

interface Trigger {
  id: string;
  name: string;
  event_type: string;
  entity_type: string;
  is_active: boolean;
  conditions_count: number;
  executions_count: number;
  last_triggered?: string;
}

interface WorkflowStats {
  active_robots: number;
  active_triggers: number;
  total_executions: number;
  success_rate: number;
  automation_coverage: number;
}

interface PluginManagerProps {
  className?: string;
}

type TabType = 'overview' | 'robots' | 'triggers' | 'workflow' | 'plugins';

const PluginManager: React.FC<PluginManagerProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [robots, setRobots] = useState<Robot[]>([]);
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [stats, setStats] = useState<WorkflowStats>({
    active_robots: 0,
    active_triggers: 0,
    total_executions: 0,
    success_rate: 0,
    automation_coverage: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // Загрузка данных
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const [robotsRes, triggersRes] = await Promise.all([
        apiService.getAutomationRobots(),
        apiService.getAutomationTriggers(),
      ]);

      setRobots(robotsRes || []);
      setTriggers(triggersRes || []);

      // Расчет статистики
      const activeRobots = robotsRes?.filter((r: Robot) => r.is_active).length || 0;
      const activeTriggers = triggersRes?.filter((t: Trigger) => t.is_active).length || 0;

      setStats({
        active_robots: activeRobots,
        active_triggers: activeTriggers,
        total_executions: 0, // TODO: получить из analytics API
        success_rate: 95.2, // TODO: рассчитать на основе данных
        automation_coverage: Math.round(((activeRobots + activeTriggers) / 10) * 100), // TODO: рассчитать правильно
      });

    } catch (err: any) {
      console.error('Error loading automation data:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных автоматизации');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const tabs = [
    {
      id: 'overview' as TabType,
      name: 'Обзор',
      icon: ChartBarIcon,
      description: 'Статистика и дашборд автоматизации',
    },
    {
      id: 'robots' as TabType,
      name: 'Роботы',
      icon: CpuChipIcon,
      description: 'Управление исполнителями автоматизации',
    },
    {
      id: 'triggers' as TabType,
      name: 'Триггеры',
      icon: BoltIcon,
      description: 'Управление триггерами событий',
    },
    {
      id: 'workflow' as TabType,
      name: 'Workflow',
      icon: MagnifyingGlassIcon,
      description: 'Визуализатор процессов автоматизации',
    },
    {
      id: 'plugins' as TabType,
      name: 'Плагины',
      icon: PuzzlePieceIcon,
      description: 'Магазин и управление плагинами',
    },
  ];

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    colorClass: string;
  }> = ({ title, value, description, icon: Icon, colorClass }) => (
    <div className={`${colorClass} rounded-lg p-6 shadow-sm`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
        <div className="bg-white bg-opacity-20 rounded-lg p-3">
          <Icon className="w-6 h-6 text-current" />
        </div>
      </div>
    </div>
  );

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Активные роботы"
          value={stats.active_robots}
          description="Исполнителей задач"
          icon={CpuChipIcon}
          colorClass="bg-blue-50 border border-blue-200"
        />
        <StatCard
          title="Активные триггеры"
          value={stats.active_triggers}
          description="Отслеживают события"
          icon={BoltIcon}
          colorClass="bg-green-50 border border-green-200"
        />
        <StatCard
          title="Покрытие автоматизацией"
          value={`${stats.automation_coverage}%`}
          description="Бизнес-процессов"
          icon={ChartBarIcon}
          colorClass="bg-purple-50 border border-purple-200"
        />
      </div>

      {/* Быстрые действия */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Быстрые действия</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => setActiveTab('robots')}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <CpuChipIcon className="w-5 h-5 mr-2" />
              Создать робота
            </button>
            <button
              onClick={() => setActiveTab('triggers')}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <BoltIcon className="w-5 h-5 mr-2" />
              Настроить триггер
            </button>
            <button
              onClick={() => setActiveTab('workflow')}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
              Просмотр workflow
            </button>
            <button
              onClick={() => setActiveTab('plugins')}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <PuzzlePieceIcon className="w-5 h-5 mr-2" />
              Установить плагин
            </button>
          </div>
        </div>
      </div>

      {/* Недавняя активность */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Недавняя активность</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">Загрузка активности...</p>
            </div>
          ) : (
            <div className="p-6">
              <p className="text-sm text-gray-600">История активности пока недоступна</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderRobotsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Роботы автоматизации</h2>
          <p className="text-gray-600">Исполнители бизнес-процессов</p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <CpuChipIcon className="w-4 h-4 mr-2" />
          Создать робота
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {robots.map((robot) => (
          <div key={robot.id} className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${robot.is_active ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                    <CpuChipIcon className="w-6 h-6" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">{robot.name}</h3>
                    <p className="text-sm text-gray-600">{robot.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {robot.is_active ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Активен
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Неактивен
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Действий</p>
                  <p className="text-lg font-semibold text-gray-900">{robot.actions_count}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Успешность</p>
                  <p className="text-lg font-semibold text-gray-900">{robot.success_rate}%</p>
                </div>
              </div>

              {robot.last_execution && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Последнее выполнение: {new Date(robot.last_execution).toLocaleString('ru-RU')}
                  </p>
                </div>
              )}

              <div className="mt-4 flex justify-end space-x-2">
                <button className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                  <Cog6ToothIcon className="w-4 h-4 mr-1" />
                  Настроить
                </button>
                <button className={`inline-flex items-center px-3 py-1 border rounded-md text-sm font-medium ${
                  robot.is_active
                    ? 'border-red-300 text-red-700 bg-white hover:bg-red-50'
                    : 'border-green-300 text-green-700 bg-white hover:bg-green-50'
                }`}>
                  {robot.is_active ? <PauseIcon className="w-4 h-4 mr-1" /> : <PlayIcon className="w-4 h-4 mr-1" />}
                  {robot.is_active ? 'Остановить' : 'Запустить'}
                </button>
              </div>
            </div>
          </div>
        ))}

        {robots.length === 0 && !loading && (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="text-center">
              <CpuChipIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет роботов</h3>
              <p className="text-gray-600 mb-4">Создайте первого робота для автоматизации процессов</p>
              <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                <CpuChipIcon className="w-4 h-4 mr-2" />
                Создать робота
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderTriggersTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Триггеры автоматизации</h2>
          <p className="text-gray-600">События, запускающие автоматизацию</p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <BoltIcon className="w-4 h-4 mr-2" />
          Создать триггер
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {triggers.map((trigger) => (
          <div key={trigger.id} className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${trigger.is_active ? 'bg-yellow-100 text-yellow-600' : 'bg-gray-100 text-gray-400'}`}>
                    <BoltIcon className="w-6 h-6" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">{trigger.name}</h3>
                    <p className="text-sm text-gray-600">{trigger.event_type} → {trigger.entity_type}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {trigger.is_active ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Активен
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Неактивен
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Условий</p>
                  <p className="text-lg font-semibold text-gray-900">{trigger.conditions_count}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Выполнений</p>
                  <p className="text-lg font-semibold text-gray-900">{trigger.executions_count}</p>
                </div>
              </div>

              {trigger.last_triggered && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Последний срабатывание: {new Date(trigger.last_triggered).toLocaleString('ru-RU')}
                  </p>
                </div>
              )}

              <div className="mt-4 flex justify-end space-x-2">
                <button className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                  <Cog6ToothIcon className="w-4 h-4 mr-1" />
                  Настроить
                </button>
                <button className={`inline-flex items-center px-3 py-1 border rounded-md text-sm font-medium ${
                  trigger.is_active
                    ? 'border-red-300 text-red-700 bg-white hover:bg-red-50'
                    : 'border-green-300 text-green-700 bg-white hover:bg-green-50'
                }`}>
                  {trigger.is_active ? <PauseIcon className="w-4 h-4 mr-1" /> : <PlayIcon className="w-4 h-4 mr-1" />}
                  {trigger.is_active ? 'Отключить' : 'Включить'}
                </button>
              </div>
            </div>
          </div>
        ))}

        {triggers.length === 0 && !loading && (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="text-center">
              <BoltIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет триггеров</h3>
              <p className="text-gray-600 mb-4">Создайте первый триггер для запуска автоматизации</p>
              <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                <BoltIcon className="w-4 h-4 mr-2" />
                Создать триггер
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderWorkflowTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Workflow визуализатор</h2>
          <p className="text-gray-600">Графическое представление процессов автоматизации</p>
        </div>
        <div className="flex space-x-3">
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Обновить
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
            <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
            Новый workflow
          </button>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <WrenchScrewdriverIcon className="h-5 w-5 text-yellow-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Workflow визуализатор в разработке
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>Эта функция находится в активной разработке. Планируется интеграция с React Flow или Vis.js для визуализации процессов автоматизации.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder для workflow */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-center py-24">
          <div className="text-center">
            <ServerIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">Workflow в разработке</h3>
            <p className="text-gray-600 max-w-md">
              Здесь будет отображаться интерактивный граф процессов автоматизации,
              показывающий связи между триггерами, стадиями и роботами-исполнителями.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPluginsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Магазин плагинов</h2>
          <p className="text-gray-600">Расширения функциональности автоматизации</p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <PuzzlePieceIcon className="w-4 h-4 mr-2" />
          Установить плагин
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <PuzzlePieceIcon className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Система плагинов в разработке
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>Планируется создание marketplace плагинов с возможностью установки дополнительных модулей для:</p>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Интеграции с внешними сервисами (CRM, ERP, Email)</li>
                <li>Новых типов триггеров и действий</li>
                <li>AI-powered решений и аналитики</li>
                <li>Специализированных workflow шаблонов</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Категории плагинов (placeholder) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {['Интеграции', 'AI & ML', 'Business Logic', 'UI Extensions', 'Reporting', 'Communication'].map((category) => (
          <div key={category} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:border-gray-300">
            <div className="p-6">
              <div className="flex items-center">
                <PuzzlePieceIcon className="w-8 h-8 text-gray-400" />
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-gray-900">{category}</h3>
                  <p className="text-sm text-gray-600">Скоро будут доступны плагины этой категории</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading && robots.length === 0 && triggers.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ChartBarIcon className="h-5 w-5 text-red-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Ошибка загрузки</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Плагин менеджер автоматизации</h1>
        <p className="text-gray-600 mt-2">
          Централизованное управление роботами, триггерами и плагинами для полной автоматизации бизнес-процессов
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.name}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-8">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'robots' && renderRobotsTab()}
        {activeTab === 'triggers' && renderTriggersTab()}
        {activeTab === 'workflow' && renderWorkflowTab()}
        {activeTab === 'plugins' && renderPluginsTab()}
      </div>
    </div>
  );
};

export default PluginManager;
