from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aicrm.models.base import Base
from aicrm.models.ai_connection import AIConnectionSettings, AIUsageEvent
from aicrm.services import ai_connection
from aicrm.utils.crypto import encrypt_data


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _settings(db, key: str = "test-key-one") -> AIConnectionSettings:
    item = AIConnectionSettings(
        encrypted_api_key=encrypt_data(key),
        selected_model="deepseek-test",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_usage_is_recorded_from_provider_response_and_scoped_to_current_key(db_session):
    db = db_session
    connection = _settings(db)

    usage = ai_connection._record_usage(
        db,
        connection=connection,
        api_key="test-key-one",
        operation="messenger_triage",
        model="deepseek-test",
        payload={
            "id": "provider-request-1",
            "model": "deepseek-test",
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "total_tokens": 150,
                "prompt_cache_hit_tokens": 70,
                "prompt_cache_miss_tokens": 50,
                "completion_tokens_details": {"reasoning_tokens": 12},
            },
        },
    )

    assert usage == {
        "prompt_tokens": 120,
        "completion_tokens": 30,
        "total_tokens": 150,
        "prompt_cache_hit_tokens": 70,
        "prompt_cache_miss_tokens": 50,
        "reasoning_tokens": 12,
    }

    summary = ai_connection.get_ai_usage_summary(db)
    assert summary["calls"] == 1
    assert summary["total_tokens"] == 150
    assert summary["prompt_tokens"] == 120
    assert summary["completion_tokens"] == 30
    assert summary["prompt_cache_hit_tokens"] == 70
    assert summary["reasoning_tokens"] == 12

    event = db.query(AIUsageEvent).one()
    assert event.provider_request_id == "provider-request-1"
    assert event.key_fingerprint != "test-key-one"

    connection.encrypted_api_key = encrypt_data("test-key-two")
    db.commit()

    new_key_summary = ai_connection.get_ai_usage_summary(db)
    assert new_key_summary["calls"] == 0
    assert new_key_summary["total_tokens"] == 0


def test_extract_usage_supports_input_output_token_shape():
    usage = ai_connection._extract_usage(
        {
            "usage": {
                "input_tokens": 80,
                "input_tokens_details": {"cached_tokens": 25},
                "output_tokens": 20,
                "output_tokens_details": {"reasoning_tokens": 7},
                "total_tokens": 100,
            }
        }
    )
    assert usage == {
        "prompt_tokens": 80,
        "completion_tokens": 20,
        "total_tokens": 100,
        "prompt_cache_hit_tokens": 25,
        "prompt_cache_miss_tokens": 55,
        "reasoning_tokens": 7,
    }


@pytest.mark.asyncio
async def test_connection_test_records_actual_usage(db_session, monkeypatch):
    db = db_session
    _settings(db)

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "test-completion-id",
                "model": "deepseek-test",
                "choices": [{"message": {"content": "OK"}}],
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 1,
                    "total_tokens": 10,
                },
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(ai_connection.httpx, "AsyncClient", FakeClient)

    result = await ai_connection.test_ai_connection(db, model="deepseek-test")
    assert result["ok"] is True
    assert result["usage"]["total_tokens"] == 10

    summary = ai_connection.get_ai_usage_summary(db)
    assert summary["calls"] == 1
    assert summary["total_tokens"] == 10


@pytest.mark.asyncio
async def test_deepseek_balance_is_reported_as_money_not_fake_token_quota(
    db_session,
    monkeypatch,
):
    db = db_session
    _settings(db)

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "is_available": True,
                "balance_infos": [
                    {
                        "currency": "USD",
                        "total_balance": "12.34",
                        "granted_balance": "2.34",
                        "topped_up_balance": "10.00",
                    }
                ],
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, **kwargs):
            assert url == "https://api.deepseek.com/user/balance"
            return FakeResponse()

    monkeypatch.setattr(ai_connection, "_base_url", lambda: "https://api.deepseek.com")
    monkeypatch.setattr(ai_connection.httpx, "AsyncClient", FakeClient)

    result = await ai_connection.fetch_provider_balance(db)
    assert result["supported"] is True
    assert result["status"] == "ok"
    assert result["balances"][0]["total_balance"] == "12.34"
    assert result["remaining_tokens"] is None
    assert "not an exact remaining-token quota" in result["note"]
