"""
Административные эндпоинты для управления системой
Все эндпоинты требуют авторизации администратора
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_admin_user, get_current_superuser, get_db
from ...models.user import User
from ...services.auth import AuthService

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)


# Модели данных
class UserCreate(BaseModel):
    """Модель для создания пользователя"""

    email: str = Field(..., description="Email")
    password: str = Field(..., description="Пароль")
    full_name: Optional[str] = Field(None, description="Полное имя")
    company_name: Optional[str] = Field(None, description="Название компании")
    role: str = Field("user", description="Роль пользователя")
    is_active: bool = Field(True, description="Активен ли пользователь")


class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""

    email: Optional[str] = Field(None, description="Email")
    full_name: Optional[str] = Field(None, description="Полное имя")
    company_name: Optional[str] = Field(None, description="Название компании")
    role: Optional[str] = Field(None, description="Роль пользователя")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")
    password: Optional[str] = Field(None, description="Новый пароль")


class UserResponse(BaseModel):
    """Модель ответа с данными пользователя"""

    id: int
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    """Модель статистики системы"""

    total_users: int
    active_users: int
    total_customers: int
    total_tasks: int
    total_orders: int
    total_campaigns: int
    system_uptime: str
    database_status: str
    redis_status: str


class LogEntry(BaseModel):
    """Модель записи лога"""

    timestamp: datetime
    level: str
    message: str
    module: Optional[str] = None


# Эндпоинты


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """
    Получить общую статистику системы
    """
    try:
        # Подсчет пользователей
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()

        # Подсчет клиентов (предполагаем, что есть модель Customer)
        total_customers = 0
        try:
            from ...models.customer import Customer

            total_customers = db.query(Customer).count()
        except ImportError:
            pass

        # Подсчет задач
        total_tasks = 0
        try:
            from ...models.task import Task

            total_tasks = db.query(Task).count()
        except ImportError:
            pass

        # Подсчет заказов
        total_orders = 0
        try:
            from ...models.order import Order

            total_orders = db.query(Order).count()
        except ImportError:
            pass

        # Подсчет кампаний
        total_campaigns = 0
        try:
            from ...models.campaign import Campaign

            total_campaigns = db.query(Campaign).count()
        except ImportError:
            pass

        # Проверка статуса базы данных
        database_status = "healthy"
        try:
            from sqlalchemy import text

            db.execute(text("SELECT 1"))
        except Exception:
            database_status = "unhealthy"

        # Проверка статуса Redis
        redis_status = "unknown"
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"

        # Время работы системы (приблизительно)
        system_uptime = "unknown"

        return SystemStats(
            total_users=total_users,
            active_users=active_users,
            total_customers=total_customers,
            total_tasks=total_tasks,
            total_orders=total_orders,
            total_campaigns=total_campaigns,
            system_uptime=system_uptime,
            database_status=database_status,
            redis_status=redis_status,
        )

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system stats")


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Пропустить пользователей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит пользователей"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Получить список всех пользователей с пагинацией
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_orm(user) for user in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Создать нового пользователя
    """
    # Проверка уникальности email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    # Создание пользователя
    try:
        user_dict = user_data.dict()
        user = AuthService.create_user(db=db, user_data=user_dict)
        return UserResponse.from_orm(user)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Получить пользователя по ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Обновить данные пользователя
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновление полей
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            # Хэширование пароля
            user.hashed_password = User.get_password_hash(value)
        else:
            setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return UserResponse.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Удалить пользователя
    """
    # Запрет удаления самого себя
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.get("/logs")
async def get_system_logs(
    lines: int = Query(100, ge=1, le=1000, description="Количество строк логов"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Получить последние строки системных логов
    """
    try:
        log_file = "/var/log/aicrm.log"  # Предполагаемый путь к логам

        if not os.path.exists(log_file):
            return {"logs": [], "message": "Log file not found"}

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        logs = []
        for line in recent_lines:
            line = line.strip()
            if line:
                # Простой парсинг логов (можно улучшить)
                parts = line.split(" - ", 2)
                if len(parts) >= 3:
                    timestamp_str, level, message = parts
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        logs.append(
                            LogEntry(timestamp=timestamp, level=level, message=message)
                        )
                    except:
                        logs.append(
                            LogEntry(
                                timestamp=datetime.utcnow(),
                                level="UNKNOWN",
                                message=line,
                            )
                        )
                else:
                    logs.append(
                        LogEntry(
                            timestamp=datetime.utcnow(), level="UNKNOWN", message=line
                        )
                    )

        return {"logs": [log.dict() for log in logs]}

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to read system logs")


