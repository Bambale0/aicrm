"""Housing-management CRM API."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_active_user, get_db
from ...core.housing_catalog import (
    can_transition_request,
    is_request_status,
    request_status_catalog,
)
from ...models.housing import (
    Building,
    ContractorCompany,
    Incident,
    Premise,
    RequestEvent,
    Resident,
    ServiceRequest,
)
from ...models.user import User
from ...services.automation_engine import AutomationValidationError, dispatch_event
from ...services.request_notifications import (
    notify_resident_request_status_background,
)
from ...utils.logging import get_logger

router = APIRouter(prefix="/housing", tags=["housing"])
logger = get_logger(__name__)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BuildingIn(BaseModel):
    address: str
    management_area: Optional[str] = None
    entrances: Optional[int] = None
    apartments_count: Optional[int] = None
    is_active: bool = True


class BuildingOut(ORMModel, BuildingIn):
    id: int


class PremiseIn(BaseModel):
    building_id: int
    apartment: str
    entrance: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    is_residential: bool = True


class PremiseOut(ORMModel, PremiseIn):
    id: int


class ResidentIn(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    premise_id: Optional[int] = None
    preferred_channel: Optional[str] = None
    external_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class ResidentOut(ORMModel, ResidentIn):
    id: int


class ContractorIn(BaseModel):
    name: str
    legal_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    contract_number: Optional[str] = None
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    categories: Optional[List[str]] = None
    is_active: bool = True
    notes: Optional[str] = None


class ContractorPatch(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    contract_number: Optional[str] = None
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    categories: Optional[List[str]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContractorOut(ORMModel, ContractorIn):
    id: int


class RequestIntake(BaseModel):
    applicant_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=5, max_length=50)
    address: str = Field(min_length=3, max_length=500)
    apartment: Optional[str] = Field(default=None, max_length=50)
    problem: str = Field(min_length=3, max_length=5000)
    category: Optional[str] = None
    priority: Optional[str] = None
    notify_resident: bool = True


class RequestIn(BaseModel):
    resident_id: Optional[int] = None
    building_id: Optional[int] = None
    premise_id: Optional[int] = None
    incident_id: Optional[int] = None
    source_channel: str = "operator"
    source_conversation_id: Optional[str] = None
    category: str = "general"
    priority: str = "normal"
    status: str = "new"
    title: str
    description: str
    assigned_user_id: Optional[int] = None
    contractor_id: Optional[int] = None
    sla_deadline: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None


class RequestPatch(BaseModel):
    resident_id: Optional[int] = None
    building_id: Optional[int] = None
    premise_id: Optional[int] = None
    incident_id: Optional[int] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_user_id: Optional[int] = None
    contractor_id: Optional[int] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None


def _classify_request(text: str) -> Dict[str, str]:
    normalized = text.lower()

    emergency_terms = (
        "пожар", "дым", "запах газа", "газом", "прорыв", "затоп",
        "льется вода", "искрит", "короткое замыкание", "авария",
    )
    urgent_terms = (
        "нет света", "нет электр", "нет воды", "нет отоп", "не работает лифт",
        "застрял лифт", "течет", "течь", "канализац",
    )

    if any(term in normalized for term in ("элект", "свет", "розет", "провод", "щиток", "искрит")):
        category = "electrical"
    elif any(term in normalized for term in ("сантех", "труб", "стояк", "вода", "отоп", "батар", "канализац", "теч")):
        category = "plumbing"
    elif any(term in normalized for term in ("претенз", "жалоб", "нарушен", "провер")):
        category = "complaint"
    elif any(term in normalized for term in ("пожел", "благоустр", "лавоч", "улучш")):
        category = "wish"
    else:
        category = "general"

    if any(term in normalized for term in emergency_terms):
        priority = "emergency"
    elif any(term in normalized for term in urgent_terms):
        priority = "urgent"
    elif category == "wish":
        priority = "planned"
    else:
        priority = "normal"

    return {"category": category, "priority": priority}


def _default_sla_deadline(priority: str) -> datetime:
    durations = {
        "emergency": timedelta(hours=1),
        "urgent": timedelta(hours=4),
        "high": timedelta(hours=12),
        "normal": timedelta(days=3),
        "planned": timedelta(days=7),
    }
    return datetime.utcnow() + durations.get(priority, timedelta(days=3))


def _request_dict(item: ServiceRequest) -> Dict[str, Any]:
    overdue = bool(
        item.sla_deadline
        and item.status not in {"done", "cancelled", "closed"}
        and datetime.utcnow() > item.sla_deadline
    )
    return {
        "id": item.id,
        "number": item.number,
        "resident_id": item.resident_id,
        "building_id": item.building_id,
        "premise_id": item.premise_id,
        "incident_id": item.incident_id,
        "source_channel": item.source_channel,
        "source_conversation_id": item.source_conversation_id,
        "category": item.category,
        "priority": item.priority,
        "status": item.status,
        "title": item.title,
        "description": item.description,
        "assigned_user_id": item.assigned_user_id,
        "contractor_id": item.contractor_id,
        "sla_deadline": item.sla_deadline,
        "resolved_at": item.resolved_at,
        "extra_data": item.extra_data,
        "overdue": overdue,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/request-statuses/catalog")
async def get_request_status_catalog(
    _: User = Depends(get_current_active_user),
):
    return request_status_catalog()


@router.get("/dashboard")
async def dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    total = db.query(func.count(ServiceRequest.id)).scalar() or 0
    in_progress = (
        db.query(func.count(ServiceRequest.id))
        .filter(ServiceRequest.status.in_(["accepted", "assigned", "in_progress"]))
        .scalar()
        or 0
    )
    done = (
        db.query(func.count(ServiceRequest.id))
        .filter(ServiceRequest.status.in_(["done", "closed"]))
        .scalar()
        or 0
    )
    now = datetime.utcnow()
    overdue = (
        db.query(func.count(ServiceRequest.id))
        .filter(
            ServiceRequest.sla_deadline.isnot(None),
            ServiceRequest.sla_deadline < now,
            ~ServiceRequest.status.in_(["done", "closed", "cancelled"]),
        )
        .scalar()
        or 0
    )
    contractors = db.query(func.count(ContractorCompany.id)).filter(ContractorCompany.is_active.is_(True)).scalar() or 0
    residents = db.query(func.count(Resident.id)).filter(Resident.is_active.is_(True)).scalar() or 0

    recent = db.query(ServiceRequest).order_by(ServiceRequest.created_at.desc()).limit(12).all()
    return {
        "requests": {
            "total": total,
            "in_progress": in_progress,
            "done": done,
            "overdue": overdue,
        },
        "residents": residents,
        "contractors": contractors,
        "recent_requests": [_request_dict(item) for item in recent],
    }


@router.get("/buildings", response_model=List[BuildingOut])
async def list_buildings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return db.query(Building).order_by(Building.address.asc()).all()


@router.post("/buildings", response_model=BuildingOut)
async def create_building(
    payload: BuildingIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = Building(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/premises", response_model=PremiseOut)
async def create_premise(
    payload: PremiseIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    if not db.get(Building, payload.building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    item = Premise(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/residents", response_model=List[ResidentOut])
async def list_residents(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(Resident)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Resident.full_name.ilike(like))
            | (Resident.phone.ilike(like))
            | (Resident.email.ilike(like))
        )
    return query.order_by(Resident.full_name.asc()).limit(500).all()


@router.post("/residents", response_model=ResidentOut)
async def create_resident(
    payload: ResidentIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = Resident(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/contractors", response_model=List[ContractorOut])
async def list_contractors(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(ContractorCompany)
    if active_only:
        query = query.filter(ContractorCompany.is_active.is_(True))
    return query.order_by(ContractorCompany.name.asc()).all()


@router.post("/contractors", response_model=ContractorOut)
async def create_contractor(
    payload: ContractorIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = ContractorCompany(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/contractors/{contractor_id}", response_model=ContractorOut)
async def update_contractor(
    contractor_id: int,
    payload: ContractorPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = db.get(ContractorCompany, contractor_id)
    if not item:
        raise HTTPException(status_code=404, detail="Contractor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.post("/requests/intake")
async def intake_request(
    payload: RequestIntake,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    building = (
        db.query(Building)
        .filter(func.lower(Building.address) == payload.address.strip().lower())
        .first()
    )
    if not building:
        building = Building(address=payload.address.strip(), is_active=True)
        db.add(building)
        db.flush()

    premise = None
    if payload.apartment:
        premise = (
            db.query(Premise)
            .filter(
                Premise.building_id == building.id,
                Premise.apartment == payload.apartment.strip(),
            )
            .first()
        )
        if not premise:
            premise = Premise(
                building_id=building.id,
                apartment=payload.apartment.strip(),
                is_residential=True,
            )
            db.add(premise)
            db.flush()

    resident = (
        db.query(Resident)
        .filter(Resident.phone == payload.phone.strip())
        .first()
    )
    if not resident:
        resident = Resident(
            full_name=payload.applicant_name.strip(),
            phone=payload.phone.strip(),
            premise_id=premise.id if premise else None,
            is_active=True,
        )
        db.add(resident)
        db.flush()
    else:
        resident.full_name = payload.applicant_name.strip()
        if premise and not resident.premise_id:
            resident.premise_id = premise.id

    classification = _classify_request(payload.problem)
    category = payload.category or classification["category"]
    priority = payload.priority or classification["priority"]
    number = f"REQ-{datetime.utcnow():%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"

    item = ServiceRequest(
        number=number,
        resident_id=resident.id,
        building_id=building.id,
        premise_id=premise.id if premise else None,
        source_channel="operator",
        category=category,
        priority=priority,
        status="new",
        title=payload.problem.strip()[:160],
        description=payload.problem.strip(),
        created_by=current_user.id,
        sla_deadline=_default_sla_deadline(priority),
        extra_data={
            "notify_resident": payload.notify_resident,
            "classification_source": "rules_v1",
        },
    )
    db.add(item)
    db.flush()
    db.add(
        RequestEvent(
            request_id=item.id,
            actor_user_id=current_user.id,
            event_type="intake_created",
            payload={
                "category": category,
                "priority": priority,
                "building_id": building.id,
                "resident_id": resident.id,
            },
        )
    )
    db.commit()
    db.refresh(item)
    logger.info(
        "housing_request_intake_created",
        request_id=item.id,
        request_number=item.number,
        category=item.category,
        priority=item.priority,
        building_id=item.building_id,
        source_channel=item.source_channel,
    )
    try:
        dispatch_event(
            db,
            entity_type="request",
            event_type="request_created",
            entity_id=item.id,
            event_data={
                "status": item.status,
                "priority": item.priority,
                "category": item.category,
                "building_id": item.building_id,
                "source_channel": item.source_channel,
            },
        )
        db.refresh(item)
    except AutomationValidationError:
        pass
    except Exception as exc:
        logger.error(
            "housing_request_automation_failed",
            request_id=item.id,
            event_type="request_created",
            error_type=type(exc).__name__,
        )
    return _request_dict(item)


@router.get("/requests")
async def list_requests(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(ServiceRequest)
    if status:
        query = query.filter(ServiceRequest.status == status)
    if priority:
        query = query.filter(ServiceRequest.priority == priority)
    if category:
        query = query.filter(ServiceRequest.category == category)
    if overdue is True:
        query = query.filter(
            ServiceRequest.sla_deadline.isnot(None),
            ServiceRequest.sla_deadline < datetime.utcnow(),
            ~ServiceRequest.status.in_(["done", "closed", "cancelled"]),
        )
    items = query.order_by(ServiceRequest.created_at.desc()).limit(limit).all()
    return [_request_dict(item) for item in items]


@router.post("/requests")
async def create_request(
    payload: RequestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if payload.resident_id and not db.get(Resident, payload.resident_id):
        raise HTTPException(status_code=404, detail="Resident not found")
    if payload.building_id and not db.get(Building, payload.building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    if payload.contractor_id and not db.get(ContractorCompany, payload.contractor_id):
        raise HTTPException(status_code=404, detail="Contractor not found")

    number = f"REQ-{datetime.utcnow():%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"
    item = ServiceRequest(
        number=number,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(item)
    db.flush()
    db.add(
        RequestEvent(
            request_id=item.id,
            actor_user_id=current_user.id,
            event_type="created",
            payload={"status": item.status, "source_channel": item.source_channel},
        )
    )
    db.commit()
    db.refresh(item)
    logger.info(
        "housing_request_created",
        request_id=item.id,
        request_number=item.number,
        category=item.category,
        priority=item.priority,
        source_channel=item.source_channel,
    )
    return _request_dict(item)


@router.patch("/requests/{request_id}")
async def update_request(
    request_id: int,
    payload: RequestPatch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = db.get(ServiceRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")

    values = payload.model_dump(exclude_unset=True)
    requested_status = values.get("status")
    if requested_status is not None:
        requested_status = str(requested_status)
        if not is_request_status(requested_status):
            raise HTTPException(status_code=422, detail="Unsupported request status")
        if not can_transition_request(item.status, requested_status):
            raise HTTPException(
                status_code=409,
                detail=f"Transition {item.status} -> {requested_status} is not allowed",
            )

    changes: Dict[str, Any] = {}
    old_status = item.status
    old_priority = item.priority
    for field, value in values.items():
        previous = getattr(item, field)
        if previous != value:
            changes[field] = {
                "from": str(previous) if previous is not None else None,
                "to": str(value) if value is not None else None,
            }
            setattr(item, field, value)

    if item.status in {"done", "closed"} and not item.resolved_at:
        item.resolved_at = datetime.utcnow()
    elif item.status not in {"done", "closed"} and "status" in changes:
        item.resolved_at = None

    if changes:
        db.add(
            RequestEvent(
                request_id=item.id,
                actor_user_id=current_user.id,
                event_type="updated",
                payload=changes,
            )
        )
    db.commit()
    db.refresh(item)

    automation_events = [("request_updated", {})] if changes else []
    if old_status != item.status:
        automation_events.append(
            (
                "request_status_changed",
                {"old_status": old_status, "status": item.status},
            )
        )
    if old_priority != item.priority:
        automation_events.append(
            (
                "request_priority_changed",
                {"old_priority": old_priority, "priority": item.priority},
            )
        )

    for automation_event, event_data in automation_events:
        try:
            dispatch_event(
                db,
                entity_type="request",
                event_type=automation_event,
                entity_id=item.id,
                event_data=event_data,
            )
            db.refresh(item)
        except AutomationValidationError:
            continue
        except Exception as exc:
            logger.error(
                "housing_request_automation_failed",
                request_id=item.id,
                event_type=automation_event,
                error_type=type(exc).__name__,
            )

    if old_status != item.status:
        background_tasks.add_task(
            notify_resident_request_status_background,
            item.id,
            item.status,
        )
        logger.info(
            "housing_request_status_changed",
            request_id=item.id,
            request_number=item.number,
            old_status=old_status,
            status=item.status,
            actor_user_id=current_user.id,
        )

    return _request_dict(item)


@router.post("/requests/{request_id}/assign")
async def assign_request(
    request_id: int,
    assigned_user_id: Optional[int] = None,
    contractor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not assigned_user_id and not contractor_id:
        raise HTTPException(status_code=400, detail="assigned_user_id or contractor_id is required")
    item = db.get(ServiceRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    old_status = item.status
    old_priority = item.priority
    if assigned_user_id and not db.get(User, assigned_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if contractor_id and not db.get(ContractorCompany, contractor_id):
        raise HTTPException(status_code=404, detail="Contractor not found")

    item.assigned_user_id = assigned_user_id
    item.contractor_id = contractor_id
    item.status = "assigned"
    db.add(
        RequestEvent(
            request_id=item.id,
            actor_user_id=current_user.id,
            event_type="assigned",
            payload={"assigned_user_id": assigned_user_id, "contractor_id": contractor_id},
        )
    )
    db.commit()
    db.refresh(item)

    automation_events = [("request_updated", {})]
    if old_status != item.status:
        automation_events.append(("request_status_changed", {"old_status": old_status, "status": item.status}))
    if old_priority != item.priority:
        automation_events.append(("request_priority_changed", {"old_priority": old_priority, "priority": item.priority}))

    for automation_event, event_data in automation_events:
        try:
            dispatch_event(
                db,
                entity_type="request",
                event_type=automation_event,
                entity_id=item.id,
                event_data=event_data,
            )
            db.refresh(item)
        except AutomationValidationError:
            continue
        except Exception as exc:
            logger.error(
                "housing_request_automation_failed",
                request_id=item.id,
                event_type=automation_event,
                error_type=type(exc).__name__,
            )

    return _request_dict(item)
