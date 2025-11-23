import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, FunnelIcon, InformationCircleIcon, MagnifyingGlassIcon, XCircleIcon } from '@heroicons/react/24/outline';
import React, { useCallback, useEffect, useState } from 'react';
import { apiService } from '../services/api';

interface AutomationLog {
  id: number;
  timestamp: string;
  level: string;
  message: string;
  process_id?: number;
  stage_id?: number;
  details?: any;
}

const AutomationLogs: React.FC = () => {
  const [logs, setLogs] = useState<AutomationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedLog, setSelectedLog] = useState<AutomationLog | null>(null);

  const logsPerPage = 50;

  const loadLogs = useCallback(async () => {
    try {
      const params: any = {
        skip: (currentPage - 1) * logsPerPage,
        limit: logsPerPage
      };

      if (levelFilter) params.level = levelFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await apiService.getAutomationLogs(params);
      setLogs(response);
      setTotalPages(Math.ceil(response.length / logsPerPage));
    } catch (error) {
      console.error('Error loading logs:', error);
      alert('Ошибка при загрузке логов');
    } finally {
      setLoading(false);
    }
  }, [currentPage, levelFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const handleSearch = () => {
    setCurrentPage(1);
    loadLogs();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setLevelFilter('');
    setDateFrom('');
    setDateTo('');
    setCurrentPage(1);
    loadLogs();
  };

  const filteredLogs = logs.filter(log =>
    log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (log.details && JSON.stringify(log.details).toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'info':
      default:
        return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
    }
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'info':
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDetails = (details: any) => {
    if (!details) return null;
    try {
      return JSON.stringify(details, null, 2);
    } catch {
      return String(details);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Логи автоматизации</h1>
          <p className="text-gray-600">Мониторинг выполнения автоматизаций и отладка процессов</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-64">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Поиск в сообщениях
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Поиск по тексту логов..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" />
            </div>
          </div>

          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Уровень
            </label>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все уровни</option>
              <option value="error">Ошибка</option>
              <option value="warning">Предупреждение</option>
              <option value="success">Успех</option>
              <option value="info">Информация</option>
            </select>
          </div>

          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата от
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата до
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSearch}
              className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 flex items-center"
            >
              <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
              Поиск
            </button>
            <button
              onClick={clearFilters}
              className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 flex items-center"
            >
              <FunnelIcon className="w-4 h-4 mr-2" />
              Сброс
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Записи логов</h3>
          <p className="text-sm text-gray-600 mt-1">
            Показано {filteredLogs.length} записей
          </p>
        </div>

        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              {logs.length === 0 ? 'Логи автоматизации не найдены' : 'По вашему запросу ничего не найдено'}
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedLog(log)}
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    {getLevelIcon(log.level)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelBadgeColor(log.level)}`}>
                        {log.level.toUpperCase()}
                      </span>
                      <div className="flex items-center text-sm text-gray-500">
                        <ClockIcon className="w-4 h-4 mr-1" />
                        {formatTimestamp(log.timestamp)}
                      </div>
                      {log.process_id && (
                        <span className="text-xs text-gray-500">
                          Процесс: {log.process_id}
                        </span>
                      )}
                      {log.stage_id && (
                        <span className="text-xs text-gray-500">
                          Стадия: {log.stage_id}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-900 mb-2">{log.message}</p>

                    {log.details && (
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border overflow-hidden">
                        <div className="truncate">
                          {formatDetails(log.details)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Страница {currentPage} из {totalPages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Предыдущая
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Следующая
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Детали лога</h3>
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
                    <label className="block text-sm font-medium text-gray-700">Уровень</label>
                    <div className="flex items-center mt-1">
                      {getLevelIcon(selectedLog.level)}
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelBadgeColor(selectedLog.level)}`}>
                        {selectedLog.level.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Время</label>
                    <p className="text-sm text-gray-900 mt-1">{formatTimestamp(selectedLog.timestamp)}</p>
                  </div>
                </div>

                {selectedLog.process_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ID процесса</label>
                    <p className="text-sm text-gray-900 mt-1">{selectedLog.process_id}</p>
                  </div>
                )}

                {selectedLog.stage_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ID стадии</label>
                    <p className="text-sm text-gray-900 mt-1">{selectedLog.stage_id}</p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700">Сообщение</label>
                  <p className="text-sm text-gray-900 mt-1 bg-gray-50 p-3 rounded border">{selectedLog.message}</p>
                </div>

                {selectedLog.details && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Детали</label>
                    <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto whitespace-pre-wrap">
                      {formatDetails(selectedLog.details)}
                    </pre>
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setSelectedLog(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationLogs;
