"""
Основное приложение FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import engine, SessionLocal
from .models import Base
from .api.routers import auth, customer, ai, ai_manager, order, avito, task, automation, email, telegram
from .utils.logging import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Создание таблиц базы данных
    Base.metadata.create_all(bind=engine)

    yield

    # Очистка ресурсов (синхронный engine не нуждается в dispose)


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
            "name": "Tasks",
            "description": "Управление задачами: CRUD операции, завершение задач"
        },
        {
            "name": "Auth",
            "description": "Аутентификация и авторизация пользователей"
        },
        {
            "name": "avito",
            "description": "Интеграция с Avito: управление объявлениями, статистика, продвижение"
        },
        {
            "name": "automation",
            "description": "Автоматизация бизнес-процессов: триггеры, роботы, стадии"
        },
        {
            "name": "telegram",
            "description": "Управление Telegram ботом: инициализация, статистика, отправка сообщений"
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
app.include_router(ai.router)
app.include_router(ai_manager.router)
app.include_router(avito.router)
app.include_router(task.router)
app.include_router(automation.router)
app.include_router(email.router)
app.include_router(telegram.router)


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
        "aicrm.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
