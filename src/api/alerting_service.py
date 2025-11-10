"""
Alerting Service for SLA Violations and Infrastructure Failures

Provides multi-channel alerting for:
- SLA violations (insight latency, uptime, API response times)
- Error rate spikes (from Sentry)
- Infrastructure failures (Redis, PostgreSQL, Celery workers)
- Performance degradation

Supports: Email, Slack, Webhooks (PagerDuty compatible)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx
from sqlalchemy import select, and_

from src.api.config import settings
from src.database.database import get_db_session
from src.database.models import SLAMetric

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertChannel(str, Enum):
    """Alert notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"  # For PagerDuty, etc.
    LOG = "log"  # Just log, don't send


class AlertType(str, Enum):
    """Types of alerts."""
    SLA_VIOLATION = "sla_violation"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    ERROR_RATE_SPIKE = "error_rate_spike"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class Alert:
    """Represents an alert."""

    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        details: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        self.title = title
        self.message = message
        self.severity = severity
        self.alert_type = alert_type
        self.details = details or {}
        self.tags = tags or []
        self.timestamp = datetime.utcnow()
        self.alert_id = f"{alert_type.value}_{int(self.timestamp.timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "alert_type": self.alert_type.value,
            "details": self.details,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }


class AlertingService:
    """
    Service for sending alerts via multiple channels.

    Handles alert deduplication, rate limiting, and multi-channel delivery.
    """

    # Alert deduplication window (don't send same alert within this time)
    DEDUP_WINDOW_MINUTES = 15

    def __init__(self):
        """Initialize alerting service."""
        self.recent_alerts: Dict[str, datetime] = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def send_alert(
        self,
        alert: Alert,
        channels: Optional[List[AlertChannel]] = None
    ) -> Dict[str, Any]:
        """
        Send an alert via specified channels.

        Args:
            alert: Alert to send
            channels: List of channels to use (defaults to all configured)

        Returns:
            Result of alert sending
        """
        # Check for duplicate alerts
        if self._is_duplicate(alert):
            logger.info(f"Skipping duplicate alert: {alert.title}")
            return {
                "success": True,
                "message": "Alert deduplicated",
                "alert_id": alert.alert_id,
            }

        # Determine channels to use
        if channels is None:
            channels = self._get_configured_channels()

        # Send to all channels
        results = {}
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    result = await self._send_email(alert)
                elif channel == AlertChannel.SLACK:
                    result = await self._send_slack(alert)
                elif channel == AlertChannel.WEBHOOK:
                    result = await self._send_webhook(alert)
                elif channel == AlertChannel.LOG:
                    result = self._log_alert(alert)
                else:
                    result = {"success": False, "error": f"Unknown channel: {channel}"}

                results[channel.value] = result

            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                results[channel.value] = {"success": False, "error": str(e)}

        # Mark alert as sent
        self._mark_sent(alert)

        return {
            "success": any(r.get("success", False) for r in results.values()),
            "alert_id": alert.alert_id,
            "channels": results,
            "timestamp": alert.timestamp.isoformat(),
        }

    def _is_duplicate(self, alert: Alert) -> bool:
        """
        Check if alert is a duplicate.

        Args:
            alert: Alert to check

        Returns:
            True if duplicate, False otherwise
        """
        key = f"{alert.alert_type.value}_{alert.title}"

        if key in self.recent_alerts:
            last_sent = self.recent_alerts[key]
            time_since = datetime.utcnow() - last_sent

            if time_since < timedelta(minutes=self.DEDUP_WINDOW_MINUTES):
                return True

        return False

    def _mark_sent(self, alert: Alert):
        """Mark alert as sent for deduplication."""
        key = f"{alert.alert_type.value}_{alert.title}"
        self.recent_alerts[key] = alert.timestamp

    def _get_configured_channels(self) -> List[AlertChannel]:
        """Get list of configured alert channels."""
        channels = [AlertChannel.LOG]  # Always log

        # Check if email is configured
        if settings.smtp_host and settings.smtp_user:
            channels.append(AlertChannel.EMAIL)

        # Check if Slack is configured
        if getattr(settings, 'slack_webhook_url', None):
            channels.append(AlertChannel.SLACK)

        # Check if webhook is configured
        if getattr(settings, 'alert_webhook_url', None):
            channels.append(AlertChannel.WEBHOOK)

        return channels

    async def _send_email(self, alert: Alert) -> Dict[str, Any]:
        """
        Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            Send result
        """
        try:
            if not settings.smtp_host or not settings.smtp_user:
                return {"success": False, "error": "Email not configured"}

            # Get recipient email
            recipient = getattr(settings, 'alert_email', settings.smtp_from_email)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = settings.smtp_from_email or settings.smtp_user
            msg['To'] = recipient

            # Create HTML email body
            html = f"""
            <html>
                <body>
                    <h2 style="color: {'#e74c3c' if alert.severity == AlertSeverity.CRITICAL else '#f39c12'};">
                        {alert.title}
                    </h2>
                    <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                    <p><strong>Type:</strong> {alert.alert_type.value}</p>
                    <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>
                    <hr>
                    <p>{alert.message}</p>
                    <hr>
                    <h3>Details:</h3>
                    <pre>{json.dumps(alert.details, indent=2)}</pre>
                </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Sent email alert to {recipient}: {alert.title}")
            return {"success": True, "recipient": recipient}

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return {"success": False, "error": str(e)}

    async def _send_slack(self, alert: Alert) -> Dict[str, Any]:
        """
        Send alert to Slack via webhook.

        Args:
            alert: Alert to send

        Returns:
            Send result
        """
        try:
            slack_webhook_url = getattr(settings, 'slack_webhook_url', None)

            if not slack_webhook_url:
                return {"success": False, "error": "Slack webhook not configured"}

            # Determine color based on severity
            color = {
                AlertSeverity.CRITICAL: "#e74c3c",
                AlertSeverity.WARNING: "#f39c12",
                AlertSeverity.INFO: "#3498db",
            }.get(alert.severity, "#95a5a6")

            # Create Slack message
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Type",
                                "value": alert.alert_type.value,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": False
                            },
                        ],
                        "footer": "TutorMax Monitoring",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            # Add details if present
            if alert.details:
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": f"```{json.dumps(alert.details, indent=2)}```",
                    "short": False
                })

            # Send to Slack
            response = await self.http_client.post(
                slack_webhook_url,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"Sent Slack alert: {alert.title}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return {"success": False, "error": str(e)}

    async def _send_webhook(self, alert: Alert) -> Dict[str, Any]:
        """
        Send alert to webhook (PagerDuty compatible).

        Args:
            alert: Alert to send

        Returns:
            Send result
        """
        try:
            webhook_url = getattr(settings, 'alert_webhook_url', None)

            if not webhook_url:
                return {"success": False, "error": "Webhook not configured"}

            # Create PagerDuty-compatible payload
            payload = {
                "routing_key": getattr(settings, 'pagerduty_routing_key', ''),
                "event_action": "trigger",
                "payload": {
                    "summary": alert.title,
                    "severity": alert.severity.value,
                    "source": "TutorMax Monitoring",
                    "timestamp": alert.timestamp.isoformat(),
                    "custom_details": {
                        "message": alert.message,
                        "alert_type": alert.alert_type.value,
                        **alert.details
                    }
                }
            }

            # Send webhook
            response = await self.http_client.post(
                webhook_url,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"Sent webhook alert: {alert.title}")
            return {"success": True, "status_code": response.status_code}

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return {"success": False, "error": str(e)}

    def _log_alert(self, alert: Alert) -> Dict[str, Any]:
        """
        Log alert to application logs.

        Args:
            alert: Alert to log

        Returns:
            Log result
        """
        log_level = {
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.INFO: logging.INFO,
        }.get(alert.severity, logging.INFO)

        logger.log(
            log_level,
            f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}",
            extra={"alert_details": alert.details}
        )

        return {"success": True}

    async def check_sla_violations(self) -> List[Alert]:
        """
        Check for SLA violations and generate alerts.

        Returns:
            List of alerts generated
        """
        alerts = []

        try:
            # Check insight latency
            from src.api.sla_tracking_service import get_sla_tracking_service
            sla_service = get_sla_tracking_service()

            insight_latency = await sla_service.calculate_average_insight_latency(hours=1)

            if insight_latency["meets_sla_percentage"] < 95:
                alert = Alert(
                    title="Insight Latency SLA Violation",
                    message=f"Insight latency SLA compliance is {insight_latency['meets_sla_percentage']}% (target: 95%)",
                    severity=AlertSeverity.CRITICAL if insight_latency["meets_sla_percentage"] < 90 else AlertSeverity.WARNING,
                    alert_type=AlertType.SLA_VIOLATION,
                    details=insight_latency,
                    tags=["sla", "insight_latency"]
                )
                alerts.append(alert)

            # Check API response times
            api_stats = await sla_service.calculate_api_response_time_stats(hours=1)

            if not api_stats["meets_p95_sla"]:
                alert = Alert(
                    title="API Response Time SLA Violation (P95)",
                    message=f"API P95 response time is {api_stats['p95_ms']}ms (target: <{api_stats['p95_target_ms']}ms)",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.SLA_VIOLATION,
                    details=api_stats,
                    tags=["sla", "api_response_time", "p95"]
                )
                alerts.append(alert)

            if not api_stats["meets_p99_sla"]:
                alert = Alert(
                    title="API Response Time SLA Violation (P99)",
                    message=f"API P99 response time is {api_stats['p99_ms']}ms (target: <{api_stats['p99_target_ms']}ms)",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.SLA_VIOLATION,
                    details=api_stats,
                    tags=["sla", "api_response_time", "p99"]
                )
                alerts.append(alert)

            # Check uptime
            from src.api.uptime_service import get_uptime_monitor
            uptime_monitor = get_uptime_monitor()
            uptime_report = await uptime_monitor.get_uptime_report(hours=1)

            if not uptime_report["meets_sla"]:
                alert = Alert(
                    title="System Uptime SLA Violation",
                    message=f"System uptime is {uptime_report['overall_uptime']}% (target: >99.5%)",
                    severity=AlertSeverity.CRITICAL,
                    alert_type=AlertType.SLA_VIOLATION,
                    details=uptime_report,
                    tags=["sla", "uptime"]
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Failed to check SLA violations: {e}")

        return alerts

    async def check_infrastructure_health(self) -> List[Alert]:
        """
        Check infrastructure health and generate alerts.

        Returns:
            List of alerts generated
        """
        alerts = []

        try:
            from src.api.health_check_service import get_health_checker
            health_checker = get_health_checker()

            health_report = await health_checker.check_all()

            # Check for unhealthy or degraded services
            for service in health_report["services"]:
                if service["status"] == "unhealthy":
                    alert = Alert(
                        title=f"Infrastructure Failure: {service['service'].upper()}",
                        message=service["message"],
                        severity=AlertSeverity.CRITICAL,
                        alert_type=AlertType.INFRASTRUCTURE_FAILURE,
                        details=service,
                        tags=["infrastructure", service["service"]]
                    )
                    alerts.append(alert)

                elif service["status"] == "degraded":
                    alert = Alert(
                        title=f"Infrastructure Degraded: {service['service'].upper()}",
                        message=service["message"],
                        severity=AlertSeverity.WARNING,
                        alert_type=AlertType.INFRASTRUCTURE_FAILURE,
                        details=service,
                        tags=["infrastructure", service["service"]]
                    )
                    alerts.append(alert)

        except Exception as e:
            logger.error(f"Failed to check infrastructure health: {e}")

        return alerts

    async def check_performance_degradation(self) -> List[Alert]:
        """
        Check for performance degradation and generate alerts.

        Returns:
            List of alerts generated
        """
        alerts = []

        try:
            from src.api.performance_metrics_service import get_performance_metrics_service
            perf_service = get_performance_metrics_service()

            # Check Redis performance
            redis_metrics = perf_service.get_redis_performance()

            if redis_metrics.get("status") == "degraded":
                alert = Alert(
                    title="Redis Performance Degradation",
                    message=f"Redis hit rate is {redis_metrics['hit_rate_percentage']}% (target: >80%)",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.PERFORMANCE_DEGRADATION,
                    details=redis_metrics,
                    tags=["performance", "redis"]
                )
                alerts.append(alert)

            # Check database performance
            db_metrics = await perf_service.get_database_performance()

            if db_metrics.get("status") == "degraded":
                alert = Alert(
                    title="Database Performance Degradation",
                    message=f"Database cache hit ratio is {db_metrics.get('cache_hit_ratio', 0)}% (target: >90%)",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.PERFORMANCE_DEGRADATION,
                    details=db_metrics,
                    tags=["performance", "database"]
                )
                alerts.append(alert)

            # Check worker queues
            queue_metrics = perf_service.get_worker_queue_depths()

            if queue_metrics.get("total_backlog", 0) > 1000:
                alert = Alert(
                    title="Worker Queue Backlog High",
                    message=f"Total queue backlog is {queue_metrics['total_backlog']} (threshold: 1000)",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.PERFORMANCE_DEGRADATION,
                    details=queue_metrics,
                    tags=["performance", "workers", "queues"]
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Failed to check performance degradation: {e}")

        return alerts

    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all alert checks and send alerts.

        Returns:
            Summary of alerts generated and sent
        """
        all_alerts = []

        # Run all checks
        sla_alerts = await self.check_sla_violations()
        infra_alerts = await self.check_infrastructure_health()
        perf_alerts = await self.check_performance_degradation()

        all_alerts.extend(sla_alerts)
        all_alerts.extend(infra_alerts)
        all_alerts.extend(perf_alerts)

        # Send all alerts
        sent_results = []
        for alert in all_alerts:
            result = await self.send_alert(alert)
            sent_results.append(result)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_alerts": len(all_alerts),
            "sla_violations": len(sla_alerts),
            "infrastructure_failures": len(infra_alerts),
            "performance_degradations": len(perf_alerts),
            "alerts": [alert.to_dict() for alert in all_alerts],
            "sent_results": sent_results,
        }


# Singleton instance
alerting_service = AlertingService()


def get_alerting_service() -> AlertingService:
    """Get the singleton alerting service instance."""
    return alerting_service
