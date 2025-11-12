# 🤖 AI CRM System

**Многофункциональная CRM система с ИИ для управления заказами печати и производством**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Описание

AI CRM System - это полнофункциональная CRM система для компаний, занимающихся печатью и производством. Система интегрирует современные ИИ технологии для автоматизации коммуникаций, управления заказами и производственными процессами.

### 🎯 Основные возможности

- **🤖 ИИ-ассистент**: Анализ намерений клиентов, генерация ответов, поддержка OpenRouter/HuggingFace/OpenAI
- **🏭 Производственный workflow**: Автоматическое создание этапов производства, отслеживание прогресса
- **📊 Аналитика**: Отчеты о заказах, просрочках, эффективности производства
- **💬 Многоканальные коммуникации**: Telegram, Email, Website, Avito
- **📢 Avito интеграция**: Программное управление объявлениями, статистика, продвижение, оптимизация цен
- **📈 Мониторинг**: Структурированное логирование, метрики, health checks
- **🔒 Безопасность**: JWT аутентификация, валидация данных, защита API

## 🏗️ Архитектура

### Технологический стек

#### 🎯 **Core Backend Technologies**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Web Framework** | **FastAPI** | `0.104.1+` | REST API, асинхронная обработка | - Async/await нативная поддержка<br>- Автоматическая генерация OpenAPI/Swagger<br>- Зависимости через Depends()<br>- Pydantic для валидации |
| **ORM** | **SQLAlchemy** | `2.0.23+` | Работа с базой данных | - Асинхронные операции<br>- Миграции через Alembic<br>- Connection pooling<br>- Комплексные запросы |
| **База данных** | **PostgreSQL** | `15+` | Основная БД | - ACID транзакции<br>- JSONB для гибких данных<br>- Полнотекстовый поиск<br>- Репликация |
| **База данных (dev)** | **SQLite** | `3.40+` | Разработка/тестирование | - Файловая БД<br>- Нулевая конфигурация<br>- ACID транзакции |

#### 🔐 **Security & Authentication**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Аутентификация** | **JWT (PyJWT)** | `2.8.0+` | Токены доступа | - HS256 алгоритм<br>- Access/Refresh tokens<br>- Token expiration<br>- Secure headers |
| **Пароли** | **bcrypt** | `4.1.2+` | Хэширование паролей | - Salted hashing<br>- Adaptive complexity<br>- Timing attack protection |
| **CORS** | **FastAPI CORS** | - | Cross-Origin защита | - Configurable origins<br>- Methods & headers<br>- Credentials support |

#### 🤖 **AI & Machine Learning**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **AI Client** | **OpenRouter** | `v1` | Унифицированный AI API | - 100+ моделей<br>- Load balancing<br>- Fallback стратегии<br>- Cost optimization |
| **AI Client** | **OpenAI** | `1.3.0+` | GPT модели | - GPT-4, GPT-3.5<br>- Embeddings<br>- Function calling |
| **AI Client** | **HuggingFace** | `0.19.0+` | Open-source модели | - Inference API<br>- Local models<br>- Custom pipelines |
| **Intent Analysis** | **Custom ML** | - | Классификация намерений | - Rule-based + ML<br>- Confidence scoring<br>- Context awareness |

#### 📢 **External Integrations**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Avito API** | **Avito REST API** | `v1/v2/v3` | Интеграция с Avito | - OAuth 2.0<br>- Items management<br>- Statistics<br>- Messenger API |
| **Avito Messenger** | **Avito Messenger API** | `v1` | Чат интеграция | - Real-time messaging<br>- Webhook support<br>- Chat management<br>- AI responses |

#### 🛠 **Development & Testing**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Тестирование** | **pytest** | `7.4.0+` | Unit/Integration тесты | - Async support<br>- Fixtures<br>- Parametrization<br>- Coverage reports |
| **Тестирование** | **pytest-asyncio** | `0.21.0+` | Async тесты | - Async fixtures<br>- Event loop management |
| **Тестирование** | **httpx** | `0.25.0+` | HTTP клиент для тестов | - Async HTTP calls<br>- Test client<br>- Mock responses |
| **Моки** | **unittest.mock** | - | Моки и стабы | - MagicMock<br>- patch decorators<br>- AsyncMock |

