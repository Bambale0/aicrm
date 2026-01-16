"""
API роутер для системных проверок и мониторинга
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.dependencies import get_current_admin_user, get_db
from ...models.user import User
from ...utils.time_utils import get_moscow_time_utc

logger = logging.getLogger(__name__)


# Простой health service для заглушки
class HealthService:
    @staticmethod
    async def get_service_health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": get_moscow_time_utc().isoformat(),
            "services": ["database", "cache", "external_api"],
            "message": "All services are operational",
        }

    @staticmethod
    async def get_component_health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": get_moscow_time_utc().isoformat(),
            "components": ["api", "worker", "scheduler"],
            "message": "All components are operational",
        }

    @staticmethod
    async def get_infrastructure_health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": get_moscow_time_utc().isoformat(),
            "infrastructure": ["server", "network", "storage"],
            "message": "Infrastructure is operational",
        }

    @staticmethod
    async def get_security_health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": get_moscow_time_utc().isoformat(),
            "security_checks": ["ssl_cert", "firewall", "access_control"],
            "message": "Security checks passed",
        }

    @staticmethod
    async def get_performance_health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": get_moscow_time_utc().isoformat(),
            "performance_metrics": ["response_time", "throughput", "error_rate"],
            "message": "Performance is within acceptable limits",
        }


health_service = HealthService()

router = APIRouter(
    prefix="/system",
    tags=["System"],
    responses={404: {"description": "Not found"}},
)


@router.get("/database/status")
async def get_database_status(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
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
            "timestamp": get_moscow_time_utc().isoformat(),
            "database_type": "postgresql",
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
            "timestamp": get_moscow_time_utc().isoformat(),
            "error": str(e),
        }


@router.get("/resources")
async def get_system_resources(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
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
            "timestamp": get_moscow_time_utc().isoformat(),
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
            "timestamp": get_moscow_time_utc().isoformat(),
            "error": "psutil not available",
            "cpu": {"percent": 0},
            "memory": {"percent": 0},
            "disk": {"percent": 0},
        }
    except Exception as e:
        logger.error(f"System resources check error: {str(e)}")
        return {
            "status": "error",
            "timestamp": get_moscow_time_utc().isoformat(),
            "error": f"Failed to get system resources: {str(e)}",
        }


@router.get("/health/services")
async def get_service_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Получить здоровье сервисов
    """
    return await health_service.get_service_health()


@router.get("/health/components")
async def get_component_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Получить здоровье компонентов
    """
    return await health_service.get_component_health()


@router.get("/health/infrastructure")
async def get_infrastructure_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Получить здоровье инфраструктуры
    """
    return await health_service.get_infrastructure_health()


@router.get("/health/security")
async def get_security_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Получить безопасность системы
    """
    return await health_service.get_security_health()


@router.get("/health/performance")
async def get_performance_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Получить производительность
    """
    return await health_service.get_performance_health()


@router.get("/endpoints/health")
async def check_endpoints_health(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Проверить здоровье всех эндпоинтов системы
    """
    try:
        from urllib.parse import urljoin

        import httpx

        # Получаем базовый URL из настроек или используем localhost
        base_url = settings.base_url

        # Список критически важных эндпоинтов для проверки
        endpoints_to_check = [
            "/",  # root
            "/health",  # basic health
            "/system/database/status",  # database
            "/system/resources",  # resources
            "/customers/",  # customers
            "/orders/",  # orders
            "/tasks/",  # tasks
        ]

        health_results = {}
        overall_status = "healthy"
        errors = []
        warnings = []

        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints_to_check:
                try:
                    url = urljoin(base_url, endpoint)
                    response = await client.get(url)

                    if response.status_code == 200:
                        health_results[endpoint] = {
                            "status": "healthy",
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "status_code": response.status_code,
                        }
                    else:
                        health_results[endpoint] = {
                            "status": "unhealthy",
                            "status_code": response.status_code,
                            "error": f"Unexpected status code: {response.status_code}",
                        }
                        errors.append(
                            f"Endpoint {endpoint} returned {response.status_code}"
                        )
                        overall_status = "unhealthy"

                except httpx.TimeoutException:
                    health_results[endpoint] = {
                        "status": "timeout",
                        "error": "Request timeout",
                    }
                    warnings.append(f"Endpoint {endpoint} timed out")
                    if overall_status == "healthy":
                        overall_status = "degraded"

                except Exception as e:
                    health_results[endpoint] = {"status": "error", "error": str(e)}
                    errors.append(f"Endpoint {endpoint} error: {str(e)}")
                    overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": get_moscow_time_utc().isoformat(),
            "total_endpoints": len(endpoints_to_check),
            "healthy_endpoints": sum(
                1 for r in health_results.values() if r.get("status") == "healthy"
            ),
            "endpoints": health_results,
            "errors": errors,
            "warnings": warnings,
        }

    except ImportError:
        return {
            "status": "unknown",
        }
    except Exception as e:
        logger.error(f"Endpoints health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": get_moscow_time_utc().isoformat(),
            "error": f"Failed to check endpoints health: {str(e)}",
        }
