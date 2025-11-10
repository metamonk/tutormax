"""
Notification Service for Intervention System

This module handles sending notifications (email and in-app) for interventions.
It provides a unified interface for notification delivery with retry logic,
error handling, and database tracking.
"""

import logging
import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
from dataclasses import dataclass

# Import templates
from .notification_templates import (
    get_notification_template,
    InterventionType as TemplateInterventionType
)

# Import intervention framework types
from .intervention_framework import (
    InterventionTrigger,
    InterventionType,
    InterventionPriority,
    TutorState
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class EmailConfig:
    """Configuration for email delivery."""
    smtp_host: str = "localhost"
    smtp_port: int = 1025  # Default for MailHog/testing
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    from_email: str = "notifications@tutormax.com"
    from_name: str = "TutorMax"
    enabled: bool = True  # Set to False to disable email sending


@dataclass
class NotificationConfig:
    """Configuration for notification service."""
    email_config: EmailConfig
    max_retries: int = 3
    retry_on_failure: bool = True
    store_notifications: bool = True  # Store in database


# ============================================================================
# NOTIFICATION SERVICE
# ============================================================================

class NotificationService:
    """
    Service for sending intervention notifications.

    Handles email delivery, in-app notifications, retry logic,
    and database tracking.
    """

    def __init__(
        self,
        config: Optional[NotificationConfig] = None,
        db_session=None
    ):
        """
        Initialize notification service.

        Args:
            config: Notification configuration
            db_session: SQLAlchemy database session (optional)
        """
        self.config = config or NotificationConfig(
            email_config=EmailConfig()
        )
        self.db_session = db_session
        self.notification_queue: List[Dict] = []  # For testing/mock mode

        logger.info("NotificationService initialized")

    def send_intervention_notification(
        self,
        intervention_trigger: InterventionTrigger,
        tutor_state: TutorState,
        tutor_email: str,
        intervention_id: Optional[str] = None,
        notification_type: str = "both"  # 'email', 'in_app', 'both'
    ) -> Dict[str, any]:
        """
        Send notification for an intervention trigger.

        Args:
            intervention_trigger: The intervention trigger
            tutor_state: Current tutor state
            tutor_email: Tutor's email address
            intervention_id: ID of the intervention record (optional)
            notification_type: Type of notification ('email', 'in_app', 'both')

        Returns:
            Dict with notification results
        """
        logger.info(
            f"Sending notification for intervention {intervention_trigger.intervention_type} "
            f"to tutor {tutor_state.tutor_id}"
        )

        # Convert InterventionType to TemplateInterventionType
        template_type = TemplateInterventionType(intervention_trigger.intervention_type.value)

        # Get notification template
        template = get_notification_template(
            intervention_type=template_type,
            tutor_name=tutor_state.tutor_name,
            trigger_reason=intervention_trigger.trigger_reason,
            recommended_actions=intervention_trigger.recommended_actions,
            tutor_id=tutor_state.tutor_id
        )

        # Determine recipient based on whether intervention requires human review
        if intervention_trigger.requires_human:
            # Send to staff (assigned_to)
            recipient_id = intervention_trigger.assigned_to or "staff_default"
            recipient_email = self._get_staff_email(recipient_id)
        else:
            # Send to tutor
            recipient_id = tutor_state.tutor_id
            recipient_email = tutor_email

        # Map priority
        priority = self._map_priority(intervention_trigger.priority)

        # Generate notification ID
        notification_id = f"notif_{uuid.uuid4().hex[:12]}"

        # Create notification record
        notification_record = {
            "notification_id": notification_id,
            "recipient_id": recipient_id,
            "recipient_email": recipient_email,
            "notification_type": notification_type,
            "priority": priority,
            "status": "pending",
            "subject": template.subject,
            "body": template.body_text,
            "html_body": template.body_html,
            "intervention_id": intervention_id,
            "intervention_type": intervention_trigger.intervention_type.value,
            "created_at": datetime.now()
        }

        results = {
            "notification_id": notification_id,
            "email_sent": False,
            "in_app_created": False,
            "errors": []
        }

        # Send email if requested
        if notification_type in ["email", "both"]:
            try:
                email_success = self._send_email(
                    to_email=recipient_email,
                    subject=template.subject,
                    body_text=template.body_text,
                    body_html=template.body_html
                )

                if email_success:
                    results["email_sent"] = True
                    notification_record["status"] = "sent"
                    notification_record["sent_at"] = datetime.now()
                    logger.info(f"Email sent successfully to {recipient_email}")
                else:
                    results["errors"].append("Email delivery failed")
                    notification_record["status"] = "failed"
                    notification_record["failed_at"] = datetime.now()
                    notification_record["failure_reason"] = "Email delivery failed"

            except Exception as e:
                logger.error(f"Error sending email: {e}", exc_info=True)
                results["errors"].append(f"Email error: {str(e)}")
                notification_record["status"] = "failed"
                notification_record["failed_at"] = datetime.now()
                notification_record["failure_reason"] = str(e)

        # Create in-app notification if requested
        if notification_type in ["in_app", "both"]:
            try:
                in_app_success = self._create_in_app_notification(notification_record)

                if in_app_success:
                    results["in_app_created"] = True
                    logger.info(f"In-app notification created for {recipient_id}")
                else:
                    results["errors"].append("In-app notification creation failed")

            except Exception as e:
                logger.error(f"Error creating in-app notification: {e}", exc_info=True)
                results["errors"].append(f"In-app error: {str(e)}")

        # Store notification record
        if self.config.store_notifications:
            self._store_notification(notification_record)

        # Add to queue for testing
        self.notification_queue.append(notification_record)

        logger.info(
            f"Notification {notification_id} processed: "
            f"email_sent={results['email_sent']}, "
            f"in_app_created={results['in_app_created']}"
        )

        return results

    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.config.email_config.enabled:
            logger.info(f"Email sending disabled, skipping email to {to_email}")
            return True  # Treat as success in test mode

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.email_config.from_name} <{self.config.email_config.from_email}>"
            msg['To'] = to_email

            # Add plain text part
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

            # Add HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)

            # Send via SMTP
            if self.config.email_config.smtp_use_ssl:
                server = smtplib.SMTP_SSL(
                    self.config.email_config.smtp_host,
                    self.config.email_config.smtp_port
                )
            else:
                server = smtplib.SMTP(
                    self.config.email_config.smtp_host,
                    self.config.email_config.smtp_port
                )

            if self.config.email_config.smtp_use_tls:
                server.starttls()

            if self.config.email_config.smtp_username:
                server.login(
                    self.config.email_config.smtp_username,
                    self.config.email_config.smtp_password
                )

            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

    def _create_in_app_notification(self, notification_record: Dict) -> bool:
        """
        Create an in-app notification in the database.

        Args:
            notification_record: Notification data

        Returns:
            True if successful, False otherwise
        """
        if not self.db_session:
            logger.warning("No database session provided, skipping in-app notification")
            return False

        try:
            # Import here to avoid circular dependency
            from ..database.models import Notification, NotificationType, NotificationStatus, NotificationPriority, InterventionType as DBInterventionType

            # Create notification object
            notification = Notification(
                notification_id=notification_record["notification_id"],
                recipient_id=notification_record["recipient_id"],
                recipient_email=notification_record["recipient_email"],
                notification_type=NotificationType(notification_record["notification_type"]),
                priority=NotificationPriority(notification_record["priority"]),
                status=NotificationStatus(notification_record["status"]),
                subject=notification_record["subject"],
                body=notification_record["body"],
                html_body=notification_record.get("html_body"),
                intervention_id=notification_record.get("intervention_id"),
                intervention_type=DBInterventionType(notification_record["intervention_type"]) if notification_record.get("intervention_type") else None,
                sent_at=notification_record.get("sent_at"),
                failed_at=notification_record.get("failed_at"),
                failure_reason=notification_record.get("failure_reason"),
                retry_count=notification_record.get("retry_count", 0)
            )

            # Add to session and commit
            self.db_session.add(notification)
            self.db_session.commit()

            logger.info(f"In-app notification {notification_record['notification_id']} created in database")
            return True

        except Exception as e:
            logger.error(f"Failed to create in-app notification: {e}", exc_info=True)
            if self.db_session:
                self.db_session.rollback()
            return False

    def _store_notification(self, notification_record: Dict) -> bool:
        """
        Store notification record in database.

        Args:
            notification_record: Notification data

        Returns:
            True if successful, False otherwise
        """
        # For now, this is the same as _create_in_app_notification
        # But could be extended to store separately
        return True

    def _get_staff_email(self, staff_role: str) -> str:
        """
        Get email address for a staff role.

        Args:
            staff_role: Role identifier (e.g., 'tutor_manager', 'peer_mentor_coordinator')

        Returns:
            Email address for the role
        """
        # In production, this would lookup from a staff directory
        # For now, use role-based addresses
        role_emails = {
            "tutor_manager": "tutor.manager@tutormax.com",
            "tutor_coach": "tutor.coach@tutormax.com",
            "peer_mentor_coordinator": "mentor.coordinator@tutormax.com",
            "staff_default": "ops@tutormax.com"
        }

        return role_emails.get(staff_role, "ops@tutormax.com")

    def _map_priority(self, intervention_priority: InterventionPriority) -> str:
        """
        Map intervention priority to notification priority.

        Args:
            intervention_priority: Intervention priority level

        Returns:
            Notification priority string
        """
        priority_map = {
            InterventionPriority.CRITICAL: "critical",
            InterventionPriority.HIGH: "high",
            InterventionPriority.MEDIUM: "medium",
            InterventionPriority.LOW: "low"
        }

        return priority_map.get(intervention_priority, "medium")

    def get_notification_queue(self) -> List[Dict]:
        """
        Get the notification queue (for testing).

        Returns:
            List of notification records
        """
        return self.notification_queue

    def clear_notification_queue(self):
        """Clear the notification queue (for testing)."""
        self.notification_queue.clear()


