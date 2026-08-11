#!/usr/bin/env python3
"""
AI CRM Performance Analysis Tools

This module provides comprehensive performance analysis tools for the AI CRM system,
including database optimization, query analysis, memory profiling, and system monitoring.

Usage:
    python scripts/analyze_performance.py --action <action> [options]

Actions:
    db_analyze         - Analyze database indexes and performance
    slow_queries       - Analyze slow queries from logs
    memory_profile     - Run memory profiling on main application
    stress_test        - Run basic stress testing
    load_test_setup    - Setup environment for load testing
    cache_analysis     - Analyze Redis cache performance
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import memory_profiler
    import psutil
    import psycopg2
    import redis
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"Missing dependency: {e}")
    print(
        "Install with: pip install psycopg2-binary redis sqlalchemy psutil memory-profiler"
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseAnalyzer:
    """Database performance analysis tools"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)

    def analyze_indexes(self) -> Dict[str, Any]:
        """Analyze existing indexes and suggest optimizations"""
        logger.info("Analyzing database indexes...")

        results = {
            "tables_without_indexes": [],
            "unused_indexes": [],
            "missing_indexes": [],
            "index_suggestions": [],
        }

        with self.engine.connect() as conn:
            # Get all tables
            tables_result = conn.execute(
                text(
                    """
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
                )
            )

            tables = [row[0] for row in tables_result]

            for table in tables:
                # Check if table has indexes
                index_result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM pg_catalog.pg_indexes
                    WHERE tablename = :table
                """
                    ),
                    {"table": table},
                )

                index_count = index_result.scalar()

                if index_count == 0:
                    results["tables_without_indexes"].append(table)

                # Analyze potential missing indexes based on foreign keys
                fk_result = conn.execute(
                    text(
                        """
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE constraint_type = 'FOREIGN KEY'
                      AND tc.table_name = :table
                """
                    ),
                    {"table": table},
                )

                fks = [(row[0], row[1], row[2], row[3]) for row in fk_result]

                for table_name, column_name, foreign_table, foreign_column in fks:
                    # Check if foreign key column has index
                    index_check = conn.execute(
                        text(
                            """
                        SELECT COUNT(*) FROM pg_catalog.pg_indexes
                        WHERE tablename = :table
                          AND indexdef LIKE :pattern
                    """
                        ),
                        {"table": table_name, "pattern": f"%{column_name}%"},
                    )

                    if index_check.scalar() == 0:
                        results["missing_indexes"].append(
                            {
                                "table": table_name,
                                "column": column_name,
                                "foreign_table": foreign_table,
                                "suggestion": f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});",
                            }
                        )

        return results

    def analyze_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Extract slow queries from PostgreSQL logs"""
        logger.info("Analyzing slow queries...")

        try:
            # Try to get slow queries from pg_stat_statements
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        temp_blks_written,
                        shared_blks_hit,
                        shared_blks_read
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT :limit
                """
                    ),
                    {"limit": limit},
                )

                slow_queries = []
                for row in result:
                    slow_queries.append(
                        {
                            "query": row[0],
                            "calls": row[1],
                            "total_time": row[2],
                            "mean_time": row[3],
                            "rows_returned": row[4],
                            "temp_blocks": row[5],
                            "cache_hits": row[6],
                            "cache_misses": row[7],
                            "analysis": self._analyze_query_performance(row),
                        }
                    )

                return slow_queries

        except Exception as e:
            logger.error(f"Could not analyze slow queries: {e}")
            logger.info("Make sure pg_stat_statements extension is enabled")
            return []

    def _analyze_query_performance(self, query_data) -> str:
        """Provide performance analysis for a query"""
        mean_time = query_data[3]
        cache_hits = query_data[6]
        cache_misses = query_data[7]

        analysis = []

        if mean_time > 1000:  # > 1 second
            analysis.append("VERY SLOW: Query takes more than 1 second on average")
        elif mean_time > 100:  # > 100ms
            analysis.append("SLOW: Query takes more than 100ms on average")

        if cache_misses > cache_hits:
            analysis.append("HIGH CACHE MISS: Consider query optimization or caching")

        return " | ".join(analysis) if analysis else "PERFORMANCE OK"


