"""
Роутер для учета токенов AI - OpenAPI 3.1.0 compliant
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.token_accounting import (
    TokenAlertInfo,
    TokenQuotaListResponse,
    TokenQuotaResponse,
    TokenQuotaSetRequest,
    TokenQuotaUpdateRequest,
    TokenTransactionListResponse,
    TokenTransactionResponse,
    TokenUsageStats,
)
from ...services.token_accounting_service import TokenAccountingService

router = APIRouter(
    prefix="/token-quotas",
    tags=["Token Accounting"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Ресурс не найден"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"},
    },
)


def get_token_accounting_service(
    db: Session = Depends(get_db),
) -> TokenAccountingService:
    """
    Зависимость для получения сервиса учета токенов.

    Returns:
        TokenAccountingService: Экземпляр сервиса учета токенов
    """
    return TokenAccountingService(db)


@router.post(
    "",
    response_model=TokenQuotaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Установить или обновить квоту токенов",
    description="""
    Создает новую квоту токенов или обновляет существующую для компании/пользователя.

    **Типы квот:**
    - `monthly` - месячный лимит с автоматическим сбросом
    - `total` - общий лимит без сброса
    - `per_workflow` - лимит на отдельный workflow

    **Алерт:** Устанавливает порог в процентах для уведомлений о приближении к лимиту.
    """,
    response_description="Созданная или обновленная квота токенов",
)
async def set_token_quota(
    request: TokenQuotaSetRequest,
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> TokenQuotaResponse:
    """
    Устанавливает или обновляет квоту токенов.

    Args:
        request: Запрос с параметрами квоты
        service: Сервис учета токенов

    Returns:
        TokenQuotaResponse: Информация о квоте

    Raises:
        HTTPException: При ошибке создания/обновления квоты
    """
    try:
        quota = await service.create_or_update_quota(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            quota_type=request.quota_type,
            limit_tokens=request.limit_tokens,
            alert_threshold=request.alert_threshold,
        )

        return TokenQuotaResponse(
            id=quota.id,
            entity_type=quota.entity_type,
            entity_id=quota.entity_id,
            quota_type=quota.quota_type,
            limit_tokens=quota.limit_tokens,
            used_tokens=quota.used_tokens,
            reset_at=quota.reset_at,
            alert_threshold=quota.alert_threshold,
            is_active=quota.is_active,
            created_at=quota.created_at,
            updated_at=quota.updated_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось установить квоту: {str(e)}",
        )


@router.get(
    "/{entity_type}/{entity_id}/current",
    response_model=TokenUsageStats,
    status_code=status.HTTP_200_OK,
    summary="Получить текущий баланс токенов",
    description="""
    Возвращает текущую статистику использования токенов для компании или пользователя.

    **Включает:**
    - Текущий лимит и использование
    - Процент использования
    - Дату следующего сброса
    - Топ workflow по потреблению токенов
    - Среднее дневное использование
    """,
    response_description="Текущая статистика использования токенов",
)
async def get_current_token_usage(
    entity_type: str,
    entity_id: int,
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> TokenUsageStats:
    """
    Получает текущую статистику использования токенов.

    Args:
        entity_type: Тип сущности ('company' или 'user')
        entity_id: ID сущности
        service: Сервис учета токенов

    Returns:
        TokenUsageStats: Статистика использования

    Raises:
        HTTPException: Если квота не найдена или ошибка получения данных
    """
    try:
        stats = service.get_quota_usage_stats(entity_type, entity_id, "monthly")

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Квота для {entity_type} {entity_id} не найдена",
            )

        return TokenUsageStats(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить статистику: {str(e)}",
        )


@router.get(
    "",
    response_model=TokenQuotaListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить список квот токенов",
    description="""
    Возвращает список всех квот токенов с пагинацией.

    **Фильтры:**
    - `entity_type`: Тип сущности ('company' или 'user')
    - `entity_id`: ID конкретной сущности
    - `quota_type`: Тип квоты
    - `is_active`: Только активные квоты
    """,
    response_description="Список квот токенов",
)
async def list_token_quotas(
    entity_type: Optional[str] = Query(None, description="Тип сущности"),
    entity_id: Optional[int] = Query(None, description="ID сущности"),
    quota_type: Optional[str] = Query(None, description="Тип квоты"),
    is_active: Optional[bool] = Query(True, description="Только активные квоты"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> TokenQuotaListResponse:
    """
    Получает список квот токенов с фильтрами.

    Args:
        entity_type: Фильтр по типу сущности
        entity_id: Фильтр по ID сущности
        quota_type: Фильтр по типу квоты
        is_active: Фильтр по активности
        page: Номер страницы
        per_page: Элементов на странице
        service: Сервис учета токенов

    Returns:
        TokenQuotaListResponse: Список квот
    """
    try:
        # Здесь должна быть реализация фильтрации и пагинации
        # Пока возвращаем пустой список для примера
        quotas = []  # TODO: Реализовать получение списка квот

        return TokenQuotaListResponse(
            quotas=quotas,
            total=len(quotas),
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить список квот: {str(e)}",
        )


@router.put(
    "/{quota_id}",
    response_model=TokenQuotaResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить квоту токенов",
    description="""
    Обновляет параметры существующей квоты токенов.

    **Можно обновить:**
    - Лимит токенов
    - Порог уведомлений
    - Активность квоты
    """,
    response_description="Обновленная квота токенов",
)
async def update_token_quota(
    quota_id: int,
    request: TokenQuotaUpdateRequest,
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> TokenQuotaResponse:
    """
    Обновляет квоту токенов.

    Args:
        quota_id: ID квоты
        request: Данные для обновления
        service: Сервис учета токенов

    Returns:
        TokenQuotaResponse: Обновленная квота

    Raises:
        HTTPException: Если квота не найдена или ошибка обновления
    """
    try:
        # TODO: Реализовать обновление квоты в сервисе
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Функция обновления квоты пока не реализована",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить квоту: {str(e)}",
        )


@router.delete(
    "/{quota_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить квоту токенов",
    description="""
    Удаляет квоту токенов и все связанные транзакции.

    **Внимание:** Операция необратима!
    """,
)
async def delete_token_quota(
    quota_id: int,
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> None:
    """
    Удаляет квоту токенов.

    Args:
        quota_id: ID квоты
        service: Сервис учета токенов

    Raises:
        HTTPException: Если квота не найдена или ошибка удаления
    """
    try:
        # TODO: Реализовать удаление квоты в сервисе
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Функция удаления квоты пока не реализована",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить квоту: {str(e)}",
        )


@router.get(
    "/alerts",
    response_model=List[TokenAlertInfo],
    status_code=status.HTTP_200_OK,
    summary="Получить алерты о превышении лимитов",
    description="""
    Возвращает список квот, которые достигли порога уведомлений.

    **Алерт срабатывает когда:**
    - Процент использования >= установленного порога
    - Квота активна и имеет лимит
    """,
    response_description="Список алертов о превышении лимитов",
)
async def get_token_alerts(
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> List[TokenAlertInfo]:
    """
    Получает список алертов о превышении лимитов.

    Args:
        service: Сервис учета токенов

    Returns:
        List[TokenAlertInfo]: Список алертов
    """
    try:
        alerts = service.get_quota_alerts()
        return [TokenAlertInfo(**alert) for alert in alerts]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить алерты: {str(e)}",
        )


@router.get(
    "/transactions",
    response_model=TokenTransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить историю транзакций токенов",
    description="""
    Возвращает историю использования токенов с фильтрами.

    **Фильтры:**
    - `quota_id`: ID конкретной квоты
    - `entity_type` + `entity_id`: Для сущности (компания/пользователь)
    - `limit`: Максимальное количество записей
    - `offset`: Смещение для пагинации
    """,
    response_description="История транзакций токенов",
)
async def get_token_transactions(
    quota_id: Optional[int] = Query(None, description="ID квоты"),
    entity_type: Optional[str] = Query(None, description="Тип сущности"),
    entity_id: Optional[int] = Query(None, description="ID сущности"),
    limit: int = Query(
        100, ge=1, le=1000, description="Максимальное количество записей"
    ),
    offset: int = Query(0, ge=0, description="Смещение"),
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> TokenTransactionListResponse:
    """
    Получает историю транзакций токенов.

    Args:
        quota_id: ID квоты
        entity_type: Тип сущности
        entity_id: ID сущности
        limit: Максимальное количество записей
        offset: Смещение
        service: Сервис учета токенов

    Returns:
        TokenTransactionListResponse: Список транзакций
    """
    try:
        transactions = service.get_transaction_history(
            quota_id=quota_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

        # Преобразуем в схемы ответа
        transaction_responses = []
        for tx in transactions:
            transaction_responses.append(
                TokenTransactionResponse(
                    id=tx.id,
                    quota_id=tx.quota_id,
                    workflow_execution_id=tx.workflow_execution_id,
                    ai_provider=tx.ai_provider,
                    ai_model=tx.ai_model,
                    prompt_tokens=tx.prompt_tokens,
                    completion_tokens=tx.completion_tokens,
                    total_tokens=tx.total_tokens,
                    estimated_cost=tx.estimated_cost,
                    request_payload=tx.request_payload,
                    response_metadata=tx.response_metadata,
                    timestamp=tx.created_at,
                )
            )

        return TokenTransactionListResponse(
            transactions=transaction_responses,
            total=len(transaction_responses),
            page=(offset // limit) + 1,
            per_page=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить историю транзакций: {str(e)}",
        )


@router.post(
    "/reset-monthly",
    status_code=status.HTTP_200_OK,
    summary="Сбросить месячные квоты",
    description="""
    Сбрасывает использованные токены для всех месячных квот,
    дата сброса которых уже прошла.

    **Вызывается автоматически по расписанию.**
    """,
    response_description="Результат сброса квот",
)
async def reset_monthly_quotas(
    service: TokenAccountingService = Depends(get_token_accounting_service),
) -> dict:
    """
    Сбрасывает месячные квоты.

    Args:
        service: Сервис учета токенов

    Returns:
        dict: Результат операции
    """
    try:
        reset_count = service.reset_monthly_quotas()

        return {
            "success": True,
            "message": f"Сброшено {reset_count} месячных квот",
            "reset_count": reset_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сбросить квоты: {str(e)}",
        )
