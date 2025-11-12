"""
Alert Service for Operations Dashboard

Generates alerts and intervention tasks based on tutor performance metrics.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from src.database.models import TutorPerformanceMetric

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for generating alerts and intervention tasks based on performance metrics.
    """

    # Alert thresholds
    CRITICAL_RATING_THRESHOLD = 3.0
    WARNING_RATING_THRESHOLD = 4.0
    CRITICAL_RESCHEDULE_RATE = 0.3
    WARNING_RESCHEDULE_RATE = 0.2
    CRITICAL_NO_SHOW_COUNT = 5
    WARNING_NO_SHOW_COUNT = 3
    CRITICAL_ENGAGEMENT_THRESHOLD = 60.0
    WARNING_ENGAGEMENT_THRESHOLD = 70.0

    @staticmethod
    def generate_alerts(metric: TutorPerformanceMetric, tutor_name: str) -> List[Dict[str, Any]]:
        """
        Generate alerts based on performance metrics.

        Args:
            metric: TutorPerformanceMetric instance
            tutor_name: Name of the tutor

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Low rating alert
        if metric.avg_rating <= AlertService.CRITICAL_RATING_THRESHOLD:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "critical",
                "severity": "high",
                "title": "Critical: Very Low Average Rating",
                "message": f"Average rating has dropped to {metric.avg_rating:.2f}. Immediate intervention required.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "avg_rating": metric.avg_rating,
                    "sessions_completed": metric.sessions_completed,
                    "performance_tier": metric.performance_tier,
                },
            })
        elif metric.avg_rating <= AlertService.WARNING_RATING_THRESHOLD:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "warning",
                "severity": "medium",
                "title": "Warning: Low Average Rating",
                "message": f"Average rating is {metric.avg_rating:.2f}. Consider providing coaching support.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "avg_rating": metric.avg_rating,
                    "sessions_completed": metric.sessions_completed,
                },
            })

        # High reschedule rate alert
        if metric.reschedule_rate >= AlertService.CRITICAL_RESCHEDULE_RATE:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "critical",
                "severity": "high",
                "title": "Critical: High Reschedule Rate",
                "message": f"Reschedule rate is {metric.reschedule_rate * 100:.1f}%. Investigate scheduling issues.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "reschedule_rate": f"{metric.reschedule_rate * 100:.1f}%",
                    "sessions_completed": metric.sessions_completed,
                },
            })
        elif metric.reschedule_rate >= AlertService.WARNING_RESCHEDULE_RATE:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "warning",
                "severity": "medium",
                "title": "Warning: Elevated Reschedule Rate",
                "message": f"Reschedule rate is {metric.reschedule_rate * 100:.1f}%. Monitor scheduling patterns.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "reschedule_rate": f"{metric.reschedule_rate * 100:.1f}%",
                },
            })

        # High no-show count alert
        if metric.no_show_count >= AlertService.CRITICAL_NO_SHOW_COUNT:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "critical",
                "severity": "high",
                "title": "Critical: High No-Show Count",
                "message": f"{metric.no_show_count} no-shows in {metric.window} window. Review attendance patterns.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "no_show_count": metric.no_show_count,
                    "window": metric.window,
                },
            })
        elif metric.no_show_count >= AlertService.WARNING_NO_SHOW_COUNT:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "warning",
                "severity": "medium",
                "title": "Warning: Multiple No-Shows",
                "message": f"{metric.no_show_count} no-shows detected. Follow up required.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "no_show_count": metric.no_show_count,
                },
            })

        # Low engagement alert
        if metric.engagement_score <= AlertService.CRITICAL_ENGAGEMENT_THRESHOLD:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "critical",
                "severity": "high",
                "title": "Critical: Very Low Engagement Score",
                "message": f"Engagement score is {metric.engagement_score:.1f}. Student engagement is suffering.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "engagement_score": metric.engagement_score,
                    "performance_tier": metric.performance_tier,
                },
            })
        elif metric.engagement_score <= AlertService.WARNING_ENGAGEMENT_THRESHOLD:
            alerts.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "alert_type": "warning",
                "severity": "medium",
                "title": "Warning: Low Engagement Score",
                "message": f"Engagement score is {metric.engagement_score:.1f}. Consider engagement training.",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "metrics": {
                    "engagement_score": metric.engagement_score,
                },
            })

        return alerts

    @staticmethod
    def generate_intervention_tasks(
        metric: TutorPerformanceMetric,
        tutor_name: str,
        alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate intervention tasks based on alerts and metrics.

        Args:
            metric: TutorPerformanceMetric instance
            tutor_name: Name of the tutor
            alerts: List of alerts generated for this tutor

        Returns:
            List of intervention task dictionaries
        """
        tasks = []

        # Performance tier-based interventions
        if metric.performance_tier == "Needs Attention":
            tasks.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "task_type": "coaching",
                "title": "Comprehensive Performance Coaching",
                "description": f"Provide intensive coaching session to address low performance tier. Focus on rating improvement, engagement, and scheduling reliability.",
                "priority": "high",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now().replace(hour=23, minute=59, second=59)).isoformat(),
                "assigned_to": "Performance Coach",
            })

        elif metric.performance_tier == "Developing":
            tasks.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "task_type": "training",
                "title": "Skills Development Training",
                "description": f"Schedule training session to help tutor advance to 'Strong' tier. Focus on identified weak areas.",
                "priority": "medium",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now().replace(hour=23, minute=59, second=59)).isoformat(),
                "assigned_to": "Training Team",
            })

        # Alert-specific interventions
        if any(alert["alert_type"] == "critical" for alert in alerts):
            tasks.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "task_type": "review",
                "title": "Urgent Performance Review",
                "description": f"Conduct urgent review meeting to discuss critical alerts and create action plan.",
                "priority": "high",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now().replace(hour=23, minute=59, second=59)).isoformat(),
                "assigned_to": "Performance Manager",
            })

        # Follow-up task for tutors with warnings
        if any(alert["alert_type"] == "warning" for alert in alerts):
            tasks.append({
                "id": str(uuid.uuid4()),
                "tutor_id": metric.tutor_id,
                "tutor_name": tutor_name,
                "task_type": "followup",
                "title": "Performance Check-In",
                "description": f"Schedule follow-up meeting to discuss recent warnings and provide support.",
                "priority": "medium",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now().replace(hour=23, minute=59, second=59)).isoformat(),
                "assigned_to": "Team Lead",
            })

        return tasks


# Singleton instance
alert_service = AlertService()


def get_alert_service() -> AlertService:
    """
    Get the singleton alert service instance.
    """
    return alert_service