class CacheAnalyzer:
    """Redis cache performance analysis"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)

    def analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyze cache hit/miss ratios and usage"""
        try:
            info = self.redis_client.info()

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
                "keys_by_pattern": self._analyze_keys_by_pattern(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def _analyze_keys_by_pattern(self) -> Dict[str, int]:
        """Analyze cache keys by pattern"""
        patterns = {
            "user:*": 0,
            "session:*": 0,
            "cache:*": 0,
            "rate_limit:*": 0,
            "ai:*": 0,
        }

        for key in self.redis_client.scan_iter("*"):
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            for pattern in patterns:
                if key_str.startswith(pattern.rstrip("*")):
                    patterns[pattern] += 1
                    break

        return patterns


class MemoryProfiler:
    """Memory usage profiling tools"""

    def run_memory_profile(self, module_path: str = "src.aicrm.main"):
        """Run memory profiling on the application"""
        logger.info("Starting memory profiling...")

        try:
            # Import the main module
            import importlib

            # This would run memory profiler on startup
            # In practice, you'd modify this to profile specific functions
            cmd = [
                sys.executable,
                "-m",
                "memory_profiler",
                "--format=tab",
                f"{module_path}:app",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "profile": result.stdout,
                    "errors": result.stderr,
                }
            else:
                return {"success": False, "error": result.stderr or result.stdout}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Memory profiling timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            pass


class PerformanceReporter:
    """Generate performance reports"""

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a markdown performance report"""
        report = ["# AI CRM Performance Analysis Report\n"]
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Database section
        if "database" in results:
            db_results = results["database"]
            report.append("## Database Analysis\n")

            if db_results.get("tables_without_indexes"):
                report.append("### Tables Without Indexes ❌")
                for table in db_results["tables_without_indexes"]:
                    report.append(f"- `{table}`")
                report.append("")

            if db_results.get("missing_indexes"):
                report.append("### Missing Foreign Key Indexes ⚠️")
                for idx in db_results["missing_indexes"]:
                    report.append(
                        f"- **{idx['table']}.{idx['column']}** -> `{idx['suggestion']}`"
                    )
                report.append("")

            if db_results.get("slow_queries"):
                report.append("### Slow Queries 🔍")
                for i, query in enumerate(db_results["slow_queries"][:5], 1):
                    report.append(
                        f"**Query {i}** (Mean time: {query['mean_time']:.2f}ms)"
                    )
                    report.append(f"- Calls: {query['calls']}")
                    report.append(f"- Analysis: {query['analysis']}")
                    report.append("```sql")
                    report.append(
                        query["query"][:200] + "..."
                        if len(query["query"]) > 200
                        else query["query"]
                    )
                    report.append("```")
                report.append("")

        # Cache section
        if "cache" in results:
            cache_results = results["cache"]
            report.append("## Redis Cache Analysis\n")

            report.append(f"- **Hit Rate**: {cache_results.get('hit_rate', 0):.1f}%")
            report.append(
                f"- **Connected Clients**: {cache_results.get('connected_clients', 0)}"
            )
            report.append(
                f"- **Used Memory**: {cache_results.get('used_memory', 'unknown')}"
            )

            if "keys_by_pattern" in cache_results:
                report.append("\n### Keys by Pattern")
                for pattern, count in cache_results["keys_by_pattern"].items():
                    report.append(f"- `{pattern}`: {count} keys")
            report.append("")

        # Memory section
        if "memory" in results:
            memory_results = results["memory"]
            report.append("## Memory Analysis\n")

            if memory_results.get("success"):
                report.append("Memory profiling completed successfully.")
            else:
                report.append(
                    f"❌ Memory profiling failed: {memory_results.get('error', 'Unknown error')}"
                )
            report.append("")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="AI CRM Performance Analysis Tools")
    parser.add_argument(
        "--action",
        choices=[
            "db_analyze",
            "slow_queries",
            "memory_profile",
            "stress_test",
            "load_test_setup",
            "cache_analysis",
            "full_report",
        ],
        required=True,
        help="Action to perform",
    )
    parser.add_argument(
        "--db-url",
        default="postgresql://user:password@localhost:5432/aicrm",
        help="Database URL",
    )
    parser.add_argument(
        "--redis-url", default="redis://localhost:6379/0", help="Redis URL"
    )
    parser.add_argument(
        "--output", default="performance_report.md", help="Output file for reports"
    )
    parser.add_argument("--limit", type=int, default=20, help="Limit for query results")

    args = parser.parse_args()

    # Initialize analyzers
    db_analyzer = DatabaseAnalyzer(args.db_url)
    cache_analyzer = CacheAnalyzer(args.redis_url)
    memory_profiler = MemoryProfiler()
    reporter = PerformanceReporter()

    results = {}

    logger.info(f"Starting performance analysis: {args.action}")

    try:
        if args.action in ["db_analyze", "full_report"]:
            results["database"] = db_analyzer.analyze_indexes()

        if args.action in ["slow_queries", "full_report"]:
            results["database"]["slow_queries"] = db_analyzer.analyze_slow_queries(
                args.limit
            )

        if args.action in ["cache_analysis", "full_report"]:
            results["cache"] = cache_analyzer.analyze_cache_performance()

        if args.action == "memory_profile":
            results["memory"] = memory_profiler.run_memory_profile()

        if args.action == "stress_test":
            # Basic stress test using locust
            logger.info("Running basic stress test...")
            cmd = [
                sys.executable,
                "-m",
                "locust",
                "--locustfile",
                "locustfile.py",
                "--headless",
                "--users",
                "10",
                "--spawn-rate",
                "5",
                "--run-time",
                "30s",
            ]

            result = subprocess.run(cmd, cwd=Path(__file__).parent)
            if result.returncode == 0:
                logger.info("Stress test completed successfully")
            else:
                logger.error("Stress test failed")

        if args.action == "load_test_setup":
            logger.info("Setting up environment for load testing...")

            # Check if locust is available
            try:
                import locust

                logger.info("✓ Locust is available")
            except ImportError:
                logger.error("✗ Locust not installed. Run: pip install locust")
                return

            # Check database connectivity
            try:
                with db_analyzer.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✓ Database connection")
            except Exception as e:
                logger.error(f"✗ Database connection failed: {e}")
                return

            # Check Redis connectivity
            try:
                cache_analyzer.redis_client.ping()
                logger.info("✓ Redis connection")
            except Exception as e:
                logger.error(f"✗ Redis connection failed: {e}")
                return

            logger.info("🎯 Load testing environment is ready!")

        # Generate report if we have results
        if results:
            report = reporter.generate_report(results)

            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"📄 Report saved to {args.output}")

            # Print summary to console
            print("\n" + "=" * 60)
            print("📊 PERFORMANCE ANALYSIS SUMMARY")
            print("=" * 60)

            if "database" in results:
                db_res = results["database"]
                print(
                    f"📋 Tables without indexes: {len(db_res.get('tables_without_indexes', []))}"
                )
                print(
                    f"⚠️  Missing FK indexes: {len(db_res.get('missing_indexes', []))}"
                )
                if "slow_queries" in db_res:
                    print(f"🐌 Slow queries found: {len(db_res['slow_queries'])}")

            if "cache" in results:
                cache_res = results["cache"]
                hit_rate = cache_res.get("hit_rate", 0)
                print(f"💾 Cache hit rate: {hit_rate:.1f}%")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
