"""
AI CRM System Metrics Service
Provides Prometheus metrics for monitoring system health and business analytics
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest

# Business Metrics
# User activity metrics
USER_LOGINS = Counter("user_logins_total", "Total user logins", ["user_type"])
USER_REGISTRATIONS = Counter("user_registrations_total", "Total user registrations")
ACTIVE_SESSIONS = Gauge("active_sessions", "Number of active user sessions")

# AI Usage Metrics
AI_REQUESTS = Counter(
    "ai_requests_total", "Total AI API requests", ["model", "provider", "status"]
)
AI_TOKENS_USED = Counter(
    "ai_tokens_total", "Total AI tokens used", ["model", "direction"]
)
AI_RESPONSE_TIME = Histogram("ai_response_time_seconds", "AI response time", ["model"])

# Communication Metrics
COMMUNICATIONS_SENT = Counter(
    "communications_sent_total", "Communications sent", ["channel", "direction"]
)
COMMUNICATIONS_RECEIVED = Counter(
    "communications_received_total", "Communications received", ["channel"]
)
EMAIL_SEND_SUCCESS = Counter("email_send_success_total", "Successful email sends")
EMAIL_SEND_FAILURE = Counter(
    "email_send_failure_total", "Failed email sends", ["error_type"]
)

# Business Process Metrics
ORDERS_CREATED = Counter("orders_created_total", "Orders created")
ORDERS_COMPLETED = Counter("orders_completed_total", "Orders completed", ["status"])
TASKS_COMPLETED = Counter("tasks_completed_total", "Tasks completed", ["category"])
PRODUCTION_STEPS_COMPLETED = Counter(
    "production_steps_completed_total", "Production steps completed"
)

# Technical Metrics
# API Performance
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)
HTTP_REQUESTS_ACTIVE = Gauge("http_requests_active", "Active HTTP requests")

# Database Metrics
DB_CONNECTIONS_ACTIVE = Gauge("db_connections_active", "Active database connections")
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds", "Database query duration", ["operation"]
)
DB_OPERATIONS_TOTAL = Counter(
    "db_operations_total", "Database operations", ["operation", "table"]
)

# Automation Metrics
AUTOMATION_EXECUTIONS = Counter(
    "automation_executions_total", "Automation executions", ["process_type", "status"]
)
AUTOMATION_ERRORS = Counter(
    "automation_errors_total", "Automation execution errors", ["error_type"]
)
ROBOT_EXECUTIONS = Gauge("robot_executions_active", "Active robot executions")

# System Health Metrics
SYSTEM_CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")
SYSTEM_MEMORY_USAGE = Gauge("system_memory_usage_percent", "Memory usage percentage")
SYSTEM_DISK_USAGE = Gauge("system_disk_usage_percent", "Disk usage percentage")
PROCESS_MEMORY_USAGE = Gauge("process_memory_bytes", "Process memory usage in bytes")

# Error Metrics
ERRORS_TOTAL = Counter("errors_total", "Total errors", ["type", "component"])
VALIDATION_ERRORS = Counter(
    "validation_errors_total", "Validation errors", ["field", "endpoint"]
)

# Cache Metrics
CACHE_HITS = Counter("cache_hits_total", "Cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Cache misses")
CACHE_SIZE = Gauge("cache_size_bytes", "Cache size in bytes")

# External API Metrics
EXTERNAL_API_REQUESTS = Counter(
    "external_api_requests_total", "External API requests", ["service", "status"]
)
EXTERNAL_API_DURATION = Histogram(
    "external_api_duration_seconds", "External API duration", ["service"]
)


class MetricsService:
    """Service for collecting and exposing monitoring metrics"""

    def __init__(self):
        self._start_time = time.time()
        self._init_business_metrics()

    def _init_business_metrics(self):
        """Initialize business-specific metrics"""
        # User metrics
        self.user_activity_summary = Summary(
            "user_session_duration_seconds", "User session duration"
        )

        # Business KPIs
        self.business_revenue = Counter(
            "business_revenue_rub", "Business revenue in RUB"
        )
        self.customer_satisfaction = Gauge(
            "customer_satisfaction_score", "Customer satisfaction score (1-5)"
        )

        # Workflow efficiency
        self.workflow_completion_rate = Gauge(
            "workflow_completion_rate_percent", "Workflow completion rate"
        )

    @staticmethod
    def record_user_login(user_type: str = "regular"):
        """Record user login event"""
        USER_LOGINS.labels(user_type=user_type).inc()

    @staticmethod
    def record_user_registration():
        """Record user registration event"""
        USER_REGISTRATIONS.inc()

    @staticmethod
    def update_active_sessions(count: int):
        """Update active sessions count"""
        ACTIVE_SESSIONS.set(count)

    @staticmethod
    def record_ai_request(
        model: str, provider: str, status: str, tokens: Optional[int] = None
    ):
        """Record AI API request"""
        AI_REQUESTS.labels(model=model, provider=provider, status=status).inc()
        if tokens:
            AI_TOKENS_USED.labels(model=model, direction="total").inc(tokens)

    @staticmethod
    def record_ai_response_time(model: str, duration: float):
        """Record AI response time"""
        AI_RESPONSE_TIME.labels(model=model).observe(duration)

    @staticmethod
    def record_communication(channel: str, direction: str):
        """Record communication event"""
        if direction == "outbound":
            COMMUNICATIONS_SENT.labels(channel=channel, direction=direction).inc()
        else:
            COMMUNICATIONS_RECEIVED.labels(channel=channel).inc()

    @staticmethod
    def record_email_send(success: bool, error_type: Optional[str] = None):
        """Record email sending event"""
        if success:
            EMAIL_SEND_SUCCESS.inc()
        else:
            EMAIL_SEND_FAILURE.labels(error_type=error_type or "unknown").inc()

    @staticmethod
    def record_order_created():
        """Record order creation"""
        ORDERS_CREATED.inc()

    @staticmethod
    def record_order_completed(status: str):
        """Record order completion"""
        ORDERS_COMPLETED.labels(status=status).inc()

    @staticmethod
    def record_task_completed(category: str):
        """Record task completion"""
        TASKS_COMPLETED.labels(category=category).inc()

    @staticmethod
    def record_http_request(method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        HTTP_REQUESTS_TOTAL.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).inc()
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    @staticmethod
    def update_http_requests_active(count: int):
        """Update active HTTP requests count"""
        HTTP_REQUESTS_ACTIVE.set(count)

    @staticmethod
    def update_db_connections_active(count: int):
        """Update active DB connections"""
        DB_CONNECTIONS_ACTIVE.set(count)

    @staticmethod
    def record_db_operation(operation: str, table: str, duration: float):
        """Record database operation"""
        DB_OPERATIONS_TOTAL.labels(operation=operation, table=table).inc()
        DB_QUERY_DURATION.labels(operation=operation).observe(duration)

    @staticmethod
    def record_automation_execution(process_type: str, status: str):
        """Record automation execution"""
        AUTOMATION_EXECUTIONS.labels(process_type=process_type, status=status).inc()
        if status == "running":
            ROBOT_EXECUTIONS.inc()
        elif status in ["completed", "failed"]:
            ROBOT_EXECUTIONS.dec()

    @staticmethod
    def record_automation_error(error_type: str):
        """Record automation error"""
        AUTOMATION_ERRORS.labels(error_type=error_type).inc()

    @staticmethod
    def update_system_metrics(
        cpu_percent: float, memory_percent: float, disk_percent: float
    ):
        """Update system resource metrics"""
        SYSTEM_CPU_USAGE.set(cpu_percent)
        SYSTEM_MEMORY_USAGE.set(memory_percent)
        SYSTEM_DISK_USAGE.set(disk_percent)

    @staticmethod
    def update_process_memory(memory_bytes: int):
        """Update process memory usage"""
        PROCESS_MEMORY_USAGE.set(memory_bytes)

    @staticmethod
    def record_error(error_type: str, component: str):
        """Record application error"""
        ERRORS_TOTAL.labels(type=error_type, component=component).inc()

    @staticmethod
    def record_validation_error(field: str, endpoint: str):
        """Record validation error"""
        VALIDATION_ERRORS.labels(field=field, endpoint=endpoint).inc()

    @staticmethod
    def record_cache_operation(hit: bool):
        """Record cache operation"""
        if hit:
            CACHE_HITS.inc()
        else:
            CACHE_MISSES.inc()

    @staticmethod
    def update_cache_size(size_bytes: int):
        """Update cache size"""
        CACHE_SIZE.set(size_bytes)

    @staticmethod
    def record_external_api_request(service: str, status: str, duration: float):
        """Record external API request"""
        EXTERNAL_API_REQUESTS.labels(service=service, status=status).inc()
        EXTERNAL_API_DURATION.labels(service=service).observe(duration)

    def get_metrics_html(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest().decode("utf-8")

    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self._start_time

    def get_business_summary(self) -> Dict[str, Any]:
        """Get business metrics summary"""
        return {
            "total_logins": USER_LOGINS._value,  # This would need proper implementation
            "total_registrations": USER_REGISTRATIONS._value,
            "active_sessions": ACTIVE_SESSIONS._value,
            "ai_requests_total": sum(AI_REQUESTS._value),
            "communications_total": sum(COMMUNICATIONS_SENT._value)
            + sum(COMMUNICATIONS_RECEIVED._value),
            "orders_completed": sum(ORDERS_COMPLETED._value),
            "uptime_hours": self.get_uptime_seconds() / 3600,
        }


# Global metrics service instance
metrics_service = MetricsService()
