"""
API роутер для системных проверок и мониторинга
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...services.health_service import health_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["System"],
    responses={404: {"description": "Not found"}},
)


@router.get("/database/status")
async def get_database_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить статус базы данных
    """
    try:
        # Проверяем подключение к БД простым запросом
        result = db.execute(text("SELECT 1")).scalar()

        # Получаем информацию о подключении
        connection_info = str(db.get_bind().engine)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_type": "postgresql",  # или определить динамически
            "connection_info": (
                connection_info.replace("://", "://[HIDDEN]@")
                if "://" in connection_info
                else connection_info
            ),
            "test_query_result": result,
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/resources")
async def get_system_resources() -> Dict[str, Any]:
    """
    Получить информацию о системных ресурсах
    """
    try:
        import psutil

        # CPU информация
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)

        # Память
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Диск
        disk = psutil.disk_usage("/")

        # Сеть (базовая информация)
        network = psutil.net_io_counters()

        # Процессы
        process_count = len(psutil.pids())

        # Определяем статус на основе порогов
        status = "healthy"
        warnings = []

        if cpu_percent > 90:
            status = "critical"
            warnings.append(f"Critical CPU usage: {cpu_percent}%")
        elif cpu_percent > 80:
            if status == "healthy":
                status = "warning"
            warnings.append(f"High CPU usage: {cpu_percent}%")

        if memory.percent > 90:
            status = "critical"
            warnings.append(f"Critical memory usage: {memory.percent}%")
        elif memory.percent > 80:
            if status == "healthy":
                status = "warning"
            warnings.append(f"High memory usage: {memory.percent}%")

        if disk.percent > 95:
            status = "critical"
            warnings.append(f"Critical disk usage: {disk.percent}%")
        elif disk.percent > 85:
            if status == "healthy":
                status = "warning"
            warnings.append(f"High disk usage: {disk.percent}%")

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "count_logical": cpu_count_logical,
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
            "processes": {
                "count": process_count,
            },
            "warnings": warnings,
        }

    except ImportError:
        # Если psutil не установлен, возвращаем базовую информацию
        return {
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "psutil not available",
            "cpu": {"percent": 0},
            "memory": {"percent": 0},
            "disk": {"percent": 0},
        }
    except Exception as e:
        logger.error(f"System resources check error: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Failed to get system resources: {str(e)}",
        }


@router.get("/health/services")
async def get_service_health() -> Dict[str, Any]:
    """
    Получить здоровье сервисов
    """
    return await health_service.get_service_health()


@router.get("/health/components")
async def get_component_health() -> Dict[str, Any]:
    """
    Получить здоровье компонентов
    """
    return await health_service.get_component_health()


@router.get("/health/infrastructure")
async def get_infrastructure_health() -> Dict[str, Any]:
    """
    Получить здоровье инфраструктуры
    """
    return await health_service.get_infrastructure_health()


@router.get("/health/security")
async def get_security_health() -> Dict[str, Any]:
    """
    Получить безопасность системы
    """
    return await health_service.get_security_health()


@router.get("/health/performance")
async def get_performance_health() -> Dict[str, Any]:
    """
    Получить производительность
    """
    return await health_service.get_performance_health()
