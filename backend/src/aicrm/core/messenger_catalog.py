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


RESIDENT_INTAKE_DEFAULTS = {
    "enabled": True,
    "prompts": {
        "full_name": "Здравствуйте! Чтобы оставить заявку, укажите, пожалуйста, ваше ФИО.",
        "address": "Укажите адрес, по которому возникла проблема.",
        "phone": "Укажите номер телефона для связи.",
        "problem": "Коротко опишите, что случилось.",
        "submitted": "Спасибо. Обращение передано диспетчеру. После принятия заявки я сообщу её номер.",
        "invalid_full_name": "Не смог распознать ФИО. Напишите его текстом, например: Иванов Иван Иванович.",
        "invalid_address": "Укажите адрес текстом чуть подробнее.",
        "invalid_phone": "Не смог распознать номер. Укажите телефон в формате +7XXXXXXXXXX.",
        "invalid_problem": "Опишите проблему чуть подробнее.",
    },
    "notifications": {
        "accepted": "✅ Заявка №{number} создана и принята диспетчером.",
        "in_progress": "🛠 По заявке №{number} началось выполнение работ.",
        "cancelled": "❌ Заявка №{number} отменена.",
        "done": "✅ Заявка №{number} выполнена.",
    },
}


def resident_intake_defaults() -> dict:
    return {
        "enabled": bool(RESIDENT_INTAKE_DEFAULTS["enabled"]),
        "prompts": dict(RESIDENT_INTAKE_DEFAULTS["prompts"]),
        "notifications": dict(RESIDENT_INTAKE_DEFAULTS["notifications"]),
    }
