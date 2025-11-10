"""
SLA Tracking Service

Tracks and calculates SLA metrics for the TutorMax system:
- Insight Latency: Time from session end to dashboard update (<60 min target)
- API Response Times: p50, p95, p99 percentiles
- System Uptime: Overall system availability (>99.5% target)
- Data Processing Latency: Time to process incoming data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import statistics

from src.database.database import get_db_session
from src.database.models import SLAMetric, Session, TutorPerformanceMetric

logger = logging.getLogger(__name__)


class SLATrackingService:
    """
    Service for tracking and calculating SLA metrics.

    Key SLAs:
    - Insight Latency: <60 minutes from session end to dashboard update
    - System Uptime: >99.5%
    - API Response Time: p95 < 500ms, p99 < 1000ms
    """

    # SLA Targets from PRD
    INSIGHT_LATENCY_TARGET_MINUTES = 60  # PRD requirement
    UPTIME_TARGET_PERCENTAGE = 99.5  # PRD requirement
    API_P95_TARGET_MS = 500
    API_P99_TARGET_MS = 1000

    async def track_insight_latency(
        self,
        session_id: str,
        session_end_time: datetime,
        dashboard_update_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Track insight latency for a session.

        Insight latency is the time from session end to when performance
        metrics appear on the dashboard.

        Args:
            session_id: Session identifier
            session_end_time: When the session ended
            dashboard_update_time: When metrics were updated (defaults to now)

        Returns:
            Latency tracking result
        """
        if dashboard_update_time is None:
            dashboard_update_time = datetime.utcnow()

        # Calculate latency
        latency = dashboard_update_time - session_end_time
        latency_minutes = latency.total_seconds() / 60

        meets_sla = latency_minutes < self.INSIGHT_LATENCY_TARGET_MINUTES

        # Store SLA metric
        await self.record_sla_metric(
            metric_name="insight_latency",
            metric_value=latency_minutes,
            metric_unit="minutes",
            threshold=self.INSIGHT_LATENCY_TARGET_MINUTES,
            meets_sla=meets_sla,
            details={
                "session_id": session_id,
                "session_end_time": session_end_time.isoformat(),
                "dashboard_update_time": dashboard_update_time.isoformat(),
                "latency_seconds": latency.total_seconds(),
            }
        )

        if not meets_sla:
            logger.warning(
                f"Insight latency SLA violation for session {session_id}: "
                f"{latency_minutes:.2f} minutes (target: {self.INSIGHT_LATENCY_TARGET_MINUTES})"
            )

        return {
            "session_id": session_id,
            "latency_minutes": round(latency_minutes, 2),
            "latency_seconds": latency.total_seconds(),
            "meets_sla": meets_sla,
            "sla_target_minutes": self.INSIGHT_LATENCY_TARGET_MINUTES,
            "session_end_time": session_end_time.isoformat(),
            "dashboard_update_time": dashboard_update_time.isoformat(),
        }

    async def calculate_average_insight_latency(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Calculate average insight latency over a time period.

        Args:
            hours: Number of hours to analyze

        Returns:
            Average latency statistics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        async with get_db_session() as session:
            # Get all insight latency metrics in the time period
            result = await session.execute(
                select(SLAMetric).where(
                    and_(
                        SLAMetric.metric_name == "insight_latency",
                        SLAMetric.recorded_at >= start_time,
                        SLAMetric.recorded_at <= end_time,
                    )
                )
            )
            metrics = result.scalars().all()

            if not metrics:
                return {
                    "period_hours": hours,
                    "sample_count": 0,
                    "average_latency_minutes": 0,
                    "min_latency_minutes": 0,
                    "max_latency_minutes": 0,
                    "meets_sla_percentage": 100,
                    "sla_target_minutes": self.INSIGHT_LATENCY_TARGET_MINUTES,
                }

            latencies = [m.metric_value for m in metrics]
            meets_sla_count = sum(1 for m in metrics if m.meets_sla)

            return {
                "period_hours": hours,
                "sample_count": len(metrics),
                "average_latency_minutes": round(statistics.mean(latencies), 2),
                "median_latency_minutes": round(statistics.median(latencies), 2),
                "min_latency_minutes": round(min(latencies), 2),
                "max_latency_minutes": round(max(latencies), 2),
                "p95_latency_minutes": round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) > 1 else round(latencies[0], 2),
                "p99_latency_minutes": round(statistics.quantiles(latencies, n=100)[98], 2) if len(latencies) > 1 else round(latencies[0], 2),
                "meets_sla_count": meets_sla_count,
                "violates_sla_count": len(metrics) - meets_sla_count,
                "meets_sla_percentage": round((meets_sla_count / len(metrics)) * 100, 2),
                "sla_target_minutes": self.INSIGHT_LATENCY_TARGET_MINUTES,
            }

    async def track_api_response_time(
        self,
        endpoint: str,
        response_time_ms: float,
        status_code: int
    ) -> Dict[str, Any]:
        """
        Track API response time for SLA monitoring.

        Args:
            endpoint: API endpoint path
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code

        Returns:
            Tracking result
        """
        # Determine if it meets SLA based on p95/p99 targets
        # For individual requests, we just record; aggregation determines SLA compliance
        meets_sla = response_time_ms < self.API_P95_TARGET_MS

        await self.record_sla_metric(
            metric_name=f"api_response_time_{endpoint}",
            metric_value=response_time_ms,
            metric_unit="milliseconds",
            threshold=self.API_P95_TARGET_MS,
            meets_sla=meets_sla,
            details={
                "endpoint": endpoint,
                "status_code": status_code,
            }
        )

        return {
            "endpoint": endpoint,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "meets_sla": meets_sla,
        }

    async def calculate_api_response_time_stats(
        self,
        endpoint: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Calculate API response time statistics.

        Args:
            endpoint: Specific endpoint to analyze (None for all)
            hours: Number of hours to analyze

        Returns:
            Response time statistics with p50, p95, p99
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        async with get_db_session() as session:
            query = select(SLAMetric).where(
                and_(
                    SLAMetric.metric_name.like("api_response_time_%"),
                    SLAMetric.recorded_at >= start_time,
                    SLAMetric.recorded_at <= end_time,
                )
            )

            if endpoint:
                query = query.where(SLAMetric.metric_name == f"api_response_time_{endpoint}")

            result = await session.execute(query)
            metrics = result.scalars().all()

            if not metrics:
                return {
                    "period_hours": hours,
                    "endpoint": endpoint or "all",
                    "sample_count": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "average_ms": 0,
                    "meets_p95_sla": True,
                    "meets_p99_sla": True,
                }

            response_times = [m.metric_value for m in metrics]

            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0]
            p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 1 else response_times[0]

            return {
                "period_hours": hours,
                "endpoint": endpoint or "all",
                "sample_count": len(metrics),
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "average_ms": round(statistics.mean(response_times), 2),
                "min_ms": round(min(response_times), 2),
                "max_ms": round(max(response_times), 2),
                "meets_p95_sla": p95 < self.API_P95_TARGET_MS,
                "meets_p99_sla": p99 < self.API_P99_TARGET_MS,
                "p95_target_ms": self.API_P95_TARGET_MS,
                "p99_target_ms": self.API_P99_TARGET_MS,
            }

    async def record_sla_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        threshold: Optional[float] = None,
        meets_sla: bool = True,
        details: Optional[Dict] = None
    ) -> None:
        """
        Record an SLA metric to the database.

        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            metric_unit: Unit of measurement
            threshold: SLA threshold value
            meets_sla: Whether the metric meets SLA
            details: Additional details
        """
        async with get_db_session() as session:
            metric = SLAMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                threshold=threshold,
                meets_sla=meets_sla,
                details=details or {},
                recorded_at=datetime.utcnow(),
            )
            session.add(metric)
            await session.commit()

    async def get_sla_dashboard_data(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive SLA dashboard data.

        Args:
            hours: Number of hours to analyze

        Returns:
            Complete SLA dashboard data
        """
        # Get insight latency stats
        insight_latency = await self.calculate_average_insight_latency(hours)

        # Get API response time stats
        api_stats = await self.calculate_api_response_time_stats(hours=hours)

        # Get uptime data from uptime monitor
        from src.api.uptime_service import get_uptime_monitor
        uptime_monitor = get_uptime_monitor()
        uptime_report = await uptime_monitor.get_uptime_report(hours=hours)

        # Calculate overall SLA compliance
        sla_compliance = {
            "insight_latency": insight_latency["meets_sla_percentage"] >= 95,  # 95% of insights must be < 60 min
            "uptime": uptime_report["meets_sla"],
            "api_response_time_p95": api_stats["meets_p95_sla"],
            "api_response_time_p99": api_stats["meets_p99_sla"],
        }

        overall_sla_met = all(sla_compliance.values())

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "overall_sla_met": overall_sla_met,
            "sla_compliance": sla_compliance,
            "insight_latency": insight_latency,
            "api_response_times": api_stats,
            "system_uptime": {
                "overall_uptime": uptime_report["overall_uptime"],
                "meets_sla": uptime_report["meets_sla"],
                "target": uptime_report.get("services", {}).get("api", {}).get("sla_target", 99.5),
            },
        }

    async def get_sla_violations(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get all SLA violations in the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of SLA violations
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        async with get_db_session() as session:
            result = await session.execute(
                select(SLAMetric).where(
                    and_(
                        SLAMetric.meets_sla == False,
                        SLAMetric.recorded_at >= start_time,
                        SLAMetric.recorded_at <= end_time,
                    )
                ).order_by(SLAMetric.recorded_at.desc())
            )
            violations = result.scalars().all()

            return [
                {
                    "metric_name": v.metric_name,
                    "metric_value": v.metric_value,
                    "metric_unit": v.metric_unit,
                    "threshold": v.threshold,
                    "timestamp": v.recorded_at.isoformat(),
                    "details": v.details,
                }
                for v in violations
            ]


# Singleton instance
sla_tracking_service = SLATrackingService()


def get_sla_tracking_service() -> SLATrackingService:
    """Get the singleton SLA tracking service instance."""
    return sla_tracking_service