#### 📊 **Monitoring & Observability**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Логирование** | **structlog** | `23.2.0+` | Структурированные логи | - JSON format<br>- Context binding<br>- Multiple outputs<br>- Performance |
| **Метрики** | **prometheus-client** | `0.19.0+` | Метрики Prometheus | - Counters, Gauges<br>- Histograms<br>- Custom metrics<br>- Exposition |
| **Трейсинг** | **OpenTelemetry** | `1.21.0+` | Распределенная трассировка | - Auto instrumentation<br>- Custom spans<br>- Context propagation |

#### 🐳 **DevOps & Deployment**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Контейнеризация** | **Docker** | `24.0+` | Контейнеры | - Multi-stage builds<br>- Non-root user<br>- Security scanning<br>- Compose |
| **WSGI/ASGI** | **uvicorn** | `0.24.0+` | ASGI сервер | - High performance<br>- Auto reload<br>- Workers<br>- SSL support |
| **Process Manager** | **gunicorn** | `21.2.0+` | Production server | - Worker processes<br>- Load balancing<br>- Logging<br>- Monitoring |

#### 📦 **Data Validation & Serialization**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Валидация** | **Pydantic** | `2.5.0+` | Схемы данных | - Type hints<br>- Validation<br>- Serialization<br>- JSON Schema |
| **Валидация** | **email-validator** | `2.1.0+` | Email валидация | - RFC compliance<br>- MX checks<br>- Disposable detection |
| **Парсинг** | **python-multipart** | `0.0.6+` | Form data | - File uploads<br>- Form parsing<br>- Streaming |

#### 🔧 **Utilities & Helpers**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **HTTP Client** | **httpx** | `0.25.0+` | HTTP запросы | - Async/sync<br>- Connection pooling<br>- Timeouts<br>- SSL |
| **Даты/Время** | **python-dateutil** | `2.8.2+` | Работа с датами | - Parsing<br>- Timezones<br>- Calculations |
| **UUID** | **python-ulid** | `2.0.0+` | Уникальные ID | - ULID format<br>- Time-based<br>- Lexicographically sortable |
| **Конфиг** | **python-dotenv** | `1.0.0+` | Переменные окружения | - .env files<br>- Validation<br>- Type casting |

#### 📋 **Code Quality**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Линтер** | **ruff** | `0.1.0+` | Код анализ | - Fast Python linter<br>- Import sorting<br>- Auto-fixes<br>- Rule configuration |
| **Форматтер** | **black** | `23.0+` | Код форматирование | - Opinionated formatting<br>- Line length 88<br>- Consistent style |
| **Type Checker** | **mypy** | `1.7.0+` | Типизация | - Static type checking<br>- Strict mode<br>- Plugin support |
| **Security** | **bandit** | `1.7.0+` | Безопасность кода | - Security issues<br>- CWE mapping<br>- Severity levels |

#### 🔄 **Background Tasks & Queues**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Background Tasks** | **FastAPI BackgroundTasks** | - | Простые задачи | - Fire-and-forget<br>- Dependency injection<br>- Error handling |
| **Task Queue** | **Celery** | `5.3.0+` | Очереди задач | - Distributed tasks<br>- Scheduling<br>- Monitoring<br>- Result backend |
| **Message Broker** | **Redis** | `7.0+` | Кэш и брокер | - Pub/Sub<br>- Key-value store<br>- Persistence<br>- Clustering |

#### 📊 **Database Tools**

| Компонент | Технология | Версия | Назначение | Детали |
|-----------|------------|--------|------------|---------|
| **Миграции** | **alembic** | `1.12.0+` | Схема БД | - Version control<br>- Auto-generation<br>- Rollbacks<br>- Multiple heads |
| **Фабрика** | **factory-boy** | `3.3.0+` | Тестовые данные | - Model factories<br>- Faker integration<br>- Sequences<br>- Traits |
| **Fixtures** | **pytest-fixtures** | - | Тестовые фикстуры | - Database fixtures<br>- API client fixtures<br>- Mock fixtures |

