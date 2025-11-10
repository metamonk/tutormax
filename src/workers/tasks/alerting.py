"""
Alerting Celery Tasks

Periodic tasks for checking and sending alerts for:
- SLA violations
- Infrastructure failures
- Performance degradation
"""

import logging
import asyncio
from datetime import datetime

from src.workers.celery_app import celery_app
from src.api.alerting_service import get_alerting_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="src.workers.tasks.alerting.check_and_send_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_and_send_alerts(self):
    """
    Check for SLA violations, infrastructure failures, and performance issues.
    Send alerts via configured channels (email, Slack, webhooks).

    This task runs every 5 minutes to ensure timely alerting.

    Returns:
        Dict with alert check results
    """
    try:
        logger.info("Starting alert check")

        async def _run_checks():
            alerting_service = get_alerting_service()
            return await alerting_service.run_all_checks()

        result = asyncio.run(_run_checks())

        if result["total_alerts"] > 0:
            logger.warning(
                f"Generated {result['total_alerts']} alerts: "
                f"{result['sla_violations']} SLA violations, "
                f"{result['infrastructure_failures']} infrastructure failures, "
                f"{result['performance_degradations']} performance issues"
            )
        else:
            logger.info("Alert check completed: no issues detected")

        return {
            "success": True,
            "timestamp": result["timestamp"],
            "total_alerts": result["total_alerts"],
            "sla_violations": result["sla_violations"],
            "infrastructure_failures": result["infrastructure_failures"],
            "performance_degradations": result["performance_degradations"],
        }

    except Exception as e:
        logger.error(f"Alert check failed: {e}", exc_info=True)

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 60, 300))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for alert check")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


@celery_app.task(
    name="src.workers.tasks.alerting.check_sla_violations",
    bind=True,
)
def check_sla_violations(self):
    """
    Check specifically for SLA violations.

    Runs every 5 minutes for faster SLA violation detection.

    Returns:
        Dict with SLA violation check results
    """
    try:
        logger.info("Checking for SLA violations")

        async def _check():
            alerting_service = get_alerting_service()
            violations = await alerting_service.check_sla_violations()

            # Send alerts for violations
            for violation in violations:
                await alerting_service.send_alert(violation)

            return violations

        violations = asyncio.run(_check())

        if violations:
            logger.warning(f"Found {len(violations)} SLA violations")

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "violations_count": len(violations),
            "violations": [v.to_dict() for v in violations],
        }

    except Exception as e:
        logger.error(f"SLA violation check failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    name="src.workers.tasks.alerting.check_infrastructure",
    bind=True,
)
def check_infrastructure(self):
    """
    Check specifically for infrastructure health issues.

    Runs every 2 minutes for faster infrastructure failure detection.

    Returns:
        Dict with infrastructure check results
    """
    try:
        logger.info("Checking infrastructure health")

        async def _check():
            alerting_service = get_alerting_service()
            issues = await alerting_service.check_infrastructure_health()

            # Send alerts for critical issues
            for issue in issues:
                if issue.severity == "critical":
                    await alerting_service.send_alert(issue)

            return issues

        issues = asyncio.run(_check())

        if issues:
            critical = sum(1 for i in issues if i.severity.value == "critical")
            logger.warning(
                f"Found {len(issues)} infrastructure issues ({critical} critical)"
            )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "issues_count": len(issues),
            "critical_count": sum(1 for i in issues if i.severity.value == "critical"),
        }

    except Exception as e:
        logger.error(f"Infrastructure check failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
