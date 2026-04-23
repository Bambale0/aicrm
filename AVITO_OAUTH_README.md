# Реализация OAuth авторизации Avito API

## Обзор

В проект добавлена поддержка двух типов авторизации Avito API:

1. **Client Credentials** - для доступа к собственным данным
2. **Authorization Code** - для доступа к данным других пользователей через приложения

## Архитектура

### Основные компоненты

- `AvitoClient` - HTTP клиент с поддержкой обоих типов авторизации
- `AvitoAuthService` - сервис управления токенами и OAuth flow
- Новые API endpoints для авторизации
- Расширенные Pydantic схемы для OAuth

### Схемы данных

#### Основные схемы авторизации:
- `AvitoAuthType` - enum типов авторизации
- `AvitoTokenRequest` / `AvitoTokenResponse` - для Client Credentials
- `AvitoAuthorizationCodeRequest` / `AvitoAuthorizationCodeResponse` - для Authorization Code
- `AvitoRefreshTokenRequest` / `AvitoRefreshTokenResponse` - для обновления токенов
- `AvitoOAuthState` - состояние для защиты от CSRF
- `AvitoAuthUrlRequest` / `AvitoAuthUrlResponse` - для генерации URL авторизации
- `AvitoAuthCallbackRequest` / `AvitoAuthCallbackResponse` - для обработки callback

## API Endpoints

### Генерация URL авторизации
```
POST /avito/auth/generate-url
```
**Request:**
```json
{
  "client_id": "your_client_id",
  "redirect_uri": "https://yourapp.com/callback",
  "scope": ["messenger:read", "messenger:write"],
  "state": "optional_custom_state"
}
```

**Response:**
```json
{
  "auth_url": "https://avito.ru/oauth?response_type=code&client_id=...&state=...",
  "state": "generated_state"
}
```

### Callback обработчик
```
GET /avito/auth/callback?code=...&state=...
```

### Получение токена (Client Credentials)
```
POST /avito/auth/token/client-credentials
```
**Request:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

### Обновление токена
```
POST /avito/auth/token/refresh
```
**Request:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "your_refresh_token"
}
```

## Использование

### Client Credentials Flow

```python
from src.aicrm.services.avito_auth_service import AvitoAuthService

auth_service = AvitoAuthService()
tokens = await auth_service.get_token_via_client_credentials(
    client_id="your_client_id",
    client_secret="your_client_secret"
)
```

### Authorization Code Flow

```python
# 1. Генерация URL авторизации
auth_url_response = await auth_service.generate_auth_url(request)

# 2. Перенаправление пользователя на auth_url

# 3. Обработка callback
callback_response = await auth_service.handle_auth_callback(
    code=request.code,
    state=request.state
)

# 4. Использование токенов
client = AvitoClient(auth_type="authorization_code")
client.set_tokens(
    access_token=callback_response.access_token,
    refresh_token=callback_response.refresh_token
)
```

## Безопасность

- **State parameter**: Защита от CSRF атак с помощью уникального state
- **Redis storage**: Временное хранение state в Redis с TTL
- **Token refresh**: Автоматическое обновление токенов
- **Rate limiting**: Ограничение запросов через существующий rate limiter

## Тестирование

Запуск тестов:
```bash
cd /root/saas/aicrm
python3 test_avito_oauth.py
```

Тесты покрывают:
- Генерацию URL авторизации
- Валидацию state
- Создание клиентов разных типов
- Очистку просроченных state

## Конфигурация

### Переменные окружения
```bash
AVITO_CLIENT_ID=your_client_id
AVITO_CLIENT_SECRET=your_client_secret
AVITO_USER_ID=your_user_id
REDIS_URL=redis://localhost:6379
```

### Настройки в коде
- TTL для state: 600 секунд (10 минут)
- TTL для токенов: согласно ответу API (обычно 24 часа)
- Максимальное время жизни refresh токена: 1 год (по документации Avito)

## Расширение

Для добавления новых типов авторизации или провайдеров:
1. Добавить новые схемы в `src/aicrm/schemas/avito.py`
2. Расширить `AvitoAuthService` новыми методами
3. Добавить соответствующие API endpoints
4. Обновить `AvitoClient` для поддержки новых flow

## Совместимость

Реализация обратно совместима с существующим кодом. Старые клиенты продолжают работать с Client Credentials авторизацией по умолчанию.
