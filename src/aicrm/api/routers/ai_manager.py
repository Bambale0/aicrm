"""
AI Manager роутер - управление промптами, услугами и товарами для ИИ
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...services.ai_prompt_service import AIPromptService
from ...services.service_service import ServiceService
from ...services.product_service import ProductService
from ..schemas.ai_manager import (
    AIPromptCreate, AIPromptUpdate, AIPromptResponse,
    ServiceCreate, ServiceUpdate, ServiceResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryResponse
)

router = APIRouter(
    prefix="/ai-manager",
    tags=["AI Manager"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Ресурс не найден"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"}
    }
)


# AI Prompts endpoints
@router.get(
    "/prompts",
    response_model=List[AIPromptResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить все AI промпты",
    description="Возвращает список всех AI промптов с их настройками"
)
async def get_prompts(db: Session = Depends(get_db)) -> List[AIPromptResponse]:
    """Получить все промпты"""
    service = AIPromptService(db)
    prompts = service.get_all_prompts()
    return [AIPromptResponse.from_orm(prompt) for prompt in prompts]


@router.get(
    "/prompts/active",
    response_model=List[AIPromptResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить активные AI промпты",
    description="Возвращает список активных AI промптов"
)
async def get_active_prompts(db: Session = Depends(get_db)) -> List[AIPromptResponse]:
    """Получить активные промпты"""
    service = AIPromptService(db)
    prompts = service.get_active_prompts()
    return [AIPromptResponse.from_orm(prompt) for prompt in prompts]


@router.get(
    "/prompts/{prompt_id}",
    response_model=AIPromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить AI промпт по ID",
    description="Возвращает AI промпт по его идентификатору"
)
async def get_prompt(prompt_id: int, db: Session = Depends(get_db)) -> AIPromptResponse:
    """Получить промпт по ID"""
    service = AIPromptService(db)
    prompt = service.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Промпт не найден")
    return AIPromptResponse.from_orm(prompt)


@router.post(
    "/prompts",
    response_model=AIPromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать AI промпт",
    description="Создает новый AI промпт с заданными параметрами"
)
async def create_prompt(prompt_data: AIPromptCreate, db: Session = Depends(get_db)) -> AIPromptResponse:
    """Создать новый промпт"""
    service = AIPromptService(db)
    prompt = service.create_prompt(**prompt_data.dict())
    return AIPromptResponse.from_orm(prompt)


@router.put(
    "/prompts/{prompt_id}",
    response_model=AIPromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить AI промпт",
    description="Обновляет существующий AI промпт"
)
async def update_prompt(prompt_id: int, prompt_data: AIPromptUpdate, db: Session = Depends(get_db)) -> AIPromptResponse:
    """Обновить промпт"""
    service = AIPromptService(db)
    prompt = service.update_prompt(prompt_id, **prompt_data.dict(exclude_unset=True))
    if not prompt:
        raise HTTPException(status_code=404, detail="Промпт не найден")
    return AIPromptResponse.from_orm(prompt)


@router.delete(
    "/prompts/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить AI промпт",
    description="Удаляет AI промпт по его идентификатору"
)
async def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """Удалить промпт"""
    service = AIPromptService(db)
    if not service.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Промпт не найден")


@router.patch(
    "/prompts/{prompt_id}/toggle",
    response_model=AIPromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Переключить статус AI промпта",
    description="Включает или выключает AI промпт"
)
async def toggle_prompt_status(prompt_id: int, db: Session = Depends(get_db)) -> AIPromptResponse:
    """Переключить статус промпта"""
    service = AIPromptService(db)
    prompt = service.toggle_prompt_status(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Промпт не найден")
    return AIPromptResponse.from_orm(prompt)


# Services endpoints
@router.get(
    "/services",
    response_model=List[ServiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить все услуги",
    description="Возвращает список всех услуг"
)
async def get_services(db: Session = Depends(get_db)) -> List[ServiceResponse]:
    """Получить все услуги"""
    service = ServiceService(db)
    services = service.get_all_services()
    return [ServiceResponse.from_orm(s) for s in services]


@router.get(
    "/services/active",
    response_model=List[ServiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить активные услуги",
    description="Возвращает список активных услуг"
)
async def get_active_services(db: Session = Depends(get_db)) -> List[ServiceResponse]:
    """Получить активные услуги"""
    service = ServiceService(db)
    services = service.get_active_services()
    return [ServiceResponse.from_orm(s) for s in services]


@router.get(
    "/services/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить услугу по ID",
    description="Возвращает услугу по ее идентификатору"
)
async def get_service(service_id: int, db: Session = Depends(get_db)) -> ServiceResponse:
    """Получить услугу по ID"""
    service = ServiceService(db)
    svc = service.get_service_by_id(service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return ServiceResponse.from_orm(svc)


@router.post(
    "/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать услугу",
    description="Создает новую услугу с заданными параметрами"
)
async def create_service(service_data: ServiceCreate, db: Session = Depends(get_db)) -> ServiceResponse:
    """Создать новую услугу"""
    service = ServiceService(db)
    svc = service.create_service(**service_data.dict())
    return ServiceResponse.from_orm(svc)


@router.put(
    "/services/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить услугу",
    description="Обновляет существующую услугу"
)
async def update_service(service_id: int, service_data: ServiceUpdate, db: Session = Depends(get_db)) -> ServiceResponse:
    """Обновить услугу"""
    service = ServiceService(db)
    svc = service.update_service(service_id, **service_data.dict(exclude_unset=True))
    if not svc:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return ServiceResponse.from_orm(svc)


@router.delete(
    "/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить услугу",
    description="Удаляет услугу по ее идентификатору"
)
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Удалить услугу"""
    service = ServiceService(db)
    if not service.delete_service(service_id):
        raise HTTPException(status_code=404, detail="Услуга не найдена")


