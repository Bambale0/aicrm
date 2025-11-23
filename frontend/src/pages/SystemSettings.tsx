import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import Button from '../components/ui/Button';
import {
  Cog6ToothIcon,
  ServerIcon,
  CpuChipIcon,
  EnvelopeIcon,
  PaperAirplaneIcon,
  KeyIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

interface AISettings {
  api_key: string;
  default_model: string;
  temperature: number;
  max_tokens: number;
}

interface AIUsageLimits {
  daily_token_limit: number;
  monthly_token_limit: number;
  concurrent_requests_limit: number;
  enabled: boolean;
}

interface EmailSMTPConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  use_tls: boolean;
  use_ssl: boolean;
  from_email: string;
  from_name: string;
  enabled: boolean;
}

interface TelegramConfig {
  bot_token: string;
  webhook_url: string;
  enabled: boolean;
  admin_chat_id?: string;
}

interface SystemConfig {
  maintenance_mode: boolean;
  debug_mode: boolean;
  log_level: string;
  backup_schedule: string;
  max_file_size_mb: number;
  allowed_domains: string[];
}

function SystemSettings() {
  const [activeTab, setActiveTab] = useState<'ai' | 'email' | 'telegram' | 'system'>('ai');
  const queryClient = useQueryClient();

  // Form states
  const [aiForm, setAiForm] = useState<AISettings>({
    api_key: '',
    default_model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: 4000
  });

  const [aiLimitsForm, setAiLimitsForm] = useState<AIUsageLimits>({
    daily_token_limit: 100000,
    monthly_token_limit: 1000000,
    concurrent_requests_limit: 10,
    enabled: true
  });

  const [emailForm, setEmailForm] = useState<EmailSMTPConfig>({
    host: '',
    port: 587,
    username: '',
    password: '',
    use_tls: true,
    use_ssl: false,
    from_email: '',
    from_name: '',
    enabled: false
  });

  const [telegramForm, setTelegramForm] = useState<TelegramConfig>({
    bot_token: '',
    webhook_url: '',
    enabled: false,
    admin_chat_id: ''
  });

  const [systemForm, setSystemForm] = useState<SystemConfig>({
    maintenance_mode: false,
    debug_mode: false,
    log_level: 'INFO',
    backup_schedule: 'daily',
    max_file_size_mb: 10,
    allowed_domains: []
  });

  // React Query hooks
  const { data: aiConfig, isLoading: aiLoading } = useQuery({
    queryKey: ['ai-config'],
    queryFn: () => apiService.getAIOpenRouterConfig(),
    enabled: activeTab === 'ai'
  });

  const { data: aiLimits, isLoading: limitsLoading } = useQuery({
    queryKey: ['ai-limits'],
    queryFn: () => apiService.getAIUsageLimits(),
    enabled: activeTab === 'ai'
  });

  const { data: emailConfig, isLoading: emailLoading } = useQuery({
    queryKey: ['email-config'],
    queryFn: () => apiService.getEmailSMTPConfig(),
    enabled: activeTab === 'email'
  });

  const { data: telegramConfig, isLoading: telegramLoading } = useQuery({
    queryKey: ['telegram-config'],
    queryFn: () => apiService.getTelegramConfig(),
    enabled: activeTab === 'telegram'
  });

  const { data: systemConfig, isLoading: systemLoading } = useQuery({
    queryKey: ['system-config'],
    queryFn: () => apiService.getSystemConfig(),
    enabled: activeTab === 'system'
  });

  // Mutations
  const aiMutation = useMutation({
    mutationFn: (data: AISettings) => apiService.updateAIOpenRouterConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
      alert('AI настройки сохранены');
    },
    onError: () => alert('Ошибка сохранения AI настроек')
  });

  const aiLimitsMutation = useMutation({
    mutationFn: (data: AIUsageLimits) => apiService.updateAIUsageLimits(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-limits'] });
      alert('Лимиты AI сохранены');
    },
    onError: () => alert('Ошибка сохранения лимитов AI')
  });

  const emailMutation = useMutation({
    mutationFn: (data: EmailSMTPConfig) => apiService.updateEmailSMTPConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-config'] });
      alert('Email настройки сохранены');
    },
    onError: () => alert('Ошибка сохранения Email настроек')
  });

  const telegramMutation = useMutation({
    mutationFn: (data: TelegramConfig) => apiService.updateTelegramConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telegram-config'] });
      alert('Telegram настройки сохранены');
    },
    onError: () => alert('Ошибка сохранения Telegram настроек')
  });

  const systemMutation = useMutation({
    mutationFn: (data: SystemConfig) => apiService.updateSystemConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-config'] });
      alert('Системные настройки сохранены');
    },
    onError: () => alert('Ошибка сохранения системных настроек')
  });

  // Initialize forms when data loads
  React.useEffect(() => {
    if (aiConfig && !aiLoading) {
      setAiForm(aiConfig);
    }
  }, [aiConfig, aiLoading]);

  React.useEffect(() => {
    if (aiLimits && !limitsLoading) {
      setAiLimitsForm(aiLimits);
    }
  }, [aiLimits, limitsLoading]);

  React.useEffect(() => {
    if (emailConfig && !emailLoading) {
      setEmailForm(emailConfig);
    }
  }, [emailConfig, emailLoading]);

  React.useEffect(() => {
    if (telegramConfig && !telegramLoading) {
      setTelegramForm(telegramConfig);
    }
  }, [telegramConfig, telegramLoading]);

  React.useEffect(() => {
    if (systemConfig && !systemLoading) {
      setSystemForm(systemConfig);
    }
  }, [systemConfig, systemLoading]);

  const handleSaveAITab = () => {
    aiMutation.mutate(aiForm);
    aiLimitsMutation.mutate(aiLimitsForm);
  };

  const handleSaveEmailTab = () => {
    emailMutation.mutate(emailForm);
  };

  const handleSaveTelegramTab = () => {
    telegramMutation.mutate(telegramForm);
  };

  const handleSaveSystemTab = () => {
    systemMutation.mutate(systemForm);
  };

  const tabs = [
    { id: 'ai', name: 'ИИ', icon: CpuChipIcon },
    { id: 'email', name: 'Email', icon: EnvelopeIcon },
    { id: 'telegram', name: 'Telegram', icon: PaperAirplaneIcon },
    { id: 'system', name: 'Система', icon: ServerIcon }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Системные настройки</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">
            Конфигурация системы и интеграций
          </p>
        </div>
        <div className="flex space-x-2">
          {activeTab === 'ai' && (
            <Button
              onClick={handleSaveAITab}
              variant="primary"
              loading={aiMutation.isPending || aiLimitsMutation.isPending}
              className="flex items-center"
            >
              <ShieldCheckIcon className="w-5 h-5 mr-2" />
              Сохранить AI
            </Button>
          )}
          {activeTab === 'email' && (
            <Button
              onClick={handleSaveEmailTab}
              variant="primary"
              loading={emailMutation.isPending}
              className="flex items-center"
            >
              <EnvelopeIcon className="w-5 h-5 mr-2" />
              Сохранить Email
            </Button>
          )}
          {activeTab === 'telegram' && (
            <Button
              onClick={handleSaveTelegramTab}
              variant="primary"
              loading={telegramMutation.isPending}
              className="flex items-center"
            >
              <PaperAirplaneIcon className="w-5 h-5 mr-2" />
              Сохранить Telegram
            </Button>
          )}
          {activeTab === 'system' && (
            <Button
              onClick={handleSaveSystemTab}
              variant="primary"
              loading={systemMutation.isPending}
              className="flex items-center"
            >
              <ServerIcon className="w-5 h-5 mr-2" />
              Сохранить System
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-van-gogh-ultramarine text-van-gogh-ultramarine'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* AI Settings Tab */}
      {activeTab === 'ai' && (
        <div className="space-y-6">
          {/* AI Provider Config */}
          <div className="card">
            <div className="flex items-center mb-4">
              <KeyIcon className="w-6 h-6 text-van-gogh-ultramarine mr-3" />
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
                Конфигурация OpenRouter
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  API Key *
                </label>
                <input
                  type="password"
                  value={aiForm.api_key}
                  onChange={(e) => setAiForm({ ...aiForm, api_key: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="sk-or-v1-xxxxxxxxxxxx"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Модель по умолчанию
                </label>
                <select
                  value={aiForm.default_model}
                  onChange={(e) => setAiForm({ ...aiForm, default_model: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                >
                  <option value="openai/gpt-4o">GPT-4o</option>
                  <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                  <option value="anthropic/claude-3-haiku">Claude 3 Haiku</option>
                  <option value="deepseek/deepseek-chat">DeepSeek Chat</option>
                  <option value="kimi/kimi-k1.5">Kimi K1.5</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Температура (0.1-2.0)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="2.0"
                  step="0.1"
                  value={aiForm.temperature}
                  onChange={(e) => setAiForm({ ...aiForm, temperature: parseFloat(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Максимум токенов
                </label>
                <input
                  type="number"
                  min="100"
                  max="32000"
                  value={aiForm.max_tokens}
                  onChange={(e) => setAiForm({ ...aiForm, max_tokens: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* AI Usage Limits */}
          <div className="card">
            <div className="flex items-center mb-4">
              <ShieldCheckIcon className="w-6 h-6 text-van-gogh-ultramarine mr-3" />
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
                Лимиты использования ИИ
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Дневной лимит токенов
                </label>
                <input
                  type="number"
                  value={aiLimitsForm.daily_token_limit}
                  onChange={(e) => setAiLimitsForm({ ...aiLimitsForm, daily_token_limit: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Месячный лимит токенов
                </label>
                <input
                  type="number"
                  value={aiLimitsForm.monthly_token_limit}
                  onChange={(e) => setAiLimitsForm({ ...aiLimitsForm, monthly_token_limit: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Конкурентные запросы
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={aiLimitsForm.concurrent_requests_limit}
                  onChange={(e) => setAiLimitsForm({ ...aiLimitsForm, concurrent_requests_limit: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div className="flex items-center pt-8">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={aiLimitsForm.enabled}
                    onChange={(e) => setAiLimitsForm({ ...aiLimitsForm, enabled: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Включить лимиты</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Settings Tab */}
      {activeTab === 'email' && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center mb-4">
              <EnvelopeIcon className="w-6 h-6 text-van-gogh-ultramarine mr-3" />
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
                Конфигурация SMTP
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2 flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailForm.enabled}
                    onChange={(e) => setEmailForm({ ...emailForm, enabled: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Включить email интеграцию</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  SMTP Host *
                </label>
                <input
                  type="text"
                  value={emailForm.host}
                  onChange={(e) => setEmailForm({ ...emailForm, host: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="smtp.gmail.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Port *
                </label>
                <input
                  type="number"
                  value={emailForm.port}
                  onChange={(e) => setEmailForm({ ...emailForm, port: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Username *
                </label>
                <input
                  type="text"
                  value={emailForm.username}
                  onChange={(e) => setEmailForm({ ...emailForm, username: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="your-email@gmail.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Password *
                </label>
                <input
                  type="password"
                  value={emailForm.password}
                  onChange={(e) => setEmailForm({ ...emailForm, password: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="your-app-password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Отправитель (Имя)
                </label>
                <input
                  type="text"
                  value={emailForm.from_name}
                  onChange={(e) => setEmailForm({ ...emailForm, from_name: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="AI CRM System"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Отправитель (Email)
                </label>
                <input
                  type="email"
                  value={emailForm.from_email}
                  onChange={(e) => setEmailForm({ ...emailForm, from_email: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="noreply@aicrm.dev"
                />
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailForm.use_tls}
                    onChange={(e) => setEmailForm({ ...emailForm, use_tls: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Use TLS</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailForm.use_ssl}
                    onChange={(e) => setEmailForm({ ...emailForm, use_ssl: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Use SSL</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Telegram Settings Tab */}
      {activeTab === 'telegram' && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center mb-4">
              <PaperAirplaneIcon className="w-6 h-6 text-van-gogh-ultramarine mr-3" />
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
                Конфигурация Telegram Bot
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2 flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={telegramForm.enabled}
                    onChange={(e) => setTelegramForm({ ...telegramForm, enabled: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Включить Telegram интеграцию</span>
                </label>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Bot Token *
                </label>
                <input
                  type="password"
                  value={telegramForm.bot_token}
                  onChange={(e) => setTelegramForm({ ...telegramForm, bot_token: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Webhook URL
                </label>
                <input
                  type="url"
                  value={telegramForm.webhook_url}
                  onChange={(e) => setTelegramForm({ ...telegramForm, webhook_url: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="https://your-domain.com/api/telegram/webhook"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Admin Chat ID
                </label>
                <input
                  type="text"
                  value={telegramForm.admin_chat_id || ''}
                  onChange={(e) => setTelegramForm({ ...telegramForm, admin_chat_id: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="123456789"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Settings Tab */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center mb-4">
              <ServerIcon className="w-6 h-6 text-van-gogh-ultramarine mr-3" />
              <h3 className="text-lg font-semibold text-van-gogh-starry-night-blue">
                Общие настройки системы
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={systemForm.maintenance_mode}
                    onChange={(e) => setSystemForm({ ...systemForm, maintenance_mode: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Режим обслуживания</span>
                </label>
              </div>

              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={systemForm.debug_mode}
                    onChange={(e) => setSystemForm({ ...systemForm, debug_mode: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-van-gogh-chrome-green">Режим отладки</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Уровень логирования
                </label>
                <select
                  value={systemForm.log_level}
                  onChange={(e) => setSystemForm({ ...systemForm, log_level: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Резервное копирование
                </label>
                <select
                  value={systemForm.backup_schedule}
                  onChange={(e) => setSystemForm({ ...systemForm, backup_schedule: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                >
                  <option value="disabled">Отключено</option>
                  <option value="daily">Ежедневно</option>
                  <option value="weekly">Еженедельно</option>
                  <option value="monthly">Ежемесячно</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Максимальный размер файла (MB)
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={systemForm.max_file_size_mb}
                  onChange={(e) => setSystemForm({ ...systemForm, max_file_size_mb: parseInt(e.target.value) })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                  Разрешенные домены (через запятую)
                </label>
                <input
                  type="text"
                  value={systemForm.allowed_domains.join(', ')}
                  onChange={(e) => setSystemForm({
                    ...systemForm,
                    allowed_domains: e.target.value.split(',').map(d => d.trim()).filter(d => d)
                  })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                  placeholder="example.com, api.example.com"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SystemSettings;
