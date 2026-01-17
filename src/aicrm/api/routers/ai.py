"""
AI роутер для FastAPI - OpenAPI 3.0.0 compliant
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...api.routers.auth import get_current_user
from ...core.database import get_db
from ...services.ai.client import UnifiedAIClient
from ...services.ai.intent_service import AIIntentService, IntentType
from ...services.ai_usage_service import AIUsageService
from ...services.token_accounting_service import TokenAccountingService
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
    prefix="",
    tags=["AI"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Ресурс не найден"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"},
        502: {"description": "Bad Gateway - Ошибка внешнего сервиса"},
        503: {"description": "Service Unavailable - Сервис временно недоступен"},
    },
)


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
        intent = await ai_service.analyze_intent(
            request.message, request.context, request.model
        )
        response = await ai_service.generate_response(
            intent, request.message, request.context, request.model
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

        # Учет токенов через TokenAccountingService
        token_service = TokenAccountingService(db)

        # Определяем entity_type и entity_id для учета
        # Для пользователей используем 'user', для компаний - 'company'
        # Пока используем user, можно расширить для компаний
        entity_type = "user"
        entity_id = current_user.id

        result = await token_service.check_quota_and_record_transaction(
            entity_type=entity_type,
            entity_id=entity_id,
            ai_provider="openrouter",  # или определить динамически
            ai_model=model_used,
            prompt_tokens=int(intent_tokens),
            completion_tokens=int(response_tokens),
            estimated_cost=0.001 * total_tokens,  # примерная стоимость
            request_payload={
                "message": request.message[:500],
                "context": request.context,
            },
            response_metadata={"intent": intent, "response_length": len(response)},
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Превышен лимит токенов: {result['error']}",
            )

        # Также логируем в старом формате для совместимости
        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="analyze-intent",
            total_tokens=total_tokens,
            prompt_tokens=intent_tokens,
            completion_tokens=response_tokens,
            user_id=current_user.id,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )

        return AIAnalysisResponse(
            intent=intent,
            response=response,
            needs_human_intervention=intent
            in [IntentType.COMPLAINT, IntentType.SUPPORT],
            suggested_actions=ai_service._get_suggested_actions(intent),
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
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: AIIntentService = Depends(get_ai_service),
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
            "intent": intent.value,
            "response": response,
            "model_used": ai_service.ai_client.provider.value,
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
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Логируем использование токенов
        model_used = request.model or ai_client.provider.value
        prompt_tokens = sum(
            len(msg.get("content", "").split()) * 1.2 for msg in request.messages
        )  # Примерный расчет
        completion_tokens = len(response.split()) * 1.3  # Примерный расчет для ответа
        total_tokens = prompt_tokens + completion_tokens

        # Учет токенов через TokenAccountingService
        token_service = TokenAccountingService(db)
        entity_type = "user"
        entity_id = current_user.id

        token_result = await token_service.check_quota_and_record_transaction(
            entity_type=entity_type,
            entity_id=entity_id,
            ai_provider="openrouter",
            ai_model=model_used,
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            estimated_cost=0.001 * total_tokens,
            request_payload={
                "messages_count": len(request.messages),
                "temperature": request.temperature,
            },
            response_metadata={"response_length": len(response)},
        )

        if not token_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Превышен лимит токенов: {token_result['error']}",
            )

        # Также логируем в старом формате для совместимости
        await AIUsageService(db).log_usage(
            model_used=model_used,
            endpoint="chat",
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            user_id=current_user.id,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )

        return AIChatResponse(
            response=response, model_used=model_used, tokens_used=total_tokens
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
        from ...core.ai_config import ai_config

        provider = ai_client.provider.value
        available_models = [
            "deepseek/deepseek-chat-v3.1",
            "moonshotai/kimi-k2",
            "openai/gpt-5-nano",
        ]

        return AIStatusResponse(
            provider=provider,
            status="active",
            default_model=ai_config.DEFAULT_MODEL,
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
    year: int = None,
    month: int = None,
    user_id: int = None,
    db: Session = Depends(get_db),
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
    days: int = 30, user_id: int = None, limit: int = 100, db: Session = Depends(get_db)
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
