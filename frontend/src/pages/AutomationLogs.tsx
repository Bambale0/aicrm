import React, { useState, useEffect, useCallback } from 'react';
import { automationApi } from '../services/automationApi';
import {
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon,
  ArrowPathIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';

interface ExecutionLog {
  id: string;
  entity_type: string;
  entity_id: number;
  robot_id?: number;
  robot_name?: string;
  stage_id?: number;
  stage_name?: string;
  action_type?: string;
  status: 'success' | 'error' | 'running' | 'pending';
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  metadata?: any;
}

interface ExecutionStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_duration_ms: number;
  success_rate: number;
}

export default function AutomationLogs() {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<ExecutionLog | null>(null);
  const [filters, setFilters] = useState({
    status: '',
    entity_type: '',
    robot_id: '',
    start_date: '',
    end_date: '',
    search: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  const loadLogs = useCallback(async () => {
    try {
      const params: any = {};
      if (filters.status) params.status = filters.status;
      if (filters.entity_type) params.entity_type = filters.entity_type;
      if (filters.robot_id) params.robot_id = filters.robot_id;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;

      const data = await automationApi.getExecutionStats(params);
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to load execution logs:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const loadStats = useCallback(async () => {
    try {
      const data = await automationApi.getExecutionStats({
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        entity_type: filters.entity_type || undefined
      });
      setStats(data.stats);
    } catch (error) {
      console.error('Failed to load execution stats:', error);
    }
  }, [filters]);

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [loadLogs, loadStats]);

  const filteredLogs = logs.filter(log =>
    !filters.search ||
    log.robot_name?.toLowerCase().includes(filters.search.toLowerCase()) ||
    log.stage_name?.toLowerCase().includes(filters.search.toLowerCase()) ||
    log.action_type?.toLowerCase().includes(filters.search.toLowerCase()) ||
    log.error_message?.toLowerCase().includes(filters.search.toLowerCase())
  );

  const handleRefresh = () => {
    setLoading(true);
    loadLogs();
    loadStats();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-600" />;
      case 'running':
        return <ArrowPathIcon className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Логи автоматизации</h1>
          <p className="text-gray-600 mt-2">Мониторинг и анализ выполнений автоматизации</p>
        </div>
        <button
          onClick={handleRefresh}
          className="btn-secondary flex items-center"
        >
          <ArrowPathIcon className="w-5 h-5 mr-2" />
          Обновить
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center">
              <ChartBarIcon className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Всего выполнений</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_executions}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <CheckCircleIcon className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Успешных</p>
                <p className="text-2xl font-bold text-green-600">{stats.successful_executions}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <XCircleIcon className="w-8 h-8 text-red-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Ошибок</p>
                <p className="text-2xl font-bold text-red-600">{stats.failed_executions}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Успешность</p>
                <p className="text-2xl font-bold text-gray-900">{(stats.success_rate * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Фильтры</h3>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary flex items-center"
          >
            <FunnelIcon className="w-5 h-5 mr-2" />
            {showFilters ? 'Скрыть фильтры' : 'Показать фильтры'}
          </button>
        </div>

        <div className="flex space-x-4 mb-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Поиск по роботу, стадии, действию или ошибке..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="input-field"
            />
          </div>
          <button
            onClick={() => setFilters({ ...filters, search: '' })}
            className="btn-secondary"
          >
            Очистить
          </button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="input-field"
              >
                <option value="">Все статусы</option>
                <option value="success">Успешно</option>
                <option value="error">Ошибка</option>
                <option value="running">Выполняется</option>
                <option value="pending">Ожидает</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Тип сущности</label>
              <select
                value={filters.entity_type}
                onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
                className="input-field"
              >
                <option value="">Все типы</option>
                <option value="order">Заказ</option>
                <option value="customer">Клиент</option>
                <option value="task">Задача</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ID робота</label>
              <input
                type="number"
                value={filters.robot_id}
                onChange={(e) => setFilters({ ...filters, robot_id: e.target.value })}
                className="input-field"
                placeholder="ID робота"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Дата начала</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Дата окончания</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={() => setFilters({
                  status: '',
                  entity_type: '',
                  robot_id: '',
                  start_date: '',
                  end_date: '',
                  search: ''
                })}
                className="btn-secondary w-full"
              >
                Сбросить все
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Logs List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Логи выполнений ({filteredLogs.length})
          </h3>
        </div>

        {filteredLogs.length > 0 ? (
          <div className="space-y-2">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                onClick={() => setSelectedLog(log)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(log.status)}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          {log.robot_name || `Робот ${log.robot_id}`}
                        </span>
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(log.status)}`}>
                          {log.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {log.stage_name && <span>Стадия: {log.stage_name} • </span>}
                        {log.action_type && <span>Действие: {log.action_type} • </span>}
                        {log.entity_type} #{log.entity_id}
                      </div>
                    </div>
                  </div>

                  <div className="text-right text-sm text-gray-500">
                    <div>{formatDuration(log.duration_ms)}</div>
                    <div>{new Date(log.started_at).toLocaleString('ru-RU')}</div>
                  </div>
                </div>

                {log.error_message && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
                      {log.error_message}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Логи выполнений не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              Попробуйте изменить фильтры или проверить настройки автоматизации
            </p>
          </div>
        )}
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Детали выполнения</h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">ID выполнения</label>
                  <p className="text-gray-900 font-mono">{selectedLog.id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <div className="flex items-center mt-1">
                    {getStatusIcon(selectedLog.status)}
                    <span className={`ml-2 inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(selectedLog.status)}`}>
                      {selectedLog.status}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Тип сущности</label>
                  <p className="text-gray-900">{selectedLog.entity_type} #{selectedLog.entity_id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Робот</label>
                  <p className="text-gray-900">{selectedLog.robot_name || `ID: ${selectedLog.robot_id}`}</p>
                </div>
              </div>

              {selectedLog.stage_name && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Стадия</label>
                  <p className="text-gray-900">{selectedLog.stage_name}</p>
                </div>
              )}

              {selectedLog.action_type && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Тип действия</label>
                  <p className="text-gray-900">{selectedLog.action_type}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Начало выполнения</label>
                  <p className="text-gray-900">{new Date(selectedLog.started_at).toLocaleString('ru-RU')}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Завершение</label>
                  <p className="text-gray-900">
                    {selectedLog.completed_at ? new Date(selectedLog.completed_at).toLocaleString('ru-RU') : 'Не завершено'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Длительность</label>
                  <p className="text-gray-900">{formatDuration(selectedLog.duration_ms)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Средняя длительность</label>
                  <p className="text-gray-900">{stats ? formatDuration(stats.average_duration_ms) : 'N/A'}</p>
                </div>
              </div>

              {selectedLog.error_message && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Сообщение об ошибке</label>
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 font-mono">
                    {selectedLog.error_message}
                  </div>
                </div>
              )}

              {selectedLog.metadata && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Метаданные</label>
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded text-sm font-mono overflow-x-auto">
                    <pre>{JSON.stringify(selectedLog.metadata, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => setSelectedLog(null)}
                className="btn-primary"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
