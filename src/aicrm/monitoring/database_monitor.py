"""
Database Monitoring Service для PostgreSQL
Предоставляет детальные метрики производительности базы данных
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..services.metrics_service import metrics_service

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Мониторинг PostgreSQL базы данных"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url
        self.engine = None
        self.last_check = 0
        self.check_interval = 60  # Проверять каждые 60 секунд

        # Метрики PostgreSQL
        self.connection_pool_metrics = {
            "active_connections": 0,
            "idle_connections": 0,
            "total_connections": 0,
            "max_connections": 0,
        }

        self.performance_metrics = {
            "slow_queries_count": 0,
            "cache_hit_ratio": 0.0,
            "deadlocks_count": 0,
            "avg_query_time": 0.0,
            "table_bloat_percentage": 0.0,
            "index_bloat_percentage": 0.0,
        }

    def set_database_url(self, database_url: str):
        """Установить URL базы данных"""
        self.database_url = database_url
        self.engine = create_engine(database_url)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Получить статистику соединений PostgreSQL"""
        if not self.engine:
            return {"error": "Database engine not initialized"}

        try:
            with self.engine.connect() as conn:
                # Активные соединения
                result = conn.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active' AND pid <> pg_backend_pid();
                """
                    )
                )
                active = result.scalar()

                # Максимальное количество соединений
                result = conn.execute(
                    text(
                        """
                    SELECT setting::int as max_connections
                    FROM pg_settings
                    WHERE name = 'max_connections';
                """
                    )
                )
                max_conn = result.scalar()

                # Всего соединений
                result = conn.execute(
                    text(
                        """
                    SELECT count(*) as total_connections
                    FROM pg_stat_activity;
                """
                    )
                )
                total = result.scalar()

                stats = {
                    "active_connections": active or 0,
                    "max_connections": max_conn or 100,
                    "total_connections": total or 0,
                    "idle_connections": (total or 0) - (active or 0),
                    "connection_utilization": round(
                        (active or 0) / (max_conn or 100) * 100, 2
                    ),
                }

                # Обновляем глобальные метрики
                metrics_service.update_db_connections_active(
                    stats["active_connections"]
                )

                return stats

        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {"error": str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получить метрики производительности PostgreSQL"""
        if not self.engine:
            return {"error": "Database engine not initialized"}

        try:
            with self.engine.connect() as conn:
                metrics = {}

                # Cache hit ratio
                result = conn.execute(
                    text(
                        """
                    SELECT
                        round(100 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) as cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database();
                """
                    )
                )
                metrics["cache_hit_ratio"] = result.scalar() or 0.0

                # Slow queries count (запросы дольше 1 секунды, вызванные более 10 раз)
                result = conn.execute(
                    text(
                        """
                    SELECT count(*) as slow_queries
                    FROM pg_stat_statements
                    WHERE mean_time > 1000 AND calls > 10;
                """
                    )
                )
                metrics["slow_queries_count"] = result.scalar() or 0

                # Average query time from pg_stat_statements
                result = conn.execute(
                    text(
                        """
                    SELECT round(avg(mean_time), 2) as avg_query_time
                    FROM pg_stat_statements
                    WHERE calls > 10;
                """
                    )
                )
                metrics["avg_query_time"] = result.scalar() or 0.0

                # Index scan ratio
                result = conn.execute(
                    text(
                        """
                    SELECT
                        round(
                            100 * sum(idx_scan) / nullif(sum(seq_scan + idx_scan), 0),
                            2
                        ) as index_scan_ratio
                    FROM pg_stat_user_tables;
                """
                    )
                )
                metrics["index_scan_ratio"] = result.scalar() or 0.0

                # Database size
                result = conn.execute(
                    text(
                        """
                    SELECT
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        pg_database_size(current_database()) as db_size_bytes
                """
                    )
                )
                db_size_result = result.fetchone()
                metrics["database_size"] = (
                    db_size_result[0] if db_size_result else "Unknown"
                )
                metrics["database_size_bytes"] = (
                    db_size_result[1] if db_size_result else 0
                )

                # Top 10 most used tables by size
                result = conn.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                    FROM pg_stat_user_tables
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """
                    )
                )

                top_tables = []
                for row in result:
                    top_tables.append(
                        {
                            "schema": row[0],
                            "table": row[1],
                            "size": row[2],
                            "inserts": row[3] or 0,
                            "updates": row[4] or 0,
                            "deletes": row[5] or 0,
                            "live_tuples": row[6] or 0,
                            "dead_tuples": row[7] or 0,
                        }
                    )

                metrics["top_tables_by_size"] = top_tables

                return metrics

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

    def get_replication_status(self) -> Dict[str, Any]:
        """Получить статус репликации"""
        if not self.engine:
            return {"error": "Database engine not initialized"}

        try:
            with self.engine.connect() as conn:
                # Проверка количества реплик
                result = conn.execute(
                    text(
                        """
                    SELECT count(*) as replica_count
                    FROM pg_stat_replication;
                """
                    )
                )
                replica_count = result.scalar() or 0

                if replica_count > 0:
                    result = conn.execute(
                        text(
                            """
                        SELECT
                            client_addr,
                            state,
                            round(extract(epoch from (now() - write_lag)), 2) as write_lag_seconds,
                            round(extract(epoch from (now() - flush_lag)), 2) as flush_lag_seconds,
                            round(extract(epoch from (now() - replay_lag)), 2) as replay_lag_seconds,
                            sent_lsn, write_lsn, flush_lsn, replay_lsn
                        FROM pg_stat_replication;
                    """
                        )
                    )

                    replicas = []
                    for row in result:
                        replicas.append(
                            {
                                "client_addr": str(row[0]),
                                "state": row[1],
                                "write_lag_seconds": row[2] or 0,
                                "flush_lag_seconds": row[3] or 0,
                                "replay_lag_seconds": row[4] or 0,
                                "sent_lsn": str(row[5]) if row[5] else None,
                                "write_lsn": str(row[6]) if row[6] else None,
                                "flush_lsn": str(row[7]) if row[7] else None,
                                "replay_lsn": str(row[8]) if row[8] else None,
                            }
                        )

                    return {
                        "replication_enabled": True,
                        "replica_count": replica_count,
                        "replicas": replicas,
                        "max_lag_seconds": (
                            max([r["replay_lag_seconds"] for r in replicas])
                            if replicas
                            else 0
                        ),
                    }
                else:
                    return {
                        "replication_enabled": False,
                        "replica_count": 0,
                        "replicas": [],
                        "max_lag_seconds": 0,
                    }

        except Exception as e:
            logger.error(f"Error getting replication status: {e}")
            return {"error": str(e)}

    def get_vacuum_stats(self) -> Dict[str, Any]:
        """Получить статистику VACUUM операций"""
        if not self.engine:
            return {"error": "Database engine not initialized"}

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count,
                        n_dead_tup,
                        n_live_tup,
                        round(
                            100 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0),
                            2
                        ) as dead_tuple_ratio
                    FROM pg_stat_user_tables
                    WHERE n_dead_tup > 1000 OR dead_tuple_ratio > 20
                    ORDER BY dead_tuple_ratio DESC
                    LIMIT 20;
                """
                    )
                )

                tables_stats = []
                for row in result:
                    tables_stats.append(
                        {
                            "schema": row[0],
                            "table": row[1],
                            "last_vacuum": str(row[2]) if row[2] else None,
                            "last_autovacuum": str(row[3]) if row[3] else None,
                            "vacuum_count": row[4] or 0,
                            "autovacuum_count": row[5] or 0,
                            "dead_tuples": row[6] or 0,
                            "live_tuples": row[7] or 0,
                            "dead_tuple_ratio": row[8] or 0.0,
                        }
                    )

                total_dead_tuples = sum([t["dead_tuples"] for t in tables_stats])

                return {
                    "tables_needing_attention": tables_stats,
                    "count": len(tables_stats),
                    "total_dead_tuples": total_dead_tuples,
                }

        except Exception as e:
            logger.error(f"Error getting vacuum stats: {e}")
            return {"error": str(e)}

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Собрать все метрики базы данных"""
        current_time = time.time()

        # Проверять не чаще чем раз в check_interval
        if current_time - self.last_check < self.check_interval:
            return self._get_cached_metrics()

        try:
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "connection_stats": self.get_connection_stats(),
                "performance_metrics": self.get_performance_metrics(),
                "replication_status": self.get_replication_status(),
                "vacuum_stats": self.get_vacuum_stats(),
            }

            self.last_check = current_time
            self._cached_metrics = results

            return results

        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {"error": str(e)}

    def _get_cached_metrics(self) -> Dict[str, Any]:
        """Вернуть кэшированные метрики"""
        if hasattr(self, "_cached_metrics"):
            return self._cached_metrics
        return {"status": "no_cached_data"}

    def get_health_status(self) -> Dict[str, Any]:
        """Получить статус здоровья базы данных"""
        try:
            metrics = self.collect_all_metrics()

            # Определяем статус на основе метрик
            health_score = 100
            issues = []

            # Проверка соединений
            conn_stats = metrics.get("connection_stats", {})
            if conn_stats.get("connection_utilization", 0) > 90:
                health_score -= 20
                issues.append("High connection utilization (>90%)")

            # Проверка cache hit ratio
            perf_metrics = metrics.get("performance_metrics", {})
            if perf_metrics.get("cache_hit_ratio", 100) < 95:
                health_score -= 15
                issues.append("Low cache hit ratio (<95%)")

            # Проверка медленных запросов
            if perf_metrics.get("slow_queries_count", 0) > 5:
                health_score -= 10
                issues.append("Too many slow queries (>5)")

            # Проверка индексов
            if perf_metrics.get("index_scan_ratio", 100) < 80:
                health_score -= 10
                issues.append("Low index scan ratio (<80%)")

            # Проверка репликации
            repl_status = metrics.get("replication_status", {})
            if repl_status.get("replication_enabled", False):
                max_lag = repl_status.get("max_lag_seconds", 0)
                if max_lag > 60:  # lag > 1 minute
                    health_score -= 25
                    issues.append(f"High replication lag ({max_lag}s)")

            status = (
                "healthy"
                if health_score >= 80
                else "warning" if health_score >= 60 else "critical"
            )

            return {
                "status": status,
                "health_score": health_score,
                "issues": issues,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "error", "error": str(e)}


# Глобальный экземпляр монитора
database_monitor = DatabaseMonitor()