### Структура проекта

```
src/aicrm/
├── core/                    # Конфигурация и инфраструктура
│   ├── config.py           # Основные настройки
│   ├── ai_config.py        # Конфигурация ИИ
│   ├── database.py         # Настройки БД
│   └── dependencies.py     # FastAPI зависимости
├── models/                 # SQLAlchemy модели
│   ├── base.py            # Базовая модель
│   ├── user.py            # Пользователи
│   ├── customer.py        # Клиенты
│   ├── order.py           # Заказы с enum статусов
│   ├── production_step.py # Этапы производства
│   └── communication.py   # Коммуникации
├── services/              # Бизнес-логика
│   ├── ai/               # ИИ сервисы
│   │   ├── client.py     # Унифицированный AI клиент
│   │   └── intent_service.py # Анализ намерений
│   ├── avito_service.py  # Сервис Avito API
│   ├── avito_handler.py  # Обработчик Avito коммуникаций
│   ├── production.py     # Управление производством
│   ├── communication_service.py # Коммуникации
│   └── auth.py           # Аутентификация
├── api/                  # REST API
│   ├── routers/          # Маршруты
│   │   ├── ai.py        # AI эндпоинты
│   │   ├── avito.py     # Avito API эндпоинты
│   │   ├── order.py     # API заказов
│   │   ├── customer.py  # API клиентов
│   │   └── auth.py      # API аутентификации
│   └── schemas/          # Pydantic схемы
│       ├── ai.py        # Схемы ИИ
│       ├── avito.py     # Схемы Avito API
│       ├── order.py     # Схемы заказов
│       └── customer.py  # Схемы клиентов
├── tests/               # Тесты
│   ├── test_avito.py    # Тесты Avito интеграции
│   └── ...             # Другие тесты
└── utils/               # Утилиты
    └── logging.py       # Настройка логирования
```

## Основные модули

### 🔐 Аутентификация (Auth Module)
- Регистрация пользователей
- JWT токены
- Защита эндпоинтов

### 👥 Управление клиентами (Customer Module)
- CRUD операции с клиентами
- Поиск и фильтрация
- Статистика клиентов
- Уровни лояльности

### 📦 Управление заказами (Order Module)
- Создание и управление заказами
- Статусы заказов
- Автоматические расчеты

### 🏭 Производство (Production Module)
- Этапы производства
- Отслеживание прогресса
- Назначение исполнителей

### 💬 Коммуникации (Communication Module)
- Многоканальные коммуникации
- Telegram, Email, Phone, Website
- Логирование взаимодействий

### 🤖 ИИ интеграция (AI Module)
- Анализ намерений
- Генерация ответов
- OpenAI, Anthropic, OpenRouter

### 📢 Avito интеграция (Avito Module)
- **API клиент**: OAuth 2.0 аутентификация, автоматическое обновление токенов
- **Управление объявлениями**: получение списка, информации, обновление цен
- **Статистика**: просмотры, контакты, звонки, аналитика по периодам
- **Продвижение**: применение VAS услуг, управление пакетами
- **Messenger API**: Полная интеграция с Avito Messenger API v1/v2
- **Коммуникации**: обработка сообщений из Avito, автоматические AI ответы
- **Оптимизация**: AI-powered анализ эффективности, рекомендации по ценам
- **Webhook поддержка**: Обработка входящих сообщений и уведомлений

### ✅ Управление задачами (Task Module)
- Канбан доска
- Приоритеты и сроки
- Назначение задач

## 🚀 Быстрый старт

### 1. Клонирование и установка
```bash
git clone <repository-url>
cd aicrm
pip install -e .
```

### 2. Настройка переменных окружения
```bash
# Копируем пример конфигурации
cp src/.env.example src/.env

# Редактируем настройки
nano src/.env
```

