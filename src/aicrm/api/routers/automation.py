"""
API эндпоинты для управления автоматизацией
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...api.schemas.automation import (
    AutomationChainRequest,
    AutomationChainResponse,
    ProcessCreate,
    ProcessUpdate,
    RobotCreate,
    RobotUpdate,
    StageCreate,
    StageUpdate,
    TriggerCreate,
    TriggerUpdate,
)
from ...core.dependencies import get_current_active_user, get_db
from ...models.automation import (
    EntityType,
    Process,
    Robot,
    Stage,
    Trigger,
    TriggerEvent,
)
from ...models.user import User
from ...services.automation.analytics_service import AutomationAnalyticsService
from ...services.automation.automation_service import AutomationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/ping")
async def ping():
    return "pong"


@router.post("/events/{entity_type}/{event_type}")
async def fire_automation_event(
    entity_type: EntityType,
    event_type: TriggerEvent,
    entity_id: int,
    event_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Инициировать событие автоматизации

    Примеры событий:
    - customer_created: Клиент создан
    - order_completed: Заказ завершен
    - task_deadline_approaching: Приближается дедлайн задачи
    - production_overdue: Производство просрочено
    """
    automation_service = AutomationService(db)
    result = await automation_service.handle_event(
        entity_type, event_type, entity_id, event_data
    )

    return {"message": "Automation event processed", "result": result}


