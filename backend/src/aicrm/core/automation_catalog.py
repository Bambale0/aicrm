"""Metadata for the universal automation builder.

Only protocol/domain capabilities live here. Customer-specific rules are persisted
in the database and are never hardcoded in application code.
"""
from __future__ import annotations

REQUEST_STATUSES = [
    {"value": "new", "label": "Новая"},
    {"value": "assigned", "label": "Назначена"},
    {"value": "in_progress", "label": "В работе"},
    {"value": "waiting", "label": "Ожидание"},
    {"value": "done", "label": "Выполнена"},
    {"value": "closed", "label": "Закрыта"},
    {"value": "cancelled", "label": "Отменена"},
]

REQUEST_PRIORITIES = [
    {"value": "emergency", "label": "Аварийная"},
    {"value": "urgent", "label": "Срочная"},
    {"value": "high", "label": "Высокая"},
    {"value": "normal", "label": "Обычная"},
    {"value": "planned", "label": "Плановая"},
]

WORKFLOW_STATUSES = [
    {"value": "running", "label": "В работе"},
    {"value": "waiting", "label": "Ожидание"},
    {"value": "done", "label": "Завершён"},
    {"value": "cancelled", "label": "Отменён"},
]

ENTITY_TYPES = [
    {
        "value": "request",
        "label": "Заявки",
        "description": "Автоматизация заявок жителей: назначение, приоритеты, статусы и SLA.",
        "fields": [
            {"path": "entity.id", "label": "ID заявки", "type": "number"},
            {"path": "entity.number", "label": "Номер заявки", "type": "text"},
            {"path": "entity.status", "label": "Статус", "type": "select", "options": REQUEST_STATUSES},
            {"path": "entity.priority", "label": "Приоритет", "type": "select", "options": REQUEST_PRIORITIES},
            {"path": "entity.category", "label": "Категория", "type": "text"},
            {"path": "entity.building_id", "label": "Дом", "type": "number"},
            {"path": "entity.assigned_user_id", "label": "Исполнитель", "type": "number"},
            {"path": "entity.contractor_id", "label": "Подрядчик", "type": "number"},
            {"path": "entity.source_channel", "label": "Источник", "type": "text"},
            {"path": "entity.title", "label": "Заголовок", "type": "text"},
        ],
    },
    {
        "value": "incident",
        "label": "Инциденты",
        "description": "Автоматизация аварий, общедомовых событий и связанных действий.",
        "fields": [
            {"path": "entity.id", "label": "ID инцидента", "type": "number"},
            {"path": "entity.status", "label": "Статус", "type": "text"},
            {"path": "entity.priority", "label": "Приоритет", "type": "select", "options": REQUEST_PRIORITIES},
            {"path": "entity.category", "label": "Категория", "type": "text"},
            {"path": "entity.building_id", "label": "Дом", "type": "number"},
            {"path": "entity.title", "label": "Название", "type": "text"},
        ],
    },
    {
        "value": "conversation",
        "label": "Диалоги",
        "description": "Реакции на сообщения жителей и состояние диспетчерских диалогов.",
        "fields": [
            {"path": "entity.id", "label": "ID диалога", "type": "number"},
            {"path": "entity.provider", "label": "Мессенджер", "type": "text"},
            {"path": "entity.status", "label": "Статус", "type": "text"},
            {"path": "entity.requires_attention", "label": "Требует внимания", "type": "boolean"},
        ],
    },
    {
        "value": "workflow",
        "label": "Свой процесс",
        "description": "Универсальный процесс: согласование, закупка, обход, приёмка, проверка или любой другой сценарий.",
        "fields": [
            {"path": "entity.id", "label": "ID запуска", "type": "number"},
            {"path": "entity.name", "label": "Название запуска", "type": "text"},
            {"path": "entity.status", "label": "Статус процесса", "type": "select", "options": WORKFLOW_STATUSES},
            {"path": "entity.stage_id", "label": "Текущий этап", "type": "number"},
            {"path": "event.event_name", "label": "Имя произвольного события", "type": "text"},
        ],
    },
]

CONDITION_OPERATORS = [
    {"value": "equals", "label": "равно"},
    {"value": "not_equals", "label": "не равно"},
    {"value": "contains", "label": "содержит"},
    {"value": "not_contains", "label": "не содержит"},
    {"value": "starts_with", "label": "начинается с"},
    {"value": "ends_with", "label": "заканчивается на"},
    {"value": "gt", "label": "больше"},
    {"value": "gte", "label": "больше или равно"},
    {"value": "lt", "label": "меньше"},
    {"value": "lte", "label": "меньше или равно"},
    {"value": "in", "label": "входит в список"},
    {"value": "not_in", "label": "не входит в список"},
    {"value": "is_empty", "label": "пусто"},
    {"value": "not_empty", "label": "не пусто"},
    {"value": "is_true", "label": "да"},
    {"value": "is_false", "label": "нет"},
]

