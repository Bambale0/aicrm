# 🎯 Система Маркетинговых Кампаний с AI

## Обзор

Реализована полнофункциональная система маркетинговых кампаний с индивидуальными AI настройками. Каждая кампания может иметь свои собственные API токены OpenRouter/OpenAI/HuggingFace и кастомные настройки для работы с AI.

## 🚀 Ключевые Возможности

### ✅ Реализованная Функциональность

- **Индивидуальные AI токены для каждой кампании**
  - Поддержка OpenRouter, OpenAI, HuggingFace
  - Хранение API ключей в базе данных
  - Изоляция токенов между кампаниями

- **Кастомные AI настройки кампании**
  - Кастомные промпты для каждой кампании
  - Настройка целевой аудитории и стиля общения
  - Индивидуальные температуры и лимиты токенов
  - Лимиты для биллинга (дневные/месячные)

- **AI API эндпоинты для кампаний**
  - `/ai/campaigns/{id}/chat` - чат с учетом настроек кампании
  - `/ai/campaigns/{id}/analyze-intent` - анализ намерения с контекстом кампании

- **Управление кампаниями через API**
  - CRUD операции для кампаний
  - Управление AI настройками кампаний
  - Получение статистики кампаний

## 📊 Архитектура Базы Данных

### Таблицы

```sql
-- Маркетинговые кампании
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI настройки кампаний
CREATE TABLE campaign_ai_settings (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    provider VARCHAR(50) DEFAULT 'openrouter', -- openrouter, openai, huggingface

    -- API ключи
    openrouter_api_key TEXT,
    openai_api_key TEXT,
    huggingface_api_key TEXT,

    -- Модели и параметры
    default_model VARCHAR(255) DEFAULT 'deepseek/deepseek-chat-v3.1',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,

    -- Настройки кампании
    custom_prompt TEXT,
    target_audience TEXT,
    brand_voice TEXT,

    -- Лимиты для биллинга
    daily_token_limit INTEGER DEFAULT 10000,
    monthly_token_limit INTEGER DEFAULT 300000,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Расширение ai_usage для учета кампаний
ALTER TABLE ai_usage ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id);
```

## 🔌 API Endpoints

### Campaign Management

```
POST   /api/campaigns/                    # Создать кампанию
GET    /api/campaigns/                    # Получить все кампании
GET    /api/campaigns/{id}               # Получить кампанию по ID
PUT    /api/campaigns/{id}               # Обновить кампанию
DELETE /api/campaigns/{id}               # Удалить кампанию

PUT    /api/campaigns/{id}/ai-settings    # Обновить AI настройки кампании
GET    /api/campaigns/{id}/ai-settings    # Получить AI настройки кампании
```

### AI Operations with Campaigns

```
POST /api/ai/campaigns/{id}/analyze-intent  # Анализ намерения через кампанию
POST /api/ai/campaigns/{id}/chat           # Чат через кампанию
```

### Примеры Использования

#### 1. Создание кампании
```bash
curl -X POST "http://localhost:8000/api/campaigns/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Зимняя акция на печать",
    "description": "Акция на новогоднюю продукцию",
    "organization_id": 1
  }'
```

#### 2. Настройка AI для кампании
```bash
curl -X PUT "http://localhost:8000/api/campaigns/1/ai-settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "default_model": "deepseek/deepseek-chat-v3.1",
    "provider": "openrouter",
    "openrouter_api_key": "sk-or-v1-your-api-key",
    "temperature": 0.8,
    "max_tokens": 1200,
    "custom_prompt": "Ты - менеджер продаж зимней акции. Убеждай клиентов оформить заказ на новогоднюю продукцию.",
    "target_audience": "Розничные покупатели",
    "brand_voice": "Дружелюбный и праздничный",
    "daily_token_limit": 10000
  }'
```

#### 3. AI чат через кампанию
```bash
curl -X POST "http://localhost:8000/api/ai/campaigns/1/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Здравствуйте! Хочу заказать печать логотипов на шапках к Новому году."
      }
    ],
    "temperature": 0.8,
    "max_tokens": 500
  }'
```

## 🎯 Бизнес-Полза

### Изоляция AI Токенов
- **Безопасность**: Каждый токен привязан к конкретной кампании
- **Биллинг**: Возможность учета расходов по кампаниям
- **Контроль**: Админ может ограничивать использование AI

### Кастомные Настройки AI
- **Брендинг**: Каждая кампания имеет свой стиль общения
- **Эффективность**: Оптимизация промптов под конкретную аудиторию
- **Персонализация**: Личный подход к каждому клиенту кампании

### Технические Преимущества
- **Масштабируемость**: Архитектура на микросервисах
- **Мониторинг**: Отслеживание использования AI по кампаниям
- **Резервное копирование**: Fallback на глобальные настройки

## 🛠️ Быстрый Старт

### 1. Создание таблиц
```bash
cd backend
python create_campaigns_table.py
```

### 2. Запуск сервера
```bash
cd backend
python -m uvicorn src.aicrm.main:app --host 0.0.0.0 --port 8000
```

### 3. Тестирование
```bash
python test_campaign_ai.py
```

### 4. OpenAPI Документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📈 Логика Работы

### 1. Запрос к AI через кампанию
```
Клиент → API Gateway → Campaign Router → AI Router (с campaign_id)
                                      ↓
                         Проверка настройки кампании
                                      ↓
                         AI Client с токеном кампании → AI Provider
                                      ↓
                         Ответ с учетом контекста кампании
```

### 2. Контекст кампании
- Целевая аудитория и бренд-войс из настроек
- Кастомный промпт кампании
- Лимиты токенов для биллинга
- Отдельный токен для аутентификации

### 3. Fallback логика
- Если у кампании нет своих настроек → глобальные настройки AI
- Если API кампании недоступен → резервный API
- Если превышены лимиты → ошибка с предложением пополнить баланс

## 🔧 Конфигурация

### Переменные окружения
```env
# Глобальные AI настройки (fallback)
OPENROUTER_API_KEY=sk-or-v1-global-key
OPENAI_API_KEY=sk-global-key

# Настройки базы данных
DATABASE_URL=postgresql://user:pass@localhost:5432/aicrm

# Настройки Redis для кеширования
REDIS_URL=redis://localhost:6379/0
```

## 🎨 Frontend Интеграция

### React Hooks для работы с кампаниями

```typescript
// Получение списка кампаний
const { data: campaigns } = useCampaigns();

// Создание кампании
const createCampaign = useCreateCampaign();
const { mutate: createCampaignMutation } = createCampaign;

// Настройка AI кампании
const updateAISettings = useUpdateAISettings(1); // campaign ID
const { mutate: updateAISettingsMutation } = updateAISettings;

// AI чат через кампанию
const campaignChat = useCampaignChat(1);
const { mutate: sendMessage } = campaignChat;
```

## 🚀 Future Enhancements

- [ ] Веб-интерфейс для управления кампаниями
- [ ] Аналитика использования AI по кампаниям
- [ ] Интеграция с платежными системами для баланса токенов
- [ ] A/B тестирование промптов кампаний
- [ ] Notification о превышении лимитов

## 📝 Контрибьютинг

1. Fork проект
2. Создайте feature branch (`git checkout -b feature/campaign-ai-improvement`)
3. Commit изменения (`git commit -m 'Add some improvement'`)
4. Push в branch (`git push origin feature/campaign-ai-improvement`)
5. Создайте Pull Request

---

**Создано с ❤️ для AICRM системы | AI-powered Marketing Campaigns**
