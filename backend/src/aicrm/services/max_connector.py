"""MAX messenger HTTP adapter."""
from __future__ import annotations

import ssl
from typing import Any, Dict, Iterable

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


async def verify_bot(access_token: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=_ssl_context()) as client:
            response = await client.get(
                _base_url() + "/me",
                headers=_headers(access_token),
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError("MAX returned HTTP " + str(exc.response.status_code)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX verification request failed") from exc


async def register_webhook(
    access_token: str,
    webhook_url: str,
    *,
    secret: str | None = None,
    update_types: Iterable[str] | None = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "url": webhook_url,
        "update_types": list(update_types or [
            "message_created",
            "message_edited",
            "bot_added",
            "bot_started",
            "bot_removed",
        ]),
    }
    if secret:
        payload["secret"] = secret

    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context()) as client:
            response = await client.post(
                _base_url() + "/subscriptions",
                headers=_headers(access_token),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError("MAX webhook registration returned HTTP " + str(exc.response.status_code)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX webhook registration failed") from exc

    if isinstance(data, dict) and data.get("success") is False:
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

    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context()) as client:
            response = await client.post(
                _base_url() + "/messages",
                params={"chat_id": numeric_chat_id},
                headers=_headers(access_token),
                json={
                    "text": text[:4000],
                    "notify": notify,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError("MAX sendMessage returned HTTP " + str(exc.response.status_code)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX message delivery failed") from exc


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

    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context()) as client:
            response = await client.get(
                _base_url() + "/messages",
                params={
                    "chat_id": numeric_chat_id,
                    "count": max(1, min(int(count), 100)),
                },
                headers=_headers(access_token),
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError("MAX messages request returned HTTP " + str(exc.response.status_code)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX messages request failed") from exc

    messages = data.get("messages") if isinstance(data, dict) else None
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

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=_ssl_context()) as client:
            response = await client.get(
                _base_url() + f"/chats/{numeric_chat_id}",
                headers=_headers(access_token),
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError(
            "MAX chat request returned HTTP " + str(exc.response.status_code)
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX chat request failed") from exc


async def get_bot_chat_membership(
    access_token: str,
    *,
    chat_id: str,
) -> Dict[str, Any]:
    try:
        numeric_chat_id = int(chat_id)
    except (TypeError, ValueError) as exc:
        raise MaxAPIError("Invalid MAX chat_id") from exc

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=_ssl_context()) as client:
            response = await client.get(
                _base_url() + f"/chats/{numeric_chat_id}/members/me",
                headers=_headers(access_token),
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise MaxAPIError(
            "MAX chat membership returned HTTP " + str(exc.response.status_code)
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise MaxAPIError("MAX chat membership request failed") from exc
