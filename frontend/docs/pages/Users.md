# Управление пользователями (Users)

## Обзор
Страница управления пользователями предоставляет полный CRUD интерфейс для администрирования пользователей системы AI CRM.

## Функциональность

### 📋 Просмотр пользователей
- **Список пользователей** в виде карточек с основной информацией
- **Поиск** по email, имени и роли
- **Фильтрация** по статусу активности и роли
- **Пагинация** для больших списков

### 👤 Детали пользователя
- **Просмотр полной информации** о пользователе
- **Статус аккаунта** (активен/неактивен)
- **Роль в системе** (user/manager/admin)
- **Дата создания и обновления**
- **Супер администратор** статус

### ➕ Создание пользователя
- **Регистрация нового пользователя**
- **Установка роли** (user/manager/admin)
- **Настройка статуса** (активен по умолчанию)
- **Установка пароля**

### ✏️ Редактирование пользователя
- **Изменение личных данных** (email, имя)
- **Смена роли** в системе
- **Изменение статуса** аккаунта
- **Смена пароля** (опционально)

### 🗑️ Удаление пользователя
- **Безопасное удаление** с подтверждением
- **Проверка зависимостей** (нельзя удалить пользователя с активными процессами)

## API Endpoints

```typescript
GET    /users/           // Список пользователей
POST   /users/           // Создание пользователя
GET    /users/{id}       // Получение пользователя
PATCH  /users/{id}       // Обновление пользователя
DELETE /users/{id}       // Удаление пользователя
GET    /auth/me          // Текущий пользователь
```

## Права доступа

- **Администраторы**: полный доступ ко всем функциям
- **Менеджеры**: просмотр пользователей, ограниченное редактирование
- **Пользователи**: только просмотр своего профиля

## UX/UI особенности

- **Адаптивный дизайн** для мобильных устройств
- **Интуитивные иконки** для разных ролей
- **Цветовые индикаторы** статуса
- **Модальные окна** для создания/редактирования
- **Подтверждения** для опасных действий

## Безопасность

### 🔐 Аутентификация и авторизация
- **JWT токены** с HS256 алгоритмом и 24-часовым сроком действия
- **Bcrypt хэширование** паролей с солью и адаптивной сложностью
- **Email верификация** с 32-символьными URL-safe токенами
- **Многоуровневая авторизация** - superuser/admin/manager/user роли

### 🛡️ Защита от атак
- **CSRF защита** для всех форм и API endpoints
- **Rate limiting** через Redis с настраиваемыми лимитами
- **SQL injection предотвращение** через SQLAlchemy ORM
- **XSS защита** через input sanitization и CSP headers

### 📊 Аудит и мониторинг
- **Структурированное логирование** всех операций с пользователями
- **Audit trail** для изменений ролей и прав доступа
- **Real-time monitoring** подозрительной активности
- **Automated alerts** на security incidents

### 🔑 Многофакторная аутентификация (MFA)
- **OTP через email** для чувствительных операций
- **Device fingerprinting** для обнаружения подозрительной активности
- **Session management** с возможностью удаленного logout
- **Automatic logout** при подозрительной активности

## Связанные компоненты

- `ProtectedRoute` - защита маршрута
- `apiService.getUsers()` - API клиент
- `Sidebar` - навигация
- `Header` - верхняя панель

## Архитектурный анализ

### Домен бизнеса
- **Multi-tenant система** с изоляцией пользователей по компаниям
- **RBAC (Role-Based Access Control)** с cascading permissions
- **Audit compliance** для enterprise клиентов
- **GDPR compliance** для обработки персональных данных

### Техническая архитектура
- **SQLAlchemy 2.0** с async/await native support
- **Pydantic v2** для validation и type safety
- **Redis-backed sessions** для distributed deployment
- **PostgreSQL** для enterprise-grade data persistence

### Производительность
- **Connection pooling** через SQLAlchemy
- **Redis caching** для frequent user lookups
- **Lazy loading** для связанных данных
- **Database indexes** на email и role fields

## Аналитика и метрики

### 📊 User Engagement
- **Active users** vs total users ratio
- **Role distribution** analytics
- **Registration conversion** rates
- **Session duration** tracking

### 🔒 Security Metrics
- **Failed login attempts** monitoring
- **Password reset frequency**
- **Email verification rates**
- **Suspicious activity detection**

### 🎯 Business KPIs
- **User growth rate** по месяцам
- **Churn rate** analysis
- **Feature adoption** по ролям
- **Support ticket volume**

## Рекомендации по улучшению

### 🚀 Scalability
- **Implement database sharding** для 100k+ пользователей
- **Add read replicas** для high-traffic scenarios
- **Implement user data partitioning** по географическим регионам
- **Consider microservices split** для user management

### 🔐 Security Enhancements
- **OAuth 2.0 integration** для third-party logins
- **Hardware security keys** (FIDO2/WebAuthn)
- **Biometric authentication** для mobile devices
- **Zero-trust architecture** implementation

### 📊 Advanced Analytics
- **ML-powered user behavior analysis**
- **Predictive churn prevention**
- **Personalized onboarding flows**
- **Automated role recommendations**

### 🔧 Developer Experience
- **API versioning** для backward compatibility
- **OpenAPI/Swagger** documentation generation
- **Comprehensive test coverage** (>95%)
- **CI/CD pipelines** с automated testing

## Мониторинг и alerting

### 🚨 Critical Alerts
- **Admin role changes** - immediate notification
- **Bulk user operations** - security review required
- **Failed authentication spikes** - potential attack
- **Data export requests** - compliance tracking

### 📈 Performance Monitoring
- **API response times** по endpoints
- **Database query performance**
- **Memory usage** trends
- **Error rates** по компонентам

## Compliance и аудит

### 📋 Regulatory Requirements
- **GDPR Article 17** - right to erasure
- **ISO 27001** - information security management
- **SOX compliance** для financial data
- **HIPAA** если health data involved

### 🏛️ Audit Trails
- **Immutable logs** всех user operations
- **Compliance reporting** automated generation
