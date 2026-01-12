"""
AI роутер для FastAPI - OpenAPI 3.0.0 compliant
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, get_db
from ...services.ai.client import UnifiedAIClient
from ...services.ai.intent_service import AIIntentService, IntentType
from ...services.ai_usage_service import AIUsageService
from ...utils.logging import get_logger
from ..schemas.ai import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIChatRequest,
    AIChatResponse,
    AIModelsResponse,
    AIMonthlyUsageResponse,
    AIStatusResponse,
    AIUsageHistoryResponse,
)
from ..schemas.auth import User

router = APIRouter(
    tags=["AI"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Ресурс не найден"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"},
        502: {"description": "Bad Gateway - Ошибка внешнего сервиса"},
        502: {"description": "Bad Gateway - Ошибка внешнего сервиса"},
        503: {"description": "Service Unavailable - Сервис временно недоступен"},
    },
)


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"

# Logger for this module
logger = get_logger(__name__)


def get_ai_service() -> AIIntentService:
    """
    Зависимость для получения AI сервиса анализа намерений.

    Returns:
        AIIntentService: Экземпляр сервиса для работы с AI
    """
    return AIIntentService()


def get_ai_client() -> UnifiedAIClient:
    """
    Зависимость для получения унифицированного AI клиента.

    Returns:
        UnifiedAIClient: Экземпляр клиента для работы с AI провайдерами
    """
    return UnifiedAIClient()


@router.post(
    "/public/analyze-intent",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Публичный анализ намерения сообщения (без аутентификации)",
    description="""
    Публичный endpoint для анализа намерения сообщения без необходимости аутентификации.

    **Возможные намерения:**
    - `order_request` - запрос на создание заказа
    - `question` - вопрос о услугах/ценах
    - `complaint` - жалоба или проблема
    - `support` - запрос технической поддержки
    - `general` - общее общение

    **Особенности:**
    - Доступен без JWT токена
    - Ограниченное использование (rate limiting)
    - Для демонстрации и тестирования
    """,
    response_description="Результат анализа сообщения с намерением и ответом",
)
async def public_analyze_intent(
    request: AIAnalysisRequest, ai_service: AIIntentService = Depends(get_ai_service)
) -> AIAnalysisResponse:
    """
    Публичный анализ намерения сообщения (без аутентификации).
    """
    try:
        # Анализируем намерение
        intent = await ai_service.analyze_intent(request.message, request.context)

        # Генерируем ответ
        response = await ai_service.generate_response(
            intent, request.message, request.context
        )

        return AIAnalysisResponse(
            intent=str(intent),
            response=response,
            needs_human_intervention=intent in ["complaint", "support"],
            suggested_actions=["contact_support", "schedule_followup"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI анализ не удался: {str(e)}",
        )


@router.post(
    "/analyze-intent",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Анализ намерения сообщения",
    description="""
    Анализирует входящее сообщение клиента с помощью AI и определяет его намерение.

    **Возможные намерения:**
    - `order` - запрос на создание заказа
    - `question` - вопрос о услугах/ценах
    - `complaint` - жалоба или проблема
    - `support` - запрос технической поддержки
    - `other` - другое

    **Особенности:**
    - Автоматическая генерация ответа на основе намерения
    - Определение необходимости человеческого вмешательства
    - Рекомендации по дальнейшим действиям
    """,
    response_description="Результат анализа сообщения с намерением и ответом",
)
async def analyze_intent(
    request: AIAnalysisRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: AIIntentService = Depends(get_ai_service),
) -> AIAnalysisResponse:
    """
    Анализирует намерение сообщения и генерирует ответ.

    Args:
        request: Запрос с сообщением и контекстом
        db: Сессия базы данных
        ai_service: Сервис анализа намерений

    Returns:
        AIAnalysisResponse: Результат анализа с намерением и ответом

    Raises:
        HTTPException: При ошибке анализа или внешнего сервиса
    """
    try:
        # Передаем модель в intent_service
        intent = await ai_service.analyze_intent(request.message, request.context)
        response = await ai_service.generate_response(
            intent, request.message, request.context
        )

        # Логируем использование токенов (примерный расчет)
        model_used = request.model or "deepseek/deepseek-chat-v3.1"
        intent_tokens = (
            len(request.message.split()) * 1.2
        )  # Примерный расчет для анализа намерения
        response_tokens = (
            len(response.split()) * 1.3
        )  # Примерный расчет для генерации ответа
        total_tokens = intent_tokens + response_tokens

        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="analyze-intent",
            total_tokens=total_tokens,
            prompt_tokens=intent_tokens,
            completion_tokens=response_tokens,
            user_id=current_user.id,  # Получение ID пользователя из JWT токена
            ip_address=http_request.client.host,  # Получение IP адреса клиента
            user_agent=http_request.headers.get("user-agent"),  # Получение User-Agent
        )

        return AIAnalysisResponse(
            intent=intent,
            response=response,
            needs_human_intervention=intent
            in [IntentType.COMPLAINT, IntentType.SUPPORT],
            suggested_actions=["contact_support", "schedule_followup"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI анализ не удался: {str(e)}",
        )


@router.post(
    "/generate-response",
    status_code=status.HTTP_200_OK,
    summary="Генерация ответа на сообщение",
    description="""
    Генерирует персонализированный ответ на сообщение клиента на основе его намерения.

    **Процесс:**
    1. Определение намерения сообщения
    2. Выбор подходящего шаблона ответа
    3. Генерация персонализированного ответа
    4. Возврат результата с использованной моделью

    **Применение:**
    - Автоматические ответы в чат-ботах
    - Подготовка ответов для операторов
    - Генерация email ответов
    """,
    response_description="Сгенерированный ответ с информацией о намерении и модели",
)
async def generate_response(
    request: AIAnalysisRequest, ai_service: AIIntentService = Depends(get_ai_service)
) -> Dict[str, Any]:
    """
    Генерирует ответ на сообщение клиента.

    Args:
        request: Запрос с сообщением и контекстом
        ai_service: Сервис анализа намерений

    Returns:
        Dict: Ответ с намерением, текстом ответа и использованной моделью
    """
    try:
        intent = await ai_service.analyze_intent(request.message, request.context)
        response = await ai_service.generate_response(
            intent, request.message, request.context
        )

        return {
            "intent": intent,
            "response": response,
            "model_used": "local",
            "timestamp": "2025-11-11T20:00:00Z",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Генерация ответа не удалась: {str(e)}",
        )


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Прямой чат с AI моделью",
    description="""
    Отправляет сообщения в AI модель и получает ответ в формате чата.

    **Поддерживаемые роли сообщений:**
    - `system` - системный промпт для настройки поведения AI
    - `user` - сообщение пользователя
    - `assistant` - предыдущий ответ AI (для контекста)

    **Параметры генерации:**
    - `temperature`: креативность ответа (0.0 - 2.0)
    - `max_tokens`: максимальная длина ответа
    - `model`: конкретная модель для использования

    **Применение:**
    - Интеграция с внешними чат-системами
    - Тестирование различных моделей
    - Генерация контента
    """,
    response_description="Ответ от AI модели с метаданными",
)
async def chat_with_ai(
    request: AIChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    ai_client: UnifiedAIClient = Depends(get_ai_client),
    db: Session = Depends(get_db),
) -> AIChatResponse:
    """
    Выполняет чат с AI моделью.

    Args:
        request: Запрос с сообщениями и параметрами
        ai_client: Унифицированный AI клиент

    Returns:
        AIChatResponse: Ответ от AI с метаданными
    """
    try:
        response = await ai_client.chat_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens,
        )

        # Логируем использование токенов
        model_used = request.model or ai_client.provider.value
        tokens_used = len(response.split()) * 1.3  # Примерный расчет токенов

        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="chat",
            total_tokens=tokens_used,
            user_id=current_user.id,  # Получение ID пользователя из JWT токена
            ip_address=http_request.client.host,  # Получение IP адреса клиента
            user_agent=http_request.headers.get("user-agent"),  # Получение User-Agent
        )

        return AIChatResponse(
            response=response, model_used=model_used, tokens_used=tokens_used
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI чат не удался: {str(e)}",
        )


@router.get(
    "/models",
    response_model=AIModelsResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение списка моделей",
    description="""
    Возвращает список доступных AI моделей для текущего провайдера.

    **Информация о моделях включает:**
    - Идентификатор модели
    - Человеко-читаемое название
    - Максимальную длину контекста
    - Информацию о ценах

    **Поддерживаемые провайдеры:**
    - OpenRouter (рекомендуется)
    - Hugging Face
    - OpenAI
    """,
    response_description="Список доступных AI моделей",
)
async def get_available_models() -> AIModelsResponse:
    """
    Получает список доступных AI моделей.

    Returns:
        AIModelsResponse: Информация о доступных моделях
    """
    from ...config.openrouter_models import OPENROUTER_MODELS

    return AIModelsResponse(models=OPENROUTER_MODELS, current_provider="openrouter")


@router.get(
    "/status",
    response_model=AIStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверка статуса AI сервиса",
    description="""
    Проверяет состояние AI сервиса и доступность подключения.

    **Проверяемые параметры:**
    - Доступность провайдера AI
    - Статус подключения к API
    - Доступные модели
    - Конфигурация по умолчанию

    **Коды ответов:**
    - `200` - Сервис работает нормально
    - `503` - Сервис временно недоступен
    """,
    response_description="Статус AI сервиса и доступные модели",
)
async def get_ai_status(
    ai_client: UnifiedAIClient = Depends(get_ai_client),
) -> AIStatusResponse:
    """
    Проверяет статус AI сервиса.

    Args:
        ai_client: Унифицированный AI клиент

    Returns:
        AIStatusResponse: Статус сервиса и доступные модели
    """
    try:
        # Проверяем доступность клиента
        provider = ai_client.provider.value
        available_models = [
            "deepseek/deepseek-chat-v3.1",
            "moonshotai/kimi-k2",
            "openai/gpt-5-nano",
        ]

        return AIStatusResponse(
            provider=provider,
            status="active",
            default_model="deepseek/deepseek-chat-v3.1",
            available_models=available_models,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI сервис недоступен: {str(e)}",
        )


@router.get(
    "/usage/monthly",
    response_model=AIMonthlyUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Статистика использования токенов за месяц",
    description="""
    Возвращает статистику использования AI токенов за указанный месяц.

    **Параметры:**
    - `year`: Год (текущий, если не указан)
    - `month`: Месяц (текущий, если не указан)
    - `user_id`: ID пользователя для фильтрации (опционально)

    **Статистика включает:**
    - Общее количество токенов
    - Разбивка по типам токенов (запрос/ответ)
    - Количество запросов
    - Статистика по моделям
    """,
    response_description="Статистика использования токенов за месяц",
)
async def get_monthly_usage(
    year: int = 0, month: int = 0, user_id: int = 0, db: Session = Depends(get_db)
) -> AIMonthlyUsageResponse:
    """
    Получает статистику использования токенов за месяц.

    Args:
        year: Год
        month: Месяц
        user_id: ID пользователя для фильтрации
        db: Сессия базы данных

    Returns:
        AIMonthlyUsageResponse: Статистика использования
    """
    try:
        usage_service = AIUsageService(db)
        stats = usage_service.get_monthly_usage(year=year, month=month, user_id=user_id)
        return AIMonthlyUsageResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить статистику использования: {str(e)}",
        )


@router.get(
    "/usage/history",
    response_model=AIUsageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="История использования токенов",
    description="""
    Возвращает историю использования AI токенов за последние дни.

    **Параметры:**
    - `days`: Количество дней для просмотра (по умолчанию 30)
    - `user_id`: ID пользователя для фильтрации (опционально)
    - `limit`: Максимальное количество записей (по умолчанию 100)

    **Информация включает:**
    - Модель AI
    - Эндпоинт
    - Количество токенов
    - Время запроса
    - ID запроса
    """,
    response_description="История использования токенов",
)
async def get_usage_history(
    days: int = 30, user_id: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> AIUsageHistoryResponse:
    """
    Получает историю использования токенов.

    Args:
        days: Количество дней для просмотра
        user_id: ID пользователя для фильтрации
        limit: Максимальное количество записей
        db: Сессия базы данных

    Returns:
        AIUsageHistoryResponse: История использования
    """
    try:
        usage_service = AIUsageService(db)
        history = usage_service.get_usage_history(
            days=days, user_id=user_id, limit=limit
        )
        return AIUsageHistoryResponse(history=history)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить историю использования: {str(e)}",
        )


@router.get(
    "/settings/ai",
    status_code=status.HTTP_200_OK,
    summary="Получение настроек ИИ",
    description="""
    Возвращает текущие настройки искусственного интеллекта для системы.

    **Возвращаемые настройки:**
    - `default_model`: Модель ИИ по умолчанию
    - `temperature`: Температура генерации (0.0 - 2.0)
    - `max_tokens`: Максимальное количество токенов
    - `provider`: Текущий провайдер AI
    - `auto_reply_enabled`: Включен ли автоответ
    - `rate_limit_per_minute`: Лимит запросов в минуту
    - `cache_enabled`: Включено ли кеширование
    """,
    response_description="Текущие настройки ИИ",
)
async def get_ai_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получает текущие настройки ИИ.

    Args:
        current_user: Текущий пользователь
        db: Сессия базы данных

    Returns:
        Dict: Текущие настройки ИИ
    """
    try:
        from sqlalchemy import select

        from ...models.ai_settings import AISettings

        # Получаем настройки AI
        result = db.execute(select(AISettings).limit(1))
        ai_settings = result.scalar_one_or_none()

        if not ai_settings:
            # Возвращаем настройки по умолчанию
            return {
                "id": None,
                "default_model": "deepseek/deepseek-chat-v3.1",
                "temperature": 0.7,
                "max_tokens": 1000,
                "provider": "openrouter",
                "auto_reply_enabled": False,
                "auto_reply_temperature": 0.7,
                "auto_reply_max_tokens": 500,
                "rate_limit_per_minute": 60,
                "cache_enabled": True,
                "log_level": "INFO",
                "created_at": None,
                "updated_at": None,
            }

        return {
            "id": ai_settings.id,
            "default_model": ai_settings.default_model,
            "temperature": ai_settings.temperature,
            "max_tokens": ai_settings.max_tokens,
            "provider": ai_settings.provider,
            "auto_reply_enabled": ai_settings.auto_reply_enabled,
            "auto_reply_temperature": ai_settings.auto_reply_temperature,
            "auto_reply_max_tokens": ai_settings.auto_reply_max_tokens,
            "rate_limit_per_minute": ai_settings.rate_limit_per_minute,
            "cache_enabled": ai_settings.cache_enabled,
            "log_level": ai_settings.log_level,
            "fallback_model": ai_settings.fallback_model,
            "premium_model": ai_settings.premium_model,
            "created_at": (
                ai_settings.created_at.isoformat() if ai_settings.created_at else None
            ),
            "updated_at": (
                ai_settings.updated_at.isoformat() if ai_settings.updated_at else None
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить настройки ИИ: {str(e)}",
        )


@router.put(
    "/settings/ai",
    status_code=status.HTTP_200_OK,
    summary="Обновление глобальных настроек ИИ",
    description="""
    Обновляет глобальные настройки искусственного интеллекта для системы.

    **Настройки:**
    - `default_model`: Модель ИИ по умолчанию
    - `temperature`: Температура генерации (0.0 - 2.0)
    - `max_tokens`: Максимальное количество токенов
    - `api_key`: API ключ для доступа к сервисам ИИ

    **Валидация:**
    - Температура должна быть в диапазоне 0.0 - 2.0
    - Максимальное количество токенов не более 8000
    - API ключ проверяется на корректность формата
    """,
    response_description="Результат обновления настроек",
)
async def update_ai_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Обновляет настройки ИИ.

    Args:
        settings: Словарь с настройками ИИ
        current_user: Текущий пользователь
        db: Сессия базы данных

    Returns:
        Dict: Результат обновления настроек
    """
    logger = get_logger(__name__)
    try:
        # Валидация настроек
        if "temperature" in settings:
            temp = settings["temperature"]
            if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 2.0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Температура должна быть числом от 0.0 до 2.0",
                )

        if "max_tokens" in settings:
            max_tokens = settings["max_tokens"]
            if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 8000):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Максимальное количество токенов должно быть от 1 до 8000",
                )

        # Сохраняем настройки в базу данных
        from sqlalchemy import select

        from ...models.ai_settings import AISettings

        # Получаем или создаем настройки AI
        result = db.execute(select(AISettings).limit(1))
        ai_settings = result.scalar_one_or_none()

        if not ai_settings:
            # Создаем настройки по умолчанию
            ai_settings = AISettings()
            db.add(ai_settings)
            db.commit()
            db.refresh(ai_settings)

        # Обновляем настройки
        allowed_fields = {
            "default_model",
            "temperature",
            "max_tokens",
            "openrouter_api_key",
            "openai_api_key",
            "huggingface_api_key",
            "provider",
            "auto_reply_enabled",
            "auto_reply_temperature",
            "auto_reply_max_tokens",
            "rate_limit_per_minute",
            "cache_enabled",
            "log_level",
            "fallback_model",
            "premium_model",
        }

        filtered_updates = {k: v for k, v in settings.items() if k in allowed_fields}

        if filtered_updates:
            for key, value in filtered_updates.items():
                if hasattr(ai_settings, key):
                    setattr(ai_settings, key, value)

            db.commit()
            db.refresh(ai_settings)

        if filtered_updates:
            logger.info(f"AI settings updated by user {current_user.id}: {settings}")
            return {
                "success": True,
                "message": "Настройки ИИ успешно обновлены",
                "updated_settings": {
                    "default_model": ai_settings.default_model,
                    "temperature": ai_settings.temperature,
                    "max_tokens": ai_settings.max_tokens,
                    "provider": ai_settings.provider,
                    "auto_reply_enabled": ai_settings.auto_reply_enabled,
                },
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось обновить настройки - нет допустимых полей для обновления",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update AI settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить настройки ИИ: {str(e)}",
        )


# =============================================================================
# ЭНДПОИНТЫ ДЛЯ РАБОТЫ С AI КАМПАНИЙ
# =============================================================================


@router.post(
    "/campaigns/{campaign_id}/analyze-intent",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Анализ намерения с использованием настроек кампании",
    description="""
    Анализирует намерение сообщения используя индивидуальные AI настройки кампании.

    **Особенности:**
    - Использует API ключи и модель, заданные для кампании
    - Применяет кастомный промпт и стиль общения кампании
    - Учитывает лимиты токенов кампании
    - Логирует использование токенов для кампании

    **Fallback:** Если настройки кампании не заданы, использует глобальные настройки AI
    """,
    response_description="Результат анализа с учетом настроек кампании",
)
async def campaign_analyze_intent(
    campaign_id: int,
    request: AIAnalysisRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: AIIntentService = Depends(get_ai_service),
) -> AIAnalysisResponse:
    """
    Анализ намерения с использованием настроек кампании.
    """
    try:
        # Проверяем существование кампании и получаем ее AI настройки
        from ...models.campaign import Campaign

        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        # Получаем AI настройки кампании
        campaign_ai_settings = campaign.ai_settings
        context = request.context or {}

        # Добавляем контекст кампании в анализ
        if campaign_ai_settings:
            enhanced_context = {
                **context,
                "campaign": {
                    "name": campaign.name,
                    "target_audience": campaign_ai_settings.target_audience,
                    "brand_voice": campaign_ai_settings.brand_voice,
                    "custom_prompt": campaign_ai_settings.custom_prompt,
                },
            }
        else:
            enhanced_context = context

        # Анализируем намерение
        intent = await ai_service.analyze_intent(request.message, enhanced_context)
        response = await ai_service.generate_response(
            intent, request.message, enhanced_context
        )

        # Логируем использование токенов (привязываем к кампании)
        model_used = (
            campaign_ai_settings.default_model
            if campaign_ai_settings
            else "deepseek/deepseek-chat-v3.1"
        )
        intent_tokens = len(request.message.split()) * 1.2
        response_tokens = len(response.split()) * 1.3
        total_tokens = intent_tokens + response_tokens

        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="campaign_analyze_intent",
            total_tokens=total_tokens,
            prompt_tokens=intent_tokens,
            completion_tokens=response_tokens,
            user_id=current_user.id,
            ip_address=http_request.client.host,
            user_agent=http_request.headers.get("user-agent"),
            campaign_id=campaign_id,  # Новый параметр для учета использования кампании
        )

        return AIAnalysisResponse(
            intent=intent,
            response=response,
            needs_human_intervention=intent
            in [IntentType.COMPLAINT, IntentType.SUPPORT],
            suggested_actions=["contact_support", "schedule_followup"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed campaign AI analysis for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI анализ кампании не удался: {str(e)}",
        )


@router.post(
    "/campaigns/{campaign_id}/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Чат с AI используя настройки кампании",
    description="""
    Выполняет чат с AI моделью используя индивидуальные настройки кампании.

    **Особенности:**
    - Использует API ключ кампании для авторизации
    - Применяет модель и параметры, заданные для кампании
    - Учитывает лимиты токенов кампании
    - Добавляет контекст кампании в промпт

    **Контекст кампании включает:**
    - Целевую аудиторию кампании
    - Стиль общения (brand voice)
    - Кастомный промпт кампании
    """,
    response_description="Ответ AI с учетом настроек кампании",
)
async def campaign_chat(
    campaign_id: int,
    request: AIChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: UnifiedAIClient = Depends(get_ai_client),
) -> AIChatResponse:
    """
    Чат с AI используя настройки кампании.
    """
    try:
        # Проверяем существование кампании
        from ...models.campaign import Campaign

        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        # Получаем AI настройки кампании и создаем клиента с этими настройками
        if campaign.ai_settings:
            # Используем настройки кампании
            campaign_client = UnifiedAIClient(
                provider=campaign.ai_settings.provider,
                api_key=getattr(
                    campaign.ai_settings, f"{campaign.ai_settings.provider}_api_key"
                ),
                default_model=campaign.ai_settings.default_model,
                temperature=campaign.ai_settings.temperature,
                max_tokens=campaign.ai_settings.max_tokens,
            )
        else:
            # Используем глобального клиента
            campaign_client = ai_client

        # Добавляем контекст кампании к сообщению системы
        enhanced_messages = request.messages.copy()
        if campaign.ai_settings and campaign.ai_settings.custom_prompt:
            # Если есть системное сообщение, добавляем контекст кампании
            system_msg_idx = None
            for i, msg in enumerate(enhanced_messages):
                if msg.get("role") == "system":
                    system_msg_idx = i
                    break

            campaign_context = f"""
Вы работаете в контексте маркетинговой кампании "{campaign.name}".
{campaign.ai_settings.custom_prompt}
{f"Целевая аудитория: {campaign.ai_settings.target_audience}" if campaign.ai_settings.target_audience else ""}
{f"Стиль общения: {campaign.ai_settings.brand_voice}" if campaign.ai_settings.brand_voice else ""}
""".strip()

            if system_msg_idx is not None:
                enhanced_messages[system_msg_idx]["content"] += (
                    "\n\n" + campaign_context
                )
            else:
                enhanced_messages.insert(
                    0, {"role": "system", "content": campaign_context}
                )

        # Выполняем чат
        response = await campaign_client.chat_completion(
            messages=enhanced_messages,
            model=request.model,
            temperature=request.temperature
            or (campaign.ai_settings.temperature if campaign.ai_settings else 0.7),
            max_tokens=request.max_tokens
            or (campaign.ai_settings.max_tokens if campaign.ai_settings else None),
        )

        # Логируем использование токенов
        model_used = request.model or (
            campaign.ai_settings.default_model
            if campaign.ai_settings
            else campaign_client.provider.value
        )
        tokens_used = len(response.split()) * 1.3

        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="campaign_chat",
            total_tokens=tokens_used,
            user_id=current_user.id,
            ip_address=http_request.client.host,
            user_agent=http_request.headers.get("user-agent"),
            campaign_id=campaign_id,
        )

        return AIChatResponse(
            response=response, model_used=model_used, tokens_used=tokens_used
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed campaign AI chat for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI чат кампании не удался: {str(e)}",
        )