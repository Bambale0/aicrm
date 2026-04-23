"""
Криптографические утилиты для шифрования/дешифрования данных
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import settings


def _get_encryption_key() -> bytes:
    """
    Получить ключ шифрования из настроек или сгенерировать его.

    Returns:
        bytes: Ключ шифрования
    """
    # Используем SECRET_KEY из настроек для генерации ключа шифрования
    if not settings.secret_key:
        raise ValueError("SECRET_KEY must be set for encryption")

    # Генерация ключа из SECRET_KEY
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"aicrm_salt_2024",  # Статическая соль для детерминированности
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))
    return key


def encrypt_data(data: str) -> str:
    """
    Зашифровать строку данных.

    Args:
        data: Строка для шифрования

    Returns:
        str: Зашифрованные данные в base64
    """
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}")


def decrypt_data(encrypted_data: str) -> str:
    """
    Расшифровать строку данных.

    Args:
        encrypted_data: Зашифрованные данные в base64

    Returns:
        str: Расшифрованные данные
    """
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def generate_secure_token(length: int = 32) -> str:
    """
    Сгенерировать безопасный токен.

    Args:
        length: Длина токена в байтах

    Returns:
        str: Токен в base64
    """
    return base64.urlsafe_b64encode(os.urandom(length)).decode()


def hash_data(data: str, salt: Optional[str] = None) -> str:
    """
    Хэшировать данные с солью.

    Args:
        data: Данные для хэширования
        salt: Соль (если не указана, генерируется случайная)

    Returns:
        str: Хэш в формате base64
    """
    if salt is None:
        salt = base64.urlsafe_b64encode(os.urandom(16)).decode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(data.encode()))
    return f"{salt}${key.decode()}"


def verify_hash(data: str, hashed: str) -> bool:
    """
    Проверить хэш данных.

    Args:
        data: Исходные данные
        hashed: Хэш в формате salt$hash

    Returns:
        bool: Совпадает ли хэш
    """
    try:
        salt, expected_hash = hashed.split("$", 1)
        actual_hash = hash_data(data, salt)
        return actual_hash == hashed
    except Exception:
        return False
