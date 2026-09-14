"""Provider-agnostic messenger connection API."""
import json
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.dependencies import get_current_active_user, get_current_admin_user, get_db
from ...core.messenger_catalog import MESSENGER_CHANNEL_PURPOSES, channel_purpose_catalog
from ...models.housing import RequestEvent, ServiceRequest
from ...models.messenger import (
    MessengerChannel,
    MessengerConversation,
    MessengerInboundEvent,
    MessengerIntegration,
    MessengerMessage,
    OperatorAlert,
)
from ...models.user import User
from ...services.automation_engine import AutomationValidationError, dispatch_event
from ...services.max_connector import (
    MaxAPIError,
    get_bot_chat_membership,
    get_chat as max_get_chat,
    register_webhook as max_register_webhook,
    send_message as max_send_message,
    verify_bot as max_verify_bot,
)
from ...services.max_chat_monitor import check_max_chat_permissions_background
from ...services.messenger_ai import process_message_background
from ...utils.crypto import decrypt_data, encrypt_data
from ...utils.logging import get_logger

router = APIRouter(tags=["messengers"])
logger = get_logger(__name__)

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "max": {
        "name": "MAX",
        "primary": True,
        "credential_fields": [
            {
                "name": "access_token",
                "label": "Access token",
                "type": "secret",
                "required": True,
            }
        ],
        "capabilities": ["text", "media", "webhook", "channels"],
        "verification": "adapter",
    },
    "telegram": {
        "name": "Telegram",
        "primary": False,
        "credential_fields": [
            {
                "name": "bot_token",
                "label": "Bot token",
                "type": "secret",
                "required": True,
            }
        ],
        "capabilities": ["text", "photo", "video", "voice", "files", "webhook"],
        "verification": "adapter",
    },
    "vk": {
        "name": "VK",
        "primary": False,
        "credential_fields": [
            {
                "name": "access_token",
                "label": "Access token",
                "type": "secret",
                "required": True,
            },
            {
                "name": "group_id",
                "label": "Group ID",
                "type": "text",
                "required": True,
            },
        ],
        "capabilities": ["text", "media", "webhook"],
        "verification": "adapter_required",
    },
}


class IntegrationCreate(BaseModel):
    provider: str
    name: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)


class IntegrationPatch(BaseModel):
    name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WebhookRegisterRequest(BaseModel):
    public_base_url: Optional[str] = None
    secret_token: Optional[str] = Field(default=None, min_length=8, max_length=256)


