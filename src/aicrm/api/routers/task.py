"""
Маршруты для управления задачами
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...services.task import task_service
from ..schemas.task import Task, TaskCreate, TaskUpdate
from .auth import get_current_active_user
from ...models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создание новой задачи"""
    task = task_service.create_task(db, task_data.dict(), current_user.id)
    return task


@router.get("/", response_model=List[Task])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    assigned_to: int = Query(None),
    status: str = Query(None),
    priority: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка задач"""
    tasks = task_service.get_tasks(db, skip, limit, assigned_to, status, priority)
    return tasks


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение задачи по ID"""
    task = task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновление данных задачи"""
    task = task_service.update_task(db, task_id, task_data.dict(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удаление задачи"""
    success = task_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/complete", response_model=Task)
async def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Завершение задачи"""
    task = task_service.complete_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
