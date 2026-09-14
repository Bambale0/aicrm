"""Universal automation API: processes, stages, rules, runs and execution log."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.automation_catalog import catalog_payload
from ...core.dependencies import get_current_active_user, get_db
from ...models.automation import (
    AutomationExecution,
    AutomationInstance,
    AutomationProcess,
    AutomationRule,
    AutomationStage,
)
from ...models.housing import ContractorCompany
from ...models.user import User
from ...services.automation_engine import (
    AutomationValidationError,
    dispatch_event,
    validate_rule_payload,
)
from ...utils.logging import get_logger

router = APIRouter(prefix="/automation", tags=["automation"])
logger = get_logger(__name__)


class ProcessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    entity_type: str
    is_active: bool = True


class ProcessPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StageCreate(BaseModel):
    process_id: int
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True


class StagePatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ConditionIn(BaseModel):
    field: str = Field(min_length=1, max_length=255)
    operator: str = Field(default="equals", min_length=1, max_length=50)
    value: Any = None
    logical_operator: str = Field(default="AND", pattern="^(AND|OR)$")


class ActionIn(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    config: Dict[str, Any] = Field(default_factory=dict)


class RuleCreate(BaseModel):
    process_id: int
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    event_type: str
    conditions: List[ConditionIn] = Field(default_factory=list)
    actions: List[ActionIn] = Field(min_length=1)
    priority: int = Field(default=100, ge=0, le=100000)
    stop_after_match: bool = False
    is_active: bool = True


class RulePatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    conditions: Optional[List[ConditionIn]] = None
    actions: Optional[List[ActionIn]] = Field(default=None, min_length=1)
    priority: Optional[int] = Field(default=None, ge=0, le=100000)
    stop_after_match: Optional[bool] = None
    is_active: Optional[bool] = None


class InstanceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    variables: Dict[str, Any] = Field(default_factory=dict)
    current_stage_id: Optional[int] = None
    external_ref: Optional[str] = Field(default=None, max_length=255)


class InstancePatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[str] = Field(default=None, max_length=30)
    current_stage_id: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None
    external_ref: Optional[str] = Field(default=None, max_length=255)


class CustomEventIn(BaseModel):
    event_name: str = Field(min_length=1, max_length=100)
    data: Dict[str, Any] = Field(default_factory=dict)


class EventDispatchIn(BaseModel):
    entity_id: int
    data: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    dry_run: bool = False
    process_id: Optional[int] = None


def _entity_types() -> set[str]:
    return {item["value"] for item in catalog_payload()["entity_types"]}


def _workflow_statuses() -> set[str]:
    return {item["value"] for item in catalog_payload()["workflow_statuses"]}


def _process_or_404(db: Session, process_id: int) -> AutomationProcess:
    item = db.get(AutomationProcess, process_id)
    if not item:
        raise HTTPException(status_code=404, detail="Process not found")
    return item


def _stage_or_404(db: Session, stage_id: int) -> AutomationStage:
    item = db.get(AutomationStage, stage_id)
    if not item:
        raise HTTPException(status_code=404, detail="Stage not found")
    return item


def _rule_or_404(db: Session, rule_id: int) -> AutomationRule:
    item = db.get(AutomationRule, rule_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rule not found")
    return item


def _instance_or_404(db: Session, instance_id: int) -> AutomationInstance:
    item = db.get(AutomationInstance, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="Process run not found")
    return item


def _assert_stage_process(stage: AutomationStage, process_id: int) -> None:
    if stage.process_id != process_id:
        raise HTTPException(status_code=422, detail="Stage belongs to another process")


def _process_dict(item: AutomationProcess) -> Dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "entity_type": item.entity_type,
        "is_active": item.is_active,
        "stages_count": len(item.stages),
        "rules_count": len(item.rules),
        "instances_count": len(item.instances),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _stage_dict(item: AutomationStage) -> Dict[str, Any]:
    return {
        "id": item.id,
        "process_id": item.process_id,
        "name": item.name,
        "description": item.description,
        "order_index": item.order_index,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _rule_dict(item: AutomationRule) -> Dict[str, Any]:
    return {
        "id": item.id,
        "process_id": item.process_id,
        "name": item.name,
        "description": item.description,
        "event_type": item.event_type,
        "conditions": item.conditions or [],
        "actions": item.actions or [],
        "priority": item.priority,
        "stop_after_match": item.stop_after_match,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _instance_dict(item: AutomationInstance, db: Session) -> Dict[str, Any]:
    stage = db.get(AutomationStage, item.current_stage_id) if item.current_stage_id else None
    return {
        "id": item.id,
        "process_id": item.process_id,
        "name": item.name,
        "status": item.status,
        "current_stage_id": item.current_stage_id,
        "current_stage_name": stage.name if stage else None,
        "variables": item.variables or {},
        "external_ref": item.external_ref,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/catalog")
async def get_catalog(_: User = Depends(get_current_active_user)):
    return catalog_payload()


@router.get("/options")
async def get_options(
    source: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    if source == "users":
        items = (
            db.query(User)
            .filter(User.is_active.is_(True))
            .order_by(User.full_name.asc().nullslast(), User.email.asc())
            .all()
        )
        return {
            "data": [
                {
                    "value": item.id,
                    "label": item.full_name or item.email,
                }
                for item in items
            ]
        }

    if source == "contractors":
        items = (
            db.query(ContractorCompany)
            .filter(ContractorCompany.is_active.is_(True))
            .order_by(ContractorCompany.name.asc())
            .all()
        )
        return {
            "data": [
                {"value": item.id, "label": item.name}
                for item in items
            ]
        }

    raise HTTPException(status_code=404, detail="Unknown option source")


@router.get("/summary")
async def get_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return {
        "processes": db.query(func.count(AutomationProcess.id)).scalar() or 0,
        "active_processes": (
            db.query(func.count(AutomationProcess.id))
            .filter(AutomationProcess.is_active.is_(True))
            .scalar()
            or 0
        ),
        "rules": db.query(func.count(AutomationRule.id)).scalar() or 0,
        "active_rules": (
            db.query(func.count(AutomationRule.id))
            .filter(AutomationRule.is_active.is_(True))
            .scalar()
            or 0
        ),
        "running_instances": (
            db.query(func.count(AutomationInstance.id))
            .filter(AutomationInstance.status.in_(["running", "waiting"]))
            .scalar()
            or 0
        ),
        "failed_executions": (
            db.query(func.count(AutomationExecution.id))
            .filter(AutomationExecution.status == "failed")
            .scalar()
            or 0
        ),
    }


@router.get("/processes")
async def list_processes(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(AutomationProcess)
    if entity_type:
        query = query.filter(AutomationProcess.entity_type == entity_type)
    return [_process_dict(item) for item in query.order_by(AutomationProcess.name.asc()).all()]


@router.post("/processes")
async def create_process(
    payload: ProcessCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    if payload.entity_type not in _entity_types():
        raise HTTPException(status_code=422, detail="Unsupported process type")

    item = AutomationProcess(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(
        "automation_process_created",
        process_id=item.id,
        entity_type=item.entity_type,
    )
    return _process_dict(item)


@router.patch("/processes/{process_id}")
async def update_process(
    process_id: int,
    payload: ProcessPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _process_or_404(db, process_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _process_dict(item)


@router.delete("/processes/{process_id}")
async def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _process_or_404(db, process_id)
    db.delete(item)
    db.commit()
    logger.info("automation_process_deleted", process_id=process_id)
    return {"deleted": True, "id": process_id}


@router.get("/stages")
async def list_stages(
    process_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return [
        _stage_dict(item)
        for item in (
            db.query(AutomationStage)
            .filter(AutomationStage.process_id == process_id)
            .order_by(AutomationStage.order_index.asc(), AutomationStage.id.asc())
            .all()
        )
    ]


@router.post("/stages")
async def create_stage(
    payload: StageCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    process = _process_or_404(db, payload.process_id)
    if process.entity_type != "workflow":
        raise HTTPException(
            status_code=422,
            detail="Stages are only used by custom processes",
        )

    data = payload.model_dump()
    if data["order_index"] is None:
        current_max = (
            db.query(func.max(AutomationStage.order_index))
            .filter(AutomationStage.process_id == process.id)
            .scalar()
        )
        data["order_index"] = (current_max if current_max is not None else -1) + 1

    item = AutomationStage(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _stage_dict(item)


@router.patch("/stages/{stage_id}")
async def update_stage(
    stage_id: int,
    payload: StagePatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _stage_or_404(db, stage_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _stage_dict(item)


@router.delete("/stages/{stage_id}")
async def delete_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _stage_or_404(db, stage_id)
    db.delete(item)
    db.commit()
    return {"deleted": True, "id": stage_id}


@router.get("/rules")
async def list_rules(
    process_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return [
        _rule_dict(item)
        for item in (
            db.query(AutomationRule)
            .filter(AutomationRule.process_id == process_id)
            .order_by(AutomationRule.priority.asc(), AutomationRule.id.asc())
            .all()
        )
    ]


@router.post("/rules")
async def create_rule(
    payload: RuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    process = _process_or_404(db, payload.process_id)
    conditions = [item.model_dump() for item in payload.conditions]
    actions = [item.model_dump() for item in payload.actions]

    try:
        validate_rule_payload(
            db,
            process,
            payload.event_type,
            conditions,
            actions,
        )
    except AutomationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    item = AutomationRule(
        process_id=process.id,
        name=payload.name,
        description=payload.description,
        event_type=payload.event_type,
        conditions=conditions,
        actions=actions,
        priority=payload.priority,
        stop_after_match=payload.stop_after_match,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(
        "automation_rule_created",
        process_id=process.id,
        rule_id=item.id,
        event_type=item.event_type,
        action_count=len(actions),
    )
    return _rule_dict(item)


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    payload: RulePatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _rule_or_404(db, rule_id)
    process = _process_or_404(db, item.process_id)
    values = payload.model_dump(exclude_unset=True)

    conditions = values.get("conditions")
    if conditions is not None:
        conditions = [
            value.model_dump() if hasattr(value, "model_dump") else value
            for value in conditions
        ]
        values["conditions"] = conditions
    else:
        conditions = item.conditions or []

    actions = values.get("actions")
    if actions is not None:
        actions = [
            value.model_dump() if hasattr(value, "model_dump") else value
            for value in actions
        ]
        values["actions"] = actions
    else:
        actions = item.actions or []

    event_type = values.get("event_type", item.event_type)

    try:
        validate_rule_payload(db, process, event_type, conditions, actions)
    except AutomationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for field, value in values.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return _rule_dict(item)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _rule_or_404(db, rule_id)
    db.delete(item)
    db.commit()
    return {"deleted": True, "id": rule_id}


@router.get("/instances")
async def list_instances(
    process_id: int,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(AutomationInstance).filter(
        AutomationInstance.process_id == process_id
    )
    if status:
        query = query.filter(AutomationInstance.status == status)

    return [
        _instance_dict(item, db)
        for item in query.order_by(AutomationInstance.updated_at.desc()).limit(limit).all()
    ]


@router.post("/processes/{process_id}/instances")
async def create_instance(
    process_id: int,
    payload: InstanceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    process = _process_or_404(db, process_id)
    if process.entity_type != "workflow":
        raise HTTPException(
            status_code=422,
            detail="Runs can only be created for custom processes",
        )

    stage_id = payload.current_stage_id
    if stage_id:
        _assert_stage_process(_stage_or_404(db, stage_id), process.id)
    else:
        first_stage = (
            db.query(AutomationStage)
            .filter(
                AutomationStage.process_id == process.id,
                AutomationStage.is_active.is_(True),
            )
            .order_by(AutomationStage.order_index.asc(), AutomationStage.id.asc())
            .first()
        )
        stage_id = first_stage.id if first_stage else None

    item = AutomationInstance(
        process_id=process.id,
        name=payload.name,
        status="running",
        current_stage_id=stage_id,
        variables=payload.variables,
        external_ref=payload.external_ref,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    try:
        dispatch_event(
            db,
            entity_type="workflow",
            event_type="workflow_started",
            entity_id=item.id,
            event_data={},
            process_id=process.id,
        )
        db.refresh(item)
    except AutomationValidationError:
        pass

    logger.info(
        "automation_instance_created",
        process_id=process.id,
        instance_id=item.id,
    )
    return _instance_dict(item, db)


@router.patch("/instances/{instance_id}")
async def update_instance(
    instance_id: int,
    payload: InstancePatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _instance_or_404(db, instance_id)
    process = _process_or_404(db, item.process_id)
    values = payload.model_dump(exclude_unset=True)

    if "status" in values and values["status"] not in _workflow_statuses():
        raise HTTPException(status_code=422, detail="Unsupported workflow status")

    old_stage_id = item.current_stage_id
    changed_fields: List[str] = []

    if "variables" in values and values["variables"] is not None:
        merged = dict(item.variables or {})
        merged.update(values["variables"])
        item.variables = merged
        changed_fields.append("variables")
        values.pop("variables")

    if "current_stage_id" in values and values["current_stage_id"] is not None:
        _assert_stage_process(
            _stage_or_404(db, values["current_stage_id"]),
            process.id,
        )

    for field, value in values.items():
        if getattr(item, field) != value:
            setattr(item, field, value)
            changed_fields.append(field)

    db.commit()
    db.refresh(item)

    if old_stage_id != item.current_stage_id:
        dispatch_event(
            db,
            entity_type="workflow",
            event_type="workflow_stage_changed",
            entity_id=item.id,
            event_data={
                "old_stage_id": old_stage_id,
                "stage_id": item.current_stage_id,
            },
            process_id=process.id,
        )
        db.refresh(item)

    if changed_fields:
        dispatch_event(
            db,
            entity_type="workflow",
            event_type="workflow_updated",
            entity_id=item.id,
            event_data={"changed_fields": changed_fields},
            process_id=process.id,
        )
        db.refresh(item)

    return _instance_dict(item, db)


@router.post("/instances/{instance_id}/events")
async def emit_custom_event(
    instance_id: int,
    payload: CustomEventIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _instance_or_404(db, instance_id)

    return dispatch_event(
        db,
        entity_type="workflow",
        event_type="custom_event",
        entity_id=item.id,
        event_data={
            "event_name": payload.event_name,
            **payload.data,
        },
        process_id=item.process_id,
    )


@router.delete("/instances/{instance_id}")
async def delete_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = _instance_or_404(db, instance_id)
    db.delete(item)
    db.commit()
    return {"deleted": True, "id": instance_id}


@router.post("/events/{entity_type}/{event_type}")
async def dispatch_manual_event(
    entity_type: str,
    event_type: str,
    payload: EventDispatchIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    try:
        return dispatch_event(
            db,
            entity_type=entity_type,
            event_type=event_type,
            entity_id=payload.entity_id,
            event_data=payload.data,
            correlation_id=payload.correlation_id,
            dry_run=payload.dry_run,
            process_id=payload.process_id,
        )
    except AutomationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/executions")
async def list_executions(
    process_id: Optional[int] = None,
    instance_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(AutomationExecution)
    if process_id:
        query = query.filter(AutomationExecution.process_id == process_id)
    if instance_id:
        query = query.filter(AutomationExecution.instance_id == instance_id)
    if status:
        query = query.filter(AutomationExecution.status == status)

    items = query.order_by(AutomationExecution.created_at.desc()).limit(limit).all()
    return [
        {
            "id": item.id,
            "process_id": item.process_id,
            "rule_id": item.rule_id,
            "instance_id": item.instance_id,
            "correlation_id": item.correlation_id,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "event_type": item.event_type,
            "action_index": item.action_index,
            "status": item.status,
            "duration_ms": item.duration_ms,
            "result": item.result,
            "error": item.error,
            "created_at": item.created_at,
        }
        for item in items
    ]


@router.get("/validate")
async def validate_configuration(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    errors: List[Dict[str, Any]] = []
    processes = db.query(AutomationProcess).all()
    rules = db.query(AutomationRule).all()

    for process in processes:
        if process.entity_type not in _entity_types():
            errors.append(
                {
                    "type": "process",
                    "id": process.id,
                    "error": "Unsupported process type",
                }
            )

    for rule in rules:
        process = db.get(AutomationProcess, rule.process_id)
        if not process:
            errors.append(
                {"type": "rule", "id": rule.id, "error": "Process not found"}
            )
            continue
        try:
            validate_rule_payload(
                db,
                process,
                rule.event_type,
                rule.conditions or [],
                rule.actions or [],
            )
        except AutomationValidationError as exc:
            errors.append(
                {"type": "rule", "id": rule.id, "error": str(exc)}
            )

    return {
        "valid": not errors,
        "errors": errors,
        "counts": {
            "processes": len(processes),
            "rules": len(rules),
            "instances": db.query(func.count(AutomationInstance.id)).scalar() or 0,
        },
    }
