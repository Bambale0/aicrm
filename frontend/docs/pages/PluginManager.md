# 🔌 Система плагинов AI CRM

## Обзор

**Plugin Manager** - это полнофункциональная система управления плагинами для расширения функциональности AI CRM. Позволяет устанавливать, настраивать и управлять плагинами различных типов: действия, хуки, интеграции, аналитика и автоматизация. Система предоставляет RESTful API для полного программного доступа к функциональности плагинов.

## 🎯 Реализованные Типы Плагинов

### 1. 🔧 Action Plugins
Плагины, предоставляющие исполняемые действия через API

```typescript
interface ActionPlugin {
  name: string;
  available_actions: string[];
  execute_action(action_name: string, params: any): Promise<ActionResult>;
}
```

**Пример использования:**
```typescript
POST /api/plugins/example-action-plugin/actions/send_greeting/execute
{
  "parameters": {"name": "Иван"},
  "context": {"user_id": 1, "entity_type": "customer"}
}
```

### 2. 🎣 Hook Plugins
Плагины, реагирующие на события системы

```typescript
interface HookPlugin {
  registered_hooks: HookRegistration[];
  handle_hook(context: HookContext): Promise<HookResult>;
}
```

**Доступные хуки:**
- `before_save` - перед сохранением сущности
- `after_create` - после создания сущности
- `before_delete` - перед удалением сущности

### 3. 🔗 Integration Plugins
Интеграции с внешними сервисами

```typescript
interface IntegrationPlugin extends ActionPlugin {
  test_connection(): Promise<boolean>;
  sync_data(config: any): Promise<SyncResult>;
}
```

### 4. 📊 Analytics Plugins
Аналитические расширения для сбора метрик

### 5. 🤖 Automation Plugins
Расширение системы бизнес-автоматизации

## 🖥️ API Endpoints

### Статус системы
```http
GET /api/plugins/status
```

### Управление плагинами
```http
GET    /api/plugins/installed        # Список установленных
POST   /api/plugins/install/{name}   # Установка плагина
DELETE /api/plugins/uninstall/{name} # Удаление плагина
POST   /api/plugins/{name}/activate  # Активация
POST   /api/plugins/{name}/deactivate # Деактивация
```

### Выполнение действий
```http
POST /api/plugins/{plugin}/actions/{action}/execute
Content-Type: application/json

{
  "parameters": {"key": "value"},
  "context": {
    "user_id": 1,
    "entity_type": "order",
    "entity_id": 123
  }
}
```

### Конфигурация
```http
GET    /api/plugins/{name}/settings/schema  # Схема настроек
PUT    /api/plugins/{name}/settings         # Обновить настройки
GET    /api/plugins/registry               # Registry плагинов
GET    /api/plugins/marketplace            # Marketplace
```

## 🏗️ Архитектура Фронтенда

### Структура компонентов
```
frontend/src/components/PluginManager/
├── PluginManager.tsx           # Главный компонент
├── PluginList.tsx             # Список плагинов
├── PluginDetails.tsx          # Детали плагина
├── PluginActions.tsx          # Выполнение действий
├── PluginSettings.tsx         # Настройки плагинов
├── PluginMarket.tsx           # Marketplace
└── hooks/
    ├── usePlugins.ts          # Хук для управления плагинами
    └── usePluginExecution.ts  # Хук для выполнения действий
```

### TypeScript интерфейсы
```typescript
interface Plugin {
  name: string;
  display_name: string;
  version: string;
  description?: string;
  author?: string;
  is_active: boolean;
  is_installed: boolean;
  interfaces: PluginInterface[];
  current_settings?: any;
}

interface PluginInterface {
  type: 'ActionPlugin' | 'HookPlugin' | 'IntegrationPlugin' | 'AnalyticsPlugin' | 'AutomationPlugin';
  capabilities: string[];
}

interface ActionResult {
  success: boolean;
  result?: any;
  error?: string;
  execution_time_ms: number;
}
```

## 🚀 Быстрый старт

### Установка нового плагина
1. Открыть **Plugin Marketplace**
2. Найти нужный плагин по категории
3. Нажать **"Install"**
4. Настроить параметры через UI или API
5. Активировать плагин

### Выполнение действия плагина
```typescript
// Через React компонент
const { executeAction } = usePluginExecution();

const result = await executeAction({
  pluginName: 'example-action-plugin',
  actionName: 'send_greeting',
  parameters: { name: 'World' },
  context: { user_id: currentUser.id }
});

// Через API
const response = await fetch('/api/plugins/example-action-plugin/actions/send_greeting/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    parameters: { name: 'World' },
    context: { user_id: currentUser.id }
  })
});
```

### Мониторинг выполнений
```typescript
const { recentExecutions } = usePluginExecutions();

// Показать статистику выполнений
executions.forEach(exec => {
  console.log(`${exec.plugin_name}:${exec.action_name} - ${exec.status} (${exec.duration_ms}ms)`);
});
```