@router.get("/health/detailed")
async def get_detailed_health(current_user: User = Depends(get_current_admin_user)):
    """
    Получить детальную информацию о здоровье системы
    """
    try:
        import psutil
        import redis

        # Redis статус
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_status = "healthy"
            redis_info = r.info()
        except Exception as e:
            redis_status = "unhealthy"
            redis_info = {"error": str(e)}

        # Системные метрики
        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "network_connections": len(psutil.net_connections()),
        }

        # Процессы Python
        python_processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                if "python" in proc.info["name"].lower():
                    python_processes.append(proc.info)
            except:
                pass

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {
                "redis": redis_status,
                "database": "unknown",  # Можно добавить проверку БД
            },
            "system": system_info,
            "redis_info": redis_info,
            "python_processes": python_processes[:10],  # Ограничим до 10
        }

    except ImportError:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": {"redis": "unknown"},
            "system": {"cpu_percent": 0, "memory_percent": 0},
            "error": "psutil not available",
        }


@router.get("/system/health/superuser")
async def get_superuser_system_health_check(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_superuser)
):
    """
    Комплексная проверка здоровья всей системы и всех сервисов.
    Доступно только для Super User.
    """
    health_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "checks": {},
        "warnings": [],
        "errors": [],
    }

    try:
        # 1. Проверка базы данных
        health_report["checks"]["database"] = {"status": "checking", "details": {}}
        try:
            from sqlalchemy import text

            db.execute(text("SELECT 1"))
            db.execute(text("SELECT COUNT(*) FROM users"))
            db.execute(text("SELECT COUNT(*) FROM tasks"))
            health_report["checks"]["database"] = {
                "status": "healthy",
                "details": {"connection": "OK", "basic_queries": "OK"},
            }
        except Exception as e:
            health_report["checks"]["database"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }
            health_report["errors"].append(f"Database error: {str(e)}")
            health_report["overall_status"] = "unhealthy"

        # 2. Проверка Redis
        health_report["checks"]["redis"] = {"status": "checking", "details": {}}
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_info = r.info()
            health_report["checks"]["redis"] = {
                "status": "healthy",
                "details": {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory", 0),
                    "total_connections_received": redis_info.get(
                        "total_connections_received", 0
                    ),
                },
            }
        except Exception as e:
            health_report["checks"]["redis"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }
            health_report["errors"].append(f"Redis error: {str(e)}")
            health_report["overall_status"] = "degraded"

        # 3. Системные ресурсы
        health_report["checks"]["system_resources"] = {
            "status": "checking",
            "details": {},
        }
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            system_details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "network_connections": len(psutil.net_connections()),
            }

            # Проверка порогов
            if cpu_percent > 90:
                health_report["warnings"].append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 90:
                health_report["warnings"].append(
                    f"High memory usage: {memory.percent}%"
                )
            if disk.percent > 95:
                health_report["warnings"].append(f"High disk usage: {disk.percent}%")

            health_report["checks"]["system_resources"] = {
                "status": "healthy",
                "details": system_details,
            }

        except Exception as e:
            health_report["checks"]["system_resources"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }
            health_report["errors"].append(f"System resources error: {str(e)}")

        # 4. Проверка процессов Python
        health_report["checks"]["python_processes"] = {
            "status": "checking",
            "details": {},
        }
        try:
            python_procs = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "status"]
            ):
                try:
                    if "python" in proc.info["name"].lower():
                        python_procs.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cpu_percent": proc.info["cpu_percent"],
                                "memory_percent": proc.info["memory_percent"],
                                "status": proc.info["status"],
                            }
                        )
                except:
                    pass

            health_report["checks"]["python_processes"] = {
                "status": "healthy",
                "details": {
                    "count": len(python_procs),
                    "processes": python_procs[:5],  # Ограничим до 5 процессов
                },
            }

        except Exception as e:
            health_report["checks"]["python_processes"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }

        # 5. Проверка дискового пространства для логов и бэкапов
        health_report["checks"]["disk_space"] = {"status": "checking", "details": {}}
        try:
            critical_paths = ["/var/log", "/tmp", "/opt/aicrm"]
            disk_checks = {}

            for path in critical_paths:
                try:
                    if os.path.exists(path):
                        usage = psutil.disk_usage(path)
                        disk_checks[path] = {
                            "free_gb": round(usage.free / (1024**3), 2),
                            "percent": usage.percent,
                        }
                        if usage.percent > 90:
                            health_report["warnings"].append(
                                f"Low disk space on {path}: {usage.percent}% used"
                            )
                except:
                    disk_checks[path] = {"error": "Path not accessible"}

            health_report["checks"]["disk_space"] = {
                "status": "healthy",
                "details": disk_checks,
            }

        except Exception as e:
            health_report["checks"]["disk_space"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }

        # 6. Проверка сетевых подключений
        health_report["checks"]["network"] = {"status": "checking", "details": {}}
        try:
            # Проверка основных портов
            import socket

            ports_to_check = [8000, 5432, 6379]  # HTTP, PostgreSQL, Redis
            network_checks = {}

            for port in ports_to_check:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    sock.close()
                    network_checks[f"port_{port}"] = "open" if result == 0 else "closed"
                except:
                    network_checks[f"port_{port}"] = "error"

            health_report["checks"]["network"] = {
                "status": "healthy",
                "details": network_checks,
            }

        except Exception as e:
            health_report["checks"]["network"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }

        # 7. Проверка целостности данных
        health_report["checks"]["data_integrity"] = {
            "status": "checking",
            "details": {},
        }
        try:
            # Проверка основных таблиц
            tables_to_check = ["users", "tasks", "customers"]
            integrity_checks = {}

            for table in tables_to_check:
                try:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    integrity_checks[table] = {"count": count, "status": "OK"}
                except Exception as e:
                    integrity_checks[table] = {"error": str(e), "status": "ERROR"}
                    health_report["errors"].append(
                        f"Data integrity error in {table}: {str(e)}"
                    )

            health_report["checks"]["data_integrity"] = {
                "status": (
                    "healthy"
                    if all(c.get("status") == "OK" for c in integrity_checks.values())
                    else "unhealthy"
                ),
                "details": integrity_checks,
            }

        except Exception as e:
            health_report["checks"]["data_integrity"] = {
                "status": "unhealthy",
                "details": {"error": str(e)},
            }

        # Финальная оценка статуса
        if health_report["errors"]:
            health_report["overall_status"] = "unhealthy"
        elif health_report["warnings"]:
            health_report["overall_status"] = "degraded"
        else:
            health_report["overall_status"] = "healthy"

        return health_report

    except Exception as e:
        logger.error(f"Superuser health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e),
            "checks": {},
            "warnings": [],
            "errors": ["Health check system failure"],
        }