@router.patch(
    "/services/{service_id}/toggle",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Переключить статус услуги",
    description="Включает или выключает услугу"
)
async def toggle_service_status(service_id: int, db: Session = Depends(get_db)) -> ServiceResponse:
    """Переключить статус услуги"""
    service = ServiceService(db)
    svc = service.toggle_service_status(service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return ServiceResponse.from_orm(svc)


@router.get(
    "/services/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить категории услуг",
    description="Возвращает список уникальных категорий услуг"
)
async def get_service_categories(db: Session = Depends(get_db)) -> CategoryResponse:
    """Получить категории услуг"""
    service = ServiceService(db)
    categories = service.get_categories()
    return CategoryResponse(categories=categories)


# Products endpoints
@router.get(
    "/products",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить все товары",
    description="Возвращает список всех товаров"
)
async def get_products(db: Session = Depends(get_db)) -> List[ProductResponse]:
    """Получить все товары"""
    service = ProductService(db)
    products = service.get_all_products()
    return [ProductResponse.from_orm(p) for p in products]


@router.get(
    "/products/active",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить активные товары",
    description="Возвращает список активных товаров"
)
async def get_active_products(db: Session = Depends(get_db)) -> List[ProductResponse]:
    """Получить активные товары"""
    service = ProductService(db)
    products = service.get_active_products()
    return [ProductResponse.from_orm(p) for p in products]


@router.get(
    "/products/in-stock",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить товары в наличии",
    description="Возвращает список товаров, которые есть в наличии"
)
async def get_in_stock_products(db: Session = Depends(get_db)) -> List[ProductResponse]:
    """Получить товары в наличии"""
    service = ProductService(db)
    products = service.get_in_stock_products()
    return [ProductResponse.from_orm(p) for p in products]


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить товар по ID",
    description="Возвращает товар по его идентификатору"
)
async def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Получить товар по ID"""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse.from_orm(product)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать товар",
    description="Создает новый товар с заданными параметрами"
)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    """Создать новый товар"""
    service = ProductService(db)
    product = service.create_product(**product_data.dict())
    return ProductResponse.from_orm(product)


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить товар",
    description="Обновляет существующий товар"
)
async def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)) -> ProductResponse:
    """Обновить товар"""
    service = ProductService(db)
    product = service.update_product(product_id, **product_data.dict(exclude_unset=True))
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse.from_orm(product)


@router.put(
    "/products/{product_id}/stock",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить количество товара",
    description="Обновляет количество товара на складе"
)
async def update_product_stock(product_id: int, stock_quantity: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Обновить количество товара на складе"""
    service = ProductService(db)
    product = service.update_stock(product_id, stock_quantity)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse.from_orm(product)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить товар",
    description="Удаляет товар по его идентификатору"
)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Удалить товар"""
    service = ProductService(db)
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Товар не найден")


@router.patch(
    "/products/{product_id}/toggle",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Переключить статус товара",
    description="Включает или выключает товар"
)
async def toggle_product_status(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Переключить статус товара"""
    service = ProductService(db)
    product = service.toggle_product_status(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse.from_orm(product)


@router.get(
    "/products/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить категории товаров",
    description="Возвращает список уникальных категорий товаров"
)
async def get_product_categories(db: Session = Depends(get_db)) -> CategoryResponse:
    """Получить категории товаров"""
    service = ProductService(db)
    categories = service.get_categories()
    return CategoryResponse(categories=categories)


@router.get(
    "/products/low-stock",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить товары с низким остатком",
    description="Возвращает список товаров с низким остатком на складе"
)
async def get_low_stock_products(threshold: int = 10, db: Session = Depends(get_db)) -> List[ProductResponse]:
    """Получить товары с низким остатком"""
    service = ProductService(db)
    products = service.get_low_stock_products(threshold)
    return [ProductResponse.from_orm(p) for p in products]


@router.get(
    "/products/out-of-stock",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить товары, которых нет в наличии",
    description="Возвращает список товаров, которых нет в наличии"
)
async def get_out_of_stock_products(db: Session = Depends(get_db)) -> List[ProductResponse]:
    """Получить товары, которых нет в наличии"""
    service = ProductService(db)
    products = service.get_out_of_stock_products()
    return [ProductResponse.from_orm(p) for p in products]
