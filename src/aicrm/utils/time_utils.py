"""
Утилиты для работы со временем
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def get_moscow_time() -> datetime:
    """
    Получить текущее время по МСК (UTC+3)
    """
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


def get_moscow_time_utc() -> datetime:
    """
    Получить текущее время по МСК, но без timezone info (для совместимости с существующим кодом)
    """
    return get_moscow_time().replace(tzinfo=None)


def format_moscow_time(dt: Optional[datetime] = None) -> str:
    """
    Форматировать время по МСК
    """
    if dt is None:
        dt = get_moscow_time()
    return dt.strftime("%Y-%m-%d %H:%M:%S MSK")
