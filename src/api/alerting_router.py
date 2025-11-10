"""
Alerting API Endpoints

Provides endpoints for managing alerts and testing alert delivery.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import logging

from src.api.alerting_service import (
    get_alerting_service,
    Alert,
    AlertSeverity,
    AlertType,
    AlertChannel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# ============================================================================
# Alert Management Endpoints
# ============================================================================

@router.post("/check")
async def run_alert_checks() -> Dict[str, Any]:
    """
    Manually trigger all alert checks.

    Checks:
    - SLA violations (insight latency, uptime, API response times)
    - Infrastructure health (Redis, PostgreSQL, Celery workers)
    - Performance degradation

    Returns:
        Summary of alerts generated and sent
    """
    try:
        alerting_service = get_alerting_service()
        return await alerting_service.run_all_checks()
    except Exception as e:
        logger.error(f"Failed to run alert checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def send_test_alert(
    channel: AlertChannel = Query(AlertChannel.LOG, description="Channel to test"),
    severity: AlertSeverity = Query(AlertSeverity.INFO, description="Alert severity")
) -> Dict[str, Any]:
    """
    Send a test alert to verify alerting configuration.

    Args:
        channel: Channel to test (email, slack, webhook, log)
        severity: Alert severity level

    Returns:
        Result of test alert
    """
    try:
        alerting_service = get_alerting_service()

        test_alert = Alert(
            title="Test Alert",
            message=f"This is a test alert sent via {channel.value}",
            severity=severity,
            alert_type=AlertType.INFO,
            details={
                "test": True,
                "channel": channel.value,
                "timestamp": "Test timestamp"
            },
            tags=["test"]
        )

        result = await alerting_service.send_alert(test_alert, channels=[channel])

        return {
            "success": True,
            "message": f"Test alert sent via {channel.value}",
            **result
        }

    except Exception as e:
        logger.error(f"Failed to send test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sla-violations")
async def check_sla_violations() -> Dict[str, Any]:
    """
    Check for SLA violations without sending alerts.

    Useful for monitoring dashboard.

    Returns:
        List of current SLA violations
    """
    try:
        alerting_service = get_alerting_service()
        violations = await alerting_service.check_sla_violations()

        return {
            "timestamp": violations[0].timestamp.isoformat() if violations else None,
            "total_violations": len(violations),
            "violations": [v.to_dict() for v in violations]
        }

    except Exception as e:
        logger.error(f"Failed to check SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure-issues")
async def check_infrastructure_issues() -> Dict[str, Any]:
    """
    Check for infrastructure issues without sending alerts.

    Useful for monitoring dashboard.

    Returns:
        List of current infrastructure issues
    """
    try:
        alerting_service = get_alerting_service()
        issues = await alerting_service.check_infrastructure_health()

        return {
            "timestamp": issues[0].timestamp.isoformat() if issues else None,
            "total_issues": len(issues),
            "issues": [i.to_dict() for i in issues]
        }

    except Exception as e:
        logger.error(f"Failed to check infrastructure issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-issues")
async def check_performance_issues() -> Dict[str, Any]:
    """
    Check for performance degradation without sending alerts.

    Useful for monitoring dashboard.

    Returns:
        List of current performance issues
    """
    try:
        alerting_service = get_alerting_service()
        issues = await alerting_service.check_performance_degradation()

        return {
            "timestamp": issues[0].timestamp.isoformat() if issues else None,
            "total_issues": len(issues),
            "issues": [i.to_dict() for i in issues]
        }

    except Exception as e:
        logger.error(f"Failed to check performance issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_custom_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    alert_type: AlertType = AlertType.PERFORMANCE_DEGRADATION,
    channels: List[AlertChannel] = None
) -> Dict[str, Any]:
    """
    Send a custom alert.

    Useful for manual alerts or integrations.

    Args:
        title: Alert title
        message: Alert message
        severity: Alert severity
        alert_type: Type of alert
        channels: Channels to use (defaults to all configured)

    Returns:
        Result of alert sending
    """
    try:
        alerting_service = get_alerting_service()

        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            alert_type=alert_type,
            tags=["custom"]
        )

        result = await alerting_service.send_alert(alert, channels=channels)

        return {
            "success": True,
            "message": "Custom alert sent",
            **result
        }

    except Exception as e:
        logger.error(f"Failed to send custom alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))
