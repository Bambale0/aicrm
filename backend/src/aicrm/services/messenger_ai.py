"""AI triage for messenger conversations.

Incoming messages are first normalized by the messenger adapter. This service
looks at recent context and emits a business event. Request creation and
operator notification remain automation actions, mirroring Bitrix-style
triggers and robots.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.messenger import (
    MessengerChannel,
    MessengerConversation,
    MessengerIntegration,
    MessengerMessage,
    OperatorAlert,
)
from ..services.ai_connection import AIConnectionError, complete_chat_json
from ..services.automation_engine import AutomationValidationError, dispatch_event
from ..services.max_connector import MaxAPIError, send_message as max_send_message
from ..utils.crypto import decrypt_data
from ..utils.logging import get_logger

logger = get_logger(__name__)

_ALLOWED_PRIORITIES = {"emergency", "urgent", "high", "normal", "planned"}
_ALLOWED_CATEGORIES = {"electrical", "plumbing", "complaint", "wish", "general"}


def _context_messages(db: Session, conversation_id: int, limit: int) -> list[MessengerMessage]:
    items = (
        db.query(MessengerMessage)
        .filter(
            MessengerMessage.conversation_id == conversation_id,
            MessengerMessage.direction == "inbound",
        )
        .order_by(MessengerMessage.created_at.desc())
        .limit(max(1, min(limit, 50)))
        .all()
    )
    return list(reversed(items))


def _has_open_alert(db: Session, conversation_id: int) -> bool:
    return (
        db.query(OperatorAlert)
        .filter(
            OperatorAlert.conversation_id == conversation_id,
            OperatorAlert.status == "new",
        )
        .first()
        is not None
    )


def _build_prompt(
    *,
    source_mode: str,
    messages: list[MessengerMessage],
) -> str:
    lines = []
    for index, message in enumerate(messages, start=1):
        text = (message.text or "").strip()
        if not text:
            text = "[" + (message.message_type or "message") + "]"
        lines.append(f"{index}. {text}")

    mode_explanation = (
        "Это общий чат жителей дома. Большинство сообщений может быть обычным разговором. "
        "Нужно отделить бытовой трёп от реальной проблемы ЖКХ."
        if source_mode == "group_monitor"
        else
        "Это личный диалог жителя с ботом управляющей компании. "
        "Сообщение может быть заявкой, уточнением к заявке или обычным вопросом."
    )

    return f"""
Режим: {source_mode}.
{mode_explanation}

Последние сообщения, от старых к новым:
{chr(10).join(lines)}

Верни ТОЛЬКО JSON без markdown:
{{
  "classification": "chatter|problem|request|question|unclear",
  "confidence": 0.0,
  "should_create_request": true,
  "alert_operator": true,
  "title": "краткий заголовок до 100 символов",
  "summary": "короткая сводка для диспетчера: что произошло и что требуется",
  "category": "electrical|plumbing|complaint|wish|general",
  "priority": "emergency|urgent|high|normal|planned",
  "missing_info": ["что ещё полезно уточнить"],
  "resident_reply": "короткий ответ жителю, если это личный диалог",
  "issue_key": "короткий стабильный ключ проблемы, например lift-entrance-2"
}}

