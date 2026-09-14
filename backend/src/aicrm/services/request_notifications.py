"""Resident notifications emitted by service-request status transitions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.housing_catalog import REQUEST_RESIDENT_NOTIFICATION_STATUSES
from ..core.messenger_catalog import resident_intake_defaults
from ..models.housing import RequestEvent, ServiceRequest
from ..models.messenger import MessengerConversation, MessengerIntegration
from ..services.messenger_delivery import send_conversation_text
from ..utils.logging import get_logger

logger = get_logger(__name__)


def _notification_template(
    integration: MessengerIntegration,
    status: str,
) -> str | None:
    defaults = resident_intake_defaults()["notifications"]
    configured = dict((integration.settings or {}).get("resident_intake") or {})
    notifications = dict(defaults)
    notifications.update(
        {
            str(key): str(value)
            for key, value in dict(configured.get("notifications") or {}).items()
            if value is not None
        }
    )
    return notifications.get(status)


async def notify_resident_request_status(
    db: Session,
    *,
    request_id: int,
    status: str,
) -> bool:
    if status not in REQUEST_RESIDENT_NOTIFICATION_STATUSES:
        return False

    request_item = db.get(ServiceRequest, request_id)
    if request_item is None or not request_item.source_conversation_id:
        return False

    try:
        conversation_id = int(request_item.source_conversation_id)
    except (TypeError, ValueError):
        return False

    conversation = db.get(MessengerConversation, conversation_id)
    if conversation is None:
        return False
    integration = db.get(MessengerIntegration, conversation.integration_id)
    if integration is None or not integration.is_active:
        return False

    template = _notification_template(integration, status)
    if not template:
        return False

    text = (
        template
        .replace("{number}", request_item.number)
        .replace("{title}", request_item.title or "")
    )

    await send_conversation_text(
        db,
        conversation_id=conversation.id,
        text=text,
    )

    db.add(
        RequestEvent(
            request_id=request_item.id,
            actor_user_id=None,
            event_type="resident_notified",
            payload={
                "status": status,
                "provider": integration.provider,
                "conversation_id": conversation.id,
            },
        )
    )
    db.commit()

    logger.info(
        "request_resident_notified",
        request_id=request_item.id,
        request_number=request_item.number,
        status=status,
        integration_id=integration.id,
        provider=integration.provider,
        conversation_id=conversation.id,
    )
    return True


async def notify_resident_request_status_background(
    request_id: int,
    status: str,
) -> None:
    db = SessionLocal()
    try:
        await notify_resident_request_status(
            db,
            request_id=request_id,
            status=status,
        )
    except Exception as exc:
        db.rollback()
        logger.warning(
            "request_resident_notification_failed",
            request_id=request_id,
            status=status,
            error_type=type(exc).__name__,
            error=str(exc),
        )
    finally:
        db.close()