@router.post("/move-to-stage/{entity_type}/{entity_id}/{stage_id}")
async def move_entity_to_stage(
    entity_type: EntityType,
    entity_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Переместить сущность на указанную стадию с выполнением роботов

    Это может быть как автоматическое перемещение триггерами,
    так и ручное действие пользователя.
    """
    automation_service = AutomationService(db)
    result = await automation_service.move_to_stage(entity_type, entity_id, stage_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to move to stage")
        )

    return {"message": f"Entity moved to stage {stage_id}", "result": result}


# Специфические эндпоинты для разных типов событий


@router.post("/customers/{customer_id}/created")
async def on_customer_created(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Клиент создан"""
    automation_service = AutomationService(db)
    result = await automation_service.on_customer_created(customer_id)
    return {"result": result}


@router.post("/customers/{customer_id}/updated")
async def on_customer_updated(
    customer_id: int,
    changes: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Клиент обновлен"""
    automation_service = AutomationService(db)
    result = await automation_service.on_customer_updated(customer_id, changes)
    return {"result": result}


@router.post("/orders/{order_id}/created")
async def on_order_created(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Заказ создан"""
    automation_service = AutomationService(db)
    result = await automation_service.on_order_created(order_id)
    return {"result": result}


@router.post("/orders/{order_id}/status-changed")
async def on_order_status_changed(
    order_id: int,
    old_status: str,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Статус заказа изменен"""
    automation_service = AutomationService(db)
    result = await automation_service.on_order_status_changed(
        order_id, old_status, new_status
    )
    return {"result": result}


@router.post("/orders/{order_id}/completed")
async def on_order_completed(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Заказ завершен"""
    automation_service = AutomationService(db)
    result = await automation_service.on_order_completed(order_id)
    return {"result": result}


@router.post("/orders/{order_id}/payment-received")
async def on_payment_received(
    order_id: int,
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Получена оплата"""
    automation_service = AutomationService(db)
    result = await automation_service.on_payment_received(order_id, amount)
    return {"result": result}


@router.post("/tasks/{task_id}/created")
async def on_task_created(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Задача создана"""
    automation_service = AutomationService(db)
    result = await automation_service.on_task_created(task_id)
    return {"result": result}


@router.post("/tasks/{task_id}/status-changed")
async def on_task_status_changed(
    task_id: int,
    old_status: str,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Статус задачи изменен"""
    automation_service = AutomationService(db)
    result = await automation_service.on_task_status_changed(
        task_id, old_status, new_status
    )
    return {"result": result}


@router.post("/tasks/{task_id}/completed")
async def on_task_completed(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Задача завершена"""
    automation_service = AutomationService(db)
    result = await automation_service.on_task_completed(task_id)
    return {"result": result}


@router.post("/tasks/{task_id}/deadline-approaching")
async def on_deadline_approaching(
    task_id: int,
    hours_left: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Приближается дедлайн задачи"""
    automation_service = AutomationService(db)
    result = await automation_service.on_deadline_approaching(task_id, hours_left)
    return {"result": result}


@router.post("/production/{order_id}/started")
async def on_production_started(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Производство начато"""
    automation_service = AutomationService(db)
    result = await automation_service.on_production_started(order_id)
    return {"result": result}


@router.post("/production/steps/{step_id}/completed")
async def on_production_step_completed(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Этап производства завершен"""
    automation_service = AutomationService(db)
    result = await automation_service.on_production_step_completed(step_id)
    return {"result": result}


@router.post("/production/{order_id}/completed")
async def on_production_completed(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Производство завершено"""
    automation_service = AutomationService(db)
    result = await automation_service.on_production_completed(order_id)
    return {"result": result}


@router.post("/production/steps/{step_id}/overdue")
async def on_production_overdue(
    step_id: int,
    overdue_hours: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Производство просрочено"""
    automation_service = AutomationService(db)
    result = await automation_service.on_production_overdue(step_id, overdue_hours)
    return {"result": result}


@router.post("/communications/{communication_id}/message-received")
async def on_message_received(
    communication_id: int,
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Получено сообщение"""
    automation_service = AutomationService(db)
    result = await automation_service.on_message_received(
        communication_id, entity_type, entity_id
    )
    return {"result": result}


@router.post("/communications/{communication_id}/message-sent")
async def on_message_sent(
    communication_id: int,
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Отправлено сообщение"""
    automation_service = AutomationService(db)
    result = await automation_service.on_message_sent(
        communication_id, entity_type, entity_id
    )
    return {"result": result}


@router.post("/communications/{communication_id}/email-opened")
async def on_email_opened(
    communication_id: int,
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Событие: Email открыт"""
    automation_service = AutomationService(db)
    result = await automation_service.on_email_opened(
        communication_id, entity_type, entity_id
    )
    return {"result": result}


# CRUD операции для процессов


@router.get("/processes", response_model=List[Dict[str, Any]])
async def get_processes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[EntityType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список процессов"""
    query = db.query(Process)
    if entity_type:
        query = query.filter(Process.entity_type == entity_type)
    processes = query.offset(skip).limit(limit).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "entity_type": p.entity_type,
            "is_active": p.is_active,
            "stages_count": len(p.stages),
        }
        for p in processes
    ]


@router.post("/processes/", response_model=Dict[str, Any])
async def create_process(
    process: ProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создать новый процесс"""
    db_process = Process(**process.dict())
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return {
        "id": db_process.id,
        "name": db_process.name,
        "description": db_process.description,
        "entity_type": db_process.entity_type,
        "is_active": db_process.is_active,
        "created_at": db_process.created_at,
    }


@router.get("/processes/{process_id}", response_model=Dict[str, Any])
async def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить процесс по ID"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return {
        "id": process.id,
        "name": process.name,
        "description": process.description,
        "entity_type": process.entity_type,
        "is_active": process.is_active,
        "created_at": process.created_at,
        "updated_at": process.created_at,  # Process model doesn't have updated_at field
    }


@router.put("/processes/{process_id}", response_model=Dict[str, Any])
async def update_process(
    process_id: int,
    process_update: ProcessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновить процесс"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")

    for field, value in process_update.dict(exclude_unset=True).items():
        setattr(process, field, value)

    db.commit()
    db.refresh(process)
    return {
        "id": process.id,
        "name": process.name,
        "description": process.description,
        "entity_type": process.entity_type,
        "is_active": process.is_active,
        "created_at": process.created_at,
    }


@router.delete("/processes/{process_id}")
async def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить процесс"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")

    db.delete(process)
    db.commit()
    return {"message": "Process deleted"}


# CRUD операции для стадий


@router.get("/stages/", response_model=List[Dict[str, Any]])
async def get_stages(
    process_id: Optional[int] = None,
    entity_type: Optional[EntityType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список стадий"""
    query = db.query(Stage)
    if process_id:
        query = query.filter(Stage.process_id == process_id)
    if entity_type:
        query = query.filter(Stage.entity_type == entity_type)
    stages = query.offset(skip).limit(limit).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "entity_type": s.entity_type,
            "process_id": s.process_id,
            "order_index": s.order_index,
            "color": s.color,
            "is_active": s.is_active,
            "created_at": s.created_at,
        }
        for s in stages
    ]


@router.post("/stages/", response_model=Dict[str, Any])
async def create_stage(
    stage: StageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создать новую стадию"""
    db_stage = Stage(**stage.dict())
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    return {
        "id": db_stage.id,
        "name": db_stage.name,
        "description": db_stage.description,
        "entity_type": db_stage.entity_type,
        "process_id": db_stage.process_id,
        "order_index": db_stage.order_index,
        "color": db_stage.color,
        "is_active": db_stage.is_active,
        "created_at": db_stage.created_at,
    }


@router.get("/stages/{stage_id}", response_model=Dict[str, Any])
async def get_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить стадию по ID"""
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return {
        "id": stage.id,
        "name": stage.name,
        "description": stage.description,
        "entity_type": stage.entity_type,
        "process_id": stage.process_id,
        "order_index": stage.order_index,
        "color": stage.color,
        "is_active": stage.is_active,
        "created_at": stage.created_at,
    }


@router.put("/stages/{stage_id}", response_model=Dict[str, Any])
async def update_stage(
    stage_id: int,
    stage_update: StageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновить стадию"""
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    for field, value in stage_update.dict(exclude_unset=True).items():
        setattr(stage, field, value)

    db.commit()
    db.refresh(stage)
    return {
        "id": stage.id,
        "name": stage.name,
        "description": stage.description,
        "entity_type": stage.entity_type,
        "process_id": stage.process_id,
        "order_index": stage.order_index,
        "color": stage.color,
        "is_active": stage.is_active,
        "created_at": stage.created_at,
    }


@router.delete("/stages/{stage_id}")
async def delete_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить стадию"""
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    db.delete(stage)
    db.commit()
    return {"message": "Stage deleted"}


# CRUD операции для триггеров


@router.get("/triggers/", response_model=List[Dict[str, Any]])
async def get_triggers(
    entity_type: Optional[EntityType] = None,
    event_type: Optional[TriggerEvent] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список триггеров"""
    query = db.query(Trigger)
    if entity_type:
        query = query.filter(Trigger.entity_type == entity_type)
    if event_type:
        query = query.filter(Trigger.event_type == event_type)
    if is_active is not None:
        query = query.filter(Trigger.is_active == is_active)
    triggers = query.offset(skip).limit(limit).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "entity_type": t.entity_type,
            "event_type": t.event_type,
            "conditions": t.conditions,
            "target_stage_id": t.target_stage_id,
            "is_active": t.is_active,
            "created_at": t.created_at,
        }
        for t in triggers
    ]


@router.post("/triggers/", response_model=Dict[str, Any])
async def create_trigger(
    trigger: TriggerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создать новый триггер"""
    db_trigger = Trigger(**trigger.dict())
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)
    return {
        "id": db_trigger.id,
        "name": db_trigger.name,
        "description": db_trigger.description,
        "entity_type": db_trigger.entity_type,
        "event_type": db_trigger.event_type,
        "conditions": db_trigger.conditions,
        "target_stage_id": db_trigger.target_stage_id,
        "is_active": db_trigger.is_active,
        "created_at": db_trigger.created_at,
    }


@router.get("/triggers/{trigger_id}", response_model=Dict[str, Any])
async def get_trigger(
    trigger_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить триггер по ID"""
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return {
        "id": trigger.id,
        "name": trigger.name,
        "description": trigger.description,
        "entity_type": trigger.entity_type,
        "event_type": trigger.event_type,
        "conditions": trigger.conditions,
        "target_stage_id": trigger.target_stage_id,
        "is_active": trigger.is_active,
        "created_at": trigger.created_at,
    }


@router.put("/triggers/{trigger_id}", response_model=Dict[str, Any])
async def update_trigger(
    trigger_id: int,
    trigger_update: TriggerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновить триггер"""
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    for field, value in trigger_update.dict(exclude_unset=True).items():
        setattr(trigger, field, value)

    db.commit()
    db.refresh(trigger)
    return {
        "id": trigger.id,
        "name": trigger.name,
        "description": trigger.description,
        "entity_type": trigger.entity_type,
        "event_type": trigger.event_type,
        "conditions": trigger.conditions,
        "target_stage_id": trigger.target_stage_id,
        "is_active": trigger.is_active,
        "created_at": trigger.created_at,
    }


@router.delete("/triggers/{trigger_id}")
async def delete_trigger(
    trigger_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить триггер"""
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    db.delete(trigger)
    db.commit()
    return {"message": "Trigger deleted"}


# CRUD операции для роботов


@router.get("/robots/", response_model=List[Dict[str, Any]])
async def get_robots(
    entity_type: Optional[EntityType] = None,
    stage_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список роботов"""
    query = db.query(Robot)
    if entity_type:
        query = query.filter(Robot.entity_type == entity_type)
    if stage_id:
        query = query.filter(Robot.stage_id == stage_id)
    if is_active is not None:
        query = query.filter(Robot.is_active == is_active)
    robots = query.offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "entity_type": r.entity_type,
            "stage_id": r.stage_id,
            "actions_count": len(r.actions),
            "is_active": r.is_active,
            "created_at": r.created_at,
        }
        for r in robots
    ]


@router.post("/robots/", response_model=Dict[str, Any])
async def create_robot(
    robot: RobotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Создать нового робота"""
    db_robot = Robot(**robot.dict())
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return {
        "id": db_robot.id,
        "name": db_robot.name,
        "description": db_robot.description,
        "entity_type": db_robot.entity_type,
        "stage_id": db_robot.stage_id,
        "is_active": db_robot.is_active,
        "created_at": db_robot.created_at,
    }


@router.get("/robots/{robot_id}", response_model=Dict[str, Any])
async def get_robot(
    robot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получить робота по ID"""
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {
        "id": robot.id,
        "name": robot.name,
        "description": robot.description,
        "entity_type": robot.entity_type,
        "stage_id": robot.stage_id,
        "is_active": robot.is_active,
        "created_at": robot.created_at,
    }


@router.put("/robots/{robot_id}", response_model=Dict[str, Any])
async def update_robot(
    robot_id: int,
    robot_update: RobotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Обновить робота"""
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    for field, value in robot_update.dict(exclude_unset=True).items():
        setattr(robot, field, value)

    db.commit()
    db.refresh(robot)
    return {
        "id": robot.id,
        "name": robot.name,
        "description": robot.description,
        "entity_type": robot.entity_type,
        "stage_id": robot.stage_id,
        "is_active": robot.is_active,
        "created_at": robot.created_at,
    }


@router.delete("/robots/{robot_id}")
async def delete_robot(
    robot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить робота"""
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    db.delete(robot)
    db.commit()
    return {"message": "Robot deleted"}


@router.post("/robots/{robot_id}/execute-action")
async def execute_robot_action(
    robot_id: int,
    action_config: Dict[str, Any],
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Выполнить отдельное действие робота для тестирования

    Пример запроса:
    {
        "action_config": {
            "action_type": "SEND_TELEGRAM",
            "config": {
                "telegram_id": "123456789",
                "message": "Тестовое сообщение"
            }
        },
        "entity_type": "CUSTOMER",
        "entity_id": 1
    }
    """
    from ...services.automation.robot_service import RobotService

    robot_service = RobotService(db)
    result = await robot_service.execute_robot_action(
        robot_id=robot_id,
        action_config=action_config,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    return result


# ИИ-функционал для создания цепочек автоматизации


@router.post("/ai/generate-chain", response_model=AutomationChainResponse)
async def generate_automation_chain(
    request: AutomationChainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    ИИ-генерация цепочки автоматизации на основе описания бизнес-процесса

    Пример запроса:
    {
        "description": "Когда создается новый клиент, отправить приветственное email, создать задачу менеджеру и переместить в стадию 'Новый лид'",
        "entity_type": "customer"
    }
    """
    logger.info(f"Generate automation chain request: {request.dict()}")

    automation_service = AutomationService(db)
    result = await automation_service.generate_automation_chain_with_ai(
        request.description, request.entity_type, request.complexity_level or "medium"
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to generate automation chain"),
        )

    return result


# Аналитические эндпоинты


@router.get("/analytics/executions")
async def get_execution_stats(
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    entity_type: Optional[EntityType] = Query(None, description="Тип сущности"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить статистику выполнений автоматизаций

    Возвращает:
    - Общее количество выполнений
    - Процент успешных/неуспешных
    - Метрики производительности
    - Статистику действий
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_execution_stats(
        start_date=start_dt, end_date=end_dt, entity_type=entity_type
    )

    return result


@router.get("/analytics/robots")
async def get_robot_performance(
    robot_id: Optional[int] = Query(None, description="ID конкретного робота"),
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить метрики производительности роботов

    Возвращает:
    - Количество выполнений по роботам
    - Среднее время выполнения
    - Процент успешных действий
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_robot_performance(
        robot_id=robot_id, start_date=start_dt, end_date=end_dt
    )

    return result


@router.get("/analytics/actions")
async def get_action_type_stats(
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить статистику по типам действий

    Возвращает:
    - Количество выполнений каждого типа действия
    - Процент успешности по типам
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_action_type_stats(
        start_date=start_dt, end_date=end_dt
    )

    return result


@router.get("/analytics/errors")
async def get_error_analysis(
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество ошибок"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить анализ ошибок в автоматизациях

    Возвращает:
    - Список последних ошибок
    - Классификация ошибок по типам
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_error_analysis(
        start_date=start_dt, end_date=end_dt, limit=limit
    )

    return result


@router.get("/analytics/processes")
async def get_process_efficiency(
    process_id: Optional[int] = Query(None, description="ID конкретного процесса"),
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить метрики эффективности бизнес-процессов

    Возвращает:
    - Статистику по стадиям процессов
    - Время выполнения стадий
    - Процент успешности
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_process_efficiency(
        process_id=process_id, start_date=start_dt, end_date=end_dt
    )

    return result


@router.get("/analytics/hourly")
async def get_hourly_distribution(
    start_date: Optional[str] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конец периода (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить почасовое распределение выполнений

    Возвращает:
    - Количество выполнений по часам
    - Пиковые часы активности
    """
    start_dt = None
    end_dt = None

    if start_date:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        from datetime import datetime

        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    analytics_service = AutomationAnalyticsService(db)
    result = await analytics_service.get_hourly_distribution(
        start_date=start_dt, end_date=end_dt
    )

    return result


@router.post("/ai/optimize-chain/{process_id}")
async def optimize_automation_chain(
    process_id: int,
    optimization_goal: str = Query(
        ..., description="Цель оптимизации: performance, reliability, cost"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    ИИ-оптимизация существующей цепочки автоматизации

    Оптимизация целей:
    - performance: Улучшение производительности
    - reliability: Повышение надежности
    - cost: Снижение затрат на выполнение
    """
    automation_service = AutomationService(db)
    result = await automation_service.optimize_automation_chain_with_ai(
        process_id, optimization_goal
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to optimize automation chain"),
        )

    return result


@router.post("/ai/suggest-improvements")
async def suggest_automation_improvements(
    entity_type: Optional[EntityType] = None,
    analysis_period_days: int = Query(30, description="Период анализа в днях"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    ИИ-анализ и предложения по улучшению автоматизации

    Анализирует:
    - Эффективность существующих процессов
    - Узкие места и bottlenecks
    - Возможности оптимизации
    - Новые сценарии автоматизации
    """
    automation_service = AutomationService(db)
    result = await automation_service.analyze_and_suggest_improvements(
        entity_type, analysis_period_days
    )

    return result


# Логи автоматизации


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_automation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(
        None, description="Уровень логирования: error, warning, success, info"
    ),
    process_id: Optional[int] = Query(None, description="ID процесса"),
    stage_id: Optional[int] = Query(None, description="ID стадии"),
    date_from: Optional[str] = Query(None, description="Дата начала (ISO format)"),
    date_to: Optional[str] = Query(None, description="Дата окончания (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить логи автоматизации с фильтрами

    Возвращает историю выполнения автоматизаций с возможностью фильтрации
    по уровню, процессу, стадии и временному периоду.
    """
    logger.info("get_automation_logs called")
    try:
        # Импортируем модель внутри функции для избежания проблем с загрузкой
        from datetime import datetime

        from ...models.automation_log import AutomationLog

        logger.info("Querying automation logs")
        query = db.query(AutomationLog)

        # Применяем фильтры
        if level:
            query = query.filter(AutomationLog.level == level)
        if process_id:
            query = query.filter(AutomationLog.process_id == process_id)
        if stage_id:
            query = query.filter(AutomationLog.stage_id == stage_id)
        if date_from:
            query = query.filter(
                AutomationLog.timestamp
                >= datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            )
        if date_to:
            query = query.filter(
                AutomationLog.timestamp
                <= datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            )

        # Сортировка по времени (новые сверху)
        query = query.order_by(AutomationLog.timestamp.desc())

        logs = query.offset(skip).limit(limit).all()
        logger.info(f"Found {len(logs)} logs")

        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "process_id": log.process_id,
                "stage_id": log.stage_id,
                "details": log.details,
            }
            for log in logs
        ]
    except Exception as e:
        # Возвращаем пустой массив в случае ошибки
        logger.error(f"Error getting automation logs: {e}")
        return []