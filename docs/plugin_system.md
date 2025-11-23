# 🔌 Система плагинов AI CRM

## Обзор

**Plugin System** - это расширяемая архитектура плагинов для AI CRM системы, которая позволяет добавлять новую функциональность без изменения основного кода. Система поддерживает различные типы плагинов: действия, хуки, интеграции, аналитика и автоматизация.

## 🎯 Возможности

### Архитектура плагинов
- **Модульная система** - плагины независимы друг от друга
- **Горячая загрузка** - активация плагинов без перезапуска
- **Безопасность** - изолированное выполнение с разрешениями
- **Валидация** - автоматическая проверка совместимости
- **Мониторинг** - полное логирование действий плагинов

### Типы плагинов

#### 1. 🔧 Action Plugin
Плагины, предоставляющие исполняемые действия

```python
class ExampleActionPlugin(ActionPlugin):
    async def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action_name == "send_greeting":
            return {"message": f"Hello, {parameters['name']}!"}
```

#### 2. 🎣 Hook Plugin
Плагины, реагирующие на события системы

```python
class ExampleHookPlugin(HookPlugin):
    def get_registered_hooks(self) -> List[Dict[str, Any]]:
        return [{"hook_type": "after_create", "hook_event": "customer_created"}]

    async def handle_hook(self, context: HookContext) -> HookResult:
        # Отправить приветственное email
        return HookResult(success=True, message="Welcome email sent")
```

#### 3. 🔗 Integration Plugin
Интеграции с внешними сервисами

```python
class SlackIntegrationPlugin(IntegrationPlugin):
    async def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Slack API connected"}

    async def sync_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Синхронизация данных с Slack
        pass
```

#### 4. 📊 Analytics Plugin
Аналитические возможности

```python
class ConversionAnalyticsPlugin(AnalyticsPlugin):
    async def collect_metrics(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        # Подсчёт конверсий и метрик
        pass
```

#### 5. 🤖 Automation Plugin
Расширение системы автоматизации

```python
class SmsAutomationPlugin(AutomationPlugin):
    def get_custom_actions(self) -> List[Dict[str, Any]]:
        return [{"action_type": "CUSTOM_SEND_SMS", "display_name": "Отправить SMS"}]

    async def execute_custom_action(self, action_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        # Отправка SMS через кастомного провайдера
        pass
```

## 📁 Структура проекта

```
backend/src/aicrm/
├── services/plugin/           # Ядро системы плагинов
│   ├── __init__.py
│   ├── plugin_interfaces.py   # Интерфейсы плагинов
│   ├── plugin_manager.py      # Менеджер плагинов
│   └── example_plugins.py     # Примеры плагинов
├── models/plugin.py           # Модели данных плагинов
└── api/routers/plugin.py      # REST API для плагинов

frontend/
├── components/PluginManager/  # UI компонент менеджер плагинов
└── docs/pages/PluginManager.md # Документация UI

docs/
├── plugin_system.md         # Эта документация
└── database_plugin_migration.sql # Миграция БД
```

## 🗄️ База данных

### Основные таблицы

#### `plugins` - Основная таблица плагинов
```sql
CREATE TABLE plugins (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,          -- Уникальное имя
    display_name VARCHAR(255) NOT NULL,         -- Читабельное имя
    version VARCHAR(50) NOT NULL,               -- Версия плагина
    description TEXT,                           -- Описание
    module_name VARCHAR(255),                   -- Python модуль
    class_name VARCHAR(255),                   -- Класс плагина
    is_active BOOLEAN DEFAULT FALSE,           -- Активен ли плагин
    is_system BOOLEAN DEFAULT FALSE,           -- Системный плагин
    settings_schema JSON,                      -- JSON Schema настроек
    current_settings JSON,                     -- Текущие настройки
    dependencies JSON,                         -- Зависимости
    installed_at TIMESTAMP,                    -- Дата установки
    installed_by INTEGER                       -- Кто установил
);
```

#### `plugin_actions` - Логи выполнения действий
```sql
CREATE TABLE plugin_actions (
    id INTEGER PRIMARY KEY,
    plugin_id INTEGER NOT NULL REFERENCES plugins(id),
    action_name VARCHAR(255) NOT NULL,
    execution_status VARCHAR(50) NOT NULL,     -- success/error/running
    started_at TIMESTAMP DEFAULT NOW(),
    parameters JSON,                           -- Входные параметры
    result JSON,                               -- Результат выполнения
    error_message TEXT,                        -- Сообщение об ошибке
    entity_type VARCHAR(50),                   -- Связанная сущность
    user_id INTEGER                            -- Пользователь
);
```

