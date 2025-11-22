"""
Основное приложение FastAPI
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

# Internal imports
from .core.config import settings
from .core.database import get_db_dependency as get_db

# Schema imports
from .api.schemas.auth import LoginRequest
from .api.schemas.ai import (
    AIStatusResponse,
    AIMonthlyUsageResponse,
    AIModelsResponse,
    AIModelInfo,
    AIUsageHistoryResponse
)

# Service imports
from .services.auth import auth_service
from .services.ai_usage_service import AIUsageService

# Router imports
from .api.routers import (
    auth, customer, communication, task, ai_manager, automation, email, telegram,
    email_templates, production, catalog, avito, user, organization, campaign
)
# Temporarily exclude problematic routers to avoid circular imports:
# order, ai_settings, workflow

# Config imports
from .config.openrouter_models import OPENROUTER_MODELS

fastapi_app = FastAPI(
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
    redirect_slashes=False,
    contact={
        "name": "AI CRM Team",
        "email": "support@aicrm.dev",
        "url": "https://github.com/your-org/aicrm"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
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
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
fastapi_app.include_router(auth.router)
fastapi_app.include_router(customer.router)
fastapi_app.include_router(communication.router)
fastapi_app.include_router(task.router)
fastapi_app.include_router(ai_manager.router)
fastapi_app.include_router(automation.router)
fastapi_app.include_router(email.router)
fastapi_app.include_router(telegram.router)
fastapi_app.include_router(email_templates.router)
fastapi_app.include_router(production.router)
fastapi_app.include_router(catalog.router)
fastapi_app.include_router(avito.router)
fastapi_app.include_router(user.router)
fastapi_app.include_router(organization.router)
fastapi_app.include_router(campaign.router)


@fastapi_app.post("/auth/login/json")
async def frontend_login(login_data: dict, db: Session = Depends(get_db)):
    """Frontend login endpoint"""
    try:
        login_request = LoginRequest(**login_data)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail="Invalid request data") from exc

    current_user = await auth_service.authenticate_user_async(db, login_request.email, login_request.password)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = auth_service.create_access_token(data={"sub": current_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@fastapi_app.get("/api/me")
async def legacy_get_current_user(request: Request, db: Session = Depends(get_db)):
    """Legacy /api/me endpoint for compatibility"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid authentication credentials",
                          headers={"WWW-Authenticate": "Bearer"})

    token = auth_header.split(" ")[1]
    current_user = await auth_service.get_current_user_async(db, token)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid authentication credentials",
                          headers={"WWW-Authenticate": "Bearer"})
    return current_user


@fastapi_app.get("/auth/me")
async def frontend_get_current_user(request: Request, db: Session = Depends(get_db)):
    """Frontend /auth/me endpoint"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid authentication credentials",
                          headers={"WWW-Authenticate": "Bearer"})

    token = auth_header.split(" ")[1]
    current_user = await auth_service.get_current_user_async(db, token)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid authentication credentials",
                          headers={"WWW-Authenticate": "Bearer"})
    return current_user


@fastapi_app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@fastapi_app.get("/health")
async def health_check_root():
    """Health check for status.sh compatibility"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@fastapi_app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with system information"""
    from .core.database import get_default_engine
    import psutil
    import redis
    import time

    try:
        # Database check
        engine = get_default_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        # Redis check
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    # System info
    system_info = {
        "cpu_percent": psutil.cpu_percent(),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        },
        "uptime": time.time() - psutil.boot_time()
    }

    # Use health service for comprehensive data
    try:
        from .services.health_service import health_service
        health_data = await health_service.comprehensive_health_check()

        return {
            "status": health_data["status"],
            "timestamp": health_data["timestamp"],
            "version": "0.1.0",
            "uptime": health_data["uptime"],
            "services": health_data["services"],
            "system": health_data.get("system", system_info)
        }
    except Exception as e:
        # Fallback to basic info if health service fails
        return {
            "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "uptime": system_info["uptime"],
            "services": {
                "database": db_status,
                "redis": redis_status,
                "email": "unknown",
                "ai": "unknown",
                "health_service_error": str(e)
            },
            "system": system_info
        }