**Обязательные переменные:**
```env
# База данных (SQLite для разработки)
DATABASE_URL=sqlite+aiosqlite:///./test.db

# Безопасность
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=true

# ИИ интеграция (для работы AI функций)
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Avito интеграция (для работы с Avito API)
AVITO_CLIENT_ID=your_avito_client_id
AVITO_CLIENT_SECRET=your_avito_client_secret
AVITO_USER_ID=your_avito_user_id
```

### 3. Запуск системы
```bash
# Через скрипт запуска
./start.sh

# Или напрямую через uvicorn
cd src && python3 -c "from aicrm.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)"
```

### 4. Проверка работы
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health
- **Avito health**: http://localhost:8000/avito/health

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | URL базы данных |
| `SECRET_KEY` | - | Ключ для JWT токенов |
| `DEBUG` | `false` | Режим разработки |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `AI_PROVIDER` | `openrouter` | Провайдер ИИ (openrouter/huggingface/openai) |
| `OPENROUTER_API_KEY` | - | Ключ OpenRouter API |
| `HUGGINGFACE_API_KEY` | - | Ключ Hugging Face API |
| `DEFAULT_MODEL` | `deepseek/deepseek-coder:33b-instruct` | Модель ИИ по умолчанию |
| `AVITO_CLIENT_ID` | - | Client ID для Avito API |
| `AVITO_CLIENT_SECRET` | - | Client Secret для Avito API |
| `AVITO_USER_ID` | - | User ID в Avito |

### Конфигурация ИИ провайдеров

#### OpenRouter (рекомендуется)
```env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DEFAULT_MODEL=deepseek/deepseek-coder:33b-instruct
```

#### Hugging Face
```env
AI_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_xxxxxxxxxx
HUGGINGFACE_BASE_URL=https://api-inference.huggingface.co
```

#### OpenAI
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Конфигурация Avito API

