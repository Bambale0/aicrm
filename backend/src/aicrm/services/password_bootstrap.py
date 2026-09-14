"""One-time password bootstrap tokens for administrator account recovery."""
from __future__ import annotations

import hashlib
from typing import Optional

import redis.asyncio as redis

from ..core.config import settings

BOOTSTRAP_TTL_SECONDS = 1800
BOOTSTRAP_KEY_PREFIX = "admin_password_bootstrap:"


def bootstrap_token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return BOOTSTRAP_KEY_PREFIX + digest


async def consume_admin_password_bootstrap(token: str) -> Optional[int]:
    """Atomically consume a one-time bootstrap token and return target user_id."""
    if not token or len(token) < 20:
        return None

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        value = await client.execute_command("GETDEL", bootstrap_token_key(token))
    finally:
        await client.aclose()

    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def validate_admin_password_bootstrap(token: str) -> bool:
    """Check whether a bootstrap token currently exists without consuming it."""
    if not token or len(token) < 20:
        return False

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        return bool(await client.exists(bootstrap_token_key(token)))
    finally:
        await client.aclose()
