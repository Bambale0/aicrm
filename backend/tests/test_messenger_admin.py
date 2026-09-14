from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aicrm.api.routers import housing as housing_router_module
from aicrm.api.routers import messengers as messenger_router_module
from aicrm.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from aicrm.models import housing as _housing_models  # noqa: F401
from aicrm.models.base import Base
from aicrm.models.housing import Resident, ServiceRequest
from aicrm.models.messenger import (
    MessengerChannel,
    MessengerIntegration,
    MessengerIntakeSession,
    OperatorAlert,
)
from aicrm.models.user import User
from aicrm.utils.crypto import decrypt_data


@pytest.fixture()
def app_and_session(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = Session()
    admin = User(
        email="admin@example.test",
        hashed_password="not-used",
        full_name="Admin",
        is_active=True,
        is_superuser=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    admin_id = admin.id
    db.close()

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    def override_admin():
        session = Session()
        try:
            return session.get(User, admin_id)
        finally:
            session.close()

    async def noop_chat_check(*args, **kwargs):
        return None

    app = FastAPI()
    app.include_router(messenger_router_module.router)
    app.include_router(housing_router_module.router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_admin_user] = override_admin
    app.dependency_overrides[get_current_active_user] = override_admin
    monkeypatch.setattr(
        messenger_router_module,
        "check_max_chat_permissions_background",
        noop_chat_check,
    )

    yield app, Session, admin_id

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_max(client: TestClient) -> dict:
    response = client.post(
        "/messengers",
        json={
            "provider": "max",
            "name": "Primary MAX",
            "credentials": {"access_token": "max-secret-token"},
            "settings": {
                "ai_monitoring_enabled": True,
                "send_private_ack": True,
                "ai_context_messages": 12,
                "operator_chat_id": "must-not-survive",
                "webhook_secret": "must-not-survive",
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_integration_credentials_are_encrypted_and_not_returned(app_and_session):
    app, Session, _ = app_and_session
    client = TestClient(app)

    payload = _create_max(client)

    rendered = json.dumps(payload, ensure_ascii=False)
    assert "max-secret-token" not in rendered
    assert "must-not-survive" not in rendered
    assert payload["has_credentials"] is True
    assert payload["credential_status"]["access_token"] is True
    assert payload["settings"]["ai_context_messages"] == 12
    assert "operator_chat_id" not in payload["settings"]
    assert "webhook_secret" not in payload["settings"]

    db = Session()
    try:
        item = db.query(MessengerIntegration).one()
        assert "max-secret-token" not in item.credentials_encrypted
        credentials = json.loads(decrypt_data(item.credentials_encrypted))
        assert credentials["access_token"] == "max-secret-token"
        assert "webhook_secret" not in (item.settings or {})
    finally:
        db.close()


def test_webhook_secret_is_generated_encrypted_and_never_returned(app_and_session, monkeypatch):
    app, Session, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)

    captured = {}

    async def fake_register(access_token, webhook_url, *, secret=None, update_types=None):
        captured.update(
            access_token=access_token,
            webhook_url=webhook_url,
            secret=secret,
            update_types=list(update_types or []),
        )
        return {"success": True}

    monkeypatch.setattr(messenger_router_module, "max_register_webhook", fake_register)

    response = client.post(
        f"/messengers/{integration['id']}/webhook/register",
        json={},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["webhook_secret_configured"] is True
    assert captured["access_token"] == "max-secret-token"
    assert captured["secret"]
    assert captured["secret"] not in json.dumps(data)

    db = Session()
    try:
        item = db.get(MessengerIntegration, integration["id"])
        credentials = json.loads(decrypt_data(item.credentials_encrypted))
        assert credentials["webhook_secret"] == captured["secret"]
        assert "webhook_secret" not in (item.settings or {})
    finally:
        db.close()


def test_channel_crud_preserves_large_max_chat_id(app_and_session):
    app, Session, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)
    large_chat_id = "9223372036854775806"

    response = client.post(
        "/messenger-channels",
        json={
            "integration_id": integration["id"],
            "external_chat_id": large_chat_id,
            "purpose": "operator_alert",
            "name": "Диспетчер",
            "is_active": True,
        },
    )
    assert response.status_code == 200, response.text
    channel = response.json()
    assert channel["external_chat_id"] == large_chat_id
    assert channel["purpose"] == "operator_alert"

    response = client.get("/messenger-channels")
    assert response.status_code == 200
    assert response.json()[0]["external_chat_id"] == large_chat_id

    duplicate = client.post(
        "/messenger-channels",
        json={
            "integration_id": integration["id"],
            "external_chat_id": large_chat_id,
            "purpose": "operator_alert",
        },
    )
    assert duplicate.status_code == 409

    db = Session()
    try:
        stored = db.query(MessengerChannel).one()
        assert stored.external_chat_id == large_chat_id
    finally:
        db.close()


def test_max_bot_added_discovers_monitor_channel_and_webhook_secret_is_checked(
    app_and_session,
):
    app, Session, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)

    db = Session()
    try:
        item = db.get(MessengerIntegration, integration["id"])
        credentials = json.loads(decrypt_data(item.credentials_encrypted))
        credentials["webhook_secret"] = "webhook-secret-123"
        from aicrm.utils.crypto import encrypt_data

        item.credentials_encrypted = encrypt_data(json.dumps(credentials))
        item.is_active = True
        item.status = "active"
        db.commit()
    finally:
        db.close()

    event = {
        "update_type": "bot_added",
        "timestamp": 123456789,
        "chat_id": 987654321012345678,
        "is_channel": True,
        "user": {"user_id": 42},
    }

    bad = client.post(
        f"/webhooks/messengers/max/{integration['id']}",
        headers={"X-Max-Bot-Api-Secret": "wrong"},
        json=event,
    )
    assert bad.status_code == 401

    good = client.post(
        f"/webhooks/messengers/max/{integration['id']}",
        headers={"X-Max-Bot-Api-Secret": "webhook-secret-123"},
        json=event,
    )
    assert good.status_code == 200, good.text

    db = Session()
    try:
        channel = db.query(MessengerChannel).one()
        assert channel.integration_id == integration["id"]
        assert channel.external_chat_id == "987654321012345678"
        assert channel.purpose == "monitor"
        assert channel.is_active is True
    finally:
        db.close()


def test_channel_purpose_catalog_is_backend_owned(app_and_session):
    app, _, _ = app_and_session
    client = TestClient(app)
    response = client.get("/messenger-channels/catalog")
    assert response.status_code == 200
    purposes = {item["value"] for item in response.json()}
    assert {"monitor", "operator_alert", "broadcast"} <= purposes



def test_disabled_monitor_channel_blocks_group_ai_triage(app_and_session, monkeypatch):
    app, Session, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)
    chat_id = "987654321012345679"

    triaged: list[tuple[int, str]] = []

    async def capture_triage(message_id: int, source_mode: str):
        triaged.append((message_id, source_mode))

    monkeypatch.setattr(
        messenger_router_module,
        "process_message_background",
        capture_triage,
    )

    db = Session()
    try:
        item = db.get(MessengerIntegration, integration["id"])
        credentials = json.loads(decrypt_data(item.credentials_encrypted))
        credentials["webhook_secret"] = "webhook-secret-456"
        from aicrm.utils.crypto import encrypt_data

        item.credentials_encrypted = encrypt_data(json.dumps(credentials))
        item.is_active = True
        item.status = "active"
        db.add(
            MessengerChannel(
                integration_id=item.id,
                external_chat_id=chat_id,
                purpose="monitor",
                status="verified",
                is_active=False,
            )
        )
        db.commit()
    finally:
        db.close()

    def message_event(mid: str) -> dict:
        return {
            "update_type": "message_created",
            "message": {
                "recipient": {"chat_id": int(chat_id), "chat_type": "chat"},
                "sender": {"user_id": 42},
                "body": {"mid": mid, "text": "В подвале течёт труба"},
                "timestamp": 123456789,
            },
        }

    disabled = client.post(
        f"/webhooks/messengers/max/{integration['id']}",
        headers={"X-Max-Bot-Api-Secret": "webhook-secret-456"},
        json=message_event("message-disabled"),
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["source_mode"] == "unmanaged_group"
    assert triaged == []

    db = Session()
    try:
        channel = db.query(MessengerChannel).one()
        channel.is_active = True
        db.commit()
    finally:
        db.close()

    enabled = client.post(
        f"/webhooks/messengers/max/{integration['id']}",
        headers={"X-Max-Bot-Api-Secret": "webhook-secret-456"},
        json=message_event("message-enabled"),
    )
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["source_mode"] == "group_monitor"
    assert len(triaged) == 1
    assert triaged[0][1] == "group_monitor"


def test_private_max_questionnaire_creates_resident_and_new_request(
    app_and_session,
    monkeypatch,
):
    app, Session, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)

    replies: list[str] = []
    triaged: list[tuple[int, str]] = []

    async def capture_reply(conversation_id: int, text: str, **kwargs):
        replies.append(text)

    async def capture_triage(message_id: int, source_mode: str):
        triaged.append((message_id, source_mode))

    monkeypatch.setattr(
        messenger_router_module,
        "send_conversation_text_background",
        capture_reply,
    )
    monkeypatch.setattr(
        messenger_router_module,
        "process_message_background",
        capture_triage,
    )

    db = Session()
    try:
        item = db.get(MessengerIntegration, integration["id"])
        credentials = json.loads(decrypt_data(item.credentials_encrypted))
        credentials["webhook_secret"] = "private-intake-secret"
        from aicrm.utils.crypto import encrypt_data

        item.credentials_encrypted = encrypt_data(json.dumps(credentials))
        item.is_active = True
        item.status = "active"
        db.commit()
    finally:
        db.close()

    chat_id = 777001
    user_id = 991122

    def send(mid: str, text: str):
        response = client.post(
            f"/webhooks/messengers/max/{integration['id']}",
            headers={"X-Max-Bot-Api-Secret": "private-intake-secret"},
            json={
                "update_type": "message_created",
                "message": {
                    "recipient": {
                        "chat_id": chat_id,
                        "chat_type": "dialog",
                    },
                    "sender": {"user_id": user_id},
                    "body": {"mid": mid, "text": text},
                    "timestamp": 123456789,
                },
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    assert send("m1", "Здравствуйте")["intake"]["state"] == "full_name"
    assert "ФИО" in replies[-1]

    assert send("m2", "Иванов Иван Иванович")["intake"]["state"] == "address"
    assert "адрес" in replies[-1].lower()

    assert send("m3", "Санкт-Петербург, Невский проспект, 10")["intake"]["state"] == "phone"
    assert "телефон" in replies[-1].lower()

    assert send("m4", "+7 (999) 123-45-67")["intake"]["state"] == "problem"
    assert "случилось" in replies[-1].lower()

    completed = send("m5", "Течёт труба в ванной")
    assert completed["intake"]["state"] == "submitted"
    assert completed["intake"]["request_id"] is not None
    assert "передано диспетчеру" in replies[-1].lower()

    # The deterministic questionnaire owns private intake, so AI triage is not
    # invoked for these five messages.
    assert triaged == []

    db = Session()
    try:
        resident = db.query(Resident).one()
        assert resident.full_name == "Иванов Иван Иванович"
        assert resident.phone == "+79991234567"
        assert resident.preferred_channel == "max"
        assert resident.external_id == f"max:{integration['id']}:{user_id}"

        request_item = db.query(ServiceRequest).one()
        assert request_item.status == "new"
        assert request_item.resident_id == resident.id
        assert request_item.description == "Течёт труба в ванной"
        assert request_item.extra_data["address"] == "Санкт-Петербург, Невский проспект, 10"
        assert request_item.extra_data["phone"] == "+79991234567"

        session = db.query(MessengerIntakeSession).one()
        assert session.state == "submitted"
        assert session.request_id == request_item.id
        assert session.resident_id == resident.id

        alert = db.query(OperatorAlert).one()
        assert alert.request_id == request_item.id
        assert alert.status == "new"
    finally:
        db.close()


def test_request_status_transition_schedules_resident_notification(
    app_and_session,
    monkeypatch,
):
    app, Session, admin_id = app_and_session
    client = TestClient(app)

    db = Session()
    try:
        request_item = ServiceRequest(
            number="REQ-TEST-1",
            source_channel="max",
            source_conversation_id="123",
            category="general",
            priority="normal",
            status="new",
            title="Тестовая заявка",
            description="Описание",
            created_by=admin_id,
        )
        db.add(request_item)
        db.commit()
        db.refresh(request_item)
        request_id = request_item.id
    finally:
        db.close()

    scheduled: list[tuple[int, str]] = []

    async def capture_notification(request_id: int, status: str):
        scheduled.append((request_id, status))

    monkeypatch.setattr(
        housing_router_module,
        "notify_resident_request_status_background",
        capture_notification,
    )

    accepted = client.patch(
        f"/housing/requests/{request_id}",
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"
    assert scheduled == [(request_id, "accepted")]

    in_progress = client.patch(
        f"/housing/requests/{request_id}",
        json={"status": "in_progress"},
    )
    assert in_progress.status_code == 200, in_progress.text
    assert in_progress.json()["status"] == "in_progress"
    assert scheduled[-1] == (request_id, "in_progress")

    done = client.patch(
        f"/housing/requests/{request_id}",
        json={"status": "done"},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "done"
    assert scheduled[-1] == (request_id, "done")


def test_request_status_catalog_prevents_invalid_jump(app_and_session):
    app, Session, admin_id = app_and_session
    client = TestClient(app)

    catalog = client.get("/housing/request-statuses/catalog")
    assert catalog.status_code == 200
    assert any(
        item["to"] == "accepted" and item["label"] == "Принять"
        for item in catalog.json()["transitions"]["new"]
    )

    db = Session()
    try:
        request_item = ServiceRequest(
            number="REQ-TEST-2",
            source_channel="operator",
            category="general",
            priority="normal",
            status="new",
            title="Тест",
            description="Тест",
            created_by=admin_id,
        )
        db.add(request_item)
        db.commit()
        db.refresh(request_item)
        request_id = request_item.id
    finally:
        db.close()

    invalid = client.patch(
        f"/housing/requests/{request_id}",
        json={"status": "done"},
    )
    assert invalid.status_code == 409


def test_intake_copy_catalog_and_defaults_are_admin_managed(app_and_session):
    app, _, _ = app_and_session
    client = TestClient(app)
    integration = _create_max(client)

    catalog = client.get("/messengers/intake/catalog")
    assert catalog.status_code == 200
    data = catalog.json()
    assert {item["key"] for item in data["notification_fields"]} == {
        "accepted",
        "in_progress",
        "cancelled",
        "done",
    }

    stored = client.get("/messengers").json()
    item = next(row for row in stored if row["id"] == integration["id"])
    assert item["settings"]["resident_intake"]["enabled"] is True
    assert "accepted" in item["settings"]["resident_intake"]["notifications"]