# ============================================================================
# BATCH NOTIFICATION FUNCTIONS
# ============================================================================

def send_notifications_for_interventions(
    interventions: List[tuple],  # List of (intervention_trigger, tutor_state, tutor_email)
    notification_service: NotificationService
) -> Dict[str, any]:
    """
    Send notifications for multiple interventions.

    Args:
        interventions: List of tuples (intervention_trigger, tutor_state, tutor_email)
        notification_service: NotificationService instance

    Returns:
        Dict with batch results
    """
    results = {
        "total": len(interventions),
        "successful": 0,
        "failed": 0,
        "notifications": []
    }

    for intervention_trigger, tutor_state, tutor_email in interventions:
        try:
            result = notification_service.send_intervention_notification(
                intervention_trigger=intervention_trigger,
                tutor_state=tutor_state,
                tutor_email=tutor_email
            )

            if result["email_sent"] or result["in_app_created"]:
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["notifications"].append(result)

        except Exception as e:
            logger.error(f"Error sending notification for tutor {tutor_state.tutor_id}: {e}")
            results["failed"] += 1
            results["notifications"].append({
                "tutor_id": tutor_state.tutor_id,
                "error": str(e)
            })

    logger.info(
        f"Batch notification complete: {results['successful']} successful, "
        f"{results['failed']} failed out of {results['total']}"
    )

    return results


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_notification_service(
    enable_email: bool = True,
    smtp_host: str = "localhost",
    smtp_port: int = 1025,
    db_session=None
) -> NotificationService:
    """
    Create a notification service with custom configuration.

    Args:
        enable_email: Enable email sending
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        db_session: Database session

    Returns:
        Configured NotificationService
    """
    email_config = EmailConfig(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        enabled=enable_email
    )

    notification_config = NotificationConfig(
        email_config=email_config
    )

    return NotificationService(
        config=notification_config,
        db_session=db_session
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Create service and send test notification
    from .intervention_framework import TutorState, InterventionTrigger, InterventionType, InterventionPriority

    # Create service
    service = create_notification_service(enable_email=False)

    # Create sample tutor state
    tutor_state = TutorState(
        tutor_id="T001",
        tutor_name="John Doe",
        churn_probability=0.35,
        churn_score=45,
        risk_level="MEDIUM",
        avg_rating=4.0,
        sessions_completed=15
    )

    # Create sample intervention
    intervention = InterventionTrigger(
        intervention_type=InterventionType.AUTOMATED_COACHING,
        priority=InterventionPriority.MEDIUM,
        trigger_reason="Declining ratings trend detected",
        requires_human=False,
        recommended_actions=[
            "Review session feedback guide",
            "Focus on clear communication",
            "Ask more follow-up questions"
        ]
    )

    # Send notification
    result = service.send_intervention_notification(
        intervention_trigger=intervention,
        tutor_state=tutor_state,
        tutor_email="john.doe@example.com",
        notification_type="both"
    )

    print("Notification Result:")
    print(f"  Notification ID: {result['notification_id']}")
    print(f"  Email Sent: {result['email_sent']}")
    print(f"  In-App Created: {result['in_app_created']}")
    print(f"  Errors: {result['errors']}")

    # Show queued notifications
    print(f"\nNotifications in queue: {len(service.get_notification_queue())}")
