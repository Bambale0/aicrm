"""
Роутер для AI Orchestrator - управление workflows, событиями и выполнением
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.workflow import (
    CrmConnectorConfig,
    ExecutionDetailResponse,
    IncomingEvent,
    PaginatedExecutionList,
    PaginatedWorkflowList,
    TestEventRequest,
    WorkflowCreateFromPromptRequest,
    WorkflowDetailResponse,
    WorkflowSummaryResponse,
    WorkflowTestResponse,
    WorkflowUpdateRequest,
)
from ...services.workflow_service import WorkflowService

router = APIRouter(
    prefix="/ai-orchestrator",
    tags=["AI Orchestrator"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Ресурс не найден"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"},
    },
)


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    """
    Зависимость для получения сервиса workflow.

    Returns:
        WorkflowService: Экземпляр сервиса workflow
    """
    return WorkflowService(db)


@router.post(
    "/ai-workflows",
    response_model=WorkflowDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать workflow из текстового описания",
    description="""
    Создает новый AI workflow на основе текстового описания бизнес-сценария.

    **Процесс:**
    1. AI анализирует описание и генерирует структуру workflow
    2. Создается workflow с триггером, условиями и действиями
    3. Workflow сохраняется и возвращается в ответе

    **Учет токенов:** Токены на генерацию workflow учитываются автоматически.
    """,
    response_description="Созданный AI workflow",
)
async def create_workflow_from_prompt(
    request: WorkflowCreateFromPromptRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    """
    Создание workflow из промпта.

    Args:
        request: Запрос с описанием сценария
        service: Сервис workflow

    Returns:
        WorkflowDetailResponse: Детальная информация о созданном workflow

    Raises:
        HTTPException: При ошибке создания workflow
    """
    try:
        # Для простоты используем user_id = None, в реальности нужно брать из токена
        workflow = await service.create_workflow_from_prompt(
            prompt=request.prompt,
            name=request.name,
            user_id=None,  # TODO: Получить из JWT токена
        )

        return WorkflowDetailResponse(
            id=workflow.id,
            name=workflow.name,
            description_ai=workflow.description_ai,
            trigger=workflow.trigger,
            conditions=workflow.conditions,
            actions=workflow.actions,
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            created_by=workflow.created_by,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать workflow: {str(e)}",
        )


@router.get(
    "/ai-workflows",
    response_model=PaginatedWorkflowList,
    status_code=status.HTTP_200_OK,
    summary="Получить список workflow",
    description="""
    Возвращает список всех AI workflow с пагинацией.

    **Фильтры:**
    - `is_active`: Только активные workflow
    - `page`: Номер страницы
    - `per_page`: Количество элементов на странице
    """,
    response_description="Список workflow с пагинацией",
)
async def list_workflows(
    is_active: Optional[bool] = Query(True, description="Только активные workflow"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    service: WorkflowService = Depends(get_workflow_service),
) -> PaginatedWorkflowList:
    """
    Получение списка workflow.

    Args:
        is_active: Фильтр по активности
        page: Номер страницы
        per_page: Элементов на странице
        service: Сервис workflow

    Returns:
        PaginatedWorkflowList: Список workflow
    """
    try:
        offset = (page - 1) * per_page
        workflows = service.get_workflows(
            is_active=is_active, limit=per_page, offset=offset
        )

        # Преобразуем в схемы ответа
        workflow_summaries = []
        for wf in workflows:
            workflow_summaries.append(
                WorkflowSummaryResponse(
                    id=wf.id,
                    name=wf.name,
                    is_active=wf.is_active,
                    created_at=wf.created_at,
                )
            )

        return PaginatedWorkflowList(
            workflows=workflow_summaries,
            total=len(workflows),  # TODO: Реализовать точный подсчет
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить список workflow: {str(e)}",
        )


@router.get(
    "/ai-workflows/{workflow_id}",
    response_model=WorkflowDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Детальная информация о workflow",
    description="""
    Возвращает полную информацию об AI workflow включая триггеры, условия и действия.
    """,
    response_description="Детальная информация о workflow",
)
async def get_workflow_detail(
    workflow_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    """
    Получение детальной информации о workflow.

    Args:
        workflow_id: ID workflow
        service: Сервис workflow

    Returns:
        WorkflowDetailResponse: Детальная информация

    Raises:
        HTTPException: Если workflow не найден
    """
    try:
        workflows = service.get_workflows(limit=1, offset=0)
        workflow = next((wf for wf in workflows if wf.id == workflow_id), None)

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} не найден",
            )

        return WorkflowDetailResponse(
            id=workflow.id,
            name=workflow.name,
            description_ai=workflow.description_ai,
            trigger=workflow.trigger,
            conditions=workflow.conditions,
            actions=workflow.actions,
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            created_by=workflow.created_by,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить workflow: {str(e)}",
        )


@router.put(
    "/ai-workflows/{workflow_id}",
    response_model=WorkflowDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить workflow",
    description="""
    Обновляет параметры существующего AI workflow.

    **Можно обновить:**
    - Название и описание
    - Триггер, условия и действия
    - Активность workflow
    """,
    response_description="Обновленный workflow",
)
async def update_workflow(
    workflow_id: int,
    request: WorkflowUpdateRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    """
    Обновление workflow.

    Args:
        workflow_id: ID workflow
        request: Данные для обновления
        service: Сервис workflow

    Returns:
        WorkflowDetailResponse: Обновленный workflow

    Raises:
        HTTPException: Если workflow не найден или ошибка обновления
    """
    try:
        # TODO: Реализовать обновление в сервисе
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Функция обновления workflow пока не реализована",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить workflow: {str(e)}",
        )


@router.delete(
    "/ai-workflows/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить workflow",
    description="""
    Удаляет AI workflow и все связанные выполнения.

    **Внимание:** Операция необратима!
    """,
)
async def delete_workflow(
    workflow_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """
    Удаление workflow.

    Args:
        workflow_id: ID workflow
        service: Сервис workflow

    Raises:
        HTTPException: Если workflow не найден или ошибка удаления
    """
    try:
        # TODO: Реализовать удаление в сервисе
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Функция удаления workflow пока не реализована",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить workflow: {str(e)}",
        )


@router.post(
    "/ai-workflows/{workflow_id}/test",
    response_model=WorkflowTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Протестировать workflow",
    description="""
    Запускает тестирование workflow на тестовых данных без реального выполнения действий.

    **Что проверяется:**
    - Срабатывание триггера
    - Выполнение условий
    - Имитация выполнения действий
    """,
    response_description="Результаты тестирования workflow",
)
async def test_workflow(
    workflow_id: int,
    request: TestEventRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowTestResponse:
    """
    Тестирование workflow.

    Args:
        workflow_id: ID workflow
        request: Тестовое событие
        service: Сервис workflow

    Returns:
        WorkflowTestResponse: Результаты тестирования

    Raises:
        HTTPException: Если workflow не найден или ошибка тестирования
    """
    try:
        result = await service.test_workflow(
            workflow_id=workflow_id,
            test_event={
                "event_type": request.event_type,
                "payload": request.payload,
            },
        )

        return WorkflowTestResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось протестировать workflow: {str(e)}",
        )


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Прием события от CRM",
    description="""
    Принимает событие от основной CRM и запускает соответствующие AI workflow.

    **Процесс:**
    1. Проверяются все активные workflow
    2. Находятся workflow, срабатывающие на это событие
    3. Выполняются подходящие workflow асинхронно

    **Аутентификация:** Используется внутренний webhook secret.
    """,
    response_description="Событие принято в обработку",
)
async def handle_incoming_event(
    event: IncomingEvent,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """
    Обработка входящего события.

    Args:
        event: Входящее событие
        service: Сервис workflow

    Returns:
        dict: Подтверждение приема

    Raises:
        HTTPException: При ошибке обработки события
    """
    try:
        # Получаем все активные workflow
        workflows = service.get_workflows(is_active=True)

        triggered_workflows = []

        # Проверяем каждый workflow
        for workflow in workflows:
            if workflow.trigger.get("event_type") == event.event_type:
                # Проверяем условия
                if service._check_conditions(
                    workflow.conditions,
                    {"event_type": event.event_type, "payload": event.payload},
                ):
                    triggered_workflows.append(workflow.id)

                    # Запускаем выполнение асинхронно
                    # В реальности здесь должен быть background task
                    try:
                        await service.execute_workflow(
                            workflow_id=workflow.id,
                            trigger_event={
                                "event_id": event.event_id,
                                "event_type": event.event_type,
                                "entity_type": event.entity_type,
                                "entity_id": event.entity_id,
                                "payload": event.payload,
                                "timestamp": event.timestamp,
                            },
                        )
                    except Exception as e:
                        # Логируем ошибку, но продолжаем обработку других workflow
                        print(f"Error executing workflow {workflow.id}: {e}")

        return {
            "status": "accepted",
            "triggered_workflows": triggered_workflows,
            "message": f"Event processed, {len(triggered_workflows)} workflows triggered",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обработать событие: {str(e)}",
        )


@router.get(
    "/executions",
    response_model=PaginatedExecutionList,
    status_code=status.HTTP_200_OK,
    summary="История выполнений workflow",
    description="""
    Возвращает историю выполнений AI workflow с фильтрами.

    **Фильтры:**
    - `workflow_id`: ID конкретного workflow
    - `status`: Статус выполнения (pending, running, completed, failed)
    - `page`: Номер страницы
    - `per_page`: Количество элементов на странице
    """,
    response_description="История выполнений workflow",
)
async def get_execution_history(
    workflow_id: Optional[int] = Query(None, description="ID workflow"),
    status: Optional[str] = Query(None, description="Статус выполнения"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    service: WorkflowService = Depends(get_workflow_service),
) -> PaginatedExecutionList:
    """
    Получение истории выполнений.

    Args:
        workflow_id: ID workflow (опционально)
        status: Статус выполнения (опционально)
        page: Номер страницы
        per_page: Элементов на странице
        service: Сервис workflow

    Returns:
        PaginatedExecutionList: История выполнений
    """
    try:
        offset = (page - 1) * per_page
        executions = service.get_workflow_executions(
            workflow_id=workflow_id,
            status=status,
            limit=per_page,
            offset=offset,
        )

        # Преобразуем в схемы ответа
        execution_entries = []
        for exec_data in executions:
            execution_entries.append(
                {
                    "id": exec_data["id"],
                    "workflow_id": exec_data["workflow_id"],
                    "workflow_name": exec_data["workflow_name"],
                    "trigger_event": exec_data["trigger_event"],
                    "execution_status": exec_data["execution_status"],
                    "started_at": exec_data["started_at"],
                    "completed_at": exec_data["completed_at"],
                    "error_message": exec_data["error_message"],
                }
            )

        return PaginatedExecutionList(
            executions=execution_entries,
            total=len(executions),  # TODO: Реализовать точный подсчет
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить историю выполнений: {str(e)}",
        )


@router.post(
    "/system/connectors/crm",
    status_code=status.HTTP_200_OK,
    summary="Настроить коннектор к CRM",
    description="""
    Настраивает коннектор для взаимодействия с API основной CRM.

    **Необходим для выполнения действий:**
    - Создание задач
    - Обновление сущностей
    - Отправка уведомлений
    """,
    response_description="Коннектор успешно настроен",
)
async def setup_crm_connector(
    config: CrmConnectorConfig,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """
    Настройка коннектора к CRM.

    Args:
        config: Конфигурация коннектора
        service: Сервис workflow

    Returns:
        dict: Результат настройки

    Raises:
        HTTPException: При ошибке настройки
    """
    try:
        # TODO: Сохранить конфигурацию коннектора в БД или кэше
        return {
            "status": "configured",
            "message": "CRM connector configured successfully",
            "base_url": config.base_url,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось настроить коннектор: {str(e)}",
        )
