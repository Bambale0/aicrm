"""Background verification of MAX group-chat monitoring permissions."""
from __future__ import annotations

import json
from datetime import datetime

from ..core.database import SessionLocal
from ..models.messenger import MessengerIntegration
from ..utils.crypto import decrypt_data
from ..utils.logging import get_logger
from .max_connector import MaxAPIError, get_bot_chat_membership

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

        settings = dict(integration.settings or {})
        statuses = dict(settings.get("monitor_chat_status") or {})

        try:
            membership = await get_bot_chat_membership(
                access_token,
                chat_id=chat_id,
            )
            permissions = membership.get("permissions")
            if not isinstance(permissions, list):
                permissions = []

            is_admin = bool(membership.get("is_admin"))
            can_read_all = "read_all_messages" in permissions
            statuses[str(chat_id)] = {
                "is_admin": is_admin,
                "read_all_messages": can_read_all,
                "checked_at": datetime.utcnow().isoformat(),
                "error": None,
            }

            logger.info(
                "max_chat_permissions_checked",
                integration_id=integration.id,
                chat_id=str(chat_id),
                is_admin=is_admin,
                read_all_messages=can_read_all,
            )
        except MaxAPIError as exc:
            statuses[str(chat_id)] = {
                "is_admin": False,
                "read_all_messages": False,
                "checked_at": datetime.utcnow().isoformat(),
                "error": str(exc),
            }
            logger.warning(
                "max_chat_permissions_check_failed",
                integration_id=integration.id,
                chat_id=str(chat_id),
                error=str(exc),
            )

        settings["monitor_chat_status"] = statuses
        integration.settings = settings
        db.commit()
    finally:
        db.close()
