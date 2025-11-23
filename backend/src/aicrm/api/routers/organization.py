"""
Маршруты для управления организациями в мультитенантной системе
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List

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


# Импорты для аутентификации
from ...core.dependencies import get_current_admin_user

class OrganizationUpdate(BaseModel):
    """Схема обновления организации"""
    name: Optional[constr(min_length=2, max_length=255)] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = None
    max_storage_mb: Optional[int] = None


class OrganizationAdminResponse(BaseModel):
    """Схема ответа с детальной информацией об организации для админов"""
    id: int
    name: str
    slug: str
    description: Optional[str]
    email: str
    phone: Optional[str]
    website: Optional[str]
    plan: str
    is_active: bool
    is_verified: bool
    max_users: int
    max_storage_mb: int
    db_name: str
    db_host: str
    db_port: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# API для администрирования организаций
@router.get("/", response_model=List[OrganizationAdminResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Получить список всех организаций (только для админов).

    Args:
        skip: Количество пропускаемых записей
        limit: Максимальное количество возвращаемых записей
        active_only: Показывать только активные организации

    Returns:
        List[OrganizationAdminResponse]: Список организаций
    """
    query = db.query(Organization)

    if active_only:
        query = query.filter(Organization.is_active == True)

    organizations = query.offset(skip).limit(limit).all()

    return [OrganizationAdminResponse.model_validate(org.__dict__) for org in organizations]


@router.get("/{organization_id}", response_model=OrganizationAdminResponse)
async def get_organization(
    organization_id: int,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Получить информацию об организации по ID (только для админов).

    Args:
        organization_id: ID организации

    Returns:
        OrganizationAdminResponse: Информация об организации

    Raises:
        HTTPException: Если организация не найдена
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return OrganizationAdminResponse..model_validate(organization)


@router.put("/{organization_id}", response_model=OrganizationAdminResponse)
async def update_organization(
    organization_id: int,
    updates: OrganizationUpdate,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Обновить информацию об организации (только для админов).

    Args:
        organization_id: ID организации
        updates: Данные для обновления

    Returns:
        OrganizationAdminResponse: Обновленная информация об организации

    Raises:
        HTTPException: Если организация не найдена или данные невалидны
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Проверка уникальности email при изменении
    if updates.email and updates.email != organization.email:
        existing = db.query(Organization).filter(Organization.email == updates.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken by another organization"
            )

    # Обновление полей
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(organization, field):
            setattr(organization, field, value)

    # Обновление временной метки
    from datetime import datetime
    organization.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(organization)

    logger.info(f"Organization updated: {organization.name} (ID: {organization.id})")

    return OrganizationAdminResponse..model_validate(organization)


@router.post("/{organization_id}/activate")
async def activate_organization(
    organization_id: int,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Активировать организацию (только для админов).

    Args:
        organization_id: ID организации

    Returns:
        dict: Результат операции
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if organization.is_active:
        return {"message": "Organization is already active", "organization_id": organization_id}

    organization.is_active = True
    organization.updated_at = datetime.utcnow()

    db.commit()

    logger.info(f"Organization activated: {organization.name} (ID: {organization.id})")

    return {"message": "Organization activated successfully", "organization_id": organization_id}


@router.post("/{organization_id}/deactivate")
async def deactivate_organization(
    organization_id: int,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Деактивировать организацию (только для админов).

    Args:
        organization_id: ID организации

    Returns:
        dict: Результат операции

    Raises:
        HTTPException: Если организация не найдена
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if not organization.is_active:
        return {"message": "Organization is already inactive", "organization_id": organization_id}

    organization.is_active = False
    organization.updated_at = datetime.utcnow()

    db.commit()

    logger.info(f"Organization deactivated: {organization.name} (ID: {organization.id})")

    return {"message": "Organization deactivated successfully", "organization_id": organization_id}


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Удалить организацию и все связанные данные (только для админов).
    ВНИМАНИЕ: Это необратимая операция!

    Args:
        organization_id: ID организации

    Returns:
        dict: Результат операции

    Raises:
        HTTPException: Если организация не найдена или активна
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active organization. Deactivate it first."
        )

    try:
        # Удаление базы данных организации
        organization_service._cleanup_organization_database(organization)

        # Удаление записи из мастер-базы
        db.delete(organization)
        db.commit()

        # Инвалидация кэша
        organization_service.invalidate_organization_cache(organization_id)

        logger.warning(f"Organization deleted: {organization.name} (ID: {organization.id})")

        return {"message": "Organization deleted successfully", "organization_id": organization_id}

    except Exception as e:
        logger.error(f"Failed to delete organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )


@router.get("/stats/summary")
async def get_organizations_stats(
    db: Session = Depends(get_master_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Получить статистику по организациям (только для админов).

    Returns:
        dict: Статистика организаций
    """
    total_count = db.query(Organization).count()
    active_count = db.query(Organization).filter(Organization.is_active == True).count()
    verified_count = db.query(Organization).filter(Organization.is_verified == True).count()

    # Статистика по планам
    plans_stats = db.query(Organization.plan, db.func.count(Organization.id)).group_by(Organization.plan).all()
    plans_distribution = {plan: count for plan, count in plans_stats}

    return {
        "total_organizations": total_count,
        "active_organizations": active_count,
        "verified_organizations": verified_count,
        "inactive_organizations": total_count - active_count,
        "plans_distribution": plans_distribution
    }
