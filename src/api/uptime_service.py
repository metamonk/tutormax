"""
Uptime Monitoring Service

Tracks uptime for all system services to ensure >99.5% uptime SLA.
Records health check results and calculates uptime percentages.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_db_session
from src.workers.monitoring import HealthCheck

logger = logging.getLogger(__name__)


class ServiceStatus:
    """Service status constants."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class UptimeMonitor:
    """
    Monitor and track service uptime.

    Performs periodic health checks and stores results for SLA tracking.
    Target: >99.5% uptime per PRD requirements.
    """

    # Services to monitor
    SERVICES = {
        "api": "TutorMax API",
        "redis": "Redis Cache/Queue",
        "postgresql": "PostgreSQL Database",
        "celery_workers": "Celery Worker Pool",
    }

    # SLA target (99.5% uptime)
    SLA_TARGET = 99.5

    def __init__(self):
        """Initialize uptime monitor."""
        self.health_check = HealthCheck()

    async def perform_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health checks for all services.

        Returns:
            Dict mapping service names to health check results
        """
        results = {}

        # API is up if we're running this code
        results["api"] = {
            "service": "api",
            "status": ServiceStatus.UP,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": 0,
        }

        # Check Redis
        redis_health = self.health_check.check_redis()
        results["redis"] = {
            "service": "redis",
            "status": ServiceStatus.UP if redis_health["status"] == "healthy" else ServiceStatus.DOWN,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": redis_health.get("latency_ms", 0),
            "details": redis_health,
        }

        # Check PostgreSQL
        db_health = self.health_check.check_database()
        results["postgresql"] = {
            "service": "postgresql",
            "status": ServiceStatus.UP if db_health["status"] == "healthy" else ServiceStatus.DOWN,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": db_health.get("latency_ms", 0),
            "details": db_health,
        }

        # Check Celery workers
        celery_health = self.health_check.check_celery_workers()
        results["celery_workers"] = {
            "service": "celery_workers",
            "status": ServiceStatus.UP if celery_health["status"] == "healthy" else ServiceStatus.DOWN,
            "timestamp": datetime.utcnow().isoformat(),
            "details": celery_health,
        }

        return results

    async def record_health_check(self, service: str, status: str, latency_ms: float = 0, details: Optional[Dict] = None):
        """
        Record a health check result to the database.

        Args:
            service: Service name
            status: Service status (up/down/degraded)
            latency_ms: Response latency in milliseconds
            details: Additional details about the check
        """
        # Import here to avoid circular imports
        from src.database.models import ServiceHealthCheck

        async with get_db_session() as session:
            health_check = ServiceHealthCheck(
                service_name=service,
                status=status,
                latency_ms=latency_ms,
                details=details or {},
                checked_at=datetime.utcnow(),
            )
            session.add(health_check)
            await session.commit()

        logger.debug(f"Recorded health check for {service}: {status}")

    async def record_all_health_checks(self) -> Dict[str, Any]:
        """
        Perform and record health checks for all services.

        Returns:
            Summary of health checks
        """
        results = await self.perform_health_checks()

        # Record each result
        for service, result in results.items():
            await self.record_health_check(
                service=service,
                status=result["status"],
                latency_ms=result.get("latency_ms", 0),
                details=result.get("details"),
            )

        # Calculate overall status
        statuses = [r["status"] for r in results.values()]
        overall_status = ServiceStatus.UP if all(s == ServiceStatus.UP for s in statuses) else ServiceStatus.DEGRADED

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "services": results,
        }

    async def calculate_uptime(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculate uptime percentage for a service over a time period.

        Args:
            service: Service name
            start_time: Start of time period
            end_time: End of time period

        Returns:
            Uptime statistics
        """
        from src.database.models import ServiceHealthCheck

        async with get_db_session() as session:
            # Count total checks
            total_result = await session.execute(
                select(func.count(ServiceHealthCheck.id)).where(
                    and_(
                        ServiceHealthCheck.service_name == service,
                        ServiceHealthCheck.checked_at >= start_time,
                        ServiceHealthCheck.checked_at <= end_time,
                    )
                )
            )
            total_checks = total_result.scalar() or 0

            # Count successful checks (status = 'up')
            up_result = await session.execute(
                select(func.count(ServiceHealthCheck.id)).where(
                    and_(
                        ServiceHealthCheck.service_name == service,
                        ServiceHealthCheck.status == ServiceStatus.UP,
                        ServiceHealthCheck.checked_at >= start_time,
                        ServiceHealthCheck.checked_at <= end_time,
                    )
                )
            )
            up_checks = up_result.scalar() or 0

            # Calculate uptime percentage
            uptime_pct = (up_checks / total_checks * 100) if total_checks > 0 else 0

            # Get average latency for successful checks
            latency_result = await session.execute(
                select(func.avg(ServiceHealthCheck.latency_ms)).where(
                    and_(
                        ServiceHealthCheck.service_name == service,
                        ServiceHealthCheck.status == ServiceStatus.UP,
                        ServiceHealthCheck.checked_at >= start_time,
                        ServiceHealthCheck.checked_at <= end_time,
                    )
                )
            )
            avg_latency = latency_result.scalar() or 0

            return {
                "service": service,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "total_checks": total_checks,
                "successful_checks": up_checks,
                "failed_checks": total_checks - up_checks,
                "uptime_percentage": round(uptime_pct, 3),
                "meets_sla": uptime_pct >= self.SLA_TARGET,
                "sla_target": self.SLA_TARGET,
                "avg_latency_ms": round(avg_latency, 2),
            }

    async def get_uptime_report(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate uptime report for all services.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            Comprehensive uptime report
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        report = {
            "generated_at": end_time.isoformat(),
            "period_hours": hours,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "services": {},
            "overall_uptime": 0,
            "meets_sla": False,
        }

        # Calculate uptime for each service
        uptimes = []
        for service_key, service_name in self.SERVICES.items():
            uptime_data = await self.calculate_uptime(service_key, start_time, end_time)
            report["services"][service_key] = {
                "name": service_name,
                **uptime_data,
            }
            uptimes.append(uptime_data["uptime_percentage"])

        # Calculate overall uptime (average of all services)
        if uptimes:
            overall_uptime = sum(uptimes) / len(uptimes)
            report["overall_uptime"] = round(overall_uptime, 3)
            report["meets_sla"] = overall_uptime >= self.SLA_TARGET

        return report

    async def get_downtime_incidents(
        self,
        service: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get downtime incidents for services.

        Args:
            service: Specific service to check (None for all)
            hours: Number of hours to look back

        Returns:
            List of downtime incidents
        """
        from src.database.models import ServiceHealthCheck

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        async with get_db_session() as session:
            query = select(ServiceHealthCheck).where(
                and_(
                    ServiceHealthCheck.status != ServiceStatus.UP,
                    ServiceHealthCheck.checked_at >= start_time,
                    ServiceHealthCheck.checked_at <= end_time,
                )
            )

            if service:
                query = query.where(ServiceHealthCheck.service_name == service)

            query = query.order_by(ServiceHealthCheck.checked_at.desc())

            result = await session.execute(query)
            incidents = result.scalars().all()

            return [
                {
                    "id": incident.id,
                    "service": incident.service_name,
                    "status": incident.status,
                    "timestamp": incident.checked_at.isoformat(),
                    "latency_ms": incident.latency_ms,
                    "details": incident.details,
                }
                for incident in incidents
            ]


# Singleton instance
uptime_monitor = UptimeMonitor()


def get_uptime_monitor() -> UptimeMonitor:
    """Get the singleton uptime monitor instance."""
    return uptime_monitor
