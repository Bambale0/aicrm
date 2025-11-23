"""
Роутер для управления производственными шагами
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...models.user import User
from ...core.dependencies import get_current_active_user

router = APIRouter(
    prefix="/production",
    tags=["production"]
)

@router.get("/steps/")
async def get_production_steps(
    order_id: Optional[int] = Query(None, description="ID заказа для фильтрации"),
    status: Optional[str] = Query(None, description="Статус шага"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить список производственных шагов
    """
    from ...models.production_step import ProductionStep

    query = db.query(ProductionStep)

    if order_id:
        query = query.filter(ProductionStep.order_id == order_id)

    if status:
        query = query.filter(ProductionStep.status == status)

    steps = query.all()
    return [step.to_dict() for step in steps]

@router.get("/steps/{step_id}")
async def get_production_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить производственный шаг по ID
    """
    from ...models.production_step import ProductionStep

    step = db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Production step not found")
    return step.to_dict()

@router.put("/steps/{step_id}")
async def update_production_step(
    step_id: int,
    step_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Обновить производственный шаг
    """
    from ...models.production_step import ProductionStep

    step = db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Production step not found")

    for key, value in step_update.items():
        if hasattr(step, key):
            setattr(step, key, value)

    db.commit()
    db.refresh(step)
    return step.to_dict()

@router.post("/steps/{step_id}/start")
async def start_production_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Начать выполнение производственного шага
    """
    from ...models.production_step import ProductionStep
    from datetime import datetime

    step = db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Production step not found")

    if step.status != "PENDING":
        raise HTTPException(status_code=400, detail="Step cannot be started")

    step.status = "IN_PROGRESS"
    step.started_at = datetime.utcnow()
    step.assigned_user_id = current_user.id

    db.commit()
    return {"message": "Production step started successfully"}

@router.post("/steps/{step_id}/complete")
async def complete_production_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Завершить выполнение производственного шага
    """
    from ...models.production_step import ProductionStep
    from datetime import datetime

    step = db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Production step not found")

    if step.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="Step cannot be completed")

    step.status = "COMPLETED"
    step.completed_at = datetime.utcnow()

    db.commit()
    return {"message": "Production step completed successfully"}

@router.get("/orders/{order_id}/steps")
async def get_order_production_steps(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить все производственные шаги для заказа
    """
    from ...models.production_step import ProductionStep

    steps = db.query(ProductionStep).filter(ProductionStep.order_id == order_id).all()
    return [step.to_dict() for step in steps]