#### `plugin_hooks` - Регистрация хуков
```sql
CREATE TABLE plugin_hooks (
    id INTEGER PRIMARY KEY,
    plugin_id INTEGER NOT NULL REFERENCES plugins(id),
    hook_type VARCHAR(100) NOT NULL,           -- before_save, after_create
    hook_event VARCHAR(100) NOT NULL,          -- customer_created, order_updated
    priority INTEGER DEFAULT 10,               -- Приоритет выполнения
    conditions JSON,                           -- Условия срабатывания
    is_active BOOLEAN DEFAULT TRUE
);
```

#### `plugin_registry` - Marketplace плагинов
```sql
CREATE TABLE plugin_registry (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    version VARCHAR(50) NOT NULL,
    category VARCHAR(100),                      -- integration, automation, report
    repository_url VARCHAR(500),               -- Ссылка на репозиторий
    is_official BOOLEAN DEFAULT FALSE,          -- Официальный плагин
    download_count INTEGER DEFAULT 0,          -- Статистика скачиваний
    rating JSON                                -- Рейтинг пользователей
);
```

## 🚀 Быстрый старт

### 1. Установка плагина

```bash
# Через API
POST /api/plugins/install/example-action-plugin
Authorization: Bearer <token>
```

### 2. Активация плагина

```bash
POST /api/plugins/example-action-plugin/activate
```

### 3. Выполнение действия

```bash
POST /api/plugins/example-action-plugin/actions/send_greeting/execute
Content-Type: application/json

{
  "parameters": {"name": "Иван"},
  "context": {"user_id": 1, "entity_type": "customer"}
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Hello, Иван!",
  "timestamp": "2025-11-23T11:15:00Z"
}
```

## 📚 Разработка плагинов

### Шаблон базового плагина

```python
from typing import Dict, Any, List
from ..services.plugin.plugin_interfaces import BasePlugin, PluginInfo

class MyCustomPlugin(BasePlugin):

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="my-custom-plugin",
            display_name="Мой плагин",
            version="1.0.0",
            description="Описание функциональности",
            author="Ваше имя"
        )

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация плагина"""
        self._config = config
        # Настройка подключений, инициализация ресурсов
        return True

    async def shutdown(self) -> bool:
        """Корректное завершение работы"""
        # Очистка ресурсов
        return True

    def get_settings_schema(self) -> Dict[str, Any]:
        """JSON Schema для настроек"""
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["api_key"]
        }

    def get_default_settings(self) -> Dict[str, Any]:
        """Значения по умолчанию"""
        return {"timeout": 30}
```

### Регистрация нового действия

```python
from ..services.plugin.plugin_interfaces import ActionPlugin

class MyActionPlugin(BasePlugin, ActionPlugin):

    def get_available_actions(self) -> List[str]:
        return ["send_notification", "calculate_metric"]

    def get_action_schema(self, action_name: str) -> Dict[str, Any]:
        schemas = {
            "send_notification": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"]}
                },
                "required": ["message"]
            }
        }
        return schemas.get(action_name, {})

    async def execute_action(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        if action_name == "send_notification":
            # Логика отправки уведомления
            return {"success": True, "notification_id": "123"}

        return {"success": False, "error": f"Unknown action: {action_name}"}
```

### Регистрация хуков

```python
from ..services.plugin.plugin_interfaces import HookPlugin, HookContext, HookResult

class MyHookPlugin(BasePlugin, HookPlugin):

    def get_registered_hooks(self) -> List[Dict[str, Any]]:
        return [
            {
                "hook_type": "after_create",
                "hook_event": "order_created",
                "priority": 10,
                "conditions": {"order_type": "premium"}
            },
            {
                "hook_type": "before_save",
                "hook_event": "customer_updated",
                "priority": 5
            }
        ]

    async def handle_hook(self, hook_context: HookContext) -> HookResult:
        if hook_context.hook_event == "order_created":
            # Отправить приветственное email для премиум заказов
            return HookResult(
                success=True,
                message="Welcome email sent for premium order"
            )

        elif hook_context.hook_event == "customer_updated":
            # Проверить изменения данных клиента
            if self._has_sensitive_changes(hook_context.data):
                return HookResult(
                    success=False,
                    message="Sensitive data change requires approval",
                    should_continue=False
                )

        return HookResult(success=True)
```

