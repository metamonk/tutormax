"""
Monitoring and observability for Celery workers.

This module provides:
- Health check endpoints
- Metrics collection
- Task performance tracking
- Worker status monitoring
- Integration with monitoring systems (Prometheus, Flower)
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import redis

from src.api.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Health Checks
# ============================================================================

class HealthCheck:
    """
    Health check system for workers and dependencies.
    """

    def __init__(self):
        """Initialize health check system."""
        self.redis_client = redis.Redis.from_url(settings.redis_url)

    def check_redis(self) -> Dict[str, Any]:
        """
        Check Redis broker health.

        Returns:
            Health check result with status and details
        """
        try:
            start_time = time.time()
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000  # ms

            info = self.redis_client.info()

            return {
                "status": "healthy",
                "service": "redis",
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 2),
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "redis",
                "error": str(e),
            }

    def check_celery_workers(self) -> Dict[str, Any]:
        """
        Check Celery worker status.

        Returns:
            Worker health information
        """
        try:
            from src.workers.celery_app import celery_app

            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            stats = inspect.stats()

            if not active_workers:
                return {
                    "status": "unhealthy",
                    "service": "celery_workers",
                    "error": "No active workers found",
                    "worker_count": 0,
                }

            worker_count = len(active_workers)
            total_tasks = sum(len(tasks) for tasks in active_workers.values())

            return {
                "status": "healthy",
                "service": "celery_workers",
                "worker_count": worker_count,
                "active_tasks": total_tasks,
                "workers": list(active_workers.keys()),
                "registered_tasks_count": len(registered_tasks) if registered_tasks else 0,
            }

        except Exception as e:
            logger.error(f"Celery worker health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "celery_workers",
                "error": str(e),
            }

    def check_database(self) -> Dict[str, Any]:
        """
        Check database connectivity.

        Returns:
            Database health information
        """
        try:
            from sqlalchemy import create_engine, text

            # Use sync connection for health check
            db_url = f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
            engine = create_engine(db_url, pool_pre_ping=True)

            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            latency = (time.time() - start_time) * 1000  # ms
            engine.dispose()

            return {
                "status": "healthy",
                "service": "postgresql",
                "latency_ms": round(latency, 2),
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "postgresql",
                "error": str(e),
            }

    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.

        Returns:
            Complete health check results
        """
        checks = {
            "redis": self.check_redis(),
            "celery_workers": self.check_celery_workers(),
            "database": self.check_database(),
        }

        # Determine overall status
        statuses = [check["status"] for check in checks.values()]
        overall_status = "healthy" if all(s == "healthy" for s in statuses) else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        }


# ============================================================================
# Metrics Collection
# ============================================================================

class MetricsCollector:
    """
    Collect and track worker metrics.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.redis_client = redis.Redis.from_url(settings.redis_url)
        self.metrics_key_prefix = "tutormax:metrics:"

    def record_task_execution(
        self,
        task_name: str,
        duration_seconds: float,
        status: str,
        **metadata
    ):
        """
        Record task execution metrics.

        Args:
            task_name: Name of the task
            duration_seconds: Execution duration
            status: success or failure
            **metadata: Additional metadata
        """
        timestamp = datetime.utcnow().isoformat()

        metric_data = {
            "task_name": task_name,
            "duration_seconds": duration_seconds,
            "status": status,
            "timestamp": timestamp,
            **metadata,
        }

        # Store in Redis with 7-day TTL
        key = f"{self.metrics_key_prefix}task:{task_name}:{timestamp}"
        self.redis_client.setex(
            key,
            timedelta(days=7),
            str(metric_data)
        )

        # Update counters
        counter_key = f"{self.metrics_key_prefix}counter:{task_name}:{status}"
        self.redis_client.incr(counter_key)
        self.redis_client.expire(counter_key, timedelta(days=7))

        logger.debug(f"Recorded metric for {task_name}: {status} in {duration_seconds:.2f}s")

    def get_task_metrics(self, task_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get metrics for a specific task.

        Args:
            task_name: Name of the task
            hours: Hours to look back

        Returns:
            Task metrics summary
        """
        success_key = f"{self.metrics_key_prefix}counter:{task_name}:success"
        failure_key = f"{self.metrics_key_prefix}counter:{task_name}:failure"

        success_count = int(self.redis_client.get(success_key) or 0)
        failure_count = int(self.redis_client.get(failure_key) or 0)
        total_count = success_count + failure_count

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        return {
            "task_name": task_name,
            "period_hours": hours,
            "total_executions": total_count,
            "successful": success_count,
            "failed": failure_count,
            "success_rate": round(success_rate, 2),
        }

    def get_all_task_metrics(self) -> List[Dict[str, Any]]:
        """
        Get metrics for all tasks.

        Returns:
            List of task metrics
        """
        from src.workers.celery_app import celery_app

        # Get all registered tasks
        inspect = celery_app.control.inspect()
        registered = inspect.registered()

        if not registered:
            return []

        # Get unique task names
        task_names = set()
        for worker_tasks in registered.values():
            task_names.update(worker_tasks)

        # Get metrics for each task
        metrics = []
        for task_name in task_names:
            metrics.append(self.get_task_metrics(task_name))

        return metrics


