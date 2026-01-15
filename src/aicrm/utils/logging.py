"""
Настройка логирования с использованием structlog
"""

import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from ..core.config import settings


def setup_logging():
    """
    Настройка структурированного логирования
    """
    # Настройка стандартного logging
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    # Настройка процессоров structlog
    processors = [
        # Добавление контекста
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Выбор рендерера в зависимости от режима
    if settings.debug:
        # В режиме разработки - читаемый вывод
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # В продакшене - JSON логи
        processors.append(structlog.processors.JSONRenderer())

    # Конфигурация structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Настройка стандартных логгеров
    for logger_name in ["uvicorn", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.addHandler(logging.StreamHandler(sys.stdout))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Получение настроенного логгера
    """
    return structlog.get_logger(name)


def get_messenger_logger() -> structlog.stdlib.BoundLogger:
    """
    Получение логгера специально для операций мессенджера
    """
    return structlog.get_logger("messenger").bind(
        component="messenger", service="avito"
    )


# Глобальная настройка логирования при импорте
setup_logging()