## 🔌 API Reference

### Получение статуса системы
```http
GET /api/plugins/status
```

**Ответ:**
```json
{
  "status": "operational",
  "loaded_plugins": 5,
  "available_plugins": 12,
  "system_initialized": true
}
```

### Получение установленных плагинов
```http
GET /api/plugins/installed
```

**Ответ:**
```json
{
  "plugins": [
    {
      "name": "example-action-plugin",
      "display_name": "Пример плагина действий",
      "version": "1.0.0",
      "is_active": true,
      "interfaces": ["ActionPlugin"]
    }
  ]
}
```

### Установка плагина
```http
POST /api/plugins/install/{plugin_name}
Authorization: Bearer <token>
```

### Выполнение действия плагина
```http
POST /api/plugins/{plugin_name}/actions/{action_name}/execute
Content-Type: application/json

{
  "parameters": {
    "param1": "value1"
  },
  "context": {
    "user_id": 1,
    "entity_type": "order",
    "entity_id": 123
  }
}
```

### Получение схемы настроек
```http
GET /api/plugins/{plugin_name}/settings/schema
```

### Обновление настроек плагина
```http
PUT /api/plugins/{plugin_name}/settings
Content-Type: application/json

{
  "api_key": "new-api-key",
  "timeout": 60
}
```

## 🔐 Безопасность и разрешения

### Уровни доступа плагинов

#### Read (Чтение)
- Просмотр данных системы
- Получение списков заказов/клиентов
- Доступ к публичным API

#### Write (Запись)
- Создание/обновление заказов
- Управление клиентами
- Отправка коммуникаций

#### Admin (Администрирование)
- Управление пользователями
- Изменение системных настроек
- Доступ к административным API

### Пример разрешений
```json
[
  {
    "permission_name": "orders.read",
    "permission_type": "read",
    "resource_type": "order",
    "resource_id": "*"
  },
  {
    "permission_name": "customers.write",
    "permission_type": "write",
    "resource_type": "customer",
    "resource_id": "business_*"
  }
]
```

## 📊 Мониторинг и логирование

### Логи выполнения

Система автоматически логирует все действия плагинов:

```sql
SELECT * FROM plugin_actions
WHERE plugin_id = 1
  AND started_at >= '2025-01-01'
ORDER BY started_at DESC
LIMIT 100;
```

### Метрики производительности

```sql
SELECT
    plugin_id,
    action_name,
    AVG(duration_ms) as avg_duration,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN execution_status = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate
FROM plugin_actions
GROUP BY plugin_id, action_name;
```

## 🎯 Лучшие практики

### Разработка

1. **Одна ответственность** - каждый плагин решает одну задачу
2. **Обработка ошибок** - корректная обработка исключений
3. **Валидация данных** - проверка входных параметров
4. **Документация** - подробное описание API и настроек

### Развертывание

1. **Версионирование** - семантическое версионирование плагинов
2. **Зависимости** - явное указание требований совместимости
3. **Миграции** - поддержка обновлений с сохранением данных
4. **Откат** - возможность отката при проблемах

### Эксплуатация

1. **Мониторинг** - отслеживание производительности плагинов
2. **Логирование** - подробные логи для отладки
3. **Резервное копирование** - сохранение настроек плагинов
4. **Обновления** - безопасное обновление без простоя

## 🚀 Roadmap

### Phase 1 (Текущая) ✅
- [x] Базовая архитектура плагинов
- [x] Поддержка Action и Hook плагинов
- [x] REST API управления
- [x] Примеры плагинов

### Phase 2 (Следующая)
- [ ] Marketplace плагинов
- [ ] Визуальный конструктор workflow
- [ ] Advanced permissions system
- [ ] Plugin discovery из репозиториев

### Phase 3 (Будущая)
- [ ] Distributed plugin execution
- [ ] Hot reload plugins
- [ ] Plugin clustering и load balancing
- [ ] Machine learning интеграция

## 📞 Поддержка

Для вопросов по разработке плагинов:
- **Документация:** `docs/plugin_system.md`
- **Примеры:** `backend/src/aicrm/services/plugin/example_plugins.py`
- **API Spec:** FastAPI автодокументация `/docs`

---

*Система плагинов предоставляет гибкую и безопасную платформу для расширения функциональности AI CRM без изменения основного кода системы.*