# ============================================================================
# Worker Status Monitoring
# ============================================================================

class WorkerMonitor:
    """
    Monitor worker status and performance.
    """

    def __init__(self):
        """Initialize worker monitor."""
        from src.workers.celery_app import celery_app
        self.celery_app = celery_app

    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get detailed worker statistics.

        Returns:
            Worker statistics
        """
        inspect = self.celery_app.control.inspect()

        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()
        registered = inspect.registered()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "active_tasks": active,
            "scheduled_tasks": scheduled,
            "reserved_tasks": reserved,
            "registered_tasks": registered,
        }

    def get_queue_lengths(self) -> Dict[str, int]:
        """
        Get queue lengths for all queues.

        Returns:
            Queue name to length mapping
        """
        redis_client = redis.Redis.from_url(settings.redis_url)

        queues = [
            "default",
            "data_generation",
            "evaluation",
            "prediction",
            "training",
        ]

        queue_lengths = {}
        for queue in queues:
            # Celery uses list keys for queues
            key = f"celery:queue:{queue}"
            length = redis_client.llen(key)
            queue_lengths[queue] = length

        return queue_lengths

    def get_task_queue_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all task queues.

        Returns:
            List of queue information
        """
        queue_lengths = self.get_queue_lengths()

        queue_info = []
        for queue_name, length in queue_lengths.items():
            queue_info.append({
                "name": queue_name,
                "length": length,
                "status": "normal" if length < 1000 else "high",
            })

        return queue_info


# ============================================================================
# Performance Tracking
# ============================================================================

class PerformanceTracker:
    """
    Track and analyze worker performance.
    """

    def __init__(self):
        """Initialize performance tracker."""
        self.metrics_collector = MetricsCollector()

    def track_execution(self, func):
        """
        Decorator to track function execution time.

        Args:
            func: Function to track

        Returns:
            Wrapped function
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error = None

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                status = "failure"
                error = str(e)
                raise

            finally:
                duration = time.time() - start_time

                # Record metrics
                self.metrics_collector.record_task_execution(
                    task_name=func.__name__,
                    duration_seconds=duration,
                    status=status,
                    error=error,
                )

        return wrapper


# ============================================================================
# Monitoring Dashboard Data
# ============================================================================

def get_monitoring_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive monitoring data for dashboard.

    Returns:
        Complete monitoring dashboard data
    """
    health_check = HealthCheck()
    metrics_collector = MetricsCollector()
    worker_monitor = WorkerMonitor()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "health": health_check.get_overall_health(),
        "worker_stats": worker_monitor.get_worker_stats(),
        "queue_info": worker_monitor.get_task_queue_info(),
        "task_metrics": metrics_collector.get_all_task_metrics(),
    }


# ============================================================================
# Alerting
# ============================================================================

class AlertManager:
    """
    Manage alerts for worker issues.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.redis_client = redis.Redis.from_url(settings.redis_url)
        self.alert_key_prefix = "tutormax:alerts:"

    def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        **metadata
    ):
        """
        Create an alert.

        Args:
            severity: critical, warning, info
            title: Alert title
            message: Alert message
            **metadata: Additional metadata
        """
        alert_data = {
            "severity": severity,
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata,
        }

        # Store alert in Redis
        alert_id = f"{int(time.time() * 1000)}"
        key = f"{self.alert_key_prefix}{severity}:{alert_id}"

        self.redis_client.setex(
            key,
            timedelta(days=7),
            str(alert_data)
        )

        logger.warning(f"Alert created: [{severity}] {title}")

        # Future enhancement: Send alerts to external systems
        # Integrate with:
        # 1. Email via email_service.py (send to operations managers)
        # 2. Slack webhook for real-time notifications
        # 3. PagerDuty for critical/high severity alerts requiring immediate action
        # 4. SMS for after-hours critical alerts
        #
        # Implementation example:
        #   if severity in ["critical", "high"]:
        #       email_service = EmailService()
        #       await email_service.send_alert_email(
        #           subject=title,
        #           body=message,
        #           priority=severity
        #       )

    def check_and_alert_queue_backlog(self, threshold: int = 1000):
        """
        Check queue lengths and create alerts if needed.

        Args:
            threshold: Queue length threshold for alerts
        """
        worker_monitor = WorkerMonitor()
        queue_info = worker_monitor.get_task_queue_info()

        for queue in queue_info:
            if queue["length"] >= threshold:
                self.create_alert(
                    severity="warning",
                    title=f"Queue backlog: {queue['name']}",
                    message=f"Queue {queue['name']} has {queue['length']} pending tasks",
                    queue_name=queue["name"],
                    queue_length=queue["length"],
                )

    def check_and_alert_worker_health(self):
        """
        Check worker health and create alerts if needed.
        """
        health_check = HealthCheck()
        health = health_check.get_overall_health()

        if health["status"] != "healthy":
            unhealthy_services = [
                name for name, check in health["checks"].items()
                if check["status"] != "healthy"
            ]

            self.create_alert(
                severity="critical",
                title="Worker health check failed",
                message=f"Unhealthy services: {', '.join(unhealthy_services)}",
                unhealthy_services=unhealthy_services,
            )
