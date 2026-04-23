# Интеграция с Avito API

## Обзор

Данная система предоставляет полную интеграцию с Avito API для автоматизации работы с объявлениями, чатами и аналитикой. Интеграция включает Core API, Stats API и Messenger API.

## Конфигурация

Для работы интеграции необходимо настроить следующие параметры в конфигурации:

```python
# Avito API настройки
avito_client_id: str  # Client ID из личного кабинета Avito
avito_client_secret: str  # Client Secret из личного кабинета Avito
avito_user_id: int  # ID пользователя Avito
```

## Аутентификация

Система использует OAuth 2.0 Client Credentials Flow для получения access токенов.

### Получение токена
```
POST https://api.avito.ru/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}
```

**Ответ:**
```json
{
  "access_token": "token_string",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## Core API (Объявления)

### Получение списка объявлений

**Эндпоинт:** `GET /core/v1/items`

**Параметры:**
- `status` (string): Статус объявления (`active`, `removed`, `old`, `blocked`, `rejected`, `not_found`, `another_user`)
- `per_page` (int): Количество объявлений на страницу (макс. 100)
- `page` (int): Номер страницы

**Пример запроса:**
```bash
GET /core/v1/items?status=active&per_page=50
```

**Ответ:**
```json
{
  "resources": [
    {
      "id": 12345,
      "title": "Продажа автомобиля",
      "status": "active",
      "price": 500000,
      "category": {"id": 9, "name": "Автомобили"},
      "url": "https://www.avito.ru/moskva/avtomobili/prodazha_avtomobilya_12345"
    }
  ]
}
```

### Получение информации об объявлении

**Эндпоинт:** `GET /core/v1/accounts/{user_id}/items/{item_id}/`

**Пример запроса:**
```bash
GET /core/v1/accounts/12345/items/67890/
```

**Ответ:**
```json
{
  "id": 67890,
  "title": "Продажа автомобиля",
  "description": "Продам автомобиль в отличном состоянии",
  "price": 500000,
  "category": {"id": 9, "name": "Автомобили"},
  "status": "active",
  "vas": [
    {"vas_id": "x2", "finish_time": "2024-01-15T10:00:00Z"}
  ],
  "url": "https://www.avito.ru/item/67890"
}
```

### Обновление цены объявления

**Эндпоинт:** `POST /core/v1/items/{item_id}/update_price`

**Тело запроса:**
```json
{
  "price": 550000
}
```

**Ответ:**
```json
{
  "result": "success"
}
```

## Stats API (Статистика и аналитика)

### Получение статистики объявлений

**Эндпоинт:** `POST /stats/v1/accounts/{user_id}/items`

**Тело запроса:**
```json
{
  "itemIds": [12345, 67890],
  "dateFrom": "2024-01-01",
  "dateTo": "2024-01-31",
  "fields": ["uniqViews", "uniqContacts", "uniqFavorites"],
  "periodGrouping": "day"
}
```

**Ответ:**
```json
{
  "result": [
    {
      "itemId": 12345,
      "stats": [
        {
          "date": "2024-01-01",
          "uniqViews": 150,
          "uniqContacts": 5,
          "uniqFavorites": 12
        }
      ]
    }
  ]
}
```

### Получение аналитики профиля

**Эндпоинт:** `POST /stats/v2/accounts/{user_id}/items`

**Тело запроса:**
```json
{
  "dateFrom": "2024-01-01",
  "dateTo": "2024-01-31",
  "metrics": ["views", "contacts", "favorites"],
  "grouping": "item",
  "limit": 1000,
  "offset": 0
}
```

## VAS API (Услуги продвижения)

### Получение цен на услуги продвижения

**Эндпоинт:** `POST /core/v1/accounts/{user_id}/vas/prices`

**Тело запроса:**
```json
{
  "itemIds": [12345, 67890]
}
```

**Ответ:**
```json
[
  {
    "itemId": 12345,
    "vas": [
      {
        "slug": "x2",
        "price": 150,
        "priceOld": 200
      },
      {
        "slug": "highlight",
        "price": 100,
        "priceOld": null
      }
    ],
    "stickers": [
      {
        "id": 1,
        "title": "Скидка",
        "description": "Скидка 10%"
      }
    ]
  }
]
```

### Применение услуг продвижения

**Эндпоинт:** `PUT /core/v2/items/{item_id}/vas/`

**Тело запроса:**
```json
{
  "slugs": ["x2", "highlight"],
  "stickers": [1, 2]
}
```

**Ответ:**
```json
{
  "operationId": 123456
}
```

## Calls API (Звонки)

### Получение статистики звонков

**Эндпоинт:** `POST /core/v1/accounts/{user_id}/calls/stats/`

**Тело запроса:**
```json
{
  "dateFrom": "2024-01-01",
  "dateTo": "2024-01-31",
  "itemIds": [12345]
}
```

**Ответ:**
```json
{
  "result": {
    "items": [
      {
        "itemId": 12345,
        "days": [
          {
            "date": "2024-01-01",
            "calls": 25,
            "answered": 20,
            "new": 15,
            "newAnswered": 12
          }
        ]
      }
    ]
  }
}
```

## Messenger API (Чаты и сообщения)

### Получение списка чатов

**Эндпоинт:** `GET /messenger/v1/accounts/{user_id}/chats`

**Параметры:**
- `itemIds` (string): ID объявлений через запятую
- `unreadOnly` (boolean): Только непрочитанные чаты
- `limit` (int): Максимальное количество (макс. 100)
- `offset` (int): Смещение

**Пример запроса:**
```bash
GET /messenger/v1/accounts/12345/chats?limit=50&unreadOnly=true
```

**Ответ:**
```json
{
  "chats": [
    {
      "id": "chat_123",
      "user": {
        "id": "user_456",
        "name": "Иван Петров"
      },
      "item": {
        "id": 12345,
        "title": "Продажа автомобиля"
      },
      "last_message": {
        "text": "Здравствуйте, товар в наличии?",
        "direction": "inbound",
        "created": "2024-01-10T10:00:00Z"
      },
      "unread_count": 2
    }
  ]
}
```

### Получение информации о чате

**Эндпоинт:** `GET /messenger/v1/accounts/{user_id}/chats/{chat_id}`

**Ответ:**
```json
{
  "id": "chat_123",
  "status": "active",
  "created": "2024-01-10T09:00:00Z",
  "item": {
    "id": 12345,
    "title": "Продажа автомобиля"
  },
  "users": [
    {
      "id": "user_456",
      "name": "Иван Петров",
      "role": "buyer"
    }
  ]
}
```

### Получение сообщений чата

**Эндпоинт:** `GET /messenger/v2/accounts/{user_id}/chats/{chat_id}/messages/`

**Параметры:**
- `limit` (int): Максимальное количество сообщений
- `offset` (int): Смещение

**Ответ:**
```json
{
  "messages": [
    {
      "id": "msg_789",
      "text": "Здравствуйте, товар в наличии?",
      "direction": "inbound",
      "created": "2024-01-10T10:00:00Z",
      "author": {
        "id": "user_456",
        "name": "Иван Петров"
      }
    },
    {
      "id": "msg_790",
      "text": "Да, товар в наличии. Можете подъехать посмотреть.",
      "direction": "outbound",
      "created": "2024-01-10T10:05:00Z",
      "author": {
        "id": "seller",
        "name": "Продавец"
      }
    }
  ]
}
```

### Отправка сообщения

**Эндпоинт:** `POST /messenger/v1/accounts/{user_id}/chats/{chat_id}/messages`

**Тело запроса:**
```json
{
  "message": {
    "text": "Здравствуйте! Товар в наличии, можете подъехать посмотреть."
  }
}
```

**Ответ:**
```json
{
  "id": "msg_791",
  "created": "2024-01-10T10:10:00Z"
}
```

### Отметка чата как прочитанного

**Эндпоинт:** `POST /messenger/v1/accounts/{user_id}/chats/{chat_id}/read`

**Ответ:**
```json
{
  "result": "success"
}
```

### Удаление сообщения

**Эндпоинт:** `POST /messenger/v1/accounts/{user_id}/chats/{chat_id}/messages/{message_id}`

**Ответ:**
```json
{
  "result": "deleted"
}
```

## Webhook интеграция

### Подписка на webhook (v2)

**Эндпоинт:** `POST /messenger/v2/webhook`

**Тело запроса:**
```json
{
  "url": "https://your-domain.com/webhook/avito",
  "events": ["message", "chat_created", "chat_closed"]
}
```

**Ответ:**
```json
{
  "id": "webhook_123",
  "url": "https://your-domain.com/webhook/avito",
  "events": ["message", "chat_created", "chat_closed"],
  "status": "active"
}
```

### Формат webhook уведомлений

**Новое сообщение:**
```json
{
  "event": "message",
  "timestamp": "2024-01-10T10:00:00Z",
  "payload": {
    "chat_id": "chat_123",
    "message": {
      "id": "msg_789",
      "text": "Здравствуйте, товар в наличии?",
      "direction": "inbound",
      "created": "2024-01-10T10:00:00Z"
    },
    "user": {
      "id": "user_456",
      "name": "Иван Петров"
    },
    "item": {
      "id": 12345,
      "title": "Продажа автомобиля"
    }
  }
}
```

**Создание чата:**
```json
{
  "event": "chat_created",
  "timestamp": "2024-01-10T09:00:00Z",
  "payload": {
    "chat_id": "chat_123",
    "user": {
      "id": "user_456",
      "name": "Иван Петров"
    },
    "item": {
      "id": 12345,
      "title": "Продажа автомобиля"
    }
  }
}
```

## Обработка ошибок

### Типы ошибок API

- **400 Bad Request**: Неверные параметры запроса
- **401 Unauthorized**: Неверный или просроченный токен
- **403 Forbidden**: Недостаточно прав доступа
- **404 Not Found**: Ресурс не найден
- **422 Unprocessable Entity**: Ошибка валидации данных
- **429 Too Many Requests**: Превышен лимит запросов
- **500 Internal Server Error**: Внутренняя ошибка сервера Avito
- **502 Bad Gateway**: Сервис временно недоступен
- **503 Service Unavailable**: Сервис на обслуживании

### Rate Limiting

API имеет ограничения на количество запросов:
- Core API: 1000 запросов в час
- Stats API: 100 запросов в час
- Messenger API: 1000 запросов в час

Система автоматически отслеживает лимиты и приостанавливает запросы при достижении порога.

## Кэширование

Для оптимизации производительности система использует Redis для кэширования:

- **Активные объявления**: TTL 5 минут
- **Статистика объявлений**: TTL 10 минут
- **Цены VAS**: TTL 30 минут

## Мониторинг и логирование

Все запросы к Avito API логируются с указанием:
- HTTP метод и URL
- Время выполнения
- Статус ответа
- Использованные токены (анонимизированные)

## Безопасность

- **Токены**: Хранятся в памяти, автоматически обновляются
- **Rate Limiting**: Защита от превышения лимитов
- **Валидация**: Все входные данные проверяются
- **HTTPS**: Все запросы используют шифрование
- **Аудит**: Все действия логируются для аудита

## Примеры использования в коде

### Получение активных объявлений

```python
async with AvitoService() as avito:
    items = await avito.get_active_items()
    print(f"Найдено {len(items)} активных объявлений")
```

### Отправка сообщения в чат

```python
async with AvitoService() as avito:
    result = await avito.send_avito_message(
        chat_id="chat_123",
        message="Здравствуйте! Товар в наличии."
    )
```

### Получение статистики объявления

```python
async with AvitoService() as avito:
    stats = await avito.get_item_performance(item_id=12345, days=30)
    print(f"Просмотры: {stats['total_views']}")
    print(f"Контакты: {stats['total_contacts']}")
```

## Заключение

Интеграция с Avito API предоставляет полный набор инструментов для автоматизации работы с объявлениями, чатами и аналитикой. Система обеспечивает надежность, безопасность и высокую производительность взаимодействия с платформой Avito.
