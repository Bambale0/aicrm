#!/usr/bin/env python3
"""Non-destructive smoke test for universal automation."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from uuid import uuid4

BASE_URL = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("SMOKE_BEARER_TOKEN", "")

if not BASE_URL:
    raise SystemExit("SMOKE_BASE_URL is required and must point to the API root")


def request(method: str, path: str, payload=None):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE_URL + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc


suffix = uuid4().hex[:8]
process_id = None
instance_id = None

try:
    status, health = request("GET", "/health")
    assert status == 200 and health["status"] == "healthy"

    _, catalog = request("GET", "/automation/catalog")
    assert any(item["value"] == "workflow" for item in catalog["entity_types"])
    assert any(item["value"] == "custom_event" for item in catalog["events"])
    assert any(item["value"] == "set_variable" for item in catalog["actions"])

    _, process = request("POST", "/automation/processes", {
        "name": "Smoke workflow " + suffix,
        "description": "Temporary smoke process",
        "entity_type": "workflow",
        "is_active": True,
    })
    process_id = process["id"]

    _, first_stage = request("POST", "/automation/stages", {
        "process_id": process_id,
        "name": "Старт",
    })
    _, second_stage = request("POST", "/automation/stages", {
        "process_id": process_id,
        "name": "Готово",
    })

    _, rule = request("POST", "/automation/rules", {
        "process_id": process_id,
        "name": "Smoke rule",
        "event_type": "custom_event",
        "conditions": [{
            "field": "event.event_name",
            "operator": "equals",
            "value": "approved",
            "logical_operator": "AND",
        }],
        "actions": [
            {
                "type": "set_variable",
                "config": {"key": "approved", "value": "true"},
            },
            {
                "type": "move_stage",
                "config": {"stage_id": second_stage["id"]},
            },
            {
                "type": "emit_event",
                "config": {"event_name": "finish"},
            },
        ],
        "priority": 100,
        "stop_after_match": False,
        "is_active": True,
    })

    _, finish_rule = request("POST", "/automation/rules", {
        "process_id": process_id,
        "name": "Smoke finish rule",
        "event_type": "custom_event",
        "conditions": [{
            "field": "event.event_name",
            "operator": "equals",
            "value": "finish",
            "logical_operator": "AND",
        }],
        "actions": [{
            "type": "set_workflow_status",
            "config": {"status": "done"},
        }],
        "priority": 200,
        "stop_after_match": False,
        "is_active": True,
    })

    _, dry_run = request("POST", "/automation/events/workflow/custom_event", {
        "entity_id": 0,
        "process_id": process_id,
        "data": {"event_name": "approved"},
        "dry_run": True,
        "correlation_id": "smoke-" + suffix,
    })
    assert rule["id"] in dry_run["matched_rule_ids"]
    assert len(dry_run["action_results"]) == 3
    assert all(item["status"] == "completed" for item in dry_run["action_results"])

    _, instance = request("POST", f"/automation/processes/{process_id}/instances", {
        "name": "Smoke run " + suffix,
        "variables": {"source": "smoke"},
        "current_stage_id": first_stage["id"],
    })
    instance_id = instance["id"]
    assert instance["current_stage_id"] == first_stage["id"]

    _, event_result = request("POST", f"/automation/instances/{instance_id}/events", {
        "event_name": "approved",
        "data": {"approved_by": "smoke"},
    })
    assert rule["id"] in event_result["matched_rule_ids"]
    assert len(event_result["action_results"]) == 3
    assert all(item["status"] == "completed" for item in event_result["action_results"])

    _, instances = request("GET", f"/automation/instances?process_id={process_id}")
    current = next(item for item in instances if item["id"] == instance_id)
    assert current["current_stage_id"] == second_stage["id"]
    assert current["status"] == "done"
    assert current["variables"]["approved"] is True
    assert any(
        finish_rule["id"] in nested.get("matched_rule_ids", [])
        for nested in event_result.get("nested_results", [])
    )

    _, moved = request("PATCH", f"/automation/instances/{instance_id}", {
        "variables": {"manual_check": True},
    })
    assert moved["variables"]["manual_check"] is True

    _, validation = request("GET", "/automation/validate")
    assert validation["valid"] is True, validation

    print(json.dumps({
        "ok": True,
        "process_id": process_id,
        "rule_id": rule["id"],
        "finish_rule_id": finish_rule["id"],
        "instance_id": instance_id,
        "correlation_id": dry_run["correlation_id"],
        "actions_checked": len(dry_run["action_results"]),
        "actual_actions": len(event_result["action_results"]),
        "nested_events": len(event_result.get("nested_results") or []),
    }, ensure_ascii=False))
finally:
    if instance_id is not None:
        try:
            request("DELETE", f"/automation/instances/{instance_id}")
        except Exception as exc:
            print(f"WARNING: instance cleanup failed: {exc}", file=sys.stderr)
    if process_id is not None:
        try:
            request("DELETE", f"/automation/processes/{process_id}")
        except Exception as exc:
            print(f"WARNING: process cleanup failed: {exc}", file=sys.stderr)