#### Получение учетных данных
1. Зарегистрируйтесь в [Avito для бизнеса](https://pro.avito.ru/)
2. Создайте приложение в разделе разработчика
3. Получите Client ID и Client Secret
4. Настройте переменные окружения

```env
AVITO_CLIENT_ID=your_client_id_here
AVITO_CLIENT_SECRET=your_client_secret_here
AVITO_USER_ID=your_numeric_user_id
```

## API Документация

После запуска сервера откройте:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Avito API**: http://localhost:8000/docs#/avito

## 📖 Использование API

### 🤖 Работа с ИИ

#### Анализ намерений клиента
```bash
curl -X POST "http://localhost:8000/ai/analyze-intent" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Хочу заказать печать логотипа на 50 футболках",
    "context": {
      "customer_name": "Иван Петров",
      "previous_orders": 3
    }
  }'
```

**Ответ:**
```json
{
  "intent": "order",
  "response": "Отлично! Я помогу вам оформить заказ на печать логотипа на футболках...",
  "needs_human_intervention": false,
  "suggested_actions": ["create_order_draft", "assign_sales_agent"]
}
```

#### Генерация ответа на вопрос
```bash
curl -X POST "http://localhost:8000/ai/generate-response" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Сколько стоит печать на одной футболке?",
    "context": {"customer_type": "new"}
  }'
```

#### Прямой чат с AI
```bash
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Ты помощник компании по печати"},
      {"role": "user", "content": "Какие материалы вы используете?"}
    ],
    "model": "deepseek/deepseek-coder:33b-instruct",
    "temperature": 0.7
  }'
```

### 📢 Работа с Avito

#### Получение активных объявлений
```bash
curl "http://localhost:8000/avito/items"
```

**Ответ:**
```json
[
  {
    "id": 12345678,
    "title": "Печать логотипов на футболках",
    "status": "active",
    "price": 1500,
    "url": "https://www.avito.ru/moskva/odezhda/pechat_logotipov_na_futbolkah_12345678"
  }
]
```

#### Получение производительности объявления
```bash
curl "http://localhost:8000/avito/items/12345678/performance?days=30"
```

**Ответ:**
```json
{
  "item_id": 12345678,
  "title": "Печать логотипов на футболках",
  "status": "active",
  "url": "https://www.avito.ru/...",
  "stats": {
    "items": [
      {
        "itemId": 12345678,
        "stats": [
          {"date": "2023-11-01", "uniqViews": 45, "uniqContacts": 3},
          {"date": "2023-11-02", "uniqViews": 52, "uniqContacts": 5}
        ]
      }
    ]
  },
  "calls": {
    "items": [
      {
        "itemId": 12345678,
        "days": [
          {"date": "2023-11-01", "calls": 2, "answered": 1}
        ]
      }
    ]
  },
  "vas_active": [
    {"vas_id": "xl", "finish_time": "2023-11-15T00:00:00Z"}
  ]
}
```

#### Получение статистики по объявлениям
```bash
curl -X POST "http://localhost:8000/avito/items/stats" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": [12345678, 87654321],
    "date_from": "2023-11-01",
    "date_to": "2023-11-30",
    "fields": ["uniqViews", "uniqContacts", "uniqFavorites"]
  }'
```

#### Получение аналитики профиля
```bash
curl -X POST "http://localhost:8000/avito/analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2023-11-01",
    "date_to": "2023-11-30",
    "metrics": ["views", "contacts", "favorites"],
    "grouping": "item"
  }'
```

#### Получение цен на услуги продвижения
```bash
curl "http://localhost:8000/avito/items/12345678/vas-prices"
```

**Ответ:**
```json
{
  "prices": [
    {
      "itemId": 12345678,
      "vas": [
        {"slug": "xl", "price": 200, "priceOld": 300},
        {"slug": "highlight", "price": 100, "priceOld": 150},
        {"slug": "x2_1", "price": 50, "priceOld": 70}
      ],
      "stickers": [
        {"id": 1, "title": "Без ДТП", "description": "Подходит для автомобилей"}
      ]
    }
  ]
}
```

#### Применение услуги продвижения
```bash
curl -X POST "http://localhost:8000/avito/items/12345678/vas" \
  -H "Content-Type: application/json" \
  -d '{
    "slugs": ["xl", "x2_1"],
    "stickers": [1]
  }'
```

**Ответ:**
```json
{
  "operationId": 987654321
}
```

#### Обновление цены объявления
```bash
curl -X PUT "http://localhost:8000/avito/items/12345678/price" \
  -H "Content-Type: application/json" \
  -d '{"price": 1800}'
```

#### AI оптимизация цены
```bash
curl -X POST "http://localhost:8000/avito/items/12345678/optimize-price"
```

**Ответ:**
```json
{
  "item_id": 12345678,
  "current_conversion": 0.067,
  "total_views": 1500,
  "total_contacts": 100,
  "recommendation": "Цена в оптимальном диапазоне"
}
```

#### Быстрое продвижение объявления
```bash
curl -X POST "http://localhost:8000/avito/items/12345678/promote" \
  -H "Content-Type: application/json" \
  -d '{
    "service_slug": "x5_7",
    "stickers": [1, 2]
  }'
```

#### Получение статистики звонков
```bash
curl -X POST "http://localhost:8000/avito/calls/stats" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2023-11-01",
    "date_to": "2023-11-30",
    "item_ids": [12345678]
  }'
```

#### Обработка входящего сообщения из Avito
```bash
curl -X POST "http://localhost:8000/avito/messages/incoming" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "chat_123",
    "user_id": "user_456",
    "message": {
      "text": "Здравствуйте, сколько стоит печать на 100 футболках?",
      "timestamp": "2023-11-12T10:30:00Z"
    },
    "item_id": 12345678
  }'
```

### � Avito Messenger API

#### Получение списка чатов
```bash
curl "http://localhost:8000/avito/messenger/v1/accounts/123/chats"
```

**Ответ:**
```json
[
  {
    "chat_id": "chat_123",
    "customer_name": "Иван Петров",
    "customer_email": "ivan@example.com",
    "last_message": "Здравствуйте, сколько стоит печать?",
    "last_message_at": "2025-11-12T14:32:39.308046",
    "message_count": 5,
    "ai_enabled": true,
    "unread_count": 0
  }
]
```

#### Получение информации о чате
```bash
curl "http://localhost:8000/avito/messenger/v1/accounts/123/chats/chat_123"
```

**Ответ:**
```json
{
  "id": 1,
  "chat_id": "chat_123",
  "customer_id": 1,
  "ai_enabled": true,
  "ai_model": "deepseek/deepseek-coder:33b-instruct",
  "ai_temperature": 70,
  "notifications_enabled": true,
  "message_count": 5,
  "last_message_at": "2025-11-12T14:32:39.308046",
  "last_ai_response_at": null,
  "created_at": "2025-11-12T14:32:39.291383",
  "updated_at": "2025-11-12T14:32:48.115000"
}
```

#### Обновление настроек чата
```bash
curl -X PUT "http://localhost:8000/avito/messenger/v1/accounts/123/chats/chat_123" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_enabled": false,
    "notifications_enabled": true,
    "ai_temperature": 80
  }'
```

#### Получение истории сообщений чата
```bash
curl "http://localhost:8000/avito/messenger/v1/accounts/123/chats/chat_123/messages?limit=20&offset=0"
```

**Ответ:**
```json
[
  {
    "id": 10,
    "chat_id": "chat_123",
    "direction": "incoming",
    "message_content": "Здравствуйте, сколько стоит печать на футболках?",
    "intent": "pricing_inquiry",
    "ai_generated": false,
    "created_at": "2025-11-12T14:30:00.000000"
  },
  {
    "id": 11,
    "chat_id": "chat_123",
    "direction": "outgoing",
    "message_content": "Здравствуйте! Стоимость печати зависит от тиража и сложности дизайна...",
    "intent": "response",
    "ai_generated": true,
    "created_at": "2025-11-12T14:30:15.000000"
  }
]
```

#### Отправка сообщения в чат
```bash
curl -X POST "http://localhost:8000/avito/messenger/v1/accounts/123/chats/chat_123/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Здравствуйте! Мы можем напечатать логотип на футболках. Стоимость от 150 руб/шт при тираже от 50 шт.",
    "use_ai": false
  }'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Сообщение отправлено"
}
```

#### Отправка AI-сгенерированного сообщения
```bash
curl -X POST "http://localhost:8000/avito/messenger/v1/accounts/123/chats/chat_123/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Расскажите подробнее о вашем заказе",
    "use_ai": true
  }'
```

#### Получение статистики мессенджера
```bash
curl "http://localhost:8000/avito/messenger/stats"
```

**Ответ:**
```json
{
  "total_chats": 15,
  "active_chats": 8,
  "ai_enabled_chats": 12,
  "total_messages": 245,
  "ai_messages": 89,
  "avg_response_time": null
}
```

#### Включение/выключение AI для чата
```bash
curl -X POST "http://localhost:8000/avito/messenger/chats/chat_123/toggle-ai" \
  -H "Content-Type: application/json" \
  -d 'true'
```

**Ответ:**
```json
{
  "success": true,
  "ai_enabled": true
}
```

### 🔗 Webhook интеграция

#### Настройка webhook для получения уведомлений
```bash
curl -X POST "https://api.avito.ru/messenger/v1/webhook" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/avito/webhook"
  }'
```

#### Обработка webhook уведомлений
```python
# Пример обработчика webhook
@app.post("/avito/webhook")
async def handle_avito_webhook(webhook_data: dict):
    """
    Обработка уведомлений от Avito
    """
    event_type = webhook_data.get("type")

    if event_type == "message":
        # Новое сообщение в чате
        await process_new_message(webhook_data["payload"])
    elif event_type == "chat_read":
        # Чат прочитан
        await mark_chat_as_read(webhook_data["payload"])

    return {"status": "ok"}
```

### 📊 Мониторинг Avito интеграции

#### Проверка здоровья всех компонентов
```bash
# Общая проверка здоровья
curl "http://localhost:8000/health"

# Проверка здоровья Avito интеграции
curl "http://localhost:8000/avito/health"

# Проверка подключения к Avito API
curl "http://localhost:8000/avito/status"
```

#### Метрики производительности
```bash
# Статистика API запросов
curl "http://localhost:8000/metrics/avito"

# Логи интеграции
tail -f logs/avito_integration.log
```

### �📦 Управление заказами

#### Создание заказа (с автоматическим workflow)
```bash
curl -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "items": [
      {
        "product_type": "футболка",
        "quantity": 50,
        "size": "M",
        "color": "белый"
      }
    ],
    "requirements": "Печать логотипа на груди, полноцветная",
    "deadline": "2025-12-01T00:00:00Z",
    "notes": "Срочный заказ"
  }'
```

**Автоматически создается:**
- Заказ со статусом `IN_DESIGN`
- 5 этапов производства:
  1. Подготовка макета
  2. Подготовка материалов
  3. Печать
  4. Пост-обработка
  5. Контроль качества

#### Получение прогресса производства
```bash
curl "http://localhost:8000/orders/1/production-progress"
```

**Ответ:**
```json
{
  "total_steps": 5,
  "completed_steps": 2,
  "in_progress_steps": 1,
  "pending_steps": 2,
  "progress": 50.0,
  "current_step": "Печать",
  "next_step": "Пост-обработка",
  "is_overdue": false,
  "steps": [
    {
      "id": 1,
      "name": "Подготовка макета",
      "status": "completed",
      "sequence_number": 1,
      "progress_percentage": 100.0
    }
  ]
}
```

#### Управление этапами производства
```bash
# Запуск этапа
curl -X POST "http://localhost:8000/orders/1/production-steps/3/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# Завершение этапа
curl -X POST "http://localhost:8000/orders/1/production-steps/3/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "actual_hours": 6.5,
    "notes": "Печать выполнена качественно"
  }'
```

#### Получение просроченных задач
```bash
curl "http://localhost:8000/orders/production/overdue"
```

**Ответ:**
```json
{
  "overdue_steps": [
    {
      "step_id": 5,
      "step_name": "Контроль качества",
      "order_id": 2,
      "customer_name": "ООО Рога и Копыта",
      "overdue_hours": 12.5,
      "started_at": "2025-11-10T08:00:00Z"
    }
  ],
  "count": 1
}
```

### 👥 Работа с клиентами

#### Создание клиента
```bash
curl -X POST "http://localhost:8000/customers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван Петров",
    "email": "ivan@example.com",
    "phone": "+7-999-123-45-67",
    "company": "ООО Пример",
    "preferences": {
      "preferred_contact": "email",
      "budget_range": "medium"
    }
  }'
```

#### Поиск клиентов
```bash
curl "http://localhost:8000/customers/search/?query=петров&page=1&per_page=10"
```

## 🔍 Мониторинг и отладка

### Проверка здоровья системы
```bash
curl "http://localhost:8000/health"
# {"status": "healthy"}
```

### Проверка здоровья Avito интеграции
```bash
curl "http://localhost:8000/avito/health"
# {"status": "ok", "service": "avito_integration"}
```

### Просмотр логов
```bash
# В режиме разработки - цветные логи в консоль
# В продакшене - JSON логи для систем логирования
tail -f /var/log/aicrm/app.log
```

### Метрики производительности
```bash
# Prometheus метрики (если настроено)
curl "http://localhost:8000/metrics"
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src/aicrm --cov-report=html

# Конкретный модуль
pytest src/aicrm/tests/test_ai.py
pytest src/aicrm/tests/test_avito.py
```

### Примеры тестовых сценариев
```python
# Тест создания заказа с workflow
def test_order_creation_with_workflow():
    # Создать клиента
    # Создать заказ
    # Проверить автоматическое создание этапов
    # Проверить статусы и прогресс
    pass

# Тест AI анализа намерений
def test_ai_intent_analysis():
    # Отправить сообщение
    # Проверить определение намерения
    # Проверить генерацию ответа
    pass

# Тест Avito API клиента
def test_avito_client_token_refresh():
    # Проверить получение токена
    # Проверить автоматическое обновление
    # Проверить обработку ошибок
    pass

# Тест применения VAS услуг
def test_avito_vas_application():
    # Создать мок объявления
    # Применить услугу продвижения
    # Проверить успешное выполнение
    pass
```

## 🚨 Устранение неполадок

### Проблема: "Module not found"
```bash
# Установить зависимости
pip install -e .

# Проверить PYTHONPATH
export PYTHONPATH=/app/src:$PYTHONPATH
```

### Проблема: "Database connection failed"
```bash
# Проверить URL базы данных
echo $DATABASE_URL

# Для SQLite - файл должен быть доступен
ls -la test.db

# Для PostgreSQL - проверить подключение
psql $DATABASE_URL -c "SELECT 1;"
```

### Проблема: "AI API key not configured"
```bash
# Проверить переменные окружения
echo $AI_PROVIDER
echo $OPENROUTER_API_KEY

# Проверить статус AI
curl "http://localhost:8000/ai/status"
```

### Проблема: "Avito API authentication failed"
```bash
# Проверить учетные данные Avito
echo $AVITO_CLIENT_ID
echo $AVITO_CLIENT_SECRET
echo $AVITO_USER_ID

# Проверить статус Avito интеграции
curl "http://localhost:8000/avito/health"

# Проверить логи на ошибки авторизации
grep "Avito" /var/log/aicrm/app.log
```

### Проблема: "Avito rate limit exceeded"
```
# Avito API имеет ограничения:
# - 500 запросов в минуту для получения информации об объявлениях
# - 150 запросов в минуту для обновления цен
# - 25 запросов в минуту для получения списка объявлений
#
# Решение: реализовать кэширование и очередь запросов
```

### Проблема: "Permission denied"
```bash
# Исправить права доступа
chmod +x start.sh
chown -R www-data:www-data /app/data
```

## 📈 Производительность

### Оптимизации
- **Async/Await**: Все операции асинхронные
- **Connection pooling**: Переиспользование соединений БД
- **Caching**: Redis для сессий и кэширования
- **Rate limiting**: Защита от перегрузки API
- **Background tasks**: Асинхронная обработка тяжелых операций
- **Indexes**: Оптимизированные индексы БД

### Рекомендации по масштабированию
- **Horizonal scaling**: Запуск нескольких инстансов
- **Load balancer**: Nginx или Traefik
- **Database**: PostgreSQL с репликацией
- **Cache**: Redis кластер
- **CDN**: Для статических ресурсов
- **Queue**: Celery для фоновых задач

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code style
```bash
# Форматирование
black src/
ruff src/ --fix

# Типизация
mypy src/

# Тесты
pytest --cov=src/aicrm --cov-report=term-missing
```

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE) для подробностей.

