"""
Prometheus Metrics Exporter for TutorMax

Exposes application metrics in Prometheus format for monitoring and alerting.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import FastAPI, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import psutil
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Prometheus Metrics Definitions
# ============================================================================

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database Metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["query_type"],  # SELECT, INSERT, UPDATE, DELETE
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query execution time",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

database_connections_active = Gauge(
    "database_connections_active",
    "Number of active database connections",
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],  # redis, in-memory
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration",
    ["operation"],  # get, set, delete
)

# Celery Metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],  # success, failure, retry
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time",
    ["task_name"],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800],
)

celery_queue_length = Gauge(
    "celery_queue_length",
    "Number of tasks in Celery queue",
    ["queue_name"],
)

# Application Metrics
users_active_total = Gauge(
    "users_active_total",
    "Number of active users",
)

sessions_active_total = Gauge(
    "sessions_active_total",
    "Number of active sessions",
)

interventions_pending_total = Gauge(
    "interventions_pending_total",
    "Number of pending interventions",
)

# System Metrics
system_cpu_usage_percent = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
)

system_memory_usage_bytes = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes",
)

system_memory_available_bytes = Gauge(
    "system_memory_available_bytes",
    "System available memory in bytes",
)

# SLA Metrics
sla_violations_total = Counter(
    "sla_violations_total",
    "Total SLA violations",
    ["sla_type"],  # response_time, intervention_time
)

sla_compliance_percent = Gauge(
    "sla_compliance_percent",
    "SLA compliance percentage",
    ["sla_type"],
)


# ============================================================================
# Metrics Collection Middleware
# ============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track HTTP request metrics.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid infinite loop
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Record metrics
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(
                duration
            )
            http_requests_total.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

            return response

        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method, endpoint=path, status_code=500
            ).inc()
            raise

        finally:
            # Decrement in-progress
            http_requests_in_progress.labels(method=method, endpoint=path).dec()


# ============================================================================
# System Metrics Collector
# ============================================================================


def collect_system_metrics():
    """
    Collect system-level metrics (CPU, memory, etc.)
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage_percent.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)
        system_memory_available_bytes.set(memory.available)

    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")


# ============================================================================
# FastAPI Integration
# ============================================================================


def setup_metrics(app: FastAPI):
    """
    Set up Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add middleware
    app.add_middleware(PrometheusMiddleware)

    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """
        Prometheus metrics endpoint.
        Returns metrics in Prometheus text format.
        """
        # Collect system metrics before returning
        collect_system_metrics()

        # Generate Prometheus format
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logger.info("✅ Prometheus metrics endpoint registered at /metrics")


# ============================================================================
# Helper Functions for Custom Metrics
# ============================================================================


def track_database_query(query_type: str, duration: float):
    """Track database query execution."""
    database_queries_total.labels(query_type=query_type).inc()
    database_query_duration_seconds.labels(query_type=query_type).observe(duration)


def track_cache_operation(operation: str, hit: bool, duration: float, cache_type: str = "redis"):
    """Track cache operation."""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()

    cache_operations_duration_seconds.labels(operation=operation).observe(duration)


def track_celery_task(task_name: str, status: str, duration: float = None):
    """Track Celery task execution."""
    celery_tasks_total.labels(task_name=task_name, status=status).inc()

    if duration is not None:
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def update_application_metrics(active_users: int, active_sessions: int, pending_interventions: int):
    """Update application-level metrics."""
    users_active_total.set(active_users)
    sessions_active_total.set(active_sessions)
    interventions_pending_total.set(pending_interventions)


def track_sla_violation(sla_type: str):
    """Track SLA violation."""
    sla_violations_total.labels(sla_type=sla_type).inc()


def update_sla_compliance(sla_type: str, compliance_percent: float):
    """Update SLA compliance percentage."""
    sla_compliance_percent.labels(sla_type=sla_type).set(compliance_percent)
