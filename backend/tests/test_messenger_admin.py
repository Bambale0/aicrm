from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aicrm.api.routers import messengers as messenger_router_module
from aicrm.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from aicrm.models import housing as _housing_models  # noqa: F401
from aicrm.models.base import Base
from aicrm.models.messenger import MessengerChannel, MessengerIntegration
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
