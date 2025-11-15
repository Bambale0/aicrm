import React, { useState, useEffect } from 'react';
import { automationApi, Process, Stage, Trigger, Robot } from '../services/automationApi.ts';
import WorkflowDesigner from '../components/automation/WorkflowDesigner.tsx';
import {
  PlusIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  PlayIcon,
  PauseIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

export default function AutomationSettings() {
  const [processes, setProcesses] = useState<Process[]>([]);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [showDesigner, setShowDesigner] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProcesses();
  }, []);

  const loadProcesses = async () => {
    try {
      const processesData = await automationApi.getProcesses();
      setProcesses(processesData);
    } catch (error) {
      console.error('Failed to load processes:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewProcess = () => {
    setSelectedProcess(null);
    setShowDesigner(true);
  };

  const editProcess = (process: Process) => {
    setSelectedProcess(process);
    setShowDesigner(true);
  };

  const deleteProcess = async (processId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот процесс?')) return;

    try {
      await automationApi.deleteProcess(processId);
      setProcesses(processes.filter(p => p.id !== processId));
    } catch (error) {
      console.error('Failed to delete process:', error);
      alert('Ошибка при удалении процесса');
    }
  };

  const toggleProcess = async (process: Process) => {
    try {
      await automationApi.updateProcess(process.id, { is_active: !process.is_active });
      setProcesses(processes.map(p =>
        p.id === process.id ? { ...p, is_active: !p.is_active } : p
      ));
    } catch (error) {
      console.error('Failed to toggle process:', error);
      alert('Ошибка при изменении статуса процесса');
    }
  };

  const handleSaveWorkflow = async (workflow: { process: Process; stages: Stage[]; triggers: Trigger[]; robots: Robot[] }) => {
    try {
      // Save or update process
      if (selectedProcess) {
        await automationApi.updateProcess(selectedProcess.id, workflow.process);
      } else {
        await automationApi.createProcess(workflow.process);
      }

      // Reload processes to get updated data
      await loadProcesses();

      setShowDesigner(false);
      alert('Процесс успешно сохранен!');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Ошибка при сохранении процесса');
    }
  };

  const loadAnalytics = async () => {
    try {
      const [executions, robots, actions, errors, processes, hourly] = await Promise.all([
        automationApi.getExecutionStats(),
        automationApi.getRobotPerformance(),
        automationApi.getActionTypeStats(),
        automationApi.getErrorAnalysis(),
        automationApi.getProcessEfficiency(),
        automationApi.getHourlyDistribution()
      ]);

      setAnalytics({
        executions,
        robots,
        actions,
        errors,
        processes,
        hourly
      });
      setShowAnalytics(true);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      alert('Ошибка при загрузке аналитики');
    }
  };

  const getEntityTypeLabel = (entityType: string) => {
    switch (entityType) {
      case 'order': return 'Заказы';
      case 'customer': return 'Клиенты';
      case 'task': return 'Задачи';
      case 'production_step': return 'Производство';
      case 'communication': return 'Коммуникации';
      default: return entityType;
    }
  };

  if (showDesigner) {
    return (
      <WorkflowDesigner
        processId={selectedProcess?.id}
        onSave={handleSaveWorkflow}
        onCancel={() => setShowDesigner(false)}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Автоматизация</h1>
          <p className="text-gray-600 mt-2">Управление бизнес-процессами и автоматизацией</p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={loadAnalytics}
            className="btn-secondary flex items-center"
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            Аналитика
          </button>

          <button
            onClick={createNewProcess}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Создать процесс
          </button>
        </div>
      </div>

      {/* Analytics Modal */}
      {showAnalytics && analytics && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">Аналитика автоматизации</h3>
              <button
                onClick={() => setShowAnalytics(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Execution Stats */}
              <div className="card">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Выполнения</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Всего выполнений:</span>
                    <span className="font-medium">{analytics.executions?.total_executions || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Успешных:</span>
                    <span className="font-medium text-green-600">{analytics.executions?.successful_executions || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ошибок:</span>
                    <span className="font-medium text-red-600">{analytics.executions?.failed_executions || 0}</span>
                  </div>
                </div>
              </div>

              {/* Robot Performance */}
              <div className="card">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Производительность роботов</h4>
                <div className="space-y-2">
                  {Array.isArray(analytics.robots) && analytics.robots.slice(0, 3).map((robot: any, index: number) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{robot.name || `Робот ${robot.robot_id}`}</span>
                      <div className="text-xs">
                        <span className="text-green-600">{robot.successful_actions || 0}✓</span>
                        <span className="text-red-600 ml-1">{robot.failed_actions || 0}✗</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Types */}
              <div className="card">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Типы действий</h4>
                <div className="space-y-2">
                  {Array.isArray(analytics.actions) && analytics.actions.slice(0, 5).map((action: any, index: number) => (
                    <div key={index} className="flex justify-between">
                      <span className="text-sm text-gray-600">{action.action_type}</span>
                      <span className="font-medium">{action.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Errors */}
              <div className="card">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Последние ошибки</h4>
                <div className="space-y-2">
                  {Array.isArray(analytics.errors) && analytics.errors.slice(0, 3).map((error: any, index: number) => (
                    <div key={index} className="text-xs">
                      <div className="font-medium text-red-600">{error.error_type}</div>
                      <div className="text-gray-600 truncate">{error.error_message}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Processes List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Бизнес-процессы</h3>

        {processes.length > 0 ? (
          <div className="space-y-4">
            {processes.map((process) => (
              <div key={process.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${process.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <div>
                      <h4 className="font-medium text-gray-900">{process.name}</h4>
                      <p className="text-sm text-gray-600">{process.description}</p>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          {getEntityTypeLabel(process.entity_type)}
                        </span>
                        <span className="text-xs text-gray-500">
                          Создан: {new Date(process.created_at).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleProcess(process)}
                      className={`p-2 rounded-lg ${
                        process.is_active
                          ? 'text-green-600 hover:bg-green-50'
                          : 'text-gray-400 hover:bg-gray-50'
                      }`}
                      title={process.is_active ? 'Остановить' : 'Запустить'}
                    >
                      {process.is_active ? <PauseIcon className="w-4 h-4" /> : <PlayIcon className="w-4 h-4" />}
                    </button>

                    <button
                      onClick={() => editProcess(process)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Редактировать"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => deleteProcess(process.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Удалить"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Cog6ToothIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">Нет процессов автоматизации</h4>
            <p className="text-gray-600 mb-4">Создайте свой первый бизнес-процесс для автоматизации работы</p>
            <button
              onClick={createNewProcess}
              className="btn-primary"
            >
              Создать процесс
            </button>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={createNewProcess}
            className="btn-secondary flex items-center justify-center h-20"
          >
            <div className="text-center">
              <PlusIcon className="w-6 h-6 mx-auto mb-2" />
              <span className="text-sm">Новый процесс</span>
            </div>
          </button>

          <button
            onClick={loadAnalytics}
            className="btn-secondary flex items-center justify-center h-20"
          >
            <div className="text-center">
              <ChartBarIcon className="w-6 h-6 mx-auto mb-2" />
              <span className="text-sm">Аналитика</span>
            </div>
          </button>

          <button
            onClick={() => automationApi.suggestImprovements()}
            className="btn-secondary flex items-center justify-center h-20"
          >
            <div className="text-center">
              <EyeIcon className="w-6 h-6 mx-auto mb-2" />
              <span className="text-sm">Оптимизация</span>
            </div>
          </button>

          <button
            onClick={() => {/* TODO: Export processes */}}
            className="btn-secondary flex items-center justify-center h-20 opacity-50 cursor-not-allowed"
          >
            <div className="text-center">
              <PlayIcon className="w-6 h-6 mx-auto mb-2" />
              <span className="text-sm">Экспорт</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
