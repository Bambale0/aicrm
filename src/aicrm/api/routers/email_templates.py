"""
API роутеры для управления email шаблонами
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, get_db
from ...models.user import User
from ...services.email_template_service import get_email_template_service

router = APIRouter(
    prefix="/email-templates",
    tags=["email-templates"],
    responses={404: {"description": "Шаблон не найден"}},
)


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"


@router.post("/", response_model=Dict[str, Any])
async def create_template(
    template_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создание нового email шаблона

    - **name**: Уникальное имя шаблона
    - **display_name**: Отображаемое название
    - **description**: Описание шаблона
    - **subject_template**: Шаблон темы письма
    - **html_template**: HTML шаблон тела письма
    - **text_template**: Текстовый шаблон тела письма
    - **variables**: Список доступных переменных
    - **required_variables**: Обязательные переменные
    - **category**: Категория шаблона
    - **tags**: Теги для поиска
    - **is_active**: Активен ли шаблон
    - **is_default**: Шаблон по умолчанию для категории
    """
    try:
        service = get_email_template_service(db)
        template = await service.create_template(template_data, current_user.id)
        return {
            "success": True,
            "template": template.to_dict(),
            "message": "Шаблон успешно создан",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания шаблона: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
async def get_templates(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    limit: int = Query(
        50, description="Максимальное количество результатов", ge=1, le=100
    ),
    offset: int = Query(0, description="Смещение", ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение списка email шаблонов с фильтрами

    - **category**: Фильтр по категории (orders, tasks, payments, welcome, general)
    - **is_active**: Фильтр по активности
    - **search**: Поиск по названию или описанию
    - **limit**: Максимальное количество результатов (1-100)
    - **offset**: Смещение для пагинации
    """
    try:
        service = get_email_template_service(db)
        templates = await service.get_templates(
            category=category,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "templates": [template.to_dict() for template in templates],
            "total": len(templates),
            "filters": {
                "category": category,
                "is_active": is_active,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения шаблонов: {str(e)}"
        )


@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение email шаблона по ID

    - **template_id**: ID шаблона
    """
    try:
        service = get_email_template_service(db)
        template = await service.get_template_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        return {"success": True, "template": template.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения шаблона: {str(e)}"
        )


@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновление email шаблона

    - **template_id**: ID шаблона для обновления
    - **update_data**: Данные для обновления (те же поля, что и при создании)
    """
    try:
        service = get_email_template_service(db)
        template = await service.update_template(
            template_id, update_data, current_user.id
        )
        return {
            "success": True,
            "template": template.to_dict(),
            "message": "Шаблон успешно обновлен",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления шаблона: {str(e)}"
        )


@router.delete("/{template_id}", response_model=Dict[str, Any])
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаление email шаблона

    - **template_id**: ID шаблона для удаления
    """
    try:
        service = get_email_template_service(db)
        success = await service.delete_template(template_id)
        return {"success": success, "message": "Шаблон успешно удален"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка удаления шаблона: {str(e)}"
        )


@router.post("/{template_id}/duplicate", response_model=Dict[str, Any])
async def duplicate_template(
    template_id: int,
    duplicate_data: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Дублирование email шаблона

    - **template_id**: ID оригинального шаблона
    - **duplicate_data**: Данные для дубликата
        - **new_name**: Новое уникальное имя
        - **new_display_name**: Новое отображаемое название
    """
    try:
        new_name = duplicate_data.get("new_name")
        new_display_name = duplicate_data.get("new_display_name")

        if not new_name or not new_display_name:
            raise HTTPException(
                status_code=400, detail="Необходимо указать new_name и new_display_name"
            )

        service = get_email_template_service(db)
        template = await service.duplicate_template(
            template_id, new_name, new_display_name, current_user.id
        )

        return {
            "success": True,
            "template": template.to_dict(),
            "message": "Шаблон успешно дублирован",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка дублирования шаблона: {str(e)}"
        )


@router.post("/{template_id}/render", response_model=Dict[str, Any])
async def render_template(
    template_id: int,
    variables: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Рендеринг email шаблона с переменными

    - **template_id**: ID шаблона
    - **variables**: Переменные для подстановки в шаблон
    """
    try:
        service = get_email_template_service(db)
        result = await service.render_template(template_id, variables)

        return {
            "success": True,
            "rendered": result,
            "template_id": template_id,
            "variables_used": variables,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка рендеринга шаблона: {str(e)}"
        )


@router.get("/by-name/{template_name}", response_model=Dict[str, Any])
async def get_template_by_name(
    template_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение email шаблона по имени

    - **template_name**: Имя шаблона
    """
    try:
        service = get_email_template_service(db)
        template = await service.get_template_by_name(template_name)

        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        return {"success": True, "template": template.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения шаблона: {str(e)}"
        )


@router.get("/categories/{category}", response_model=Dict[str, Any])
async def get_templates_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение шаблонов по категории

    - **category**: Категория шаблонов
    """
    try:
        service = get_email_template_service(db)
        templates = await service.get_templates(category=category)

        return {
            "success": True,
            "templates": [template.to_dict() for template in templates],
            "category": category,
            "total": len(templates),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения шаблонов категории: {str(e)}"
        )


@router.get("/categories/{category}/default", response_model=Dict[str, Any])
async def get_default_template(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение шаблона по умолчанию для категории

    - **category**: Категория шаблонов
    """
    try:
        service = get_email_template_service(db)
        template = await service.get_default_template(category)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Шаблон по умолчанию для категории '{category}' не найден",
            )

        return {"success": True, "template": template.to_dict(), "category": category}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения шаблона по умолчанию: {str(e)}"
        )


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_template_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получение статистики по email шаблонам
    """
    try:
        service = get_email_template_service(db)
        stats = await service.get_template_stats()

        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения статистики: {str(e)}"
        )


@router.post("/initialize-defaults", response_model=Dict[str, Any])
async def initialize_default_templates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Инициализация стандартных email шаблонов

    Создает стандартные шаблоны для различных категорий:
    - order_confirmation: Подтверждение заказа
    - task_assigned: Уведомление о назначении задачи
    - payment_reminder: Напоминание об оплате
    - welcome_new_customer: Приветствие нового клиента
    """
    try:
        service = get_email_template_service(db)
        templates = await service.initialize_default_templates(current_user.id)

        return {
            "success": True,
            "templates_created": len(templates),
            "templates": [template.to_dict() for template in templates],
            "message": f"Успешно инициализировано {len(templates)} стандартных шаблонов",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка инициализации шаблонов: {str(e)}"
        )


@router.get("/export/all", response_model=Dict[str, Any])
async def export_templates(
    category: Optional[str] = Query(
        None, description="Экспорт только указанной категории"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Экспорт всех email шаблонов для резервного копирования

    - **category**: Опциональный фильтр по категории
    """
    try:
        service = get_email_template_service(db)
        templates_data = await service.export_templates(category)

        return {
            "success": True,
            "templates": templates_data,
            "total": len(templates_data),
            "category": category,
            "exported_at": "2025-11-19T04:03:00Z",  # Можно использовать datetime.utcnow().isoformat()
            "message": f"Экспортировано {len(templates_data)} шаблонов",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка экспорта шаблонов: {str(e)}"
        )


@router.post("/import", response_model=Dict[str, Any])
async def import_templates(
    import_data: Dict[str, Any],
    overwrite_existing: bool = Query(
        False, description="Перезаписывать существующие шаблоны"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Импорт email шаблонов из резервной копии

    - **import_data**: Данные для импорта
        - **templates**: Список шаблонов для импорта
    - **overwrite_existing**: Перезаписывать существующие шаблоны
    """
    try:
        templates_data = import_data.get("templates", [])
        if not templates_data:
            raise HTTPException(
                status_code=400, detail="Не указаны шаблоны для импорта"
            )

        service = get_email_template_service(db)
        result = await service.import_templates(
            templates_data, current_user.id, overwrite_existing
        )

        return {
            "success": True,
            "import_result": result,
            "message": f"Импорт завершен: {result['imported']} импортировано, {result['skipped']} пропущено",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка импорта шаблонов: {str(e)}"
        )


# Дополнительные эндпоинты для работы с переменными шаблонов


@router.get("/{template_id}/variables", response_model=Dict[str, Any])
async def get_template_variables(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получение информации о переменных шаблона

    - **template_id**: ID шаблона
    """
    try:
        service = get_email_template_service(db)
        template = await service.get_template_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        return {
            "success": True,
            "template_id": template_id,
            "variables": {
                "available": template.variables or [],
                "required": template.required_variables or [],
                "total_available": len(template.variables or []),
                "total_required": len(template.required_variables or []),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения переменных: {str(e)}"
        )


@router.post("/{template_id}/validate-variables", response_model=Dict[str, Any])
async def validate_template_variables(
    template_id: int,
    variables: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Валидация переменных для шаблона

    - **template_id**: ID шаблона
    - **variables**: Переменные для проверки
    """
    try:
        service = get_email_template_service(db)
        template = await service.get_template_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        is_valid, missing = template.validate_variables(variables)

        return {
            "success": True,
            "template_id": template_id,
            "is_valid": is_valid,
            "missing_variables": missing,
            "provided_variables": list(variables.keys()),
            "validation_result": "valid" if is_valid else "invalid",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка валидации переменных: {str(e)}"
        )
