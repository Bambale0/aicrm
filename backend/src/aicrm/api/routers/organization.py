"""
Маршруты для управления организациями в мультитенантной системе
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from typing import Optional

from ...core.database import get_master_db
from ...services.organization_service import organization_service
from ...models.organization import Organization
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    """Схема создания организации"""
    name: constr(min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    plan: str = "free"


class OrganizationResponse(BaseModel):
    """Схема ответа с информацией об организации"""
    id: int
    name: str
    slug: str
    email: str
    phone: Optional[str]
    website: Optional[str]
    plan: str
    is_active: bool
    is_verified: bool
    max_users: int
    max_storage_mb: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/register", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_master_db)
):
    """
    Регистрация новой организации с созданием отдельной базы данных.
    
    Этот эндпоинт создает:
    1. Запись организации в мастер-базу
    2. Отдельную базу данных для организации
    3. Администратора организации в новой базе
    4. Все необходимые таблицы и структуру
    
    Args:
        org_data: Данные для создания организации
        
    Returns:
        OrganizationResponse: Информация о созданной организации
        
    Raises:
        HTTPException: При ошибке создания организации
    """
    try:
        # Создание организации
        organization = organization_service.create_organization(
            db=db,
            name=org_data.name,
            email=org_data.email,
            phone=org_data.phone,
            website=org_data.website,
            plan=org_data.plan
        )
        
        logger.info(f"Organization registered successfully: {organization.name} (ID: {organization.id})")
        
        return OrganizationResponse(
            id=int(organization.id),
            name=str(organization.name),
            slug=str(organization.slug),
            email=str(organization.email),
            phone=str(organization.phone) if organization.phone else None,
            website=str(organization.website) if organization.website else None,
            plan=str(organization.plan),
            is_active=bool(organization.is_active),
            is_verified=bool(organization.is_verified),
            max_users=int(organization.max_users),
            max_storage_mb=int(organization.max_storage_mb),
            created_at=organization.created_at.isoformat()
        )
        
    except ValueError as e:
        logger.warning(f"Organization registration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Organization registration runtime error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization database. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error during organization registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get("/check-slug/{slug}")
async def check_slug_availability(
    slug: str,
    db: Session = Depends(get_master_db)
):
    """
    Проверить доступность slug для организации.
    
    Args:
        slug: Проверяемый slug
        
    Returns:
        dict: Результат проверки
    """
    exists = db.query(Organization).filter(Organization.slug == slug).first() is not None
    
    return {
        "slug": slug,
        "available": not exists,
        "message": "Slug is available" if not exists else "Slug is already taken"
    }
