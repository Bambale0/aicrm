"""
Сервис для health checks и метрик
"""

import time
from datetime import datetime
from typing import Any, Dict

import psutil
import redis.asyncio as redis
from sqlalchemy import text

from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..utils.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Сервис для проверки здоровья системы"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.start_time = time.time()

    async def check_database(self) -> Dict[str, Any]:
        """Проверка подключения к базе данных"""
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            return {"status": "healthy", "response_time": "ok"}
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            logger.error("Database health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    async def check_redis(self) -> Dict[str, Any]:
        """Проверка подключения к Redis"""
        try:
            client = redis.from_url(self.redis_url)
            await client.ping()
            await client.close()
            return {"status": "healthy", "response_time": "ok"}
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    async def check_external_services(self) -> Dict[str, Any]:
        """Проверка внешних сервисов (AI, email, etc.)"""
        services = {}

        # Проверка AI сервиса (если настроен)
        if hasattr(settings, "openrouter_api_key") and settings.openrouter_api_key:
            services["ai_service"] = {"status": "configured"}
        else:
            services["ai_service"] = {"status": "not_configured"}

        # Проверка email сервиса
        if hasattr(settings, "smtp_server") and settings.smtp_server:
            services["email_service"] = {"status": "configured"}
        else:
            services["email_service"] = {"status": "not_configured"}

        # Проверка Telegram бота
        if hasattr(settings, "telegram_bot_token") and settings.telegram_bot_token:
            services["telegram_bot"] = {"status": "configured"}
        else:
            services["telegram_bot"] = {"status": "not_configured"}

        return services

    def get_system_info(self) -> Dict[str, Any]:
        """Получение системной информации"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
                "uptime": time.time() - self.start_time,
            }
        except Exception as e:
            logger.error("Failed to get system info", error=str(e))
            return {"error": str(e)}

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Комплексная проверка здоровья"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "uptime": time.time() - self.start_time,
            "services": {},
        }

        # Проверка базы данных
        db_health = await self.check_database()
        health_data["services"]["database"] = db_health

        # Проверка Redis
        redis_health = await self.check_redis()
        health_data["services"]["redis"] = redis_health

        # Проверка внешних сервисов
        external_services = await self.check_external_services()
        health_data["services"].update(external_services)

        # Системная информация
        health_data["system"] = self.get_system_info()

        # Определение общего статуса
        unhealthy_services = [
            service
            for service in health_data["services"].values()
            if isinstance(service, dict) and service.get("status") == "unhealthy"
        ]

        if unhealthy_services:
            health_data["status"] = "degraded"

        logger.info("Health check completed", status=health_data["status"])
        return health_data

    async def readiness_check(self) -> Dict[str, Any]:
        """Проверка готовности (для Kubernetes readiness probe)"""
        # Критически важные проверки
        db_health = await self.check_database()
        redis_health = await self.check_redis()

        if db_health["status"] == "healthy" and redis_health["status"] == "healthy":
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "database": db_health, "redis": redis_health}

    async def liveness_check(self) -> Dict[str, Any]:
        """Проверка живости (для Kubernetes liveness probe)"""
        # Простая проверка - если процесс работает, то жив
        return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

    async def get_service_health(self) -> Dict[str, Any]:
        """Здоровье сервисов"""
        services = {}

        # Проверка AI сервиса
        if hasattr(settings, "openrouter_api_key") and settings.openrouter_api_key:
            services["ai_service"] = {"status": "healthy", "configured": True}
        else:
            services["ai_service"] = {"status": "not_configured", "configured": False}

        # Проверка email сервиса
        if hasattr(settings, "smtp_server") and settings.smtp_server:
            services["email_service"] = {"status": "healthy", "configured": True}
        else:
            services["email_service"] = {
                "status": "not_configured",
                "configured": False,
            }

        # Проверка Telegram бота
        if hasattr(settings, "telegram_bot_token") and settings.telegram_bot_token:
            services["telegram_bot"] = {"status": "healthy", "configured": True}
        else:
            services["telegram_bot"] = {"status": "not_configured", "configured": False}

        # Проверка SMS сервиса (Twilio)
        if hasattr(settings, "twilio_account_sid") and settings.twilio_account_sid:
            services["sms_service"] = {"status": "healthy", "configured": True}
        else:
            services["sms_service"] = {"status": "not_configured", "configured": False}

        return {
            "status": (
                "healthy"
                if all(s["status"] != "unhealthy" for s in services.values())
                else "degraded"
            ),
            "services": services,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_component_health(self) -> Dict[str, Any]:
        """Здоровье компонентов"""
        components = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "web_server": {
                "status": "healthy",
                "response_time": "ok",
            },  # FastAPI is running if this executes
        }

        return {
            "status": (
                "healthy"
                if all(c["status"] == "healthy" for c in components.values())
                else "degraded"
            ),
            "components": components,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_infrastructure_health(self) -> Dict[str, Any]:
        """Здоровье инфраструктуры"""
        try:
            system_info = self.get_system_info()
            status = "healthy"

            # Простые пороги для инфраструктуры
            if system_info.get("cpu_percent", 0) > 90:
                status = "critical"
            elif system_info.get("cpu_percent", 0) > 80:
                status = "warning"

            if system_info.get("memory", {}).get("percent", 0) > 90:
                status = "critical"
            elif system_info.get("memory", {}).get("percent", 0) > 80:
                status = "warning"

            return {
                "status": status,
                "infrastructure": system_info,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Infrastructure health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_security_health(self) -> Dict[str, Any]:
        """Безопасность системы"""
        security_checks = {
            "secret_key_configured": bool(
                hasattr(settings, "secret_key") and settings.secret_key
            ),
            "jwt_algorithm_secure": getattr(settings, "algorithm", "")
            in ["HS256", "RS256"],
            "debug_mode_off": not getattr(settings, "debug", True),
            "database_url_secure": "password"
            not in str(getattr(settings, "database_url", ""))
            or "localhost" in str(getattr(settings, "database_url", "")),
        }

        status = "healthy" if all(security_checks.values()) else "warning"

        return {
            "status": status,
            "security_checks": security_checks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_performance_health(self) -> Dict[str, Any]:
        """Производительность"""
        try:
            system_info = self.get_system_info()
            performance_metrics = {
                "cpu_usage": system_info.get("cpu_percent", 0),
                "memory_usage": system_info.get("memory", {}).get("percent", 0),
                "disk_usage": system_info.get("disk", {}).get("percent", 0),
                "uptime_seconds": system_info.get("uptime", 0),
            }

            status = "healthy"
            if (
                performance_metrics["cpu_usage"] > 85
                or performance_metrics["memory_usage"] > 85
            ):
                status = "warning"
            if (
                performance_metrics["cpu_usage"] > 95
                or performance_metrics["memory_usage"] > 95
            ):
                status = "critical"

            return {
                "status": status,
                "performance_metrics": performance_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Performance health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Глобальный экземпляр сервиса
health_service = HealthService()
