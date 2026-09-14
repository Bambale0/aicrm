"""Canonical messenger configuration catalogs exposed to the web CRM."""
from __future__ import annotations

MESSENGER_CHANNEL_PURPOSES = {
    "monitor": {
        "value": "monitor",
        "label": "Мониторинг общего чата",
        "description": "Входящие сообщения анализируются ИИ и попадают в диспетчерскую.",
    },
    "operator_alert": {
        "value": "operator_alert",
        "label": "Оповещения оператору",
        "description": "Сюда CRM дублирует важные alerts и номера созданных заявок.",
    },
    "broadcast": {
        "value": "broadcast",
        "label": "Исходящие публикации",
        "description": "Канал/чат доступен для исходящих сообщений и тестовой публикации.",
    },
}


def channel_purpose_catalog() -> list[dict[str, str]]:
    return list(MESSENGER_CHANNEL_PURPOSES.values())
