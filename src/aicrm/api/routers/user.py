"""
API эндпоинты для управления пользователями
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_admin_user, get_db
from ...services.user import user_service
from ..schemas.auth import User as UserSchema
from ..schemas.auth import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/ping")
async def ping():
    return "pong"


@router.get("/", response_model=List[UserSchema])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Получить список пользователей (только для администраторов)"""
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Создать нового пользователя (только для администраторов)"""
    try:
        db_user = user_service.create_user(db, user.dict())
        return db_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Получить пользователя по ID (только для администраторов)"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Обновить пользователя (только для администраторов)"""
    try:
        updated_user = user_service.update_user(
            db, user_id, user_update.dict(exclude_unset=True)
        )
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Удалить пользователя (только для администраторов)"""
    # Нельзя удалить самого себя
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}