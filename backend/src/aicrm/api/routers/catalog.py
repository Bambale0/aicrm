"""API роутеp для каталога товаров и услуг"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from ...core.dependencies import get_db
from ...models.product import Product
from ...models.service import Service
from ...models.category import Category

router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
    responses={404: {"description": "Не найдено"}},
)


@router.get("/categories", response_model=List[dict])
async def get_categories(
    type_filter: Optional[str] = Query(None, description="Тип категории: 'product' или 'service'"),
    db: Session = Depends(get_db)
):
    """Получение списка категорий с фильтром по типу"""
    query = db.query(Category)
    if type_filter:
        query = query.filter(Category.type == type_filter)
    return query.filter(Category.is_active.is_(True)).order_by(Category.sort_order).all()


@router.get("/products", response_model=List[dict])
async def get_products(
    category_id: Optional[int] = Query(None),
    is_featured: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Получение списка товаров с фильтрами"""
    query = db.query(Product)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.order_by(Product.sort_order).offset(offset).limit(limit).all()

    # Добавляем данные категории для каждого товара
    result = []
    for product in products:
        # Handle description length safely
        desc = product.description_short or product.description or ""
        if desc and len(desc) > 200:
            desc = desc[:200] + "..."

        # Safely handle category relationship
        category_data = None
        if product.category is not None:
            category_data = {
                "id": product.category.id,
                "name": product.category.name,
                "type": product.category.type
            }

        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": desc,
            "price": product.price,
            "price_old": product.price_old,
            "currency": product.currency,
            "main_image": product.main_image,
            "sku": product.sku,
            "category": category_data,
            "is_featured": product.is_featured,
            "view_count": product.view_count,
            "avg_rating": product.avg_rating,
            "created_at": product.created_at
        }
        result.append(product_dict)

    return result


@router.get("/products/{product_id}", response_model=dict)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Получение товара по ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Увеличиваем счетчик просмотров
    db.execute(
        text("UPDATE products SET view_count = view_count + 1 WHERE id = :product_id"),
        {"product_id": product.id}
    )
    db.commit()

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "description_short": product.description_short,
        "price": product.price,
        "price_old": product.price_old,
        "currency": product.currency,
        "images": product.images,
        "main_image": product.main_image,
        "video_url": product.video_url,
        "sku": product.sku,
        "barcode": product.barcode,
        "weight": product.weight,
        "dimensions": product.dimensions,
        "specifications": product.specifications,
        "category": {
            "id": product.category.id,
            "name": product.category.name,
            "type": product.category.type
        } if product.category is not None else None,
        "delivery_info": product.delivery_info,
        "pickup_available": product.pickup_available,
        "delivery_available": product.delivery_available,
        "seo_title": product.seo_title,
        "seo_description": product.seo_description,
        "seo_keywords": product.seo_keywords,
        "view_count": product.view_count,
        "order_count": product.order_count,
        "avg_rating": product.avg_rating,
        "tags": [tag.tag for tag in getattr(product, 'tags', [])] if getattr(product, 'tags', []) else [],
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }


