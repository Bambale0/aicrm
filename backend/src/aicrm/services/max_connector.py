"""MAX messenger HTTP adapter with bounded calls and structured telemetry."""
from __future__ import annotations

import ssl
import time
from typing import Any, Dict, Iterable, Optional

import httpx

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MaxAPIError(RuntimeError):
    pass


def _headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": access_token,
        "Content-Type": "application/json",
    }


def _base_url() -> str:
    return settings.max_api_base_url.rstrip("/")


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=settings.max_ca_bundle)


async def _request_json(
    access_token: str,
    *,
    operation: str,
    method: str,
    path: str,
    timeout_seconds: float,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    started = time.perf_counter()
    status_code: Optional[int] = None
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
            verify=_ssl_context(),
        ) as client:
            response = await client.request(
                method,
                _base_url() + path,
                headers=_headers(access_token),
                params=params,
                json=json_body,
            )
            status_code = response.status_code
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "max_api_call_failed",
            operation=operation,
            method=method,
            status_code=exc.response.status_code,
            duration_ms=duration_ms,
            error_type="http_status",
        )
        raise MaxAPIError(
            f"MAX {operation} returned HTTP {exc.response.status_code}"
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "max_api_call_failed",
            operation=operation,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
        )
        raise MaxAPIError(f"MAX {operation} request failed") from exc

    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "max_api_call_completed",
        operation=operation,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
    )
    if isinstance(data, dict):
        return data
    return {"result": data}


async def verify_bot(access_token: str) -> Dict[str, Any]:
    return await _request_json(
        access_token,
        operation="verify_bot",
        method="GET",
        path="/me",
        timeout_seconds=15.0,
    )


async def register_webhook(
    access_token: str,
    webhook_url: str,
    *,
    secret: str | None = None,
    update_types: Iterable[str] | None = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "url": webhook_url,
        "update_types": list(
            update_types
            or [
                "message_created",
                "message_edited",
                "bot_added",
                "bot_started",
                "bot_removed",
            ]
        ),
    }
    if secret:
        payload["secret"] = secret

    data = await _request_json(
        access_token,
        operation="register_webhook",
        method="POST",
        path="/subscriptions",
        timeout_seconds=20.0,
        json_body=payload,
    )
    if data.get("success") is False:
        raise MaxAPIError(str(data.get("message") or "MAX rejected webhook subscription"))
    return data


async def send_message(
    access_token: str,
    *,
    chat_id: str,
    text: str,
    notify: bool = True,
) -> Dict[str, Any]:
    try:
        numeric_chat_id = int(chat_id)
    except (TypeError, ValueError) as exc:
        raise MaxAPIError("Invalid MAX chat_id") from exc

    return await _request_json(
        access_token,
        operation="send_message",
        method="POST",
        path="/messages",
        timeout_seconds=20.0,
        params={"chat_id": numeric_chat_id},
        json_body={"text": text[:4000], "notify": notify},
    )


async def get_recent_messages(
    access_token: str,
    *,
    chat_id: str,
    count: int = 20,
) -> list[Dict[str, Any]]:
    try:
        numeric_chat_id = int(chat_id)
    except (TypeError, ValueError) as exc:
        raise MaxAPIError("Invalid MAX chat_id") from exc

    data = await _request_json(
        access_token,
        operation="get_recent_messages",
        method="GET",
        path="/messages",
        timeout_seconds=20.0,
        params={
            "chat_id": numeric_chat_id,
            "count": max(1, min(int(count), 100)),
        },
    )
    messages = data.get("messages")
    return messages if isinstance(messages, list) else []


async def get_chat(
    access_token: str,
    *,
    chat_id: str,
) -> Dict[str, Any]:
    try:
        numeric_chat_id = int(chat_id)
    except (TypeError, ValueError) as exc:
        raise MaxAPIError("Invalid MAX chat_id") from exc

    return await _request_json(
        access_token,
        operation="get_chat",
        method="GET",
        path=f"/chats/{numeric_chat_id}",
        timeout_seconds=15.0,
    )


async def get_bot_chat_membership(
    access_token: str,
    *,
    chat_id: str,
) -> Dict[str, Any]:
    try:
        numeric_chat_id = int(chat_id)
    except (TypeError, ValueError) as exc:
        raise MaxAPIError("Invalid MAX chat_id") from exc

    return await _request_json(
        access_token,
        operation="get_bot_chat_membership",
        method="GET",
        path=f"/chats/{numeric_chat_id}/members/me",
        timeout_seconds=15.0,
    )
