"""
Основное приложение FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import engine
from .models import Base
from .api.routers import auth, customer, ai, order
from .utils.logging import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Создание таблиц базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Очистка ресурсов при завершении
    await engine.dispose()


app = FastAPI(
    title="AI CRM System API",
    description="""
    ## 🤖 AI CRM System

    Полнофункциональная CRM система для компаний печати с интеграцией ИИ.

    ### 🎯 Основные возможности

    - **AI-ассистент**: Анализ намерений, генерация ответов, поддержка OpenRouter/HuggingFace/OpenAI
    - **Производственный workflow**: Автоматическое создание этапов производства, отслеживание прогресса
    - **Аналитика**: Отчеты о заказах, просрочках, эффективности производства
    - **Многоканальные коммуникации**: Telegram, Email, Website, Avito
    - **Мониторинг**: Структурированное логирование, метрики, health checks

    ### 📋 Спецификация API

    API полностью соответствует **OpenAPI 3.0.0** спецификации.

    ### 🔐 Аутентификация

    Для доступа к защищенным эндпоинтам используйте JWT токены:
    ```
    Authorization: Bearer <your-jwt-token>
    ```

    ### 📊 Статусы ответов

    - `200` - Успешный запрос
    - `201` - Ресурс создан
    - `400` - Неверные параметры
    - `401` - Не авторизован
    - `403` - Доступ запрещен
    - `404` - Ресурс не найден
    - `422` - Ошибка валидации
    - `500` - Внутренняя ошибка сервера
    - `502` - Ошибка внешнего сервиса
    - `503` - Сервис недоступен

    ### 📈 Ограничения

    - Rate limiting: 60 запросов в минуту для AI эндпоинтов
    - Максимальная длина сообщения: 10,000 символов
    - Максимальное количество токенов: 4,000

    ### 🏷️ Теги эндпоинтов

    - **AI**: Функции искусственного интеллекта
    - **Orders**: Управление заказами
    - **Customers**: Управление клиентами
    - **Auth**: Аутентификация и авторизация
    """,
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "AI CRM Team",
        "email": "support@aicrm.dev",
        "url": "https://github.com/your-org/aicrm"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "AI",
            "description": "Функции искусственного интеллекта: анализ намерений, генерация ответов, чат"
        },
        {
            "name": "Orders",
            "description": "Управление заказами: создание, обновление, прогресс производства"
        },
        {
            "name": "Customers",
            "description": "Управление клиентами: CRUD операции, поиск, статистика"
        },
        {
            "name": "Auth",
            "description": "Аутентификация и авторизация пользователей"
        }
    ],
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.aicrm.dev",
            "description": "Production server"
        }
    ]
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(order.router, prefix="/orders", tags=["Orders"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "AI CRM System API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
