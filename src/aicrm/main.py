"""
Основное приложение FastAPI
"""

from contextlib import asynccontextmanager

import socketio
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routers import (
    admin,
    ai,
    ai_prompt,
    ai_settings,
    auth,
    automation,
    avito,
    campaign,
    communication,
    customer,
    email,
    email_templates,
    order,
    organization,
    plugin,
    system,
    system_settings,
    task,
    telegram,
    user,
    user_settings,
    websocket,
    workflow,
)
from .core.config import settings
from .core.database import SessionLocal, engine
from .core.dependencies import get_current_superuser
from .models import Base
from .models.user import User
from .utils.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware для обработки ошибок"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled error: {exc}", exc_info=True)
            # Возвращаем JSON ошибку вместо HTML
            return Response(
                content='{"detail": "Internal server error"}',
                status_code=500,
                media_type="application/json",
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Создание таблиц базы данных
    Base.metadata.create_all(bind=engine)

    yield

    # Очистка ресурсов (синхронный engine не нуждается в dispose)


fastapi_app = FastAPI(
    title="AI CRM System API",
    description="""
    # 🤖 AI CRM System API

    Полнофункциональная CRM система для компаний печати с интеграцией ИИ.

    ## 🎯 Основные возможности

    - **🤖 AI-ассистент**: Анализ намерений, генерация ответов, поддержка OpenRouter/HuggingFace/OpenAI
    - **🏭 Производственный workflow**: Автоматическое создание этапов производства, отслеживание прогресса
    - **📊 Аналитика**: Отчеты о заказах, просрочках, эффективности производства
    - **💬 Многоканальные коммуникации**: Telegram, Email, Website, Avito Messenger
    - **⚡ Автоматизация**: Триггеры, роботы, бизнес-процессы
    - **📈 Мониторинг**: Структурированное логирование, метрики, health checks

    ## 📋 Техническая спецификация

    - **OpenAPI**: 3.1.0
    - **Python**: 3.11+
    - **Framework**: FastAPI
    - **База данных**: PostgreSQL 15+
    - **Кэш**: Redis 7+
    - **WebSocket**: Socket.IO для real-time коммуникаций

    ## 🔐 Аутентификация

    API использует JWT токены для аутентификации. Для доступа к защищенным эндпоинтам:

    ```
    Authorization: Bearer <your-jwt-token>
    ```

    Получить токен можно через эндпоинт `/auth/login`.

    ## 📊 Статусы ответов

    | Код | Описание |
    |-----|----------|
    | `200` | Успешный запрос |
    | `201` | Ресурс создан |
    | `400` | Неверные параметры |
    | `401` | Не авторизован |
    | `403` | Доступ запрещен |
    | `404` | Ресурс не найден |
    | `422` | Ошибка валидации |
    | `429` | Превышен лимит запросов |
    | `500` | Внутренняя ошибка сервера |
    | `502` | Ошибка внешнего сервиса |
    | `503` | Сервис недоступен |

    ## 📈 Ограничения и лимиты

    - **Rate limiting**: 60 запросов в минуту для AI эндпоинтов
    - **Максимальная длина сообщения**: 10,000 символов
    - **Максимальное количество токенов**: 4,000 для AI запросов
    - **WebSocket**: 20 сообщений в минуту на пользователя

    ## 🏷️ Группы эндпоинтов

    | Тег | Описание |
    |-----|----------|
    | **AI** | Функции искусственного интеллекта: анализ намерений, генерация ответов, чат |
    | **Orders** | Управление заказами: создание, обновление, прогресс производства |
    | **Customers** | Управление клиентами: CRUD операции, поиск, статистика |
    | **Tasks** | Управление задачами: CRUD операции, завершение задач |
    | **Auth** | Аутентификация и авторизация пользователей |
    | **Avito** | Интеграция с Avito: объявления, статистика, продвижение |
    | **Automation** | Автоматизация бизнес-процессов: триггеры, роботы, стадии |
    | **Admin** | Административные функции: управление пользователями, статистика |
    | **Communications** | Управление коммуникациями: сообщения, каналы, аналитика |
    | **System** | Системный мониторинг: здоровье, ресурсы, база данных |

    ## 🚀 Быстрый старт

    1. **Получите токен**:
    ```bash
    curl -X POST "https://dev.chillcreative.ru/auth/login" \\
         -H "Content-Type: application/json" \\
         -d '{"email": "user@example.com", "password": "password"}'
    ```

    2. **Используйте API**:
    ```bash
    curl -H "Authorization: Bearer YOUR_TOKEN" \\
         "https://dev.chillcreative.ru/customers/"
    ```

    ## 📞 Поддержка

    - **Email**: support@aicrm.dev
    - **Документация**: [GitHub](https://github.com/your-org/aicrm)
    - **Версия API**: 1.0.0
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "AI CRM Team",
        "email": "support@aicrm.dev",
        "url": "https://github.com/your-org/aicrm",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {"name": "Auth", "description": "Аутентификация и авторизация пользователей"},
        {
            "name": "Users",
            "description": "Управление пользователями: CRUD операции, профили",
        },
        {"name": "User Settings", "description": "Настройки пользователей"},
        {
            "name": "Organizations",
            "description": "Управление организациями в мультитенантной системе",
        },
        {
            "name": "Customers",
            "description": "Управление клиентами: CRUD операции, поиск, статистика",
        },
        {
            "name": "Orders",
            "description": "Управление заказами: создание, обновление, прогресс производства",
        },
        {
            "name": "Tasks",
            "description": "Управление задачами: CRUD операции, завершение задач",
        },
        {"name": "Campaigns", "description": "Управление маркетинговыми кампаниями"},
        {
            "name": "AI",
            "description": "Функции искусственного интеллекта: анализ намерений, генерация ответов, чат",
        },
        {
            "name": "AI Settings",
            "description": "Настройки AI для пользователей и кампаний",
        },
        {"name": "AI Prompts", "description": "Управление AI промптами"},
        {
            "name": "Automation",
            "description": "Автоматизация бизнес-процессов: триггеры, роботы, стадии",
        },
        {
            "name": "Communications",
            "description": "Управление коммуникациями: сообщения, каналы, аналитика",
        },
        {"name": "Email", "description": "Отправка и управление email сообщениями"},
        {"name": "Email Templates", "description": "Управление шаблонами email"},
        {
            "name": "Workflow",
            "description": "Управление рабочими процессами и автоматизацией",
        },
        {
            "name": "Avito",
            "description": "Интеграция с Avito: управление объявлениями, статистика, продвижение",
        },
        {
            "name": "Telegram",
            "description": "Интеграция с Telegram: боты, чаты, настройки",
        },
        {"name": "Plugins", "description": "Управление плагинами системы"},
        {
            "name": "System",
            "description": "Системный мониторинг: здоровье, ресурсы, база данных",
        },
        {"name": "System Settings", "description": "Глобальные настройки системы"},
        {
            "name": "Admin",
            "description": "Административные функции: управление пользователями, статистика, логи",
        },
        {
            "name": "websockets",
            "description": "WebSocket эндпоинты для real-time коммуникаций",
        },
    ],
    servers=[
        {"url": "https://dev.chillcreative.ru", "description": "Production server"},
    ],
    docs_url="/docs",  # Включаем публичную документацию
    redoc_url="/redoc",  # Включаем публичную документацию
)

# Настройка CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все origins для тестирования
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ASGI middleware для обработки ошибок
fastapi_app.add_middleware(ErrorHandlingMiddleware)

# Настройка роутеров
fastapi_app.include_router(auth.router)
fastapi_app.include_router(admin.router)
fastapi_app.include_router(order.router, prefix="/orders", tags=["Orders"])
fastapi_app.include_router(ai.router, prefix="/ai", tags=["AI"])
fastapi_app.include_router(ai_prompt.router)
fastapi_app.include_router(ai_settings.router)
fastapi_app.include_router(avito.router)
fastapi_app.include_router(campaign.router)
fastapi_app.include_router(task.router)
fastapi_app.include_router(automation.router)
fastapi_app.include_router(communication.router)
fastapi_app.include_router(customer.router)
fastapi_app.include_router(email.router)
fastapi_app.include_router(email_templates.router)
fastapi_app.include_router(organization.router)
fastapi_app.include_router(plugin.router)
fastapi_app.include_router(system.router)
fastapi_app.include_router(system_settings.router)
fastapi_app.include_router(telegram.router)
fastapi_app.include_router(user.router)
fastapi_app.include_router(user_settings.router)
fastapi_app.include_router(websocket.router, tags=["websockets"])
fastapi_app.include_router(workflow.router)


# Добавляем маршруты к FastAPI приложению
@fastapi_app.get("/")
async def root():
    """Корневой эндпоинт API"""
    return {
        "message": "🤖 AI CRM System API",
        "version": "1.0.0",
        "status": "active",
        "documentation": {
            "swagger": "https://dev.chillcreative.ru/docs",
            "redoc": "https://dev.chillcreative.ru/redoc",
            "openapi": "https://dev.chillcreative.ru/openapi.json",
        },
        "features": [
            "AI Assistant",
            "Production Workflow",
            "Multi-channel Communications",
            "Automation Engine",
            "Real-time WebSocket",
        ],
    }


@fastapi_app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


@fastapi_app.post("/api/errors")
async def report_error(error_data: dict):
    """Прием отчетов об ошибках от фронтенда"""
    logger.error(f"Frontend error reported: {error_data}")
    # Здесь можно сохранить ошибку в базу данных или отправить уведомление
    return {"status": "error_received"}


# Документация теперь публично доступна

# Основное ASGI приложение - только FastAPI
app = fastapi_app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "aicrm.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
