import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Button from '../components/ui/Button';
import {
  ServerIcon,
  ChartBarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  CircleStackIcon,
  CloudIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

interface HealthData {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  services: {
    [key: string]: {
      status: string;
      error?: string;
      response_time?: string;
    };
  };
  system: {
    cpu_percent: number;
    memory: {
      total: number;
      available: number;
      percent: number;
    };
    disk: {
      total: number;
      free: number;
      percent: number;
    };
    uptime: number;
  };
}

interface WorkflowData {
  workflows: Array<{
    id: string;
    name: string;
    entity_type: string;
    description: string;
    steps_count: number;
  }>;
}

interface MetricsData {
  [key: string]: any;
}

function SystemMonitoring() {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowData | null>(null);
  const [metrics, setMetrics] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadMonitoringData = async () => {
    try {
      setRefreshing(true);
      const [healthResponse, workflowsResponse, metricsResponse] = await Promise.all([
        apiService.getDetailedHealth(),
        apiService.getWorkflows(),
        apiService.getMetrics()
      ]);

      setHealthData(healthResponse);
      setWorkflows(workflowsResponse);
      setMetrics(metricsResponse);
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMonitoringData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMonitoringData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'configured':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'unhealthy':
      case 'inactive':
      case 'not_configured':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-van-gogh-ultramarine"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Мониторинг системы</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">Enterprise monitoring dashboard</p>
        </div>
        <Button
          onClick={loadMonitoringData}
          loading={refreshing}
          variant="secondary"
          size="sm"
        >
          <ArrowPathIcon className="w-4 h-4 mr-2" />
          Обновить
        </Button>
      </div>

      {/* System Overview */}
      {healthData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* System Status */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Статус системы</h3>
              {getStatusIcon(healthData.status)}
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-van-gogh-chrome-green">Версия:</span>
                <span className="text-sm font-medium">{healthData.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-van-gogh-chrome-green">Время работы:</span>
                <span className="text-sm font-medium">{formatUptime(healthData.uptime)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-van-gogh-chrome-green">Время проверки:</span>
                <span className="text-sm font-medium">
                  {new Date(healthData.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* System Resources */}
          <div className="card">
            <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">Ресурсы системы</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-van-gogh-chrome-green">CPU:</span>
                  <span>{healthData.system.cpu_percent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-van-gogh-ultramarine h-2 rounded-full"
                    style={{ width: `${healthData.system.cpu_percent}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-van-gogh-chrome-green">Память:</span>
                  <span>{healthData.system.memory.percent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-van-gogh-vermilion h-2 rounded-full"
                    style={{ width: `${healthData.system.memory.percent}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-van-gogh-chrome-green">Диск:</span>
                  <span>{healthData.system.disk.percent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-van-gogh-chrome-green h-2 rounded-full"
                    style={{ width: `${healthData.system.disk.percent}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Services Status */}
          <div className="card">
            <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">Сервисы</h3>
            <div className="space-y-2">
              {Object.entries(healthData.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between">
                  <span className="text-sm text-van-gogh-chrome-green capitalize">
                    {service.replace('_', ' ')}:
                  </span>
                  <div className="flex items-center">
                    {getStatusIcon(status.status)}
                    <span className="ml-1 text-xs">
                      {status.status === 'healthy' ? 'OK' :
                       status.status === 'configured' ? 'Настроен' :
                       status.status === 'not_configured' ? 'Не настроен' : 'Ошибка'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Workflow Status */}
      {workflows && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Workflow Engine</h3>
            <div className="flex items-center">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
              <span className="text-sm text-van-gogh-chrome-green">
                {workflows.workflows.length} активных процессов
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {workflows.workflows.map((workflow) => (
              <div key={workflow.id} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-van-gogh-starry-night-blue">{workflow.name}</h4>
                  <span className="text-xs bg-van-gogh-ultramarine/10 text-van-gogh-ultramarine px-2 py-1 rounded">
                    {workflow.steps_count} шагов
                  </span>
                </div>
                <p className="text-sm text-van-gogh-chrome-green mb-2">{workflow.description}</p>
                <div className="flex items-center text-xs text-gray-500">
                  <CircleStackIcon className="w-4 h-4 mr-1" />
                  {workflow.entity_type}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">Prometheus Metrics</h3>
            <div className="flex items-center">
              <ChartBarIcon className="w-5 h-5 text-van-gogh-ultramarine mr-2" />
              <span className="text-sm text-van-gogh-chrome-green">Активен</span>
            </div>
          </div>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto max-h-96">
            <pre>{metrics}</pre>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue mb-4">Enterprise Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button
            onClick={() => window.open('/docs', '_blank')}
            variant="secondary"
            fullWidth
          >
            <ServerIcon className="w-5 h-5 mr-2" />
            API Docs
          </Button>
          <Button
            onClick={() => window.open('/health/detailed', '_blank')}
            variant="secondary"
            fullWidth
          >
            <ShieldCheckIcon className="w-5 h-5 mr-2" />
            Health Check
          </Button>
          <Button
            onClick={() => window.open('/metrics', '_blank')}
            variant="secondary"
            fullWidth
          >
            <ChartBarIcon className="w-5 h-5 mr-2" />
            Raw Metrics
          </Button>
          <Button
            onClick={() => window.open('/workflow/workflows', '_blank')}
            variant="secondary"
            fullWidth
          >
            <CloudIcon className="w-5 h-5 mr-2" />
            Workflows
          </Button>
        </div>
      </div>
    </div>
  );
}

export default SystemMonitoring;
