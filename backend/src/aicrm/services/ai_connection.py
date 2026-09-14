"""OpenAI-compatible external AI API client.

The CRM does not know or care which upstream provider is behind AI_API_BASE_URL.
For the current test environment it points to DeepSeek. Later it can point to
Neyronych's own AI gateway without changing CRM business logic.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.ai_connection import AIConnectionSettings
from ..utils.crypto import decrypt_data, encrypt_data
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIConnectionError(RuntimeError):
    pass


def get_ai_settings(db: Session) -> AIConnectionSettings:
    item = db.query(AIConnectionSettings).order_by(AIConnectionSettings.id.asc()).first()
    if item is None:
        item = AIConnectionSettings()
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


def update_ai_settings(
    db: Session,
    *,
    api_key: str | None = None,
    selected_model: str | None = None,
) -> AIConnectionSettings:
    item = get_ai_settings(db)

    if api_key is not None:
        cleaned = api_key.strip()
        if cleaned:
            item.encrypted_api_key = encrypt_data(cleaned)

    if selected_model is not None:
        item.selected_model = selected_model.strip() or None

    db.commit()
    db.refresh(item)

    logger.info(
        "ai_settings_updated",
        api_key_configured=bool(item.encrypted_api_key),
        selected_model=item.selected_model,
    )
    return item


def get_api_key(item: AIConnectionSettings) -> str:
    if not item.encrypted_api_key:
        raise AIConnectionError("API key is not configured")
    return decrypt_data(item.encrypted_api_key)


def _base_url() -> str:
    return settings.ai_api_base_url.rstrip("/")


async def fetch_models(db: Session) -> list[dict[str, Any]]:
    item = get_ai_settings(db)
    api_key = get_api_key(item)
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.ai_api_timeout_seconds) as client:
            response = await client.get(
                _base_url() + "/models",
                headers={"Authorization": "Bearer " + api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ai_models_http_error",
            status_code=exc.response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError(
            "AI API returned HTTP " + str(exc.response.status_code)
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "ai_models_request_failed",
            error_type=type(exc).__name__,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError("Could not load models from AI API") from exc

    raw_models = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(raw_models, list):
        raise AIConnectionError("AI API returned an invalid models response")

    models = []
    for raw in raw_models:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        models.append(
            {
                "id": str(raw["id"]),
                "name": str(raw.get("name") or raw["id"]),
                "owned_by": raw.get("owned_by"),
            }
        )

    models.sort(key=lambda value: value["name"].lower())

    logger.info(
        "ai_models_loaded",
        model_count=len(models),
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    return models


async def test_ai_connection(
    db: Session,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    item = get_ai_settings(db)
    api_key = get_api_key(item)
    selected_model = (model or item.selected_model or "").strip()

    if not selected_model:
        raise AIConnectionError("Select a model first")

    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.ai_api_timeout_seconds) as client:
            response = await client.post(
                _base_url() + "/chat/completions",
                headers={
                    "Authorization": "Bearer " + api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": selected_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Ответь только одним словом: OK",
                        }
                    ],
                    "max_tokens": 16,
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ai_test_http_error",
            model=selected_model,
            status_code=exc.response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError(
            "AI API returned HTTP " + str(exc.response.status_code)
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "ai_test_request_failed",
            model=selected_model,
            error_type=type(exc).__name__,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError("AI API test request failed") from exc

    choices = payload.get("choices") if isinstance(payload, dict) else None
    content = None
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict):
            content = message.get("content")

    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "ai_test_succeeded",
        model=selected_model,
        duration_ms=duration_ms,
    )

    return {
        "ok": True,
        "model": selected_model,
        "duration_ms": duration_ms,
        "response": content,
    }