class MessengerChannelCreate(BaseModel):
    integration_id: int = Field(gt=0)
    external_chat_id: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class MessengerChannelPatch(BaseModel):
    external_chat_id: Optional[str] = Field(default=None, min_length=1, max_length=255)
    purpose: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class MessengerChannelTestMessage(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class OutboundMessageCreate(BaseModel):
    text: str


class ConversationRequestCreate(BaseModel):
    title: Optional[str] = None
    category: str = "general"
    priority: str = "normal"
    description: Optional[str] = None
    building_id: Optional[int] = None
    premise_id: Optional[int] = None
    sla_deadline: Optional[datetime] = None


def _normalize_inbound(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if provider == "telegram":
        message = payload.get("message") or payload.get("edited_message") or {}
        chat = message.get("chat") or {}
        sender = message.get("from") or {}
        attachments: List[Dict[str, Any]] = []
        message_type = "text"

        if message.get("photo"):
            message_type = "photo"
            attachments.append({"type": "photo", "items": message.get("photo")})
        elif message.get("video"):
            message_type = "video"
            attachments.append({"type": "video", "item": message.get("video")})
        elif message.get("voice"):
            message_type = "voice"
            attachments.append({"type": "voice", "item": message.get("voice")})
        elif message.get("document"):
            message_type = "file"
            attachments.append({"type": "file", "item": message.get("document")})

        text = message.get("text") or message.get("caption") or ""
        return {
            "event_type": "message_created",
            "external_chat_id": str(chat.get("id") or ""),
            "external_user_id": str(sender.get("id") or ""),
            "external_message_id": str(message.get("message_id") or ""),
            "message_type": message_type,
            "text": text,
            "attachments": attachments,
            "timestamp": message.get("date"),
            "source_mode": "group_monitor" if str(chat.get("type") or "") in {"group", "supergroup", "channel"} else "private_intake",
        }

    if provider == "max":
        update_type = str(payload.get("update_type") or "")
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        recipient = message.get("recipient") if isinstance(message.get("recipient"), dict) else {}
        sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}
        body = message.get("body") if isinstance(message.get("body"), dict) else {}

        external_chat_id = (
            payload.get("chat_id")
            or recipient.get("chat_id")
            or recipient.get("user_id")
            or ""
        )
        recipient_type = str(
            recipient.get("chat_type")
            or recipient.get("type")
            or payload.get("chat_type")
            or ""
        ).lower()
        source_mode = (
            "group_monitor"
            if recipient_type in {"chat", "channel", "group"}
            else "private_intake"
        )

        attachments = body.get("attachments")
        if not isinstance(attachments, list):
            attachments = []
        message_type = "text"
        if attachments:
            first = attachments[0] if isinstance(attachments[0], dict) else {}
            message_type = str(first.get("type") or "media")

        return {
            "event_type": update_type,
            "external_chat_id": str(external_chat_id),
            "external_user_id": str(sender.get("user_id") or ""),
            "external_message_id": str(
                body.get("mid")
                or message.get("message_id")
                or payload.get("message_id")
                or ""
            ),
            "message_type": message_type,
            "text": str(body.get("text") or ""),
            "attachments": attachments,
            "timestamp": message.get("timestamp") or payload.get("timestamp"),
            "source_mode": source_mode,
        }

    return {
        "event_type": str(payload.get("event_type") or "message_created"),
        "external_chat_id": str(payload.get("external_chat_id") or payload.get("chat_id") or ""),
        "external_user_id": str(payload.get("external_user_id") or payload.get("user_id") or ""),
        "external_message_id": str(payload.get("external_message_id") or payload.get("message_id") or payload.get("id") or ""),
        "message_type": str(payload.get("message_type") or "text"),
        "text": str(payload.get("text") or payload.get("message") or ""),
        "attachments": payload.get("attachments") or [],
        "timestamp": payload.get("timestamp"),
        "source_mode": str(payload.get("source_mode") or "private_intake"),
    }


def _conversation_public(item: MessengerConversation, provider: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": item.id,
        "integration_id": item.integration_id,
        "provider": provider,
        "external_chat_id": item.external_chat_id,
        "resident_id": item.resident_id,
        "status": item.status,
        "requires_attention": item.requires_attention,
        "summary": item.summary,
        "last_message_at": item.last_message_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _load_credentials(item: MessengerIntegration) -> Dict[str, Any]:
    if not item.credentials_encrypted:
        return {}
    try:
        payload = json.loads(decrypt_data(item.credentials_encrypted))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Stored integration credentials are invalid") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Stored integration credentials are invalid")
    return payload


def _store_credentials(item: MessengerIntegration, credentials: Dict[str, Any]) -> None:
    item.credentials_encrypted = encrypt_data(json.dumps(credentials, ensure_ascii=False))


def _clean_settings(values: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    result = dict(values or {})
    # Secrets and external chat IDs are first-class managed entities, never JSON settings.
    for forbidden in ("webhook_secret", "monitor_chat_ids", "monitor_chat_status", "operator_chat_id"):
        result.pop(forbidden, None)
    return result


def _public(item: MessengerIntegration) -> Dict[str, Any]:
    credentials = _load_credentials(item) if item.credentials_encrypted else {}
    fields = PROVIDERS.get(item.provider, {}).get("credential_fields", [])
    safe_settings = _clean_settings(item.settings)
    return {
        "id": item.id,
        "provider": item.provider,
        "name": item.name,
        "status": item.status,
        "settings": safe_settings,
        "webhook_url": item.webhook_url,
        "external_account_id": item.external_account_id,
        "last_health_at": item.last_health_at,
        "last_error": item.last_error,
        "is_active": item.is_active,
        "has_credentials": bool(item.credentials_encrypted),
        "credential_status": {
            str(field.get("name")): bool(credentials.get(str(field.get("name"))))
            for field in fields
            if field.get("name")
        },
        "webhook_secret_configured": bool(credentials.get("webhook_secret")),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _channel_public(item: MessengerChannel) -> Dict[str, Any]:
    return {
        "id": item.id,
        "integration_id": item.integration_id,
        "external_chat_id": item.external_chat_id,
        "name": item.name,
        "purpose": item.purpose,
        "channel_type": item.channel_type,
        "status": item.status,
        "provider_data": item.provider_data or {},
        "last_health_at": item.last_health_at,
        "last_error": item.last_error,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _validate_channel_purpose(value: str) -> str:
    purpose = str(value or "").strip()
    if purpose not in MESSENGER_CHANNEL_PURPOSES:
        raise HTTPException(status_code=422, detail="Unsupported messenger channel purpose")
    return purpose


@router.get("/messengers/providers")
async def list_providers(_: User = Depends(get_current_admin_user)):
    return [{"provider": key, **value} for key, value in PROVIDERS.items()]


@router.get("/messengers")
async def list_integrations(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    items = db.query(MessengerIntegration).order_by(MessengerIntegration.created_at.desc()).all()
    return [_public(item) for item in items]


@router.post("/messengers")
async def create_integration(
    payload: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    if payload.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported messenger provider")

    required = [
        field["name"]
        for field in PROVIDERS[payload.provider]["credential_fields"]
        if field.get("required")
    ]
    missing = [name for name in required if not payload.credentials.get(name)]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_credentials": missing})

    encrypted = encrypt_data(json.dumps(payload.credentials, ensure_ascii=False))
    integration_settings = _clean_settings(payload.settings)
    if payload.provider == "max":
        integration_settings.setdefault("ai_monitoring_enabled", True)
        integration_settings.setdefault("ai_context_messages", settings.messenger_ai_context_messages)
        integration_settings.setdefault("send_private_ack", True)

    item = MessengerIntegration(
        provider=payload.provider,
        name=payload.name,
        credentials_encrypted=encrypted,
        settings=integration_settings,
        status="configured",
        is_active=False,
        created_by=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_integration_created",
        integration_id=item.id,
        provider=item.provider,
        status=item.status,
    )
    return _public(item)


@router.patch("/messengers/{integration_id}")
async def update_integration(
    integration_id: int,
    payload: IntegrationPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    data = payload.model_dump(exclude_unset=True)
    credentials_patch = data.pop("credentials", None)
    settings_patch = data.pop("settings", None)

    if credentials_patch is not None:
        credentials = _load_credentials(item)
        for key, value in credentials_patch.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            credentials[key] = value.strip() if isinstance(value, str) else value
        _store_credentials(item, credentials)
        item.status = "configured"
        item.last_error = None

    if settings_patch is not None:
        merged_settings = _clean_settings(item.settings)
        merged_settings.update(_clean_settings(settings_patch))
        item.settings = merged_settings

    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_integration_updated",
        integration_id=item.id,
        provider=item.provider,
        credentials_rotated=credentials_patch is not None,
    )
    return _public(item)


@router.delete("/messengers/{integration_id}")
async def archive_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    item.is_active = False
    item.status = "archived"
    (
        db.query(MessengerChannel)
        .filter(MessengerChannel.integration_id == item.id)
        .update({"is_active": False, "status": "archived"}, synchronize_session=False)
    )
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_integration_archived",
        integration_id=item.id,
        provider=item.provider,
    )
    return _public(item)


@router.post("/messengers/{integration_id}/verify")
async def verify_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.credentials_encrypted:
        raise HTTPException(status_code=422, detail="Credentials are not configured")

    credentials = _load_credentials(item)

    if item.provider == "telegram":
        import httpx
        token = credentials.get("bot_token")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.telegram_api_base_url.rstrip('/')}/bot{token}/getMe")
            data = response.json()
            if response.status_code == 200 and data.get("ok"):
                result = data.get("result", {})
                item.external_account_id = str(result.get("id") or "")
                item.status = "verified"
                item.last_health_at = datetime.utcnow()
                item.last_error = None
                db.commit()
                return {"verified": True, "provider": item.provider, "account": {"id": result.get("id"), "username": result.get("username")}}
            item.status = "error"
            item.last_error = "Telegram credential verification failed"
            db.commit()
            return {"verified": False, "provider": item.provider, "detail": item.last_error}
        except Exception as exc:
            item.status = "error"
            item.last_error = f"Telegram verification error: {type(exc).__name__}"
            db.commit()
            return {"verified": False, "provider": item.provider, "detail": item.last_error}

    if item.provider == "max":
        token = credentials.get("access_token")
        try:
            result = await max_verify_bot(token)
            item.external_account_id = str(result.get("user_id") or "")
            item.status = "verified"
            item.last_health_at = datetime.utcnow()
            item.last_error = None
            db.commit()
            return {
                "verified": True,
                "provider": item.provider,
                "account": {
                    "id": result.get("user_id"),
                    "username": result.get("username"),
                    "name": result.get("name") or result.get("first_name"),
                },
            }
        except MaxAPIError as exc:
            item.status = "error"
            item.last_error = str(exc)
            db.commit()
            return {
                "verified": False,
                "provider": item.provider,
                "detail": item.last_error,
            }

    raise HTTPException(
        status_code=501,
        detail=f"Verification adapter for {item.provider} is not implemented yet",
    )


@router.post("/messengers/{integration_id}/webhook/register")
async def register_webhook(
    integration_id: int,
    payload: WebhookRegisterRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.credentials_encrypted:
        raise HTTPException(status_code=422, detail="Credentials are not configured")

    base_url = (payload.public_base_url or settings.public_base_url).rstrip("/")
    webhook_url = f"{base_url}/api/webhooks/messengers/{item.provider}/{item.id}"
    credentials = _load_credentials(item)
    integration_settings = _clean_settings(item.settings)

    if item.provider == "telegram":
        import httpx

        token = credentials.get("bot_token")
        secret = payload.secret_token or secrets.token_urlsafe(24)
        body: Dict[str, Any] = {"url": webhook_url, "secret_token": secret}
        credentials["webhook_secret"] = secret

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.telegram_api_base_url.rstrip('/')}/bot{token}/setWebhook",
                    json=body,
                )
            data = response.json()
            if response.status_code != 200 or not data.get("ok"):
                item.status = "error"
                item.last_error = "Telegram webhook registration failed"
                db.commit()
                raise HTTPException(status_code=502, detail=item.last_error)
        except HTTPException:
            raise
        except Exception as exc:
            item.status = "error"
            item.last_error = f"Telegram webhook error: {type(exc).__name__}"
            db.commit()
            raise HTTPException(status_code=502, detail=item.last_error)

    elif item.provider == "max":
        token = credentials.get("access_token")
        secret = payload.secret_token or secrets.token_urlsafe(24)
        credentials["webhook_secret"] = secret
        try:
            await max_register_webhook(
                token,
                webhook_url,
                secret=secret,
                update_types=[
                    "message_created",
                    "message_edited",
                    "bot_added",
                    "bot_started",
                    "bot_removed",
                ],
            )
        except MaxAPIError as exc:
            item.status = "error"
            item.last_error = str(exc)
            db.commit()
            raise HTTPException(status_code=502, detail=item.last_error) from exc

    else:
        raise HTTPException(
            status_code=501,
            detail=f"Webhook registration adapter for {item.provider} is not implemented yet",
        )

    _store_credentials(item, credentials)
    item.webhook_url = webhook_url
    item.settings = integration_settings
    item.status = "verified"
    item.last_error = None
    item.last_health_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return {"registered": True, "provider": item.provider, "webhook_url": webhook_url, "webhook_secret_configured": True}


@router.post("/messengers/{integration_id}/activate")
async def activate_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if item.status not in {"verified", "configured"}:
        raise HTTPException(status_code=409, detail="Integration must be configured or verified first")
    item.is_active = True
    item.status = "active"
    db.commit()
    db.refresh(item)
    return _public(item)


@router.post("/messengers/{integration_id}/deactivate")
async def deactivate_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    item.is_active = False
    item.status = "disabled"
    db.commit()
    db.refresh(item)
    return _public(item)


@router.get("/messengers/{integration_id}/health")
async def integration_health(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    return {
        "id": item.id,
        "provider": item.provider,
        "status": item.status,
        "is_active": item.is_active,
        "last_health_at": item.last_health_at,
        "last_error": item.last_error,
    }



@router.get("/messenger-channels/catalog")
async def messenger_channel_catalog(
    _: User = Depends(get_current_admin_user),
):
    return channel_purpose_catalog()


@router.get("/messenger-channels")
async def list_messenger_channels(
    integration_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    query = db.query(MessengerChannel)
    if integration_id is not None:
        query = query.filter(MessengerChannel.integration_id == integration_id)
    items = query.order_by(MessengerChannel.created_at.desc()).all()
    return [_channel_public(item) for item in items]


@router.post("/messenger-channels")
async def create_messenger_channel(
    payload: MessengerChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    integration = db.get(MessengerIntegration, payload.integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Messenger integration not found")

    purpose = _validate_channel_purpose(payload.purpose)
    external_chat_id = payload.external_chat_id.strip()
    duplicate = (
        db.query(MessengerChannel)
        .filter(
            MessengerChannel.integration_id == integration.id,
            MessengerChannel.external_chat_id == external_chat_id,
            MessengerChannel.purpose == purpose,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This channel is already configured for that purpose")

    item = MessengerChannel(
        integration_id=integration.id,
        external_chat_id=external_chat_id,
        purpose=purpose,
        name=(payload.name or "").strip() or None,
        status="configured",
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_channel_created",
        channel_id=item.id,
        integration_id=item.integration_id,
        provider=integration.provider,
        purpose=item.purpose,
        external_chat_id=item.external_chat_id,
    )
    return _channel_public(item)


@router.patch("/messenger-channels/{channel_id}")
async def update_messenger_channel(
    channel_id: int,
    payload: MessengerChannelPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerChannel, channel_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger channel not found")

    data = payload.model_dump(exclude_unset=True)
    if "purpose" in data:
        data["purpose"] = _validate_channel_purpose(data["purpose"])
    if "external_chat_id" in data:
        data["external_chat_id"] = str(data["external_chat_id"]).strip()
    if "name" in data:
        data["name"] = (data["name"] or "").strip() or None

    target_chat_id = data.get("external_chat_id", item.external_chat_id)
    target_purpose = data.get("purpose", item.purpose)
    duplicate = (
        db.query(MessengerChannel)
        .filter(
            MessengerChannel.integration_id == item.integration_id,
            MessengerChannel.external_chat_id == target_chat_id,
            MessengerChannel.purpose == target_purpose,
            MessengerChannel.id != item.id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This channel is already configured for that purpose")

    for field, value in data.items():
        setattr(item, field, value)
    if "external_chat_id" in data or "purpose" in data:
        item.status = "configured"
        item.last_error = None
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_channel_updated",
        channel_id=item.id,
        integration_id=item.integration_id,
        purpose=item.purpose,
    )
    return _channel_public(item)


@router.delete("/messenger-channels/{channel_id}")
async def delete_messenger_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerChannel, channel_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger channel not found")
    integration_id = item.integration_id
    external_chat_id = item.external_chat_id
    purpose = item.purpose
    db.delete(item)
    db.commit()
    logger.info(
        "messenger_channel_deleted",
        channel_id=channel_id,
        integration_id=integration_id,
        purpose=purpose,
        external_chat_id=external_chat_id,
    )
    return {"deleted": True, "id": channel_id}


@router.post("/messenger-channels/{channel_id}/verify")
async def verify_messenger_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerChannel, channel_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger channel not found")
    integration = db.get(MessengerIntegration, item.integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if integration.provider != "max":
        raise HTTPException(status_code=501, detail="Channel verification is currently implemented for MAX")
    credentials = _load_credentials(integration)
    token = credentials.get("access_token")
    if not token:
        raise HTTPException(status_code=422, detail="MAX access token is not configured")

    try:
        chat = await max_get_chat(token, chat_id=item.external_chat_id)
        membership = await get_bot_chat_membership(token, chat_id=item.external_chat_id)
    except MaxAPIError as exc:
        item.status = "error"
        item.last_error = str(exc)
        item.last_health_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    permissions = membership.get("permissions")
    if not isinstance(permissions, list):
        permissions = []
    is_admin = bool(membership.get("is_admin"))
    can_read_all = "read_all_messages" in permissions
    purpose_ready = (
        is_admin and can_read_all
        if item.purpose == "monitor"
        else bool(membership)
    )

    item.name = str(chat.get("title") or item.name or "") or None
    item.channel_type = str(chat.get("type") or "") or None
    item.provider_data = {
        "is_admin": is_admin,
        "read_all_messages": can_read_all,
        "permissions": permissions,
        "link": chat.get("link"),
        "is_public": chat.get("is_public"),
    }
    item.status = "verified" if purpose_ready else "limited"
    item.last_health_at = datetime.utcnow()
    item.last_error = None if purpose_ready else "Bot permissions are insufficient for channel purpose"
    db.commit()
    db.refresh(item)
    logger.info(
        "messenger_channel_verified",
        channel_id=item.id,
        integration_id=item.integration_id,
        purpose=item.purpose,
        status=item.status,
        is_admin=is_admin,
        read_all_messages=can_read_all,
    )
    return _channel_public(item)


@router.post("/messenger-channels/{channel_id}/test")
async def test_messenger_channel(
    channel_id: int,
    payload: MessengerChannelTestMessage,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = db.get(MessengerChannel, channel_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger channel not found")
    integration = db.get(MessengerIntegration, item.integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if integration.provider != "max":
        raise HTTPException(status_code=501, detail="Channel test is currently implemented for MAX")
    if not item.is_active:
        raise HTTPException(status_code=409, detail="Messenger channel is disabled")

    credentials = _load_credentials(integration)
    token = credentials.get("access_token")
    if not token:
        raise HTTPException(status_code=422, detail="MAX access token is not configured")
    try:
        result = await max_send_message(
            token,
            chat_id=item.external_chat_id,
            text=payload.text.strip(),
        )
    except MaxAPIError as exc:
        item.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    item.last_health_at = datetime.utcnow()
    item.last_error = None
    db.commit()
    logger.info(
        "messenger_channel_test_succeeded",
        channel_id=item.id,
        integration_id=item.integration_id,
        purpose=item.purpose,
    )
    return {"ok": True, "channel": _channel_public(item), "provider_response": bool(result)}


@router.get("/conversations")
async def list_conversations(
    status: Optional[str] = None,
    requires_attention: Optional[bool] = None,
    integration_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(MessengerConversation)
    if status:
        query = query.filter(MessengerConversation.status == status)
    if requires_attention is not None:
        query = query.filter(MessengerConversation.requires_attention.is_(requires_attention))
    if integration_id:
        query = query.filter(MessengerConversation.integration_id == integration_id)

    items = query.order_by(MessengerConversation.last_message_at.desc().nullslast()).limit(300).all()
    integration_ids = {item.integration_id for item in items}
    integrations = {
        integration.id: integration.provider
        for integration in db.query(MessengerIntegration).filter(MessengerIntegration.id.in_(integration_ids)).all()
    } if integration_ids else {}
    return [_conversation_public(item, integrations.get(item.integration_id)) for item in items]


@router.get("/conversations/{conversation_id}/messages")
async def list_conversation_messages(
    conversation_id: int,
    limit: int = 200,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    items = (
        db.query(MessengerMessage)
        .filter(MessengerMessage.conversation_id == conversation_id)
        .order_by(MessengerMessage.created_at.asc())
        .limit(min(max(limit, 1), 500))
        .all()
    )
    return [
        {
            "id": item.id,
            "direction": item.direction,
            "message_type": item.message_type,
            "text": item.text,
            "attachments": item.attachments or [],
            "status": item.status,
            "external_message_id": item.external_message_id,
            "created_at": item.created_at,
            "delivered_at": item.delivered_at,
        }
        for item in items
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_conversation_message(
    conversation_id: int,
    payload: OutboundMessageCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    integration = db.get(MessengerIntegration, conversation.integration_id)
    if not integration or not integration.is_active:
        raise HTTPException(status_code=409, detail="Messenger integration is inactive")

    external_message_id = None
    if integration.provider == "telegram":
        import httpx

        credentials = _load_credentials(integration)
        token = credentials.get("bot_token")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.telegram_api_base_url.rstrip('/')}/bot{token}/sendMessage",
                    json={"chat_id": conversation.external_chat_id, "text": payload.text},
                )
            data = response.json()
            if response.status_code != 200 or not data.get("ok"):
                raise HTTPException(status_code=502, detail="Telegram message delivery failed")
            external_message_id = str((data.get("result") or {}).get("message_id") or "") or None
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Telegram delivery error: {type(exc).__name__}")
    elif integration.provider == "max":
        credentials = _load_credentials(integration)
        token = credentials.get("access_token")
        try:
            data = await max_send_message(
                token,
                chat_id=conversation.external_chat_id,
                text=payload.text,
            )
            max_message = data.get("message") if isinstance(data, dict) else None
            max_body = max_message.get("body") if isinstance(max_message, dict) and isinstance(max_message.get("body"), dict) else {}
            external_message_id = str(max_body.get("mid") or "") or None
        except MaxAPIError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        raise HTTPException(
            status_code=501,
            detail=f"Outbound adapter for {integration.provider} is not implemented yet",
        )

    message = MessengerMessage(
        conversation_id=conversation.id,
        external_message_id=external_message_id,
        direction="outbound",
        message_type="text",
        text=payload.text,
        attachments=[],
        status="delivered",
        delivered_at=datetime.utcnow(),
    )
    conversation.last_message_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"id": message.id, "status": message.status, "external_message_id": external_message_id}


@router.post("/conversations/{conversation_id}/request")
async def create_request_from_conversation(
    conversation_id: int,
    payload: ConversationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    integration = db.get(MessengerIntegration, conversation.integration_id)

    last_messages = (
        db.query(MessengerMessage)
        .filter(
            MessengerMessage.conversation_id == conversation_id,
            MessengerMessage.direction == "inbound",
        )
        .order_by(MessengerMessage.created_at.desc())
        .limit(5)
        .all()
    )
    context_text = "\n".join(reversed([item.text or "" for item in last_messages])).strip()
    description = payload.description or context_text or "Обращение из мессенджера"
    title = payload.title or (description[:120] if description else "Обращение жителя")

    from uuid import uuid4
    number = f"REQ-{datetime.utcnow():%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"
    request_item = ServiceRequest(
        number=number,
        resident_id=conversation.resident_id,
        building_id=payload.building_id,
        premise_id=payload.premise_id,
        source_channel=integration.provider if integration else "messenger",
        source_conversation_id=str(conversation.id),
        category=payload.category,
        priority=payload.priority,
        status="new",
        title=title,
        description=description,
        created_by=current_user.id,
        sla_deadline=payload.sla_deadline,
    )
    db.add(request_item)
    db.flush()
    db.add(
        RequestEvent(
            request_id=request_item.id,
            actor_user_id=current_user.id,
            event_type="created_from_conversation",
            payload={"conversation_id": conversation.id, "provider": integration.provider if integration else None},
        )
    )
    conversation.requires_attention = False
    db.commit()
    db.refresh(request_item)
    try:
        dispatch_event(
            db,
            entity_type="request",
            event_type="request_created",
            entity_id=request_item.id,
            event_data={
                "source_channel": request_item.source_channel,
                "category": request_item.category,
                "priority": request_item.priority,
            },
        )
        db.refresh(request_item)
    except Exception as exc:
        logger.error(
            "conversation_request_automation_failed",
            request_id=request_item.id,
            error_type=type(exc).__name__,
        )
    return {"id": request_item.id, "number": request_item.number, "status": request_item.status}


@router.get("/operator-alerts")
async def list_operator_alerts(
    status: Optional[str] = "new",
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = db.query(OperatorAlert)
    if status:
        query = query.filter(OperatorAlert.status == status)
    items = query.order_by(OperatorAlert.created_at.desc()).limit(min(max(limit, 1), 500)).all()

    result = []
    for alert in items:
        conversation = db.get(MessengerConversation, alert.conversation_id) if alert.conversation_id else None
        integration = db.get(MessengerIntegration, conversation.integration_id) if conversation else None
        request_item = db.get(ServiceRequest, alert.request_id) if alert.request_id else None
        result.append({
            "id": alert.id,
            "conversation_id": alert.conversation_id,
            "request_id": alert.request_id,
            "request_number": request_item.number if request_item else None,
            "provider": integration.provider if integration else None,
            "external_chat_id": conversation.external_chat_id if conversation else None,
            "kind": alert.kind,
            "severity": alert.severity,
            "title": alert.title,
            "summary": alert.summary,
            "status": alert.status,
            "payload": alert.payload or {},
            "created_at": alert.created_at,
        })
    return result


@router.post("/operator-alerts/{alert_id}/read")
async def mark_operator_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    alert = db.get(OperatorAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Operator alert not found")

    alert.status = "read"
    db.commit()

    if alert.conversation_id:
        remaining = (
            db.query(OperatorAlert)
            .filter(
                OperatorAlert.conversation_id == alert.conversation_id,
                OperatorAlert.status == "new",
            )
            .first()
        )
        if not remaining:
            conversation = db.get(MessengerConversation, alert.conversation_id)
            if conversation:
                conversation.requires_attention = False
                db.commit()

    return {"id": alert.id, "status": alert.status}


@router.post("/webhooks/messengers/{provider}/{integration_id}")
async def inbound_webhook(
    provider: str,
    integration_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item or item.provider != provider:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.is_active:
        raise HTTPException(status_code=409, detail="Messenger integration is inactive")

    credentials = _load_credentials(item)
    webhook_secret = str(credentials.get("webhook_secret") or "")
    if webhook_secret:
        if provider == "telegram":
            supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        elif provider == "max":
            supplied_secret = request.headers.get("X-Max-Bot-Api-Secret")
        else:
            supplied_secret = request.headers.get("X-Webhook-Secret")
        if not supplied_secret or not secrets.compare_digest(str(supplied_secret), webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Webhook payload must be an object")

    normalized = _normalize_inbound(provider, payload)
    event_type = str(normalized.get("event_type") or "message_created")
    external_chat_id = str(normalized.get("external_chat_id") or "")
    external_message_id = str(normalized.get("external_message_id") or "")

    if provider == "max" and external_message_id:
        # MAX uses the same message id for create/edit updates, so include
        # update_type to keep edited messages from being discarded as duplicates.
        external_event_id = f"{event_type}:{external_message_id}"
    else:
        external_event_id = str(
            payload.get("update_id")
            or payload.get("event_id")
            or payload.get("id")
            or external_message_id
            or (
                f"{event_type}:{normalized.get('timestamp')}:{external_chat_id}"
                if normalized.get("timestamp") or external_chat_id
                else ""
            )
        ) or None

    if external_event_id:
        existing = (
            db.query(MessengerInboundEvent)
            .filter(
                MessengerInboundEvent.integration_id == item.id,
                MessengerInboundEvent.external_event_id == external_event_id,
            )
            .first()
        )
        if existing:
            return {
                "ok": True,
                "event_id": existing.id,
                "status": existing.status,
                "duplicate": True,
            }

    # MAX lifecycle events are persisted but are not fake chat messages.
    if provider == "max" and event_type not in {"message_created", "message_edited"}:
        if external_chat_id and event_type == "bot_added":
            channel = (
                db.query(MessengerChannel)
                .filter(
                    MessengerChannel.integration_id == item.id,
                    MessengerChannel.external_chat_id == external_chat_id,
                    MessengerChannel.purpose == "monitor",
                )
                .first()
            )
            if channel is None:
                channel = MessengerChannel(
                    integration_id=item.id,
                    external_chat_id=external_chat_id,
                    purpose="monitor",
                    status="discovered",
                    is_active=True,
                )
                db.add(channel)
                db.flush()
            else:
                channel.is_active = True
                channel.status = "discovered"
                channel.last_error = None

            background_tasks.add_task(
                check_max_chat_permissions_background,
                item.id,
                external_chat_id,
            )

        if external_chat_id and event_type == "bot_removed":
            (
                db.query(MessengerChannel)
                .filter(
                    MessengerChannel.integration_id == item.id,
                    MessengerChannel.external_chat_id == external_chat_id,
                )
                .update(
                    {"is_active": False, "status": "removed"},
                    synchronize_session=False,
                )
            )

        event = MessengerInboundEvent(
            integration_id=item.id,
            provider=provider,
            external_event_id=external_event_id,
            payload=payload,
            status="processed",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(
            "messenger_lifecycle_event_processed",
            integration_id=item.id,
            provider=provider,
            update_type=event_type,
            external_chat_id=external_chat_id or None,
            event_id=event.id,
        )
        return {
            "ok": True,
            "event_id": event.id,
            "status": event.status,
            "update_type": event_type,
        }

    if not external_chat_id:
        raise HTTPException(status_code=422, detail="Could not determine external_chat_id")

    integration_settings = _clean_settings(item.settings)
    normalized_source_mode = str(normalized.get("source_mode") or "private_intake")
    monitored_channel = (
        db.query(MessengerChannel)
        .filter(
            MessengerChannel.integration_id == item.id,
            MessengerChannel.external_chat_id == external_chat_id,
            MessengerChannel.purpose == "monitor",
            MessengerChannel.is_active.is_(True),
        )
        .first()
    )
    if normalized_source_mode == "group_monitor":
        source_mode = "group_monitor" if monitored_channel is not None else "unmanaged_group"
    else:
        source_mode = "private_intake"

    conversation = (
        db.query(MessengerConversation)
        .filter(
            MessengerConversation.integration_id == item.id,
            MessengerConversation.external_chat_id == external_chat_id,
        )
        .first()
    )
    if not conversation:
        conversation = MessengerConversation(
            integration_id=item.id,
            external_chat_id=external_chat_id,
            status="open",
            requires_attention=False,
            last_message_at=datetime.utcnow(),
        )
        db.add(conversation)
        db.flush()

    message = MessengerMessage(
        conversation_id=conversation.id,
        external_message_id=external_message_id or None,
        direction="inbound",
        message_type=normalized.get("message_type") or "text",
        text=normalized.get("text") or "",
        attachments=normalized.get("attachments") or [],
        status="received",
    )
    conversation.last_message_at = datetime.utcnow()

    event = MessengerInboundEvent(
        integration_id=item.id,
        provider=provider,
        external_event_id=external_event_id,
        payload=payload,
        status="processed",
    )
    db.add(message)
    db.add(event)
    db.commit()
    db.refresh(event)
    db.refresh(message)

    logger.info(
        "messenger_inbound_processed",
        integration_id=item.id,
        provider=provider,
        event_id=event.id,
        update_type=event_type,
        external_event_id=external_event_id,
        conversation_id=conversation.id,
        message_id=message.id,
        source_mode=source_mode,
    )

    try:
        dispatch_event(
            db,
            entity_type="conversation",
            event_type="message_received",
            entity_id=conversation.id,
            event_data={
                "provider": provider,
                "message_type": message.message_type,
                "source_mode": source_mode,
                "source_message_id": message.id,
            },
        )
        db.refresh(conversation)
    except AutomationValidationError:
        pass
    except Exception as exc:
        logger.error(
            "messenger_automation_failed",
            integration_id=item.id,
            conversation_id=conversation.id,
            event_type="message_received",
            error_type=type(exc).__name__,
        )

    if (
        integration_settings.get("ai_monitoring_enabled", True)
        and source_mode in {"private_intake", "group_monitor"}
    ):
        background_tasks.add_task(
            process_message_background,
            message.id,
            source_mode,
        )

    return {
        "ok": True,
        "event_id": event.id,
        "status": event.status,
        "conversation_id": conversation.id,
        "message_id": message.id,
        "source_mode": source_mode,
    }
