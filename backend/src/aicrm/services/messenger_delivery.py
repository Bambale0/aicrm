"""Provider-neutral outbound delivery for persisted messenger conversations."""
from __future__ import annotations

from datetime import datetime
import json

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.messenger import (
    MessengerConversation,
    MessengerIntegration,
    MessengerMessage,
)
from ..services.max_connector import MaxAPIError, send_message as max_send_message
from ..utils.crypto import decrypt_data
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MessengerDeliveryError(RuntimeError):
    pass


def _credentials(integration: MessengerIntegration) -> dict:
    if not integration.credentials_encrypted:
        return {}
    try:
        data = json.loads(decrypt_data(integration.credentials_encrypted))
    except Exception as exc:
        raise MessengerDeliveryError("Stored messenger credentials are invalid") from exc
    return data if isinstance(data, dict) else {}


async def send_conversation_text(
    db: Session,
    *,
    conversation_id: int,
    text: str,
) -> MessengerMessage:
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation:
        raise MessengerDeliveryError("Conversation not found")
    integration = db.get(MessengerIntegration, conversation.integration_id)
    if not integration or not integration.is_active:
        raise MessengerDeliveryError("Messenger integration is inactive")

    clean_text = str(text or "").strip()
    if not clean_text:
        raise MessengerDeliveryError("Message text is empty")

    credentials = _credentials(integration)
    external_message_id = None

    if integration.provider == "max":
        token = credentials.get("access_token")
        if not token:
            raise MessengerDeliveryError("MAX access token is not configured")
        try:
            data = await max_send_message(
                token,
                chat_id=conversation.external_chat_id,
                text=clean_text,
            )
        except MaxAPIError as exc:
            raise MessengerDeliveryError(str(exc)) from exc
        max_message = data.get("message") if isinstance(data, dict) else None
        max_body = (
            max_message.get("body")
            if isinstance(max_message, dict)
            and isinstance(max_message.get("body"), dict)
            else {}
        )
        external_message_id = str(max_body.get("mid") or "") or None

    elif integration.provider == "telegram":
        token = credentials.get("bot_token")
        if not token:
            raise MessengerDeliveryError("Telegram bot token is not configured")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.telegram_api_base_url.rstrip('/')}/bot{token}/sendMessage",
                    json={
                        "chat_id": conversation.external_chat_id,
                        "text": clean_text,
                    },
                )
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MessengerDeliveryError("Telegram delivery failed") from exc
        if response.status_code != 200 or not payload.get("ok"):
            raise MessengerDeliveryError("Telegram delivery failed")
        external_message_id = str(
            (payload.get("result") or {}).get("message_id") or ""
        ) or None

    else:
        raise MessengerDeliveryError(
            f"Outbound adapter for {integration.provider} is not implemented"
        )

    message = MessengerMessage(
        conversation_id=conversation.id,
        external_message_id=external_message_id,
        direction="outbound",
        message_type="text",
        text=clean_text,
        attachments=[],
        status="delivered",
        delivered_at=datetime.utcnow(),
    )
    conversation.last_message_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)

    logger.info(
        "messenger_outbound_delivered",
        integration_id=integration.id,
        provider=integration.provider,
        conversation_id=conversation.id,
        message_id=message.id,
        external_message_id=external_message_id,
    )
    return message


async def send_conversation_text_background(
    conversation_id: int,
    text: str,
    *,
    event_name: str = "messenger_background_delivery",
) -> None:
    db = SessionLocal()
    try:
        await send_conversation_text(
            db,
            conversation_id=conversation_id,
            text=text,
        )
    except Exception as exc:
        db.rollback()
        logger.warning(
            event_name + "_failed",
            conversation_id=conversation_id,
            error_type=type(exc).__name__,
            error=str(exc),
        )
    finally:
        db.close()
