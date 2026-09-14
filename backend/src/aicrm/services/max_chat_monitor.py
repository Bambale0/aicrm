"""Background verification of MAX chat/channel permissions."""
from __future__ import annotations

import json
from datetime import datetime

from ..core.database import SessionLocal
from ..models.messenger import MessengerChannel, MessengerIntegration
from ..utils.crypto import decrypt_data
from ..utils.logging import get_logger
from .max_connector import MaxAPIError, get_bot_chat_membership, get_chat

logger = get_logger(__name__)


async def check_max_chat_permissions_background(
    integration_id: int,
    chat_id: str,
) -> None:
    db = SessionLocal()
    try:
        integration = db.get(MessengerIntegration, integration_id)
        if not integration or integration.provider != "max":
            return
        if not integration.credentials_encrypted:
            return

        credentials = json.loads(decrypt_data(integration.credentials_encrypted))
        access_token = credentials.get("access_token")
        if not access_token:
            return

        channel = (
            db.query(MessengerChannel)
            .filter(
                MessengerChannel.integration_id == integration.id,
                MessengerChannel.external_chat_id == str(chat_id),
                MessengerChannel.purpose == "monitor",
            )
            .first()
        )
        if channel is None:
            channel = MessengerChannel(
                integration_id=integration.id,
                external_chat_id=str(chat_id),
                purpose="monitor",
                status="discovered",
                is_active=True,
            )
            db.add(channel)
            db.flush()

        started_at = datetime.utcnow()
        try:
            chat = await get_chat(access_token, chat_id=str(chat_id))
            membership = await get_bot_chat_membership(
                access_token,
                chat_id=str(chat_id),
            )
            permissions = membership.get("permissions")
            if not isinstance(permissions, list):
                permissions = []

            is_admin = bool(membership.get("is_admin"))
            can_read_all = "read_all_messages" in permissions

            channel.name = str(chat.get("title") or channel.name or "") or None
            channel.channel_type = str(chat.get("type") or "") or None
            channel.provider_data = {
                "is_admin": is_admin,
                "read_all_messages": can_read_all,
                "permissions": permissions,
                "link": chat.get("link"),
                "is_public": chat.get("is_public"),
            }
            channel.status = "verified" if is_admin and can_read_all else "limited"
            channel.last_health_at = started_at
            channel.last_error = None

            logger.info(
                "max_channel_permissions_checked",
                integration_id=integration.id,
                channel_id=channel.id,
                external_chat_id=str(chat_id),
                purpose=channel.purpose,
                is_admin=is_admin,
                read_all_messages=can_read_all,
            )
        except MaxAPIError as exc:
            channel.status = "error"
            channel.last_health_at = started_at
            channel.last_error = str(exc)
            logger.warning(
                "max_channel_permissions_check_failed",
                integration_id=integration.id,
                channel_id=channel.id,
                external_chat_id=str(chat_id),
                error=str(exc),
            )

        db.commit()
    finally:
        db.close()
