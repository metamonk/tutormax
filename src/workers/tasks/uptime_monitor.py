"""
Uptime Monitoring Celery Tasks

Periodic tasks for monitoring system uptime and SLA compliance.
Runs health checks every minute to track >99.5% uptime SLA.
"""

import logging
import asyncio
from celery import Task
from datetime import datetime

from src.workers.celery_app import celery_app
from src.api.uptime_service import get_uptime_monitor

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """
    Base task class for running async functions in Celery.
    """

    def __call__(self, *args, **kwargs):
        """Run the task with asyncio support."""
        return asyncio.get_event_loop().run_until_complete(
            self.run_async(*args, **kwargs)
        )

    async def run_async(self, *args, **kwargs):
        """Override this method with async implementation."""
        raise NotImplementedError


@celery_app.task(
    name="src.workers.tasks.uptime_monitor.record_health_checks",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def record_health_checks(self):
    """
    Perform and record health checks for all services.

    This task runs every minute to track service uptime for SLA compliance.
    Target: >99.5% uptime per PRD requirements.

    Monitors:
    - API availability
    - Redis health and latency
    - PostgreSQL health and latency
    - Celery worker status

    Returns:
        Dict with health check results
    """
    try:
        logger.info("Starting periodic health check")

        # Run async health check
        async def _run_health_check():
            uptime_monitor = get_uptime_monitor()
            return await uptime_monitor.record_all_health_checks()

        result = asyncio.run(_run_health_check())

        logger.info(f"Health check completed: {result['overall_status']}")

        # Log any service failures
        for service, data in result['services'].items():
            if data['status'] != 'up':
                logger.warning(
                    f"Service {service} is {data['status']}: {data.get('details', {})}"
                )

        return {
            "success": True,
            "timestamp": result["timestamp"],
            "overall_status": result["overall_status"],
            "services_checked": len(result["services"]),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 30, 300))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for health check")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


@celery_app.task(
    name="src.workers.tasks.uptime_monitor.generate_uptime_report",
    bind=True,
)
def generate_uptime_report(self, hours: int = 24):
    """
    Generate comprehensive uptime report for specified time period.

    Args:
        hours: Number of hours to analyze (default: 24)

    Returns:
        Dict with uptime report including SLA compliance status
    """
    try:
        logger.info(f"Generating {hours}-hour uptime report")

        async def _generate_report():
            uptime_monitor = get_uptime_monitor()
            return await uptime_monitor.get_uptime_report(hours=hours)

        report = asyncio.run(_generate_report())

        logger.info(
            f"Uptime report generated: {report['overall_uptime']}% uptime, "
            f"SLA {'met' if report['meets_sla'] else 'VIOLATED'}"
        )

        # Log SLA violations
        if not report['meets_sla']:
            logger.warning(
                f"SLA VIOLATION: Overall uptime {report['overall_uptime']}% "
                f"is below target {report.get('services', {}).get('api', {}).get('sla_target', 99.5)}%"
            )

            for service, data in report['services'].items():
                if not data.get('meets_sla', True):
                    logger.warning(
                        f"Service {service} failed SLA: {data['uptime_percentage']}% uptime"
                    )

        return report

    except Exception as e:
        logger.error(f"Failed to generate uptime report: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    name="src.workers.tasks.uptime_monitor.check_sla_compliance",
    bind=True,
)
def check_sla_compliance(self, hours: int = 24):
    """
    Check SLA compliance and alert on violations.

    Checks if services meet SLA targets:
    - >99.5% uptime
    - <60 minutes insight latency
    - API response times within thresholds

    Args:
        hours: Number of hours to analyze (default: 24)

    Returns:
        Dict with SLA compliance status
    """
    try:
        logger.info(f"Checking SLA compliance for last {hours} hours")

        # Generate uptime report
        report = generate_uptime_report.apply(kwargs={"hours": hours}).get()

        if not report.get('success', True):
            logger.error(f"Failed to check SLA compliance: {report.get('error')}")
            return report

        sla_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "overall_uptime": report['overall_uptime'],
            "meets_sla": report['meets_sla'],
            "violations": [],
        }

        # Check for violations
        if not report['meets_sla']:
            for service, data in report['services'].items():
                if not data.get('meets_sla', True):
                    violation = {
                        "service": service,
                        "uptime_percentage": data['uptime_percentage'],
                        "sla_target": data.get('sla_target', 99.5),
                        "failed_checks": data['failed_checks'],
                    }
                    sla_status['violations'].append(violation)

                    logger.warning(
                        f"SLA VIOLATION for {service}: {data['uptime_percentage']}% uptime "
                        f"(target: {data.get('sla_target', 99.5)}%)"
                    )

            # Future enhancement: Automate SLA violation alerts
            # When violations are detected, automatically notify operations team via:
            # 1. Email using email_service.py - send to operations managers
            # 2. Slack webhook - post to #ops-alerts channel
            # 3. PagerDuty - create incident for critical services (API, Database)
            # 4. Update dashboard with red alert banner
            #
            # Implementation example:
            #   from src.api.alert_service import AlertService
            #   alert_service = AlertService()
            #   for violation in sla_status['violations']:
            #       await alert_service.create_alert(
            #           alert_type="SLA_VIOLATION",
            #           severity="high" if violation['uptime'] < 99% else "medium",
            #           title=f"SLA Violation: {violation['service']}",
            #           description=f"Uptime: {violation['uptime']}% (Target: {violation['target']}%)"
            #       )

        return sla_status

    except Exception as e:
        logger.error(f"Failed to check SLA compliance: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    name="src.workers.tasks.uptime_monitor.cleanup_old_health_checks",
    bind=True,
)
def cleanup_old_health_checks(self, days_to_keep: int = 30):
    """
    Clean up old health check records from database.

    Keeps only the most recent data to prevent database bloat.

    Args:
        days_to_keep: Number of days of data to retain (default: 30)

    Returns:
        Dict with cleanup results
    """
    try:
        from datetime import timedelta
        from sqlalchemy import select, delete
        from src.database.models import ServiceHealthCheck
        from src.database.database import get_db_session

        logger.info(f"Cleaning up health check records older than {days_to_keep} days")

        async def _cleanup():
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            async with get_db_session() as session:
                # Delete old records
                stmt = delete(ServiceHealthCheck).where(
                    ServiceHealthCheck.checked_at < cutoff_date
                )
                result = await session.execute(stmt)
                await session.commit()

                deleted_count = result.rowcount
                return deleted_count

        deleted_count = asyncio.run(_cleanup())

        logger.info(f"Cleanup completed: deleted {deleted_count} old health check records")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_days": days_to_keep,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old health checks: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