@router.get("/services", response_model=List[dict])
async def get_services(
    category_id: Optional[int] = Query(None),
    is_featured: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Получение списка услуг с фильтрами"""
    query = db.query(Service)

    if category_id:
        query = query.filter(Service.category_id == category_id)
    if is_featured is not None:
        query = query.filter(Service.is_featured == is_featured)
    if is_active is not None:
        query = query.filter(Service.is_active == is_active)

    services = query.order_by(Service.sort_order).offset(offset).limit(limit).all()

    # Добавляем данные категории для каждой услуги
    result = []
    for service in services:
        # Handle description length safely
        desc = service.description_short or service.description or ""
        if desc and len(desc) > 200:
            desc = desc[:200] + "..."

        # Safely handle category relationship
        category_data = None
        if service.category is not None:
            category_data = {
                "id": service.category.id,
                "name": service.category.name,
                "type": service.category.type
            }

        service_dict = {
            "id": service.id,
            "name": service.name,
            "description": desc,
            "price_min": service.price_min,
            "price_max": service.price_max,
            "price_type": service.price_type,
            "duration_hours": service.duration_hours,
            "duration_days": service.duration_days,
            "category": category_data,
            "free_visit": service.free_visit,
            "contractor_name": service.contractor_name,
            "is_featured": service.is_featured,
            "view_count": service.view_count,
            "avg_rating": service.avg_rating,
            "created_at": service.created_at
        }
        result.append(service_dict)

    return result


@router.get("/services/{service_id}", response_model=dict)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Получение услуги по ID"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    # Увеличиваем счетчик просмотров
    db.execute(
        text("UPDATE services SET view_count = view_count + 1 WHERE id = :service_id"),
        {"service_id": service.id}
    )
    db.commit()

    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "description_short": service.description_short,
        "price_min": service.price_min,
        "price_max": service.price_max,
        "price_type": service.price_type,
        "duration_hours": service.duration_hours,
        "duration_days": service.duration_days,
        "work_included": service.work_included,
        "additional_services": service.additional_services,
        "requirements": service.requirements,
        "portfolio_images": service.portfolio_images,
        "portfolio_projects": service.portfolio_projects,
        "category": {
            "id": service.category.id,
            "name": service.category.name,
            "type": service.category.type
        } if service.category is not None else None,
        "warranty_info": service.warranty_info,
        "free_visit": service.free_visit,
        "service_area": service.service_area,
        "contractor_name": service.contractor_name,
        "contractor_contact": service.contractor_contact,
        "seo_title": service.seo_title,
        "seo_description": service.seo_description,
        "seo_keywords": service.seo_keywords,
        "view_count": service.view_count,
        "inquiry_count": service.inquiry_count,
        "avg_rating": service.avg_rating,
        "tags": [tag.tag for tag in getattr(service, 'tags', [])] if getattr(service, 'tags', []) else [],
        "created_at": service.created_at,
        "updated_at": service.updated_at
    }


@router.get("/search")
async def search_catalog(
    query: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None, description="'product' или 'service'"),
    category_id: Optional[int] = Query(None),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    """Поиск товаров и услуг по названию и описанию"""
    products_result = []
    services_result = []

    if not type_filter or type_filter == "product":
        # Поиск товаров
        product_query = db.query(Product).join(Category)

        if query:
            product_query = product_query.filter(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    Product.specifications.ilike(f"%{query}%")
                )
            )

        if category_id:
            product_query = product_query.filter(Product.category_id == category_id)

        products_result = product_query.filter(
            Product.is_active.is_(True)
        ).limit(limit).all()

    if not type_filter or type_filter == "service":
        # Поиск услуг
        service_query = db.query(Service).join(Category)

        if query:
            service_query = service_query.filter(
                or_(
                    Service.name.ilike(f"%{query}%"),
                    Service.description.ilike(f"%{query}%"),
                    Service.work_included.ilike(f"%{query}%")
                )
            )

        if category_id:
            service_query = service_query.filter(Service.category_id == category_id)

        services_result = service_query.filter(
            Service.is_active.is_(True)
        ).limit(limit).all()

    return {
        "query": query,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description_short": p.description_short,
                "price": p.price,
                "main_image": p.main_image,
                "category_name": p.category.name if p.category else None
            } for p in products_result
        ],
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "description_short": s.description_short,
                "price_min": s.price_min,
                "price_max": s.price_max,
                "category_name": s.category.name if s.category else None
            } for s in services_result
        ]
    }


@router.get("/featured")
async def get_featured_items(db: Session = Depends(get_db)):
    """Получение рекомендуемых товаров и услуг"""

    # Рекомендуемые товары
    featured_products = db.query(Product).join(Category).filter(
        Product.is_featured.is_(True),
        Product.is_active.is_(True),
        Category.is_active.is_(True)
    ).order_by(Product.sort_order).limit(10).all()

    # Рекомендуемые услуги
    featured_services = db.query(Service).join(Category).filter(
        Service.is_featured.is_(True),
        Service.is_active.is_(True),
        Category.is_active.is_(True)
    ).order_by(Service.sort_order).limit(10).all()

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description_short": p.description_short,
                "price": p.price,
                "price_old": p.price_old,
                "main_image": p.main_image,
                "category_name": p.category.name
            } for p in featured_products
        ],
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "description_short": s.description_short,
                "price_min": s.price_min,
                "price_max": s.price_max,
                "category_name": s.category.name
            } for s in featured_services
        ]
    }