Правила:
- chatter: разговор жильцов, эмоции, шутки, бытовое обсуждение без задачи для УК.
- problem: в общем чате описано реальное событие/неисправность/авария/нарушение, требующее внимания УК.
- request: житель явно просит выполнить работу или зарегистрировать обращение.
- question: вопрос без необходимости создавать заявку.
- Если есть риск безопасности, вода, электричество, газ, пожар, лифт, затопление или другая возможная авария — лучше поднять alert, чем пропустить.
- Не выдумывай адрес, квартиру, людей и факты, которых нет в сообщениях.
- should_create_request=true только если есть реальная задача для УК.
- В личном диалоге явное обращение о проблеме почти всегда request.
- summary должен быть понятен оператору без чтения всего чата.
""".strip()


def _normalize_result(raw: Dict[str, Any], source_mode: str) -> Dict[str, Any]:
    classification = str(raw.get("classification") or "unclear").strip().lower()
    if classification not in {"chatter", "problem", "request", "question", "unclear"}:
        classification = "unclear"

    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))

    category = str(raw.get("category") or "general").strip().lower()
    if category not in _ALLOWED_CATEGORIES:
        category = "general"

    priority = str(raw.get("priority") or "normal").strip().lower()
    if priority not in _ALLOWED_PRIORITIES:
        priority = "normal"

    title = str(raw.get("title") or "Обращение из мессенджера").strip()[:500]
    summary = str(raw.get("summary") or title).strip()
    missing_info = raw.get("missing_info")
    if not isinstance(missing_info, list):
        missing_info = []

    should_create = bool(raw.get("should_create_request"))
    alert_operator = bool(raw.get("alert_operator"))

    if confidence < settings.messenger_ai_confidence_threshold:
        # Uncertain safety-related messages should be shown to the operator,
        # but low-confidence chatter must not create tickets automatically.
        if priority in {"emergency", "urgent"}:
            alert_operator = True
        elif classification in {"chatter", "question", "unclear"}:
            should_create = False

    if source_mode == "group_monitor" and classification == "chatter":
        should_create = False
        alert_operator = False

    return {
        "classification": classification,
        "confidence": confidence,
        "should_create_request": should_create,
        "alert_operator": alert_operator,
        "title": title,
        "summary": summary,
        "category": category,
        "priority": priority,
        "missing_info": [str(item)[:200] for item in missing_info[:10]],
        "resident_reply": str(raw.get("resident_reply") or "").strip()[:1000],
        "issue_key": str(raw.get("issue_key") or "").strip().lower()[:120],
        "source_mode": source_mode,
    }


def _action_result(
    automation_result: Dict[str, Any] | None,
    action_type: str,
) -> Dict[str, Any] | None:
    if not automation_result:
        return None
    for item in automation_result.get("action_results") or []:
        if item.get("action_type") == action_type and item.get("status") == "completed":
            result = item.get("result")
            return result if isinstance(result, dict) else {}
    return None


async def _notify_via_max(
    integration: MessengerIntegration,
    *,
    chat_id: str,
    text: str,
) -> None:
    credentials = json.loads(decrypt_data(integration.credentials_encrypted))
    token = credentials.get("access_token")
    if not token:
        return
    await max_send_message(
        token,
        chat_id=chat_id,
        text=text,
    )


async def analyze_message(
    db: Session,
    *,
    message_id: int,
    source_mode: str,
) -> Dict[str, Any]:
    message = db.get(MessengerMessage, message_id)
    if not message:
        raise ValueError("Message not found")
    conversation = db.get(MessengerConversation, message.conversation_id)
    if not conversation:
        raise ValueError("Conversation not found")
    integration = db.get(MessengerIntegration, conversation.integration_id)
    if not integration:
        raise ValueError("Integration not found")

    integration_settings = dict(integration.settings or {})
    if integration_settings.get("ai_monitoring_enabled", True) is False:
        return {"skipped": True, "reason": "ai_monitoring_disabled"}

    context_limit = int(
        integration_settings.get(
            "ai_context_messages",
            settings.messenger_ai_context_messages,
        )
    )
    messages = _context_messages(db, conversation.id, context_limit)
    if not messages:
        return {"skipped": True, "reason": "empty_context"}

    raw = await complete_chat_json(
        db,
        system_prompt=(
            "Ты ИИ-диспетчер управляющей компании ЖКХ. "
            "Твоя задача — консервативно отделять обычный разговор жителей "
            "от реальных проблем и заявок. Не выдумывай данные."
        ),
        user_prompt=_build_prompt(
            source_mode=source_mode,
            messages=messages,
        ),
        max_tokens=700,
        temperature=0.1,
    )
    result = _normalize_result(raw, source_mode)

    conversation.summary = result["summary"]
    if result["alert_operator"] or result["should_create_request"]:
        conversation.requires_attention = True
    elif not _has_open_alert(db, conversation.id):
        conversation.requires_attention = False

    message.status = "triaged"
    db.commit()
    db.refresh(conversation)

    event_type = None
    if result["should_create_request"]:
        event_type = (
            "resident_request_detected"
            if source_mode == "private_intake"
            else "conversation_problem_detected"
        )
    elif result["alert_operator"]:
        event_type = "conversation_problem_detected"

    automation_result: Dict[str, Any] | None = None
    if event_type:
        try:
            automation_result = dispatch_event(
                db,
                entity_type="conversation",
                event_type=event_type,
                entity_id=conversation.id,
                event_data={
                    **result,
                    "source_message_id": message.id,
                    "provider": integration.provider,
                    "external_chat_id": conversation.external_chat_id,
                },
            )
        except AutomationValidationError as exc:
            logger.warning(
                "messenger_ai_automation_validation_failed",
                conversation_id=conversation.id,
                message_id=message.id,
                error=str(exc),
            )

    request_result = _action_result(
        automation_result,
        "create_request_from_conversation",
    )
    alert_result = _action_result(
        automation_result,
        "notify_operator",
    )

    if integration.provider == "max":
        operator_channel = (
            db.query(MessengerChannel)
            .filter(
                MessengerChannel.integration_id == integration.id,
                MessengerChannel.purpose == "operator_alert",
                MessengerChannel.is_active.is_(True),
            )
            .order_by(MessengerChannel.id.asc())
            .first()
        )
        operator_chat_id = (
            str(operator_channel.external_chat_id).strip()
            if operator_channel is not None
            else ""
        )
        if operator_chat_id and alert_result and not alert_result.get("deduplicated"):
            request_number = request_result.get("request_number") if request_result else None
            alert_text = (
                "🚨 " + result["title"] + "\n\n"
                + result["summary"]
                + ("\n\nЗаявка: " + str(request_number) if request_number else "")
                + "\nПриоритет: " + result["priority"]
                + "\nУверенность ИИ: " + str(round(result["confidence"] * 100)) + "%"
            )
            try:
                await _notify_via_max(
                    integration,
                    chat_id=operator_chat_id,
                    text=alert_text,
                )
            except MaxAPIError as exc:
                logger.warning(
                    "messenger_operator_max_alert_failed",
                    integration_id=integration.id,
                    conversation_id=conversation.id,
                    error=str(exc),
                )

        if (
            source_mode == "private_intake"
            and request_result
            and integration_settings.get("send_private_ack", True)
            and not request_result.get("deduplicated")
        ):
            acknowledgement = (
                result["resident_reply"]
                or (
                    "Заявка принята. Номер: "
                    + str(request_result.get("request_number") or "")
                    + ". Диспетчер получил уведомление."
                )
            )
            try:
                await _notify_via_max(
                    integration,
                    chat_id=conversation.external_chat_id,
                    text=acknowledgement,
                )
            except MaxAPIError as exc:
                logger.warning(
                    "messenger_private_ack_failed",
                    integration_id=integration.id,
                    conversation_id=conversation.id,
                    error=str(exc),
                )

    logger.info(
        "messenger_ai_triage_completed",
        integration_id=integration.id,
        conversation_id=conversation.id,
        message_id=message.id,
        source_mode=source_mode,
        classification=result["classification"],
        confidence=result["confidence"],
        create_request=result["should_create_request"],
        alert_operator=result["alert_operator"],
        event_type=event_type,
    )

    return {
        **result,
        "event_type": event_type,
        "automation": automation_result,
    }


async def process_message_background(
    message_id: int,
    source_mode: str,
) -> None:
    db = SessionLocal()
    try:
        await analyze_message(
            db,
            message_id=message_id,
            source_mode=source_mode,
        )
    except AIConnectionError as exc:
        message = db.get(MessengerMessage, message_id)
        if message:
            message.status = "ai_unavailable"
            db.commit()
        logger.warning(
            "messenger_ai_unavailable",
            message_id=message_id,
            error=str(exc),
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "messenger_ai_triage_failed",
            message_id=message_id,
            error_type=type(exc).__name__,
        )
    finally:
        db.close()
