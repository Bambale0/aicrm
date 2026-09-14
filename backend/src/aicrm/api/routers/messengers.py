"""Provider-agnostic messenger connection API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.dependencies import get_current_active_user, get_db
from ...models.housing import RequestEvent, ServiceRequest
from ...models.messenger import (
    MessengerConversation,
    MessengerInboundEvent,
    MessengerIntegration,
    MessengerMessage,
)
from ...models.user import User
from ...services.automation_engine import AutomationValidationError, dispatch_event
from ...utils.crypto import decrypt_data, encrypt_data
from ...utils.logging import get_logger

router = APIRouter(tags=["messengers"])
logger = get_logger(__name__)

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "telegram": {
        "name": "Telegram",
        "credential_fields": [{"name": "bot_token", "type": "secret", "required": True}],
        "capabilities": ["text", "photo", "video", "voice", "files", "webhook"],
        "verification": "adapter",
    },
    "max": {
        "name": "MAX",
        "credential_fields": [{"name": "access_token", "type": "secret", "required": True}],
        "capabilities": ["text", "media", "webhook"],
        "verification": "adapter_required",
    },
    "vk": {
        "name": "VK",
        "credential_fields": [
            {"name": "access_token", "type": "secret", "required": True},
            {"name": "group_id", "type": "text", "required": True},
        ],
        "capabilities": ["text", "media", "webhook"],
        "verification": "adapter_required",
    },
    "custom": {
        "name": "Custom Webhook",
        "credential_fields": [{"name": "signing_secret", "type": "secret", "required": False}],
        "capabilities": ["text", "media", "webhook"],
        "verification": "local",
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
    public_base_url: str
    secret_token: Optional[str] = None


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
            "external_chat_id": str(chat.get("id") or ""),
            "external_user_id": str(sender.get("id") or ""),
            "external_message_id": str(message.get("message_id") or ""),
            "message_type": message_type,
            "text": text,
            "attachments": attachments,
            "timestamp": message.get("date"),
        }

    return {
        "external_chat_id": str(payload.get("external_chat_id") or payload.get("chat_id") or ""),
        "external_user_id": str(payload.get("external_user_id") or payload.get("user_id") or ""),
        "external_message_id": str(payload.get("external_message_id") or payload.get("message_id") or payload.get("id") or ""),
        "message_type": str(payload.get("message_type") or "text"),
        "text": str(payload.get("text") or payload.get("message") or ""),
        "attachments": payload.get("attachments") or [],
        "timestamp": payload.get("timestamp"),
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


def _public(item: MessengerIntegration) -> Dict[str, Any]:
    return {
        "id": item.id,
        "provider": item.provider,
        "name": item.name,
        "status": item.status,
        "settings": item.settings or {},
        "webhook_url": item.webhook_url,
        "external_account_id": item.external_account_id,
        "last_health_at": item.last_health_at,
        "last_error": item.last_error,
        "is_active": item.is_active,
        "has_credentials": bool(item.credentials_encrypted),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/messengers/providers")
async def list_providers(_: User = Depends(get_current_active_user)):
    return [{"provider": key, **value} for key, value in PROVIDERS.items()]


@router.get("/messengers")
async def list_integrations(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    items = db.query(MessengerIntegration).order_by(MessengerIntegration.created_at.desc()).all()
    return [_public(item) for item in items]


@router.post("/messengers")
async def create_integration(
    payload: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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

    encrypted = encrypt_data(__import__("json").dumps(payload.credentials, ensure_ascii=False))
    item = MessengerIntegration(
        provider=payload.provider,
        name=payload.name,
        credentials_encrypted=encrypted,
        settings=payload.settings,
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
    _: User = Depends(get_current_active_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    data = payload.model_dump(exclude_unset=True)
    credentials = data.pop("credentials", None)
    if credentials is not None:
        item.credentials_encrypted = encrypt_data(__import__("json").dumps(credentials, ensure_ascii=False))
        item.status = "configured"
        item.last_error = None
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _public(item)


@router.post("/messengers/{integration_id}/verify")
async def verify_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.credentials_encrypted:
        raise HTTPException(status_code=422, detail="Credentials are not configured")

    credentials = __import__("json").loads(decrypt_data(item.credentials_encrypted))

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

    if item.provider == "custom":
        item.status = "verified"
        item.last_health_at = datetime.utcnow()
        item.last_error = None
        db.commit()
        return {"verified": True, "provider": item.provider, "detail": "Local custom webhook connector is ready"}

    raise HTTPException(
        status_code=501,
        detail=f"Verification adapter for {item.provider} is not implemented yet",
    )


@router.post("/messengers/{integration_id}/webhook/register")
async def register_webhook(
    integration_id: int,
    payload: WebhookRegisterRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.credentials_encrypted:
        raise HTTPException(status_code=422, detail="Credentials are not configured")

    base_url = payload.public_base_url.rstrip("/")
    webhook_url = f"{base_url}/api/webhooks/messengers/{item.provider}/{item.id}"
    credentials = __import__("json").loads(decrypt_data(item.credentials_encrypted))
    settings = dict(item.settings or {})

    if item.provider == "telegram":
        import httpx

        token = credentials.get("bot_token")
        body: Dict[str, Any] = {"url": webhook_url}
        if payload.secret_token:
            body["secret_token"] = payload.secret_token
            settings["webhook_secret"] = payload.secret_token

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

    elif item.provider == "custom":
        if payload.secret_token:
            settings["webhook_secret"] = payload.secret_token
    else:
        raise HTTPException(
            status_code=501,
            detail=f"Webhook registration adapter for {item.provider} is not implemented yet",
        )

    item.webhook_url = webhook_url
    item.settings = settings
    item.status = "verified"
    item.last_error = None
    item.last_health_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return {"registered": True, "provider": item.provider, "webhook_url": webhook_url}


@router.post("/messengers/{integration_id}/activate")
async def activate_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
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
    _: User = Depends(get_current_active_user),
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
    _: User = Depends(get_current_active_user),
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

        credentials = __import__("json").loads(decrypt_data(integration.credentials_encrypted))
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
    return {"id": request_item.id, "number": request_item.number, "status": request_item.status}


@router.post("/webhooks/messengers/{provider}/{integration_id}")
async def inbound_webhook(
    provider: str,
    integration_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    item = db.get(MessengerIntegration, integration_id)
    if not item or item.provider != provider:
        raise HTTPException(status_code=404, detail="Messenger integration not found")
    if not item.is_active:
        raise HTTPException(status_code=409, detail="Messenger integration is inactive")

    webhook_secret = (item.settings or {}).get("webhook_secret")
    if webhook_secret:
        if provider == "telegram":
            supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        else:
            supplied_secret = request.headers.get("X-Webhook-Secret")
        if supplied_secret != webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    external_event_id = None
    if isinstance(payload, dict):
        external_event_id = str(
            payload.get("update_id")
            or payload.get("event_id")
            or payload.get("id")
            or ""
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
            return {"ok": True, "event_id": existing.id, "status": existing.status, "duplicate": True}

    normalized = _normalize_inbound(provider, payload if isinstance(payload, dict) else {})
    external_chat_id = normalized.get("external_chat_id")
    if not external_chat_id:
        raise HTTPException(status_code=422, detail="Could not determine external_chat_id")

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
            requires_attention=True,
            last_message_at=datetime.utcnow(),
        )
        db.add(conversation)
        db.flush()

    message = MessengerMessage(
        conversation_id=conversation.id,
        external_message_id=normalized.get("external_message_id") or None,
        direction="inbound",
        message_type=normalized.get("message_type") or "text",
        text=normalized.get("text") or "",
        attachments=normalized.get("attachments") or [],
        status="received",
    )
    conversation.last_message_at = datetime.utcnow()
    conversation.requires_attention = True

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
        external_event_id=external_event_id,
        conversation_id=conversation.id,
        message_id=message.id,
    )
    try:
        dispatch_event(
            db,
            entity_type="conversation",
            event_type="message_received",
            entity_id=conversation.id,
            event_data={
                "provider": provider,
                "requires_attention": conversation.requires_attention,
                "message_type": message.message_type,
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
    return {
        "ok": True,
        "event_id": event.id,
        "status": event.status,
        "conversation_id": conversation.id,
        "message_id": message.id,
    }