@router.post("/db/backup")
async def create_database_backup(current_user: User = Depends(get_current_admin_user)):
    """
    Создать резервную копию базы данных
    """
    try:
        import subprocess
        from datetime import datetime

        # Предполагаем PostgreSQL
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"/tmp/aicrm_backup_{timestamp}.sql"

        # Команда для бэкапа (нужно настроить под вашу БД)
        cmd = [
            "pg_dump",
            "-h",
            "localhost",
            "-U",
            "aicrm_user",  # Замените на реальные credentials
            "-d",
            "aicrm_db",
            "-f",
            backup_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {
                "message": "Database backup created successfully",
                "backup_file": backup_file,
                "size": (
                    os.path.getsize(backup_file) if os.path.exists(backup_file) else 0
                ),
            }
        else:
            raise HTTPException(
                status_code=500, detail=f"Backup failed: {result.stderr}"
            )

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create database backup")


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(current_user: User = Depends(get_current_admin_user)):
    """
    Получить метрики мониторинга в формате Prometheus
    """
    try:
        import psutil
        import redis

        metrics = []

        # CPU метрики
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(f"# HELP system_cpu_usage System CPU usage percentage")
        metrics.append(f"# TYPE system_cpu_usage gauge")
        metrics.append(f"system_cpu_usage {cpu_percent}")

        # Память
        memory = psutil.virtual_memory()
        metrics.append(f"# HELP system_memory_usage System memory usage percentage")
        metrics.append(f"# TYPE system_memory_usage gauge")
        metrics.append(f"system_memory_usage {memory.percent}")

        metrics.append(f"# HELP system_memory_used_bytes System memory used in bytes")
        metrics.append(f"# TYPE system_memory_used_bytes gauge")
        metrics.append(f"system_memory_used_bytes {memory.used}")

        # Диск
        disk = psutil.disk_usage("/")
        metrics.append(f"# HELP system_disk_usage System disk usage percentage")
        metrics.append(f"# TYPE system_disk_usage gauge")
        metrics.append(f"system_disk_usage {disk.percent}")

        # Redis
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            redis_info = r.info()
            metrics.append(
                f"# HELP redis_connected_clients Number of connected Redis clients"
            )
            metrics.append(f"# TYPE redis_connected_clients gauge")
            metrics.append(
                f"redis_connected_clients {redis_info.get('connected_clients', 0)}"
            )
        except:
            pass

        return {"metrics": "\n".join(metrics)}

    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring metrics")
