"""OpenAI-compatible external AI API client with durable usage telemetry."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict
from urllib.parse import urlparse

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.ai_connection import AIConnectionSettings, AIUsageEvent
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


def _key_fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _safe_non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _extract_usage(payload: Dict[str, Any]) -> Dict[str, int] | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None

    prompt_tokens = _safe_non_negative_int(
        usage.get("prompt_tokens", usage.get("input_tokens"))
    )
    completion_tokens = _safe_non_negative_int(
        usage.get("completion_tokens", usage.get("output_tokens"))
    )
    total_tokens = _safe_non_negative_int(usage.get("total_tokens"))
    if not total_tokens:
        total_tokens = prompt_tokens + completion_tokens

    input_details = usage.get("input_tokens_details")
    if not isinstance(input_details, dict):
        input_details = {}

    cache_hit = _safe_non_negative_int(
        usage.get(
            "prompt_cache_hit_tokens",
            input_details.get("cached_tokens"),
        )
    )
    cache_miss = _safe_non_negative_int(usage.get("prompt_cache_miss_tokens"))
    if not cache_miss and prompt_tokens:
        cache_miss = max(0, prompt_tokens - cache_hit)

    completion_details = usage.get("completion_tokens_details")
    if not isinstance(completion_details, dict):
        completion_details = {}
    output_details = usage.get("output_tokens_details")
    if not isinstance(output_details, dict):
        output_details = {}

    reasoning_tokens = _safe_non_negative_int(
        completion_details.get(
            "reasoning_tokens",
            output_details.get("reasoning_tokens"),
        )
    )

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "prompt_cache_hit_tokens": cache_hit,
        "prompt_cache_miss_tokens": cache_miss,
        "reasoning_tokens": reasoning_tokens,
    }


def _record_usage(
    db: Session,
    *,
    connection: AIConnectionSettings,
    api_key: str,
    payload: Dict[str, Any],
    operation: str,
    model: str,
) -> Dict[str, int] | None:
    usage = _extract_usage(payload)
    if usage is None:
        logger.warning(
            "ai_usage_missing",
            operation=operation,
            model=model,
            provider_request_id=payload.get("id"),
        )
        return None

    event = AIUsageEvent(
        connection_id=connection.id,
        operation=operation,
        model=str(payload.get("model") or model),
        provider_request_id=str(payload.get("id") or "") or None,
        key_fingerprint=_key_fingerprint(api_key),
        **usage,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(
        "ai_usage_recorded",
        usage_event_id=event.id,
        operation=event.operation,
        model=event.model,
        provider_request_id=event.provider_request_id,
        prompt_tokens=event.prompt_tokens,
        completion_tokens=event.completion_tokens,
        total_tokens=event.total_tokens,
        prompt_cache_hit_tokens=event.prompt_cache_hit_tokens,
        prompt_cache_miss_tokens=event.prompt_cache_miss_tokens,
        reasoning_tokens=event.reasoning_tokens,
    )
    return usage


def get_ai_usage_summary(db: Session) -> Dict[str, Any]:
    item = get_ai_settings(db)
    if not item.encrypted_api_key:
        return {
            "api_key_configured": False,
            "tracked_since": None,
            "last_usage_at": None,
            "calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 0,
            "reasoning_tokens": 0,
        }

    fingerprint = _key_fingerprint(get_api_key(item))
    row = (
        db.query(
            func.count(AIUsageEvent.id),
            func.coalesce(func.sum(AIUsageEvent.prompt_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.completion_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.total_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.prompt_cache_hit_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.prompt_cache_miss_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.reasoning_tokens), 0),
            func.min(AIUsageEvent.created_at),
            func.max(AIUsageEvent.created_at),
        )
        .filter(
            AIUsageEvent.connection_id == item.id,
            AIUsageEvent.key_fingerprint == fingerprint,
        )
        .one()
    )

    return {
        "api_key_configured": True,
        "tracked_since": row[7],
        "last_usage_at": row[8],
        "calls": int(row[0] or 0),
        "prompt_tokens": int(row[1] or 0),
        "completion_tokens": int(row[2] or 0),
        "total_tokens": int(row[3] or 0),
        "prompt_cache_hit_tokens": int(row[4] or 0),
        "prompt_cache_miss_tokens": int(row[5] or 0),
        "reasoning_tokens": int(row[6] or 0),
    }


async def fetch_provider_balance(db: Session) -> Dict[str, Any]:
    """Return provider-reported balance without inventing a token quota."""
    item = get_ai_settings(db)
    if not item.encrypted_api_key:
        return {
            "supported": False,
            "provider": None,
            "status": "key_not_configured",
            "remaining_tokens": None,
        }

    parsed = urlparse(_base_url())
    hostname = (parsed.hostname or "").lower()
    if hostname != "api.deepseek.com":
        return {
            "supported": False,
            "provider": hostname or None,
            "status": "unsupported",
            "remaining_tokens": None,
            "note": "Upstream does not expose a configured token-quota adapter.",
        }

    api_key = get_api_key(item)
    balance_url = f"{parsed.scheme}://{parsed.netloc}/user/balance"
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.ai_api_timeout_seconds) as client:
            response = await client.get(
                balance_url,
                headers={"Authorization": "Bearer " + api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ai_balance_http_error",
            provider="deepseek",
            status_code=exc.response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        return {
            "supported": True,
            "provider": "deepseek",
            "status": "error",
            "remaining_tokens": None,
            "error": "Balance API returned HTTP " + str(exc.response.status_code),
        }
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "ai_balance_request_failed",
            provider="deepseek",
            error_type=type(exc).__name__,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        return {
            "supported": True,
            "provider": "deepseek",
            "status": "error",
            "remaining_tokens": None,
            "error": "Could not load provider balance",
        }

    infos = payload.get("balance_infos") if isinstance(payload, dict) else None
    if not isinstance(infos, list):
        infos = []

    balances = []
    for raw in infos:
        if not isinstance(raw, dict):
            continue
        balances.append(
            {
                "currency": str(raw.get("currency") or ""),
                "total_balance": str(raw.get("total_balance") or "0"),
                "granted_balance": str(raw.get("granted_balance") or "0"),
                "topped_up_balance": str(raw.get("topped_up_balance") or "0"),
            }
        )

    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "ai_balance_loaded",
        provider="deepseek",
        is_available=bool(payload.get("is_available")) if isinstance(payload, dict) else False,
        currency_count=len(balances),
        duration_ms=duration_ms,
    )
    return {
        "supported": True,
        "provider": "deepseek",
        "status": "ok",
        "is_available": bool(payload.get("is_available")) if isinstance(payload, dict) else False,
        "balances": balances,
        "remaining_tokens": None,
        "note": (
            "DeepSeek reports monetary account balance, not an exact remaining-token quota. "
            "Token cost varies by model, input/output, and cache usage."
        ),
        "duration_ms": duration_ms,
    }


async def get_ai_usage_and_balance(db: Session) -> Dict[str, Any]:
    return {
        "usage": get_ai_usage_summary(db),
        "balance": await fetch_provider_balance(db),
    }


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

    usage = _record_usage(
        db,
        connection=item,
        api_key=api_key,
        payload=payload,
        operation="connection_test",
        model=selected_model,
    )

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
        total_tokens=usage.get("total_tokens") if usage else None,
    )

    return {
        "ok": True,
        "model": selected_model,
        "duration_ms": duration_ms,
        "response": content,
        "usage": usage,
    }


def _extract_json_object(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise AIConnectionError("AI returned an empty response")

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            value = json.loads(text[start:end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    raise AIConnectionError("AI returned invalid JSON")


async def complete_chat_json(
    db: Session,
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int = 700,
    temperature: float = 0.1,
    operation: str = "chat_json",
) -> Dict[str, Any]:
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
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ai_json_http_error",
            model=selected_model,
            operation=operation,
            status_code=exc.response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError(
            "AI API returned HTTP " + str(exc.response.status_code)
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "ai_json_request_failed",
            model=selected_model,
            operation=operation,
            error_type=type(exc).__name__,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        raise AIConnectionError("AI API request failed") from exc

    usage = _record_usage(
        db,
        connection=item,
        api_key=api_key,
        payload=payload,
        operation=operation,
        model=selected_model,
    )

    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices:
        raise AIConnectionError("AI API returned no choices")

    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    result = _extract_json_object(str(content or ""))

    logger.info(
        "ai_json_completed",
        model=selected_model,
        operation=operation,
        duration_ms=int((time.perf_counter() - started) * 1000),
        total_tokens=usage.get("total_tokens") if usage else None,
    )
    return result