AUTOMATION_EVENTS = [
    {
        "value": "request_created",
        "label": "Создана заявка",
        "entity_types": ["request"],
        "description": "Срабатывает сразу после создания заявки.",
        "event_fields": [],
    },
    {
        "value": "request_updated",
        "label": "Заявка изменена",
        "entity_types": ["request"],
        "description": "Срабатывает после любого изменения заявки.",
        "event_fields": [
            {"path": "event.changed_fields", "label": "Изменённые поля", "type": "list"},
        ],
    },
    {
        "value": "request_status_changed",
        "label": "Изменился статус заявки",
        "entity_types": ["request"],
        "description": "Позволяет реагировать на переходы между статусами.",
        "event_fields": [
            {"path": "event.old_status", "label": "Предыдущий статус", "type": "select", "options": REQUEST_STATUSES},
            {"path": "event.status", "label": "Новый статус", "type": "select", "options": REQUEST_STATUSES},
        ],
    },
    {
        "value": "request_priority_changed",
        "label": "Изменился приоритет заявки",
        "entity_types": ["request"],
        "description": "Срабатывает при изменении срочности.",
        "event_fields": [
            {"path": "event.old_priority", "label": "Предыдущий приоритет", "type": "select", "options": REQUEST_PRIORITIES},
            {"path": "event.priority", "label": "Новый приоритет", "type": "select", "options": REQUEST_PRIORITIES},
        ],
    },
    {
        "value": "request_overdue",
        "label": "Заявка просрочена",
        "entity_types": ["request"],
        "description": "Событие для контроля SLA.",
        "event_fields": [],
    },
    {
        "value": "incident_created",
        "label": "Создан инцидент",
        "entity_types": ["incident"],
        "description": "Срабатывает при регистрации инцидента.",
        "event_fields": [],
    },
    {
        "value": "message_received",
        "label": "Получено сообщение",
        "entity_types": ["conversation"],
        "description": "Срабатывает при новом сообщении в подключённом мессенджере.",
        "event_fields": [
            {"path": "event.provider", "label": "Мессенджер", "type": "text"},
            {"path": "event.message_type", "label": "Тип сообщения", "type": "text"},
        ],
    },
    {
        "value": "conversation_problem_detected",
        "label": "ИИ обнаружил проблему в чате",
        "entity_types": ["conversation"],
        "description": "ИИ отделил реальную проблему ЖКХ от обычного разговора жителей.",
        "event_fields": [
            {"path": "event.title", "label": "Заголовок", "type": "text"},
            {"path": "event.summary", "label": "Сводка", "type": "text"},
            {"path": "event.category", "label": "Категория", "type": "text"},
            {"path": "event.priority", "label": "Приоритет", "type": "select", "options": REQUEST_PRIORITIES},
            {"path": "event.confidence", "label": "Уверенность ИИ", "type": "number"},
            {"path": "event.source_mode", "label": "Режим", "type": "text"},
        ],
    },
    {
        "value": "resident_request_detected",
        "label": "ИИ распознал заявку жителя",
        "entity_types": ["conversation"],
        "description": "В личном диалоге распознано обращение, которое можно перевести в заявку.",
        "event_fields": [
            {"path": "event.title", "label": "Заголовок", "type": "text"},
            {"path": "event.summary", "label": "Сводка", "type": "text"},
            {"path": "event.category", "label": "Категория", "type": "text"},
            {"path": "event.priority", "label": "Приоритет", "type": "select", "options": REQUEST_PRIORITIES},
            {"path": "event.confidence", "label": "Уверенность ИИ", "type": "number"},
            {"path": "event.source_mode", "label": "Режим", "type": "text"},
        ],
    },
    {
        "value": "conversation_requires_attention",
        "label": "Диалог требует внимания",
        "entity_types": ["conversation"],
        "description": "Срабатывает, когда оператору нужно подключиться к диалогу.",
        "event_fields": [],
    },
    {
        "value": "workflow_started",
        "label": "Процесс запущен",
        "entity_types": ["workflow"],
        "description": "Первое событие нового запуска собственного процесса.",
        "event_fields": [],
    },
    {
        "value": "workflow_updated",
        "label": "Данные процесса изменены",
        "entity_types": ["workflow"],
        "description": "Срабатывает после изменения переменных или статуса запуска.",
        "event_fields": [
            {"path": "event.changed_fields", "label": "Изменённые поля", "type": "list"},
        ],
    },
    {
        "value": "workflow_stage_changed",
        "label": "Изменился этап процесса",
        "entity_types": ["workflow"],
        "description": "Срабатывает при ручном переходе на другой этап.",
        "event_fields": [
            {"path": "event.old_stage_id", "label": "Предыдущий этап", "type": "number"},
            {"path": "event.stage_id", "label": "Новый этап", "type": "number"},
        ],
    },
    {
        "value": "custom_event",
        "label": "Произвольное событие",
        "entity_types": ["workflow"],
        "description": "Собственное событие процесса: например «счёт получен», «осмотр пройден», «согласовано».",
        "event_fields": [
            {"path": "event.event_name", "label": "Имя события", "type": "text"},
        ],
    },
]

