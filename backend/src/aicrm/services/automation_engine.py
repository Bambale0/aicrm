"""Universal rule engine for CRM entities and custom workflows."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from ..core.automation_catalog import CONDITION_OPERATORS, AUTOMATION_ACTIONS, AUTOMATION_EVENTS
from ..core.config import settings
from ..models.automation import (
    AutomationExecution,
    AutomationInstance,
    AutomationProcess,
    AutomationRule,
    AutomationStage,
)
from ..models.housing import ContractorCompany, Incident, RequestEvent, ServiceRequest
from ..models.messenger import MessengerConversation, MessengerIntegration
from ..models.user import User
from ..utils.logging import get_logger

logger = get_logger(__name__)

_TEMPLATE_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


class AutomationValidationError(ValueError):
    pass


def event_spec(entity_type: str, event_type: str) -> Optional[Dict[str, Any]]:
    return next(
        (
            item
            for item in AUTOMATION_EVENTS
            if event_type == item["value"] and entity_type in item["entity_types"]
        ),
        None,
    )


def action_spec(entity_type: str, action_type: str) -> Optional[Dict[str, Any]]:
    return next(
        (
            item
            for item in AUTOMATION_ACTIONS
            if action_type == item["value"] and entity_type in item["entity_types"]
        ),
        None,
    )


def validate_action(
    db: Session,
    process: AutomationProcess,
    action: Dict[str, Any],
) -> None:
    action_type = str(action.get("type") or "")
    spec = action_spec(process.entity_type, action_type)
    if not spec:
        raise AutomationValidationError(
            f"Action {action_type or '<empty>'} is not available for {process.entity_type}"
        )

    config = action.get("config") or {}
    missing = [
        field["name"]
        for field in spec.get("config_fields", [])
        if field.get("required") and config.get(field["name"]) in (None, "")
    ]
    if missing:
        raise AutomationValidationError(
            "Missing action fields: " + ", ".join(missing)
        )

    if action_type == "move_stage":
        stage = db.get(AutomationStage, int(config["stage_id"]))
        if not stage or stage.process_id != process.id:
            raise AutomationValidationError("Selected stage belongs to another process")


def validate_rule_payload(
    db: Session,
    process: AutomationProcess,
    event_type: str,
    conditions: Iterable[Dict[str, Any]],
    actions: Iterable[Dict[str, Any]],
) -> None:
    if not event_spec(process.entity_type, event_type):
        raise AutomationValidationError(
            f"Event {event_type} is not available for {process.entity_type}"
        )

    operator_values = {item["value"] for item in CONDITION_OPERATORS}
    for condition in conditions:
        if not str(condition.get("field") or "").strip():
            raise AutomationValidationError("Condition field is required")
        operator = str(condition.get("operator") or "equals")
        if operator not in operator_values:
            raise AutomationValidationError(f"Unsupported condition operator: {operator}")

    action_items = list(actions)
    if not action_items:
        raise AutomationValidationError("At least one action is required")
    for action in action_items:
        validate_action(db, process, action)


def _resolve_value(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {} or value == ()


def _condition_matches(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    field = str(condition.get("field") or "")
    operator = str(condition.get("operator") or "equals")
    expected = condition.get("value")
    actual = _resolve_value(context, field)

    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        return expected in actual if isinstance(actual, (str, list, tuple, set)) else False
    if operator == "not_contains":
        return expected not in actual if isinstance(actual, (str, list, tuple, set)) else True
    if operator == "starts_with":
        return isinstance(actual, str) and str(actual).startswith(str(expected))
    if operator == "ends_with":
        return isinstance(actual, str) and str(actual).endswith(str(expected))
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set)) else False
    if operator == "not_in":
        return actual not in expected if isinstance(expected, (list, tuple, set)) else True
    if operator == "is_empty":
        return _is_empty(actual)
    if operator == "not_empty":
        return not _is_empty(actual)
    if operator == "is_true":
        return actual is True
    if operator == "is_false":
        return actual is False

    if operator in {"gt", "gte", "lt", "lte"}:
        try:
            if operator == "gt":
                return actual > expected
            if operator == "gte":
                return actual >= expected
            if operator == "lt":
                return actual < expected
            return actual <= expected
        except TypeError:
            return False

    return False


def conditions_match(
    conditions: Optional[Iterable[Dict[str, Any]]],
    context: Dict[str, Any],
) -> bool:
    items = list(conditions or [])
    if not items:
        return True

    result: Optional[bool] = None
    for index, condition in enumerate(items):
        current = _condition_matches(condition, context)
        if index == 0:
            result = current
            continue

        logical = str(condition.get("logical_operator") or "AND").upper()
        if logical == "OR":
            result = bool(result) or current
        else:
            result = bool(result) and current
    return bool(result)


def _coerce_literal(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if not stripped:
        return value

    if stripped in {"true", "false", "null"}:
        return json.loads(stripped)

    if stripped[0] in "[{" or stripped.replace(".", "", 1).replace("-", "", 1).isdigit():
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            return value

    return value


def _render_value(value: Any, context: Dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    full = _TEMPLATE_RE.fullmatch(value.strip())
    if full:
        return _resolve_value(context, full.group(1))

    return _TEMPLATE_RE.sub(
        lambda match: "" if _resolve_value(context, match.group(1)) is None else str(_resolve_value(context, match.group(1))),
        value,
    )


def _request_payload(item: ServiceRequest) -> Dict[str, Any]:
    return {
        "id": item.id,
        "number": item.number,
        "status": item.status,
        "priority": item.priority,
        "category": item.category,
        "building_id": item.building_id,
        "premise_id": item.premise_id,
        "resident_id": item.resident_id,
        "assigned_user_id": item.assigned_user_id,
        "contractor_id": item.contractor_id,
        "source_channel": item.source_channel,
        "title": item.title,
        "description": item.description,
    }


def _incident_payload(item: Incident) -> Dict[str, Any]:
    return {
        "id": item.id,
        "status": item.status,
        "priority": item.priority,
        "category": item.category,
        "building_id": item.building_id,
        "title": item.title,
        "description": item.description,
    }


def _conversation_payload(
    db: Session,
    item: MessengerConversation,
) -> Dict[str, Any]:
    integration = db.get(MessengerIntegration, item.integration_id)
    return {
        "id": item.id,
        "provider": integration.provider if integration else None,
        "status": item.status,
        "requires_attention": item.requires_attention,
        "resident_id": item.resident_id,
    }


def _workflow_payload(item: AutomationInstance) -> Dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "status": item.status,
        "stage_id": item.current_stage_id,
        "external_ref": item.external_ref,
    }


def entity_context(
    db: Session,
    entity_type: str,
    entity_id: int,
    *,
    dry_run: bool = False,
) -> tuple[Dict[str, Any], Optional[AutomationInstance]]:
    if entity_type == "request":
        item = db.get(ServiceRequest, entity_id)
        if not item:
            if dry_run:
                return {"id": entity_id}, None
            raise AutomationValidationError("Request not found")
        return _request_payload(item), None

    if entity_type == "incident":
        item = db.get(Incident, entity_id)
        if not item:
            if dry_run:
                return {"id": entity_id}, None
            raise AutomationValidationError("Incident not found")
        return _incident_payload(item), None

    if entity_type == "conversation":
        item = db.get(MessengerConversation, entity_id)
        if not item:
            if dry_run:
                return {"id": entity_id}, None
            raise AutomationValidationError("Conversation not found")
        return _conversation_payload(db, item), None

    if entity_type == "workflow":
        item = db.get(AutomationInstance, entity_id)
        if not item:
            if dry_run:
                return {"id": entity_id}, None
            raise AutomationValidationError("Workflow instance not found")
        return _workflow_payload(item), item

    raise AutomationValidationError(f"Unsupported entity_type: {entity_type}")


def build_context(
    db: Session,
    entity_type: str,
    entity_id: int,
    event_data: Optional[Dict[str, Any]],
    *,
    dry_run: bool = False,
) -> tuple[Dict[str, Any], Optional[AutomationInstance]]:
    entity, instance = entity_context(
        db,
        entity_type,
        entity_id,
        dry_run=dry_run,
    )
    context = {
        "entity": entity,
        "event": event_data or {},
        "variables": dict(instance.variables or {}) if instance else {},
    }
    return context, instance


def execute_action(
    db: Session,
    process: AutomationProcess,
    action: Dict[str, Any],
    entity_id: int,
    context: Dict[str, Any],
    instance: Optional[AutomationInstance],
) -> Dict[str, Any]:
    action_type = str(action.get("type") or "")
    config = action.get("config") or {}
    validate_action(db, process, action)

    if action_type == "log_event":
        return {
            "message": _render_value(config.get("message") or "", context),
        }

    if process.entity_type == "request":
        item = db.get(ServiceRequest, entity_id)
        if not item:
            raise AutomationValidationError("Request not found")

        if action_type == "set_request_status":
            previous = item.status
            item.status = str(config["status"])
            db.add(
                RequestEvent(
                    request_id=item.id,
                    event_type="automation_status_changed",
                    payload={"from": previous, "to": item.status},
                )
            )
            context["entity"]["status"] = item.status
            result = {"from": previous, "status": item.status}
            if previous != item.status:
                result["_events"] = [{
                    "entity_type": "request",
                    "event_type": "request_status_changed",
                    "entity_id": item.id,
                    "event_data": {"old_status": previous, "status": item.status},
                }]
            return result

        if action_type == "set_request_priority":
            previous = item.priority
            item.priority = str(config["priority"])
            db.add(
                RequestEvent(
                    request_id=item.id,
                    event_type="automation_priority_changed",
                    payload={"from": previous, "to": item.priority},
                )
            )
            context["entity"]["priority"] = item.priority
            result = {"from": previous, "priority": item.priority}
            if previous != item.priority:
                result["_events"] = [{
                    "entity_type": "request",
                    "event_type": "request_priority_changed",
                    "entity_id": item.id,
                    "event_data": {"old_priority": previous, "priority": item.priority},
                }]
            return result

        if action_type == "assign_user":
            user_id = int(config["user_id"])
            if not db.get(User, user_id):
                raise AutomationValidationError("Selected employee not found")
            previous_status = item.status
            item.assigned_user_id = user_id
            if item.status == "new":
                item.status = "assigned"
            context["entity"]["assigned_user_id"] = user_id
            context["entity"]["status"] = item.status
            db.add(
                RequestEvent(
                    request_id=item.id,
                    event_type="automation_user_assigned",
                    payload={"user_id": user_id},
                )
            )
            result = {"assigned_user_id": user_id, "status": item.status}
            if previous_status != item.status:
                result["_events"] = [{
                    "entity_type": "request",
                    "event_type": "request_status_changed",
                    "entity_id": item.id,
                    "event_data": {"old_status": previous_status, "status": item.status},
                }]
            return result

        if action_type == "assign_contractor":
            contractor_id = int(config["contractor_id"])
            if not db.get(ContractorCompany, contractor_id):
                raise AutomationValidationError("Selected contractor not found")
            previous_status = item.status
            item.contractor_id = contractor_id
            if item.status == "new":
                item.status = "assigned"
            context["entity"]["contractor_id"] = contractor_id
            context["entity"]["status"] = item.status
            db.add(
                RequestEvent(
                    request_id=item.id,
                    event_type="automation_contractor_assigned",
                    payload={"contractor_id": contractor_id},
                )
            )
            result = {"contractor_id": contractor_id, "status": item.status}
            if previous_status != item.status:
                result["_events"] = [{
                    "entity_type": "request",
                    "event_type": "request_status_changed",
                    "entity_id": item.id,
                    "event_data": {"old_status": previous_status, "status": item.status},
                }]
            return result

    if process.entity_type == "conversation":
        conversation = db.get(MessengerConversation, entity_id)
        if not conversation:
            raise AutomationValidationError("Conversation not found")

        if action_type == "mark_conversation_attention":
            previous = conversation.requires_attention
            value = bool(config["requires_attention"])
            conversation.requires_attention = value
            context["entity"]["requires_attention"] = value
            result = {"from": previous, "requires_attention": value}
            if value and previous != value:
                result["_events"] = [{
                    "entity_type": "conversation",
                    "event_type": "conversation_requires_attention",
                    "entity_id": conversation.id,
                    "event_data": {},
                }]
            return result

    if process.entity_type == "workflow":
        if not instance:
            raise AutomationValidationError("Workflow instance not found")

        if action_type == "set_variable":
            key = str(config["key"]).strip()
            if not key:
                raise AutomationValidationError("Variable name is required")
            variables = dict(instance.variables or {})
            previous = variables.get(key)
            rendered = _coerce_literal(_render_value(config.get("value"), context))
            variables[key] = rendered
            instance.variables = variables
            context["variables"] = dict(variables)
            result = {"key": key, "from": previous, "value": rendered}
            if previous != rendered:
                result["_events"] = [{
                    "entity_type": "workflow",
                    "event_type": "workflow_updated",
                    "entity_id": instance.id,
                    "event_data": {"changed_fields": ["variables." + key]},
                    "process_id": process.id,
                }]
            return result

        if action_type == "move_stage":
            stage_id = int(config["stage_id"])
            stage = db.get(AutomationStage, stage_id)
            if not stage or stage.process_id != process.id:
                raise AutomationValidationError("Selected stage belongs to another process")
            previous = instance.current_stage_id
            instance.current_stage_id = stage_id
            context["entity"]["stage_id"] = stage_id
            result = {
                "from_stage_id": previous,
                "stage_id": stage_id,
                "stage_name": stage.name,
            }
            if previous != stage_id:
                result["_events"] = [{
                    "entity_type": "workflow",
                    "event_type": "workflow_stage_changed",
                    "entity_id": instance.id,
                    "event_data": {
                        "old_stage_id": previous,
                        "stage_id": stage_id,
                    },
                    "process_id": process.id,
                }]
            return result

        if action_type == "emit_event":
            event_name = str(_render_value(config["event_name"], context) or "").strip()
            if not event_name:
                raise AutomationValidationError("Event name must not be empty")
            return {
                "event_name": event_name,
                "_events": [{
                    "entity_type": "workflow",
                    "event_type": "custom_event",
                    "entity_id": instance.id,
                    "event_data": {"event_name": event_name},
                    "process_id": process.id,
                }],
            }

        if action_type == "set_workflow_status":
            previous = instance.status
            instance.status = str(config["status"])
            context["entity"]["status"] = instance.status
            result = {"from": previous, "status": instance.status}
            if previous != instance.status:
                result["_events"] = [{
                    "entity_type": "workflow",
                    "event_type": "workflow_updated",
                    "entity_id": instance.id,
                    "event_data": {"changed_fields": ["status"]},
                    "process_id": process.id,
                }]
            return result

        if action_type == "create_request":
            title = str(_render_value(config["title"], context) or "").strip()
            description = str(_render_value(config["description"], context) or "").strip()
            category = str(_render_value(config.get("category") or "general", context) or "general").strip()
            priority = str(config["priority"])
            if not title or not description:
                raise AutomationValidationError("Request title and description must not be empty")

            request_item = ServiceRequest(
                number=f"REQ-{uuid4().hex[:12].upper()}",
                source_channel="automation",
                category=category,
                priority=priority,
                status="new",
                title=title[:500],
                description=description,
                extra_data={
                    "automation_process_id": process.id,
                    "automation_instance_id": instance.id,
                },
            )
            db.add(request_item)
            db.flush()
            db.add(
                RequestEvent(
                    request_id=request_item.id,
                    event_type="created_by_automation",
                    payload={
                        "process_id": process.id,
                        "instance_id": instance.id,
                    },
                )
            )
            return {
                "request_id": request_item.id,
                "request_number": request_item.number,
                "_events": [{
                    "entity_type": "request",
                    "event_type": "request_created",
                    "entity_id": request_item.id,
                    "event_data": {},
                }],
            }

    raise AutomationValidationError(
        f"Action {action_type} is not implemented for {process.entity_type}"
    )


def _candidate_rules(
    db: Session,
    entity_type: str,
    event_type: str,
    *,
    process_id: Optional[int] = None,
    instance: Optional[AutomationInstance] = None,
) -> list[AutomationRule]:
    query = (
        db.query(AutomationRule)
        .join(AutomationProcess, AutomationRule.process_id == AutomationProcess.id)
        .filter(
            AutomationProcess.entity_type == entity_type,
            AutomationProcess.is_active.is_(True),
            AutomationRule.event_type == event_type,
            AutomationRule.is_active.is_(True),
        )
    )

    effective_process_id = process_id
    if instance:
        effective_process_id = instance.process_id
    if effective_process_id:
        query = query.filter(AutomationRule.process_id == effective_process_id)

    return query.order_by(AutomationRule.priority.asc(), AutomationRule.id.asc()).all()


def dispatch_event(
    db: Session,
    entity_type: str,
    event_type: str,
    entity_id: int,
    event_data: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    dry_run: bool = False,
    process_id: Optional[int] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    if _depth > settings.automation_max_depth:
        raise AutomationValidationError("Automation recursion limit exceeded")

    if not event_spec(entity_type, event_type):
        raise AutomationValidationError(
            f"Unsupported automation event: {entity_type}/{event_type}"
        )

    correlation = correlation_id or uuid4().hex
    started = time.perf_counter()
    context, instance = build_context(
        db,
        entity_type,
        entity_id,
        event_data,
        dry_run=dry_run,
    )

    rules = _candidate_rules(
        db,
        entity_type,
        event_type,
        process_id=process_id,
        instance=instance,
    )

    matched_rule_ids: list[int] = []
    action_results: list[Dict[str, Any]] = []
    follow_up_events: list[Dict[str, Any]] = []

    logger.info(
        "automation_event_started",
        correlation_id=correlation,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        candidate_rules=len(rules),
        dry_run=dry_run,
    )

    for rule in rules:
        if not conditions_match(rule.conditions, context):
            continue

        process = db.get(AutomationProcess, rule.process_id)
        if not process:
            continue

        matched_rule_ids.append(rule.id)

        for action_index, action in enumerate(rule.actions or []):
            execution_started = time.perf_counter()
            execution = AutomationExecution(
                process_id=rule.process_id,
                rule_id=rule.id,
                instance_id=instance.id if instance else None,
                correlation_id=correlation,
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                action_index=action_index,
                status="running",
                input_data={
                    "event": event_data or {},
                    "action": action,
                },
            )
            db.add(execution)
            db.flush()

            try:
                if dry_run:
                    validate_action(db, process, action)
                    result = {
                        "dry_run": True,
                        "valid": True,
                        "action_type": action.get("type"),
                    }
                else:
                    result = execute_action(
                        db,
                        process,
                        action,
                        entity_id,
                        context,
                        instance,
                    )

                internal_events = result.pop("_events", []) if isinstance(result, dict) else []
                if not dry_run:
                    follow_up_events.extend(internal_events)

                execution.status = "completed"
                execution.result = result
                action_results.append(
                    {
                        "rule_id": rule.id,
                        "action_index": action_index,
                        "action_type": action.get("type"),
                        "status": "completed",
                        "result": result,
                    }
                )
            except Exception as exc:
                execution.status = "failed"
                execution.error = str(exc)
                action_results.append(
                    {
                        "rule_id": rule.id,
                        "action_index": action_index,
                        "action_type": action.get("type"),
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                logger.error(
                    "automation_action_failed",
                    correlation_id=correlation,
                    rule_id=rule.id,
                    action_index=action_index,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action_type=action.get("type"),
                    error_type=type(exc).__name__,
                )
            finally:
                execution.duration_ms = int(
                    (time.perf_counter() - execution_started) * 1000
                )

        if rule.stop_after_match:
            break

    nested_results: list[Dict[str, Any]] = []
    if dry_run:
        db.rollback()
    else:
        db.commit()
        for follow_up in follow_up_events:
            try:
                nested_results.append(
                    dispatch_event(
                        db,
                        entity_type=follow_up["entity_type"],
                        event_type=follow_up["event_type"],
                        entity_id=follow_up["entity_id"],
                        event_data=follow_up.get("event_data") or {},
                        correlation_id=correlation,
                        dry_run=False,
                        process_id=follow_up.get("process_id"),
                        _depth=_depth + 1,
                    )
                )
            except Exception as exc:
                logger.error(
                    "automation_follow_up_failed",
                    correlation_id=correlation,
                    entity_type=follow_up.get("entity_type"),
                    entity_id=follow_up.get("entity_id"),
                    event_type=follow_up.get("event_type"),
                    error_type=type(exc).__name__,
                )
                nested_results.append({
                    "error": str(exc),
                    "event_type": follow_up.get("event_type"),
                })

    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "automation_event_completed",
        correlation_id=correlation,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        matched_rules=len(matched_rule_ids),
        actions_executed=len(action_results),
        duration_ms=duration_ms,
        dry_run=dry_run,
    )

    return {
        "correlation_id": correlation,
        "matched_rule_ids": matched_rule_ids,
        "action_results": action_results,
        "duration_ms": duration_ms,
        "dry_run": dry_run,
        "nested_results": nested_results,
    }
