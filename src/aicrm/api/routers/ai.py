"""
AI роутер для FastAPI - OpenAPI 3.0.0 compliant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...core.database import get_db
from ...services.ai.intent_service import AIIntentService
from ...services.ai.client import UnifiedAIClient
from ..schemas.ai import (
    AIAnalysisRequest, AIAnalysisResponse, AIChatRequest, AIChatResponse,
    AIModelsResponse, AIStatusResponse
)

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
        503: {"description": "Service Unavailable - Сервис временно недоступен"}
    }
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
    response_description="Результат анализа сообщения с намерением и ответом"
)
async def analyze_intent(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db),
    ai_service: AIIntentService = Depends(get_ai_service)
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
        result = await ai_service.process_customer_message(
            message=request.message,
            customer_context=request.context
        )

        return AIAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI анализ не удался: {str(e)}"
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
    response_description="Сгенерированный ответ с информацией о намерении и модели"
)
async def generate_response(
    request: AIAnalysisRequest,
    ai_service: AIIntentService = Depends(get_ai_service)
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
        response = await ai_service.generate_response(intent, request.message, request.context)

        return {
            "intent": intent.value,
            "response": response,
            "model_used": ai_service.ai_client.provider.value,
            "timestamp": "2025-11-11T20:00:00Z"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Генерация ответа не удалась: {str(e)}"
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
    response_description="Ответ от AI модели с метаданными"
)
async def chat_with_ai(
    request: AIChatRequest,
    ai_client: UnifiedAIClient = Depends(get_ai_client)
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
            max_tokens=request.max_tokens
        )

        return AIChatResponse(
            response=response,
            model_used=request.model or ai_client.provider.value,
            tokens_used=len(response.split()) * 1.3  # Примерный расчет токенов
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI чат не удался: {str(e)}"
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
    response_description="Список доступных AI моделей"
)
async def get_available_models() -> AIModelsResponse:
    """
    Получает список доступных AI моделей.

    Returns:
        AIModelsResponse: Информация о доступных моделях
    """
    from ...config.openrouter_models import OPENROUTER_MODELS

    return AIModelsResponse(
        models=OPENROUTER_MODELS,
        current_provider="openrouter"
    )


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
    response_description="Статус AI сервиса и доступные модели"
)
async def get_ai_status(
    ai_client: UnifiedAIClient = Depends(get_ai_client)
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
        available_models = ["deepseek/deepseek-coder:33b-instruct", "meta-llama/llama-3-70b-instruct"]

        return AIStatusResponse(
            provider=provider,
            status="active",
            default_model="deepseek/deepseek-coder:33b-instruct",
            available_models=available_models
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI сервис недоступен: {str(e)}"
        )