AUTOMATION_ACTIONS = [
    {
        "value": "log_event",
        "label": "Записать в журнал",
        "entity_types": ["request", "incident", "conversation", "workflow"],
        "description": "Сохраняет понятную отметку в журнале автоматизации.",
        "config_fields": [
            {"name": "message", "label": "Текст", "type": "text", "required": False, "supports_template": True},
        ],
    },
    {
        "value": "set_request_status",
        "label": "Изменить статус заявки",
        "entity_types": ["request"],
        "description": "Меняет статус текущей заявки.",
        "config_fields": [
            {"name": "status", "label": "Статус", "type": "select", "required": True, "options": REQUEST_STATUSES},
        ],
    },
    {
        "value": "set_request_priority",
        "label": "Изменить приоритет заявки",
        "entity_types": ["request"],
        "description": "Меняет приоритет текущей заявки.",
        "config_fields": [
            {"name": "priority", "label": "Приоритет", "type": "select", "required": True, "options": REQUEST_PRIORITIES},
        ],
    },
    {
        "value": "assign_user",
        "label": "Назначить сотрудника",
        "entity_types": ["request"],
        "description": "Назначает конкретного сотрудника исполнителем.",
        "config_fields": [
            {"name": "user_id", "label": "Сотрудник", "type": "remote_select", "required": True, "source": "users"},
        ],
    },
    {
        "value": "assign_contractor",
        "label": "Назначить подрядчика",
        "entity_types": ["request"],
        "description": "Передаёт заявку выбранной подрядной организации.",
        "config_fields": [
            {"name": "contractor_id", "label": "Подрядчик", "type": "remote_select", "required": True, "source": "contractors"},
        ],
    },
    {
        "value": "create_request_from_conversation",
        "label": "Создать заявку из диалога",
        "entity_types": ["conversation"],
        "description": "Создаёт заявку из сводки ИИ и связывает её с исходным диалогом.",
        "config_fields": [],
    },
    {
        "value": "notify_operator",
        "label": "Оповестить оператора",
        "entity_types": ["conversation"],
        "description": "Создаёт отдельный alert для диспетчерской с краткой сводкой проблемы.",
        "config_fields": [],
    },
    {
        "value": "mark_conversation_attention",
        "label": "Передать диспетчеру",
        "entity_types": ["conversation"],
        "description": "Помечает диалог как требующий внимания оператора.",
        "config_fields": [
            {"name": "requires_attention", "label": "Требует внимания", "type": "boolean", "required": True},
        ],
    },
    {
        "value": "set_variable",
        "label": "Записать данные процесса",
        "entity_types": ["workflow"],
        "description": "Создаёт или изменяет любую переменную собственного процесса.",
        "config_fields": [
            {"name": "key", "label": "Имя переменной", "type": "text", "required": True},
            {"name": "value", "label": "Значение", "type": "text", "required": False, "supports_template": True},
        ],
    },
    {
        "value": "move_stage",
        "label": "Перейти на этап",
        "entity_types": ["workflow"],
        "description": "Перемещает запуск процесса на выбранный этап.",
        "config_fields": [
            {"name": "stage_id", "label": "Этап", "type": "stage_select", "required": True},
        ],
    },
    {
        "value": "emit_event",
        "label": "Запустить другое событие",
        "entity_types": ["workflow"],
        "description": "Передаёт управление следующему правилу этого же процесса.",
        "config_fields": [
            {"name": "event_name", "label": "Название события", "type": "text", "required": True, "supports_template": True},
        ],
    },
    {
        "value": "set_workflow_status",
        "label": "Изменить статус процесса",
        "entity_types": ["workflow"],
        "description": "Завершает, останавливает или возвращает процесс в работу.",
        "config_fields": [
            {"name": "status", "label": "Статус", "type": "select", "required": True, "options": WORKFLOW_STATUSES},
        ],
    },
    {
        "value": "create_request",
        "label": "Создать заявку",
        "entity_types": ["workflow"],
        "description": "Создаёт заявку ЖКХ из данных собственного процесса.",
        "config_fields": [
            {"name": "title", "label": "Заголовок", "type": "text", "required": True, "supports_template": True},
            {"name": "description", "label": "Описание", "type": "textarea", "required": True, "supports_template": True},
            {"name": "priority", "label": "Приоритет", "type": "select", "required": True, "options": REQUEST_PRIORITIES},
            {"name": "category", "label": "Категория", "type": "text", "required": False, "supports_template": True},
        ],
    },
]


def catalog_payload():
    return {
        "entity_types": ENTITY_TYPES,
        "events": AUTOMATION_EVENTS,
        "actions": AUTOMATION_ACTIONS,
        "condition_operators": CONDITION_OPERATORS,
        "request_statuses": REQUEST_STATUSES,
        "request_priorities": REQUEST_PRIORITIES,
        "workflow_statuses": WORKFLOW_STATUSES,
        "template_help": {
            "description": "В текстовых действиях можно использовать данные события и процесса.",
            "examples": [
                "{{ entity.number }}",
                "{{ entity.priority }}",
                "{{ event.event_name }}",
                "{{ variables.amount }}",
            ],
        },
    }
