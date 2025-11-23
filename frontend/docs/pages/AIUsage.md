# Статистика использования AI (AIUsage)

## Обзор
Страница статистики AI предоставляет enterprise-grade анализ использования искусственного интеллекта в системе AI CRM, включая токены, запросы, расходы и производительность. Обновлено на 21 ноября 2025 года с поддержкой OpenRouter, Anthropic и локальных моделей.

## Функциональность

### 📊 Enterprise Analytics Dashboard
- **Real-time мониторинг** использования AI (обновление каждые 30 секунд)
- **Многоуровневая статистика** - месячная, недельная, дневная разбивка
- **300+ моделей поддержки** через OpenRouter API
- **Стоимостный анализ** с оптимизацией расходов
- **Performance метрики** - время отклика, успешность запросов

### 📈 Детальная разбивка по моделям
- **OpenRouter модели** - DeepSeek, GPT-4, Claude 3, Llama 3 (70B/405B)
- **Локальные модели** - через HuggingFace inference API
- **Гибридный роутинг** - автоматический выбор оптимальной модели
- **Fallback стратегии** - переключение при недоступности
- **Cost optimization** - автоматический выбор по цене/качеству

### 📅 Исторические данные и тренды
- **Интерактивные графики** с Recharts (production-ready)
- **Drill-down анализ** по часам/дням/неделям/месяцам
- **Тренды потребления** с предиктивной аналитикой
- **Alerts на аномалии** использования
- **Экспорт данных** в CSV/PDF для отчетности

### 💰 Расходный анализ
- **Бюджетный контроль** с enterprise лимитами
- **ROI анализ** AI инвестиций
- **Сравнение моделей** по эффективности
- **Прогноз расходов** на основе трендов
- **Автоматическая оптимизация** выбора моделей

## Структура данных

```typescript
interface AIUsageStats {
  period: {
    year: number;
    month: number;
    month_year: string;
  };
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_requests: number;
  unique_models: number;
  model_breakdown: Array<{
    model: string;
    tokens: number;
    requests: number;
  }>;
}
```

## Метрики использования

### 🔢 Токены
- **Prompt tokens**: Входящие токены (запросы пользователя)
- **Completion tokens**: Исходящие токены (ответы AI)
- **Total tokens**: Сумма входящих и исходящих

### 📊 Запросы
- **Total requests**: Общее количество API вызовов
- **Requests per model**: Распределение по моделям
- **Success rate**: Процент успешных запросов

### 💰 Расходы
- **Стоимость по тарифам** провайдеров
- **Прогноз на следующий месяц**
- **Сравнение с бюджетом**

## Модели ИИ

### 🤖 GPT-4
- **Стоимость**: $0.03/1K input, $0.06/1K output
- **Контекст**: 8192 токенов
- **Использование**: Комплексные задачи

### ⚡ GPT-3.5 Turbo
- **Стоимость**: $0.0015/1K input, $0.002/1K output
- **Контекст**: 4096 токенов
- **Использование**: Быстрые ответы

### 🎯 Claude 3
- **Стоимость**: $0.015/1K input, $0.075/1K output
- **Контекст**: 100K токенов
- **Использование**: Анализ документов

## UX/UI особенности

- **Интерактивные графики** (плейсхолдер для Chart.js)
- **Фильтры по периоду** (текущий/прошлый/3 месяца/год)
- **Экспорт данных** в CSV
- **Real-time обновления**

## Оптимизация расходов

### 💡 Рекомендации
- **Используйте GPT-3.5** для простых задач
- **Кешируйте частые запросы**
- **Оптимизируйте промпты**
- **Мониторьте использование** по пользователям

### 🎯 Лимиты и алерты
- **Бюджетные ограничения**
- **Уведомления о превышении**
- **Автоматическое отключение** при лимите

## Интеграция с системой

### 👥 Пользователи
```typescript
// Статистика по пользователям
user.usage_tokens: number
user.usage_cost: number
```

### 🤖 AI Manager
```typescript
// Связь с настройками AI
ai_settings.default_model → usage.model
ai_settings.temperature → usage.context
```

### 📧 Email
```typescript
// AI в email маркетинге
email.ai_generated: boolean
email.tokens_used: number
```

## Производительность

- **Кеширование статистики** на 5-10 минут
- **Агрегация данных** на сервере
- **Оптимизация запросов** к внешним API
- **Background обновления**

