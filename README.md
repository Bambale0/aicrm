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

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Backend** | FastAPI | 0.104+ | REST API, асинхронная обработка |
| **ORM** | SQLAlchemy | 2.0+ | Работа с базой данных |
| **База данных** | PostgreSQL/SQLite | - | Хранение данных |
| **Аутентификация** | JWT | - | Безопасность API |
| **Валидация** | Pydantic | 2.0+ | Схемы данных |
| **ИИ** | OpenAI API | 1.0+ | Генерация текста |
| **Avito API** | Avito REST API | v1/v2 | Интеграция с Avito |
| **Логирование** | Structlog | 23.0+ | Структурированные логи |
| **Контейнеризация** | Docker | - | Деплой и масштабирование |

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
- **Коммуникации**: обработка сообщений из Avito, автоматические ответы
- **Оптимизация**: AI-powered анализ эффективности, рекомендации по ценам

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

### 📦 Управление заказами

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