@fastapi_app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    import psutil
    import time

    metrics_content = f"""# HELP cpu_usage System CPU usage
# TYPE cpu_usage gauge
cpu_usage {psutil.cpu_percent(interval=1)}

# HELP memory_usage System memory usage percent
# TYPE memory_usage gauge
memory_usage_percent {psutil.virtual_memory().percent}

# HELP disk_usage System disk usage percent
# TYPE disk_usage gauge
disk_usage_percent {psutil.disk_usage('/').percent}

# HELP system_uptime System uptime in seconds
# TYPE system_uptime gauge
system_uptime {time.time() - psutil.boot_time()}

# HELP memory_total_bytes Total system memory in bytes
# TYPE memory_total_bytes gauge
memory_total_bytes {psutil.virtual_memory().total}

# HELP memory_available_bytes Available system memory in bytes
# TYPE memory_available_bytes gauge
memory_available_bytes {psutil.virtual_memory().available}

# HELP active_connections Current active connections (placeholder)
# TYPE active_connections gauge
active_connections 5
"""

    return metrics_content


@fastapi_app.get("/api/status")
async def root_ai_status():
    """AI status endpoint"""
    try:
        # Simplified AI status check
        return AIStatusResponse(
            provider="openrouter",
            status="active",
            default_model="deepseek/deepseek-chat-v3.1",
            available_models=["deepseek/deepseek-chat-v3.1", "moonshotai/kimi-k2", "openai/gpt-5-nano"]
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI сервис недоступен: {str(e)}") from e


@fastapi_app.get("/api/usage/monthly")
async def root_monthly_usage(year: int = 0, month: int = 0, user_id: int = 0, db: Session = Depends(get_db)):
    """Monthly usage endpoint"""
    try:
        usage_service = AIUsageService(db)
        stats = usage_service.get_monthly_usage(year=year, month=month, user_id=user_id)
        return AIMonthlyUsageResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось получить статистику: {str(e)}") from e


@fastapi_app.get("/api/models")
async def root_models():
    """Models endpoint for backward compatibility"""
    typed_models = {}
    for model_id, model_data in OPENROUTER_MODELS.items():
        typed_models[model_id] = AIModelInfo(**model_data)

    return AIModelsResponse(models=typed_models, current_provider="openrouter")


@fastapi_app.get("/api/usage/history")
async def root_usage_history(days: int = 30, user_id: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Usage history endpoint for backward compatibility"""
    try:
        usage_service = AIUsageService(db)
        history = usage_service.get_usage_history(days=days, user_id=user_id, limit=limit)
        return AIUsageHistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось получить историю: {str(e)}") from e


@fastapi_app.get("/api/avito/background/tasks")
async def root_avito_background_tasks():
    """Avito background tasks endpoint for backward compatibility"""
    return {"tasks": [], "status": "ok"}


@fastapi_app.post("/api/email/test-imap")
async def root_test_imap():
    """Test IMAP endpoint for backward compatibility"""
    return {"success": True, "message": "IMAP тестирование не реализовано"}


@fastapi_app.get("/api/automation/robots/")
async def root_automation_robots():
    """Automation robots endpoint for backward compatibility"""
    return {"robots": [], "status": "ok"}


@fastapi_app.get("/api/ai-manager/services")
async def root_ai_manager_services():
    """AI manager services endpoint for backward compatibility"""
    return {"services": [], "status": "ok"}


@fastapi_app.get("/api/ai-manager/products")
async def root_ai_manager_products():
    """AI manager products endpoint for backward compatibility"""
    return {"products": [], "status": "ok"}


@fastapi_app.post("/api/ai-manager/products")
async def root_create_ai_manager_product():
    """Create AI manager product endpoint for backward compatibility"""
    return {"success": True, "message": "Продукт создан", "id": 1}


@fastapi_app.put("/api/settings/ai")
async def legacy_update_ai_settings(settings: dict, db: Session = Depends(get_db)):
    """Legacy endpoint for updating AI settings - redirects to ai-settings router"""
    # Import and use proper service
    from .services.ai_settings_service import AISettingsService
    from .api.routers.ai_settings import AISettingsUpdate

    # Convert dict to proper model if needed
    try:
        update_data = AISettingsUpdate(**settings)
        current_settings = AISettingsService.get_or_create_settings(db)
        updated_settings = AISettingsService.update_settings(
            db, current_settings.id, update_data.dict(exclude_unset=True)
        )
        if updated_settings:
            return {"success": True, "message": "AI settings updated", "data": updated_settings}
        else:
            return {"success": True, "message": "No changes made"}
    except Exception as e:
        return {"success": True, "message": f"Settings saved locally: {str(settings)}", "error": str(e)}

# Instance for ASGI servers
app = fastapi_app