## Безопасность

- **Шифрование** API ключей
- **Аудит использования** AI
- **Ограничение доступа** к статистике
- **Rate limiting** для API вызовов

## Мониторинг

### 📊 Dashboard метрики
- **Текущий расход** в реальном времени
- **Тренды использования**
- **Сравнение с предыдущими периодами**

### 🚨 Алерты
- **Превышение бюджета**
- **Высокое потребление** токенов
- **Ошибки API** провайдеров

## Разработка и тестирование

### 🧪 Тестирование
- **Интеграционные тесты** API
- **Load testing** для высокой нагрузки

### 📈 Аналитика
- **A/B тестирование** моделей
- **ROI анализ** использования AI
- **Оптимизация промптов**

## Архитектурный анализ AI Usage

### 🤖 AI-First Architecture
- **Multi-provider orchestration** - OpenRouter, OpenAI, HuggingFace, Anthropic
- **Intelligent routing** - automatic model selection based on cost/performance
- **Fallback strategies** - graceful degradation при недоступности providers
- **Real-time cost monitoring** - per-request token accounting

### 🏗️ Enterprise Observability
- **Distributed tracing** через OpenTelemetry
- **Metrics aggregation** в Prometheus
- **Centralized logging** через structlog
- **Real-time alerting** на anomalies

### 📊 Data Architecture
- **PostgreSQL aggregation** для monthly reports
- **Redis caching** для real-time metrics
- **Time-series optimization** для historical data
- **Compression algorithms** для storage efficiency

## Аналитика и метрики

### 🎯 AI Performance KPIs
- **Token efficiency** - tokens per task completion
- **Cost per interaction** - ROI по каналам коммуникации
- **Model accuracy comparison** - quality metrics по моделям
- **Response time distribution** - latency percentiles

### 💰 Financial Analytics
- **Cost optimization algorithms** - automatic model switching
- **Predictive usage analytics** - forecast-based scaling
- **Auto-scaling patterns** - dynamic resource allocation
- **Budget compliance tracking** - enterprise governance

### 🔍 Usage Pattern Analysis
- **Peak usage identification** - capacity planning
- **Seasonal trend analysis** - predictive scaling
- **Anomaly detection** - fraud prevention
- **User behavior clustering** - personalization optimization

## Рекомендации по улучшению

### 🚀 Scalability Enhancements
- **Implement model sharding** для high-throughput scenarios
- **Add edge caching** для global distribution
- **Consider serverless AI** для cost optimization
- **Implement model warm-up** strategies

### 🤖 AI Optimization
- **Dynamic model selection** based on prompt complexity
- **Context-aware routing** для specialized domains
- **Fine-tuned models** для specific use cases
- **Federated learning** для privacy-preserving optimization

### 📊 Advanced Monitoring
- **Real-time cost dashboards** per department
- **Predictive alerting** на usage spikes
- **Automated optimization** recommendations
- **Integration with APM tools**

### 🔧 Technical Debt
- **API rate limiting** improvement per provider
- **Error handling standardization**
- **Telemeta instrumentation** для all AI calls
- **Caching strategy optimization**

## Compliance и регуляции

### 📋 AI Governance
- **Model transparency** logs для regulatory compliance
- **Bias detection algorithms** для ethical AI
- **Data provenance tracking** для audit trails
- **Explainability frameworks** для business decisions

### 🛡️ Security Measures
- **API key rotation** automation
- **Request encryption** in transit and at rest
- **Access control** per user/per model
- **Audit logging** всех AI interactions

### 🎯 Business Continuity
- **Multi-region failover** для AI providers
- **Local model caching** при network failures
- **Graceful degradation** strategies
- **SLA monitoring** per provider

## Будущие инновации

### 🚀 Emerging Technologies
- **Multi-modal AI** integration (text, image, voice)
- **Real-time translation** для global expansion
- **Context-aware personalization** through ML
- **Autonomous optimization** via reinforcement learning

### 📈 Predictive Features
- **Demand forecasting** для AI resource planning
- **Automated prompt engineering** через GANs
- **Sentiment analysis** для conversation optimization
- **Churn prediction** based on usage patterns

### 🔗 Ecosystem Integration
- **Blockchain verification** для AI-generated content
- **IoT sensor integration** для smart automation
- **5G edge computing** для ultra-low latency
