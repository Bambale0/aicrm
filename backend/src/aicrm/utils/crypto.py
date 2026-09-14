"""Encryption helpers for persisted integration credentials."""
import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet

from ..core.config import settings


def _get_encryption_key() -> bytes:
    if not settings.secret_key:
        raise ValueError("SECRET_KEY must be configured")
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_data(data: str) -> str:
    return Fernet(_get_encryption_key()).encrypt(data.encode("utf-8")).decode("utf-8")


def decrypt_data(encrypted_data: str) -> str:
    return Fernet(_get_encryption_key()).decrypt(encrypted_data.encode("utf-8")).decode("utf-8")


def generate_secure_token(length: int = 32) -> str:
    return base64.urlsafe_b64encode(os.urandom(length)).decode("utf-8")


def hash_data(data: str, salt: Optional[str] = None) -> str:
    effective_salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        data.encode("utf-8"),
        effective_salt.encode("utf-8"),
        100_000,
    )
    return effective_salt + "$" + base64.urlsafe_b64encode(digest).decode("utf-8")


def verify_hash(data: str, hashed: str) -> bool:
    try:
        salt, _ = hashed.split("$", 1)
        return hash_data(data, salt) == hashed
    except (ValueError, TypeError):
        return False
