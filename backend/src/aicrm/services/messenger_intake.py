"""Deterministic resident intake FSM for private messenger conversations."""
from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.messenger_catalog import resident_intake_defaults
from ..models.housing import Building, RequestEvent, Resident, ServiceRequest
from ..models.messenger import (
    MessengerConversation,
    MessengerIntegration,
    MessengerIntakeSession,
    MessengerMessage,
    OperatorAlert,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

INTAKE_STATES = ("full_name", "address", "phone", "problem")


def _merged_intake_settings(integration: MessengerIntegration) -> dict[str, Any]:
    defaults = resident_intake_defaults()
    configured = dict((integration.settings or {}).get("resident_intake") or {})

    prompts = dict(defaults["prompts"])
    prompts.update(
        {
            str(key): str(value)
            for key, value in dict(configured.get("prompts") or {}).items()
            if value is not None
        }
    )

    notifications = dict(defaults["notifications"])
    notifications.update(
        {
            str(key): str(value)
            for key, value in dict(configured.get("notifications") or {}).items()
            if value is not None
        }
    )

    return {
        "enabled": bool(configured.get("enabled", defaults["enabled"])),
        "prompts": prompts,
        "notifications": notifications,
    }


def _normalize_phone(value: str) -> str | None:
    raw = str(value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10 or len(digits) > 15:
        return None

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    if raw.startswith("+"):
        return "+" + digits
    return digits


def _identity_key(
    integration: MessengerIntegration,
    external_user_id: str,
    conversation: MessengerConversation,
) -> str:
    user_part = external_user_id.strip() or conversation.external_chat_id
    return f"{integration.provider}:{integration.id}:{user_part}"


def _start_session(
    db: Session,
    *,
    conversation: MessengerConversation,
    external_user_id: str,
) -> MessengerIntakeSession:
    session = (
        db.query(MessengerIntakeSession)
        .filter(MessengerIntakeSession.conversation_id == conversation.id)
        .first()
    )
    if session is None:
        session = MessengerIntakeSession(
            conversation_id=conversation.id,
            external_user_id=external_user_id or None,
            state="full_name",
        )
        db.add(session)
    else:
        session.external_user_id = external_user_id or session.external_user_id
        session.state = "full_name"
        session.full_name = None
        session.address = None
        session.phone = None
        session.problem = None
        session.resident_id = None
        session.request_id = None
        session.completed_at = None
    db.commit()
    db.refresh(session)
    return session


def _create_request_from_session(
    db: Session,
    *,
    integration: MessengerIntegration,
    conversation: MessengerConversation,
    session: MessengerIntakeSession,
) -> ServiceRequest:
    identity = _identity_key(
        integration,
        session.external_user_id or "",
        conversation,
    )

    resident = (
        db.query(Resident)
        .filter(Resident.external_id == identity)
        .first()
    )
    if resident is None and session.phone:
        resident = (
            db.query(Resident)
            .filter(Resident.phone == session.phone)
            .first()
        )

    if resident is None:
        resident = Resident(
            full_name=session.full_name or "Житель",
            phone=session.phone,
            preferred_channel=integration.provider,
            external_id=identity,
            is_active=True,
        )
        db.add(resident)
        db.flush()
    else:
        resident.full_name = session.full_name or resident.full_name
        resident.phone = session.phone or resident.phone
        resident.preferred_channel = integration.provider
        resident.external_id = identity
        resident.is_active = True

    address = str(session.address or "").strip()
    building = (
        db.query(Building)
        .filter(func.lower(Building.address) == address.lower())
        .first()
    )
    if building is None:
        building = Building(
            address=address,
            is_active=True,
        )
        db.add(building)
        db.flush()

    problem = str(session.problem or "").strip()
    number = f"REQ-{datetime.utcnow():%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"
    request_item = ServiceRequest(
        number=number,
        resident_id=resident.id,
        building_id=building.id,
        source_channel=integration.provider,
        source_conversation_id=str(conversation.id),
        category="general",
        priority="normal",
        status="new",
        title=problem[:160],
        description=problem,
        sla_deadline=datetime.utcnow() + timedelta(days=3),
        extra_data={
            "intake_source": "messenger_fsm",
            "intake_session_id": session.id,
            "applicant_name": session.full_name,
            "phone": session.phone,
            "address": address,
        },
    )
    db.add(request_item)
    db.flush()

    db.add(
        RequestEvent(
            request_id=request_item.id,
            actor_user_id=None,
            event_type="messenger_intake_submitted",
            payload={
                "conversation_id": conversation.id,
                "integration_id": integration.id,
                "provider": integration.provider,
                "resident_id": resident.id,
                "building_id": building.id,
            },
        )
    )

    db.add(
        OperatorAlert(
            conversation_id=conversation.id,
            request_id=request_item.id,
            kind="request",
            severity="normal",
            title=request_item.title,
            summary=(
                f"{session.full_name}\n"
                f"{address}\n"
                f"{session.phone}\n\n"
                f"{problem}"
            ),
            status="new",
            payload={
                "source": "resident_intake",
                "request_number": request_item.number,
            },
        )
    )

    conversation.resident_id = resident.id
    conversation.requires_attention = True
    conversation.summary = problem

    session.resident_id = resident.id
    session.request_id = request_item.id
    session.state = "submitted"
    session.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(request_item)

    logger.info(
        "resident_intake_request_created",
        integration_id=integration.id,
        provider=integration.provider,
        conversation_id=conversation.id,
        intake_session_id=session.id,
        resident_id=resident.id,
        request_id=request_item.id,
        request_number=request_item.number,
    )
    return request_item


def process_private_intake_message(
    db: Session,
    *,
    message_id: int,
    external_user_id: str,
) -> dict[str, Any]:
    """Consume one inbound private message and return the next bot reply."""
    message = db.get(MessengerMessage, message_id)
    if message is None:
        raise ValueError("Message not found")
    conversation = db.get(MessengerConversation, message.conversation_id)
    if conversation is None:
        raise ValueError("Conversation not found")
    integration = db.get(MessengerIntegration, conversation.integration_id)
    if integration is None:
        raise ValueError("Integration not found")

    intake = _merged_intake_settings(integration)
    if not intake["enabled"]:
        return {"handled": False, "reason": "resident_intake_disabled"}

    prompts = intake["prompts"]
    session = (
        db.query(MessengerIntakeSession)
        .filter(MessengerIntakeSession.conversation_id == conversation.id)
        .first()
    )

    if session is None or session.state not in INTAKE_STATES:
        session = _start_session(
            db,
            conversation=conversation,
            external_user_id=external_user_id,
        )
        logger.info(
            "resident_intake_started",
            integration_id=integration.id,
            conversation_id=conversation.id,
            intake_session_id=session.id,
        )
        return {
            "handled": True,
            "state": session.state,
            "reply_text": prompts["full_name"],
            "request_id": None,
        }

    session.external_user_id = external_user_id or session.external_user_id
    value = str(message.text or "").strip()

    if session.state == "full_name":
        if len(value) < 2 or len(value) > 255:
            return {
                "handled": True,
                "state": session.state,
                "reply_text": prompts["invalid_full_name"],
                "request_id": None,
            }
        session.full_name = value
        session.state = "address"
        db.commit()
        return {
            "handled": True,
            "state": session.state,
            "reply_text": prompts["address"],
            "request_id": None,
        }

    if session.state == "address":
        if len(value) < 3 or len(value) > 500:
            return {
                "handled": True,
                "state": session.state,
                "reply_text": prompts["invalid_address"],
                "request_id": None,
            }
        session.address = value
        session.state = "phone"
        db.commit()
        return {
            "handled": True,
            "state": session.state,
            "reply_text": prompts["phone"],
            "request_id": None,
        }

    if session.state == "phone":
        phone = _normalize_phone(value)
        if phone is None:
            return {
                "handled": True,
                "state": session.state,
                "reply_text": prompts["invalid_phone"],
                "request_id": None,
            }
        session.phone = phone
        session.state = "problem"
        db.commit()
        return {
            "handled": True,
            "state": session.state,
            "reply_text": prompts["problem"],
            "request_id": None,
        }

    if len(value) < 3 or len(value) > 5000:
        return {
            "handled": True,
            "state": session.state,
            "reply_text": prompts["invalid_problem"],
            "request_id": None,
        }

    session.problem = value
    request_item = _create_request_from_session(
        db,
        integration=integration,
        conversation=conversation,
        session=session,
    )
    return {
        "handled": True,
        "state": "submitted",
        "reply_text": prompts["submitted"],
        "request_id": request_item.id,
        "request_number": request_item.number,
    }