## 📞 Поддержка

- **Документация**: [Wiki](https://github.com/your-org/aicrm/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/aicrm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/aicrm/discussions)

---

**AI CRM System** - ваш надежный партнер в автоматизации бизнеса печати! 🎨🤖

## Структура проекта

```
src/aicrm/
├── core/           # Конфигурация и база данных
├── models/         # SQLAlchemy модели
├── api/
│   ├── routers/    # API маршруты
│   └── schemas/    # Pydantic схемы
├── services/       # Бизнес логика
├── utils/          # Утилиты
└── tests/          # Тесты
```

## Разработка

### Добавление нового модуля
1. Создать модель в `models/`
2. Создать схемы в `api/schemas/`
3. Реализовать сервис в `services/`
4. Создать роутер в `api/routers/`
5. Подключить роутер в `main.py`

### Тестирование
```bash
pytest
```

### Линтинг и форматирование
```bash
black src/
ruff src/
mypy src/
```

## Деплой

### Docker
```bash
docker build -t aicrm .
docker run -p 8000:8000 aicrm
```

### Kubernetes
Конфигурации в `k8s/` директории.

## Мониторинг

- **Prometheus** - метрики
- **Grafana** - дашборды
- **OpenTelemetry** - трейсинг
- **Structlog** - структурированное логирование

## Безопасность

- JWT аутентификация
- CORS защита
- Rate limiting
- SQL инъекции предотвращены ORM
- Валидация входных данных
- OAuth 2.0 для Avito API

## Лицензия

MIT License
