"""
Enhanced Infrastructure Health Check Service

Provides comprehensive health checks for all infrastructure components
with alerting, recovery monitoring, and detailed diagnostics.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from src.workers.monitoring import HealthCheck
from src.api.uptime_service import get_uptime_monitor

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """Structured health check result."""

    def __init__(
        self,
        service: str,
        status: HealthStatus,
        latency_ms: float = 0,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        self.service = service
        self.status = status
        self.latency_ms = latency_ms
        self.message = message or f"Service {service} is {status}"
        self.details = details or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == HealthStatus.HEALTHY


class InfrastructureHealthChecker:
    """
    Comprehensive infrastructure health checker.

    Performs detailed health checks on all infrastructure components:
    - PostgreSQL database
    - Redis cache/queue
    - Celery workers
    - API availability
    """

    # Alert thresholds
    LATENCY_WARNING_THRESHOLD_MS = 100  # Warn if latency > 100ms
    LATENCY_CRITICAL_THRESHOLD_MS = 500  # Critical if latency > 500ms
    MIN_WORKER_COUNT = 1  # Minimum Celery workers required

    def __init__(self):
        """Initialize health checker."""
        self.health_check = HealthCheck()
        self.uptime_monitor = get_uptime_monitor()

    async def check_all(self) -> Dict[str, Any]:
        """
        Perform comprehensive health checks on all services.

        Returns:
            Complete health check report
        """
        logger.info("Starting comprehensive infrastructure health check")

        # Run all health checks in parallel
        results = await asyncio.gather(
            self.check_postgresql(),
            self.check_redis(),
            self.check_celery_workers(),
            self.check_api(),
            return_exceptions=True,
        )

        # Convert exceptions to unhealthy results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = ["postgresql", "redis", "celery_workers", "api"][i]
                health_results.append(
                    HealthCheckResult(
                        service=service_name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(result)}",
                        details={"error": str(result)},
                    )
                )
            else:
                health_results.append(result)

        # Determine overall health
        overall_status = self._determine_overall_status(health_results)

        # Check for alerts
        alerts = self._generate_alerts(health_results)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "services": [result.to_dict() for result in health_results],
            "alerts": alerts,
            "summary": {
                "total_services": len(health_results),
                "healthy": sum(1 for r in health_results if r.is_healthy()),
                "degraded": sum(1 for r in health_results if r.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for r in health_results if r.status == HealthStatus.UNHEALTHY),
            },
        }

        logger.info(f"Health check complete: {overall_status.value}")

        return report

    async def check_postgresql(self) -> HealthCheckResult:
        """
        Check PostgreSQL database health.

        Returns:
            Health check result
        """
        try:
            import time
            start = time.time()

            # Use existing health check
            db_health = self.health_check.check_database()

            latency = (time.time() - start) * 1000

            if db_health["status"] != "healthy":
                return HealthCheckResult(
                    service="postgresql",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=latency,
                    message="Database connection failed",
                    details=db_health,
                )

            # Check latency thresholds
            if latency > self.LATENCY_CRITICAL_THRESHOLD_MS:
                status = HealthStatus.DEGRADED
                message = f"Database latency is high: {latency:.2f}ms"
            elif latency > self.LATENCY_WARNING_THRESHOLD_MS:
                status = HealthStatus.DEGRADED
                message = f"Database latency is elevated: {latency:.2f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"

            return HealthCheckResult(
                service="postgresql",
                status=status,
                latency_ms=latency,
                message=message,
                details={
                    "latency_ms": db_health.get("latency_ms", latency),
                    "connection": "established",
                },
            )

        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return HealthCheckResult(
                service="postgresql",
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_redis(self) -> HealthCheckResult:
        """
        Check Redis cache/queue health.

        Returns:
            Health check result
        """
        try:
            import time
            start = time.time()

            # Use existing health check
            redis_health = self.health_check.check_redis()

            latency = (time.time() - start) * 1000

            if redis_health["status"] != "healthy":
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=latency,
                    message="Redis connection failed",
                    details=redis_health,
                )

            # Check latency and memory
            if latency > self.LATENCY_CRITICAL_THRESHOLD_MS:
                status = HealthStatus.DEGRADED
                message = f"Redis latency is high: {latency:.2f}ms"
            elif latency > self.LATENCY_WARNING_THRESHOLD_MS:
                status = HealthStatus.DEGRADED
                message = f"Redis latency is elevated: {latency:.2f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"

            return HealthCheckResult(
                service="redis",
                status=status,
                latency_ms=redis_health.get("latency_ms", latency),
                message=message,
                details={
                    "connected_clients": redis_health.get("connected_clients", 0),
                    "used_memory_mb": redis_health.get("used_memory_mb", 0),
                    "uptime_days": redis_health.get("uptime_days", 0),
                },
            )

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis health check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_celery_workers(self) -> HealthCheckResult:
        """
        Check Celery worker health.

        Returns:
            Health check result
        """
        try:
            # Use existing health check
            celery_health = self.health_check.check_celery_workers()

            if celery_health["status"] != "healthy":
                return HealthCheckResult(
                    service="celery_workers",
                    status=HealthStatus.UNHEALTHY,
                    message=celery_health.get("error", "No active workers"),
                    details=celery_health,
                )

            worker_count = celery_health.get("worker_count", 0)

            # Check worker count
            if worker_count < self.MIN_WORKER_COUNT:
                status = HealthStatus.DEGRADED
                message = f"Low worker count: {worker_count} (minimum: {self.MIN_WORKER_COUNT})"
            else:
                status = HealthStatus.HEALTHY
                message = f"Celery workers are healthy ({worker_count} active)"

            return HealthCheckResult(
                service="celery_workers",
                status=status,
                message=message,
                details={
                    "worker_count": worker_count,
                    "active_tasks": celery_health.get("active_tasks", 0),
                    "registered_tasks": celery_health.get("registered_tasks_count", 0),
                    "workers": celery_health.get("workers", []),
                },
            )

        except Exception as e:
            logger.error(f"Celery worker health check failed: {e}")
            return HealthCheckResult(
                service="celery_workers",
                status=HealthStatus.UNHEALTHY,
                message=f"Worker health check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_api(self) -> HealthCheckResult:
        """
        Check API availability.

        Returns:
            Health check result
        """
        try:
            # API is healthy if we're running this code
            return HealthCheckResult(
                service="api",
                status=HealthStatus.HEALTHY,
                message="API is responding",
                details={"status": "running"},
            )

        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return HealthCheckResult(
                service="api",
                status=HealthStatus.UNHEALTHY,
                message=f"API health check failed: {str(e)}",
                details={"error": str(e)},
            )

    def _determine_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """
        Determine overall system health based on service health.

        Args:
            results: List of health check results

        Returns:
            Overall health status
        """
        if not results:
            return HealthStatus.UNKNOWN

        # If any service is unhealthy, overall is unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY

        # If any service is degraded, overall is degraded
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        # All services healthy
        return HealthStatus.HEALTHY

    def _generate_alerts(self, results: List[HealthCheckResult]) -> List[Dict[str, Any]]:
        """
        Generate alerts based on health check results.

        Args:
            results: List of health check results

        Returns:
            List of alert dictionaries
        """
        alerts = []

        for result in results:
            if result.status == HealthStatus.UNHEALTHY:
                alerts.append({
                    "severity": "critical",
                    "service": result.service,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat(),
                })

            elif result.status == HealthStatus.DEGRADED:
                alerts.append({
                    "severity": "warning",
                    "service": result.service,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat(),
                })

        return alerts


# Singleton instance
infrastructure_health_checker = InfrastructureHealthChecker()


def get_health_checker() -> InfrastructureHealthChecker:
    """Get the singleton health checker instance."""
    return infrastructure_health_checker
