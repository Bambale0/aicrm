"""Canonical housing request status catalog shared by API and web CRM."""
from __future__ import annotations

REQUEST_STATUSES = [
    {"value": "new", "label": "Новая", "terminal": False},
    {"value": "accepted", "label": "Принята", "terminal": False},
    {"value": "assigned", "label": "Назначена", "terminal": False},
    {"value": "in_progress", "label": "В работе", "terminal": False},
    {"value": "done", "label": "Выполнена", "terminal": True},
    {"value": "cancelled", "label": "Отменена", "terminal": True},
    {"value": "closed", "label": "Закрыта", "terminal": True},
]

REQUEST_TRANSITIONS = {
    "new": [
        {"to": "accepted", "label": "Принять", "tone": "primary"},
        {"to": "cancelled", "label": "Отменить", "tone": "danger"},
    ],
    "accepted": [
        {"to": "in_progress", "label": "Начать выполнение", "tone": "primary"},
        {"to": "cancelled", "label": "Отменить", "tone": "danger"},
    ],
    "assigned": [
        {"to": "in_progress", "label": "Начать выполнение", "tone": "primary"},
        {"to": "cancelled", "label": "Отменить", "tone": "danger"},
    ],
    "in_progress": [
        {"to": "done", "label": "Выполнить", "tone": "primary"},
        {"to": "cancelled", "label": "Отменить", "tone": "danger"},
    ],
    "done": [
        {"to": "closed", "label": "Закрыть", "tone": "secondary"},
    ],
    "cancelled": [],
    "closed": [],
}

REQUEST_RESIDENT_NOTIFICATION_STATUSES = {
    "accepted",
    "in_progress",
    "cancelled",
    "done",
}


def request_status_catalog() -> dict:
    return {
        "statuses": REQUEST_STATUSES,
        "transitions": REQUEST_TRANSITIONS,
    }


def is_request_status(value: str) -> bool:
    return any(item["value"] == value for item in REQUEST_STATUSES)


def can_transition_request(old_status: str, new_status: str) -> bool:
    if old_status == new_status:
        return True
    return any(
        item["to"] == new_status
        for item in REQUEST_TRANSITIONS.get(old_status, [])
    )
