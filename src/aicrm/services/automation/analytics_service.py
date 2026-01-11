"""
Сервис аналитики автоматизаций
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from ...models.automation import AutomationExecution, EntityType, Robot, Stage

logger = logging.getLogger(__name__)


class AutomationAnalyticsService:
    """Сервис для аналитики автоматизаций"""

    def __init__(self, db: Session):
        self.db = db

    async def get_execution_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_type: Optional[EntityType] = None,
    ) -> Dict[str, Any]:
        """
        Получение общей статистики выполнений автоматизаций

        Args:
            start_date: Начало периода
            end_date: Конец периода
            entity_type: Тип сущности для фильтрации

        Returns:
            Dict со статистикой
        """
        try:
            query = self.db.query(AutomationExecution)

            # Фильтры по дате
            if start_date:
                query = query.filter(AutomationExecution.started_at >= start_date)
            if end_date:
                query = query.filter(AutomationExecution.started_at <= end_date)

            # Фильтр по типу сущности
            if entity_type:
                query = query.filter(AutomationExecution.entity_type == entity_type)

            executions = query.all()

            # Общая статистика
            total_executions = len(executions)
            completed = sum(1 for e in executions if e.execution_status == "completed")
            failed = sum(1 for e in executions if e.execution_status == "failed")
            partial = sum(1 for e in executions if e.execution_status == "partial")

            # Метрики производительности
            execution_times = [
                e.execution_time_seconds for e in executions if e.execution_time_seconds
            ]
            avg_execution_time = (
                sum(execution_times) / len(execution_times) if execution_times else 0
            )
            max_execution_time = max(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0

            # Статистика действий
            total_actions = sum(e.actions_total for e in executions)
            successful_actions = sum(e.actions_successful for e in executions)
            failed_actions = sum(e.actions_failed for e in executions)

            return {
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
                "executions": {
                    "total": total_executions,
                    "completed": completed,
                    "failed": failed,
                    "partial": partial,
                    "success_rate": (
                        (completed / total_executions * 100)
                        if total_executions > 0
                        else 0
                    ),
                },
                "performance": {
                    "avg_execution_time_seconds": avg_execution_time,
                    "max_execution_time_seconds": max_execution_time,
                    "min_execution_time_seconds": min_execution_time,
                },
                "actions": {
                    "total": total_actions,
                    "successful": successful_actions,
                    "failed": failed_actions,
                    "success_rate": (
                        (successful_actions / total_actions * 100)
                        if total_actions > 0
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get execution stats: {e}")
            return {"error": str(e)}

    async def get_robot_performance(
        self,
        robot_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Анализ производительности роботов

        Args:
            robot_id: ID конкретного робота
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Dict с метриками роботов
        """
        try:
            query = self.db.query(
                AutomationExecution.robot_id,
                Robot.name,
                func.count(AutomationExecution.id).label("executions_count"),
                func.avg(AutomationExecution.execution_time_seconds).label("avg_time"),
                func.sum(AutomationExecution.actions_successful).label(
                    "successful_actions"
                ),
                func.sum(AutomationExecution.actions_failed).label("failed_actions"),
            ).join(Robot, AutomationExecution.robot_id == Robot.id)

            # Фильтры
            if robot_id:
                query = query.filter(AutomationExecution.robot_id == robot_id)
            if start_date:
                query = query.filter(AutomationExecution.started_at >= start_date)
            if end_date:
                query = query.filter(AutomationExecution.started_at <= end_date)

            query = query.group_by(AutomationExecution.robot_id, Robot.name)
            query = query.order_by(desc("executions_count"))

            results = query.all()

            robots_stats = []
            for row in results:
                total_actions = row.successful_actions + row.failed_actions
                success_rate = (
                    (row.successful_actions / total_actions * 100)
                    if total_actions > 0
                    else 0
                )

                robots_stats.append(
                    {
                        "robot_id": row.robot_id,
                        "robot_name": row.name,
                        "executions_count": row.executions_count,
                        "avg_execution_time_seconds": (
                            float(row.avg_time) if row.avg_time else 0
                        ),
                        "actions_successful": row.successful_actions,
                        "actions_failed": row.failed_actions,
                        "actions_success_rate": success_rate,
                    }
                )

            return {
                "robots": robots_stats,
                "summary": {
                    "total_robots": len(robots_stats),
                    "total_executions": sum(
                        r["executions_count"] for r in robots_stats
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get robot performance: {e}")
            return {"error": str(e)}

    async def get_action_type_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Статистика по типам действий

        Args:
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Dict со статистикой действий
        """
        try:
            # Получаем все выполнения и анализируем actions_executed
            query = self.db.query(AutomationExecution)

            if start_date:
                query = query.filter(AutomationExecution.started_at >= start_date)
            if end_date:
                query = query.filter(AutomationExecution.started_at <= end_date)

            executions = query.all()

            action_stats = {}

            for execution in executions:
                if execution.actions_executed:
                    for action in execution.actions_executed:
                        action_type = action.get("action_type")
                        success = action.get("success", False)

                        if action_type not in action_stats:
                            action_stats[action_type] = {
                                "executions": 0,
                                "successful": 0,
                                "failed": 0,
                            }

                        action_stats[action_type]["executions"] += 1
                        if success:
                            action_stats[action_type]["successful"] += 1
                        else:
                            action_stats[action_type]["failed"] += 1

            # Преобразуем в список с процентами
            actions_list = []
            for action_type, stats in action_stats.items():
                total = stats["executions"]
                success_rate = (stats["successful"] / total * 100) if total > 0 else 0

                actions_list.append(
                    {
                        "action_type": action_type,
                        "executions": total,
                        "successful": stats["successful"],
                        "failed": stats["failed"],
                        "success_rate": success_rate,
                    }
                )

            # Сортируем по количеству выполнений
            actions_list.sort(key=lambda x: x["executions"], reverse=True)

            return {
                "actions": actions_list,
                "summary": {
                    "total_action_types": len(actions_list),
                    "total_executions": sum(a["executions"] for a in actions_list),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get action type stats: {e}")
            return {"error": str(e)}

    async def get_error_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Анализ ошибок в автоматизациях

        Args:
            start_date: Начало периода
            end_date: Конец периода
            limit: Максимальное количество ошибок для возврата

        Returns:
            Dict с анализом ошибок
        """
        try:
            query = self.db.query(AutomationExecution).filter(
                AutomationExecution.execution_status.in_(["failed", "partial"])
            )

            if start_date:
                query = query.filter(AutomationExecution.started_at >= start_date)
            if end_date:
                query = query.filter(AutomationExecution.started_at <= end_date)

            failed_executions = (
                query.order_by(desc(AutomationExecution.started_at)).limit(limit).all()
            )

            errors = []
            error_types = {}

            for execution in failed_executions:
                error_info = {
                    "execution_id": execution.id,
                    "entity_type": execution.entity_type.value,
                    "entity_id": execution.entity_id,
                    "robot_name": execution.robot.name if execution.robot else None,
                    "error_message": execution.error_message,
                    "started_at": execution.started_at.isoformat(),
                    "execution_time_seconds": execution.execution_time_seconds,
                }
                errors.append(error_info)

                # Классификация ошибок
                error_type = self._classify_error(execution.error_message or "")
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1

            return {
                "errors": errors,
                "error_types": error_types,
                "summary": {
                    "total_errors": len(errors),
                    "error_categories": len(error_types),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get error analysis: {e}")
            return {"error": str(e)}

    async def get_process_efficiency(
        self,
        process_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Анализ эффективности бизнес-процессов

        Args:
            process_id: ID конкретного процесса
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Dict с метриками процессов
        """
        try:
            # Получаем стадии процессов
            stages_query = self.db.query(Stage)
            if process_id:
                stages_query = stages_query.filter(Stage.process_id == process_id)

            stages = stages_query.all()

            process_stats = {}

            for stage in stages:
                # Получаем выполнения для этой стадии
                executions_query = self.db.query(AutomationExecution).filter(
                    AutomationExecution.stage_id == stage.id
                )

                if start_date:
                    executions_query = executions_query.filter(
                        AutomationExecution.started_at >= start_date
                    )
                if end_date:
                    executions_query = executions_query.filter(
                        AutomationExecution.started_at <= end_date
                    )

                executions = executions_query.all()

                if executions:
                    process_name = (
                        stage.process.name
                        if stage.process
                        else f"Process {stage.process_id}"
                    )

                    if process_name not in process_stats:
                        process_stats[process_name] = {
                            "process_id": stage.process_id,
                            "stages": [],
                        }

                    # Статистика стадии
                    total_executions = len(executions)
                    successful = sum(
                        1 for e in executions if e.execution_status == "completed"
                    )
                    avg_time = (
                        sum(e.execution_time_seconds or 0 for e in executions)
                        / total_executions
                    )

                    process_stats[process_name]["stages"].append(
                        {
                            "stage_id": stage.id,
                            "stage_name": stage.name,
                            "executions": total_executions,
                            "successful": successful,
                            "success_rate": (
                                (successful / total_executions * 100)
                                if total_executions > 0
                                else 0
                            ),
                            "avg_execution_time_seconds": avg_time,
                        }
                    )

            return {
                "processes": list(process_stats.values()),
                "summary": {
                    "total_processes": len(process_stats),
                    "total_stages": sum(
                        len(p["stages"]) for p in process_stats.values()
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get process efficiency: {e}")
            return {"error": str(e)}

    async def get_hourly_distribution(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Распределение выполнений по часам

        Args:
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Dict с почасовым распределением
        """
        try:
            # Используем сырой SQL для группировки по часам
            query = """
                SELECT
                    DATE_TRUNC('hour', started_at) as hour,
                    COUNT(*) as executions_count,
                    AVG(execution_time_seconds) as avg_time,
                    SUM(actions_successful) as successful_actions,
                    SUM(actions_failed) as failed_actions
                FROM automation_executions
                WHERE 1=1
            """

            params = {}
            if start_date:
                query += " AND started_at >= :start_date"
                params["start_date"] = start_date
            if end_date:
                query += " AND started_at <= :end_date"
                params["end_date"] = end_date

            query += " GROUP BY DATE_TRUNC('hour', started_at) ORDER BY hour"

            result = self.db.execute(text(query), params)

            hourly_stats = []
            for row in result:
                total_actions = row.successful_actions + row.failed_actions
                success_rate = (
                    (row.successful_actions / total_actions * 100)
                    if total_actions > 0
                    else 0
                )

                hourly_stats.append(
                    {
                        "hour": row.hour.isoformat(),
                        "executions_count": row.executions_count,
                        "avg_execution_time_seconds": (
                            float(row.avg_time) if row.avg_time else 0
                        ),
                        "actions_success_rate": success_rate,
                    }
                )

            return {
                "hourly_distribution": hourly_stats,
                "summary": {
                    "total_hours": len(hourly_stats),
                    "peak_hour": (
                        max(hourly_stats, key=lambda x: x["executions_count"])["hour"]
                        if hourly_stats
                        else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get hourly distribution: {e}")
            return {"error": str(e)}

    def _classify_error(self, error_message: str) -> str:
        """Классификация типа ошибки"""
        error_lower = error_message.lower()

        if "timeout" in error_lower or "time" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        elif (
            "permission" in error_lower
            or "access" in error_lower
            or "auth" in error_lower
        ):
            return "permission"
        elif "validation" in error_lower or "invalid" in error_lower:
            return "validation"
        elif "not found" in error_lower or "missing" in error_lower:
            return "missing_resource"
        else:
            return "other"