## 🔄 Визуализатор Workflow

### Компонент Workflow
```typescript
const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  entities,
  stages,
  triggers,
  plugins
}) => {
  // Визуализация связей между:
  // - Сущностями -> Триггерами -> Действиями
  // - Плагинами -> Выполняемыми действиями
  // - Стадиями процесса -> Автоматизацией
};
```

### Возможности визуализатора
- **Графическое представление** всех связей
- **Интерактивные узлы** для просмотра деталей
- **Фильтрация** по типам сущностей и плагинов
- **Экспорт** диаграммы в различные форматы
- **Realtime updates** для активных процессов

## 🛡️ Безопасность и Разрешения

### Система разрешений плагинов
```typescript
interface PluginPermission {
  plugin_name: string;
  resource_type: 'order' | 'customer' | 'email' | '*';
  resource_id: string; // или '*' для всех
  permission_type: 'read' | 'write' | 'admin';
  conditions?: any;
}
```

### Уровни доступа
- **Read** - только чтение данных
- **Write** - создание и обновление
- **Admin** - полный доступ включая системные функции

## 📊 Аналитика и Мониторинг

### Dashboard метрик
```typescript
const PluginAnalytics: React.FC = () => {
  const { metrics } = usePluginMetrics();

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard title="Активные плагины" value={metrics.active_plugins} />
      <MetricCard title="Всего выполнений" value={metrics.total_executions} />
      <MetricCard title="Успешность %" value={metrics.success_rate} />
      <MetricCard title="Среднее время" value={`${metrics.avg_duration}ms`} />
    </div>
  );
};
```

### Real-time логи
```typescript
const ExecutionLogs: React.FC = () => {
  const { logs, isConnected } = useWebSocket('/ws/plugins/logs');

  return (
    <div className="bg-gray-900 text-green-400 p-4 font-mono">
      {logs.map(log => (
        <div key={log.id}>
          [{log.timestamp}] {log.plugin_name}:{log.action_name} - {log.status}
        </div>
      ))}
    </div>
  );
};
```

## 🎨 UI/UX Особенности

### Responsive дизайн
- **Адаптивные компоненты** под все размеры экрана
- **Мобильная оптимизация** с touch-гестурами
- **Dark/Light темы** с автоматическим переключением

### Взаимодействие с пользователем
- **Drag & Drop** для настройки workflow
- **Inline редактирование** настроек плагинов
- **Toast уведомления** о результатах операций
- **Loading states** для всех асинхронных операций

### Доступность (A11y)
- **ARIA labels** для всех интерактивных элементов
- **Keyboard navigation** полная поддержка
- **Screen reader** совместимость
- **High contrast** режим

## 🔧 Разработка и Расширение

### Создание нового типа плагина
```typescript
// Определение интерфейса
interface CustomPlugin extends BasePlugin {
  custom_method(): Promise<CustomResult>;
}

// React компонент для управления
const CustomPluginManager: React.FC<CustomPluginManagerProps> = () => {
  // Логика управления кастомным плагином
};
```

### Интеграция с существующими компонентами
```typescript
// Добавление плагина в существующий workflow
const EnhancedWorkflow: React.FC = () => {
  const { plugins } = usePlugins();
  const automationPlugins = plugins.filter(p =>
    p.interfaces.includes('AutomationPlugin')
  );

  return (
    <WorkflowEditor
      availablePlugins={automationPlugins}
      onPluginAdd={(plugin) => workflow.addPlugin(plugin)}
    />
  );
};
```

## 🚀 Roadmap Фронтенда

### Phase 1 ✅ (Текущая)
- [x] Базовый UI для управления плагинами
- [x] Список установленных плагинов
- [x] Выполнение действий
- [x] Простые настройки

### Phase 2 🔄 (Следующая)
- [ ] Расширенный визуализатор workflow
- [ ] Plugin marketplace с категориями
- [ ] Advanced analytics dashboard
- [ ] Batch operations для плагинов
- [ ] Export/Import конфигураций

### Phase 3 🔮 (Будущая)
- [ ] Визуальный конструктор плагинов
- [ ] Collaborative editing
- [ ] AI-assisted plugin recommendations
- [ ] Multi-tenant plugin management
- [ ] Advanced permission builder

## 📚 Ссылки и Ресурсы

- **Backend документация**: `docs/plugin_system.md`
- **API спецификация**: `/docs` (Swagger UI)
- **Примеры кода**: `backend/src/aicrm/services/plugin/example_plugins.py`
- **Компоненты**: `frontend/src/components/PluginManager/`

---

*Plugin Manager - современная, гибкая и мощная система управления плагинами с интуитивным интерфейсом и расширенными возможностями интеграции.*

---

*Плагин менеджер предоставляет единый центр управления всей автоматизацией системы, упрощая процесс создания, мониторинга и оптимизации бизнес-процессов.*
