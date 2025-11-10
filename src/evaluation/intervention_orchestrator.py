"""
Intervention Orchestrator

This module provides a high-level interface for the complete intervention workflow:
1. Evaluate tutors for interventions
2. Create intervention records in database
3. Send notifications (email and in-app)
4. Track intervention status

This is the main entry point for the intervention system.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from .intervention_framework import (
    InterventionFramework,
    InterventionRuleEngine,
    TutorState,
    InterventionTrigger,
    create_tutor_state_from_prediction
)
from .intervention_config import InterventionConfig
from .notification_service import NotificationService, NotificationConfig

logger = logging.getLogger(__name__)


# ============================================================================
# INTERVENTION ORCHESTRATOR
# ============================================================================

class InterventionOrchestrator:
    """
    Orchestrates the complete intervention workflow.

    This class integrates:
    - Intervention rule evaluation
    - Database record creation
    - Notification delivery
    - Status tracking
    """

    def __init__(
        self,
        db_session=None,
        intervention_config: Optional[InterventionConfig] = None,
        notification_config: Optional[NotificationConfig] = None,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Initialize the intervention orchestrator.

        Args:
            db_session: SQLAlchemy database session
            intervention_config: Configuration for intervention rules
            notification_config: Configuration for notifications
            notification_service: Existing notification service (optional)
        """
        self.db_session = db_session

        # Initialize intervention framework
        self.intervention_framework = InterventionFramework(config=intervention_config)

        # Initialize notification service
        if notification_service:
            self.notification_service = notification_service
        else:
            self.notification_service = NotificationService(
                config=notification_config,
                db_session=db_session
            )

        logger.info("InterventionOrchestrator initialized")

    def evaluate_and_notify(
        self,
        tutor_state: TutorState,
        tutor_email: str,
        create_interventions: bool = True,
        send_notifications: bool = True,
        notification_type: str = "both"
    ) -> Dict[str, any]:
        """
        Evaluate a tutor for interventions and send notifications.

        This is the main entry point for processing a single tutor.

        Args:
            tutor_state: Current tutor state with metrics
            tutor_email: Tutor's email address
            create_interventions: Create intervention records in database
            send_notifications: Send notification emails/in-app
            notification_type: Type of notification ('email', 'in_app', 'both')

        Returns:
            Dict with evaluation results
        """
        logger.info(f"Evaluating tutor {tutor_state.tutor_id} for interventions")

        result = {
            "tutor_id": tutor_state.tutor_id,
            "tutor_name": tutor_state.tutor_name,
            "evaluated_at": datetime.now().isoformat(),
            "triggers_found": 0,
            "interventions_created": 0,
            "notifications_sent": 0,
            "interventions": [],
            "errors": []
        }

        # Step 1: Evaluate tutor for interventions
        try:
            triggers = self.intervention_framework.evaluate_tutor_for_interventions(tutor_state)
            result["triggers_found"] = len(triggers)

            logger.info(f"Found {len(triggers)} intervention triggers for tutor {tutor_state.tutor_id}")

            if not triggers:
                logger.info(f"No interventions needed for tutor {tutor_state.tutor_id}")
                return result

        except Exception as e:
            logger.error(f"Error evaluating tutor {tutor_state.tutor_id}: {e}", exc_info=True)
            result["errors"].append(f"Evaluation error: {str(e)}")
            return result

        # Step 2: Create intervention records and send notifications
        for trigger in triggers:
            intervention_result = {
                "type": trigger.intervention_type.value,
                "priority": trigger.priority.value,
                "intervention_id": None,
                "notification_id": None,
                "notification_sent": False,
                "errors": []
            }

            # Create intervention record in database
            intervention_id = None
            if create_interventions and self.db_session:
                try:
                    intervention_id = self._create_intervention_record(tutor_state, trigger)
                    intervention_result["intervention_id"] = intervention_id
                    result["interventions_created"] += 1
                    logger.info(f"Created intervention record {intervention_id}")

                except Exception as e:
                    logger.error(f"Error creating intervention record: {e}", exc_info=True)
                    intervention_result["errors"].append(f"Database error: {str(e)}")

            # Send notification
            if send_notifications:
                try:
                    notification_result = self.notification_service.send_intervention_notification(
                        intervention_trigger=trigger,
                        tutor_state=tutor_state,
                        tutor_email=tutor_email,
                        intervention_id=intervention_id,
                        notification_type=notification_type
                    )

                    intervention_result["notification_id"] = notification_result["notification_id"]
                    intervention_result["notification_sent"] = notification_result["email_sent"] or notification_result["in_app_created"]

                    if notification_result["email_sent"] or notification_result["in_app_created"]:
                        result["notifications_sent"] += 1

                    if notification_result["errors"]:
                        intervention_result["errors"].extend(notification_result["errors"])

                    logger.info(f"Sent notification {notification_result['notification_id']}")

                except Exception as e:
                    logger.error(f"Error sending notification: {e}", exc_info=True)
                    intervention_result["errors"].append(f"Notification error: {str(e)}")

            result["interventions"].append(intervention_result)

        logger.info(
            f"Completed evaluation for tutor {tutor_state.tutor_id}: "
            f"{result['interventions_created']} interventions created, "
            f"{result['notifications_sent']} notifications sent"
        )

        return result

    def batch_evaluate_and_notify(
        self,
        tutors: List[Tuple[TutorState, str]],  # List of (tutor_state, tutor_email)
        create_interventions: bool = True,
        send_notifications: bool = True,
        notification_type: str = "both"
    ) -> Dict[str, any]:
        """
        Evaluate multiple tutors for interventions and send notifications.

        Args:
            tutors: List of tuples (tutor_state, tutor_email)
            create_interventions: Create intervention records in database
            send_notifications: Send notification emails/in-app
            notification_type: Type of notification ('email', 'in_app', 'both')

        Returns:
            Dict with batch results
        """
        logger.info(f"Batch evaluating {len(tutors)} tutors for interventions")

        batch_result = {
            "total_tutors": len(tutors),
            "tutors_with_interventions": 0,
            "total_triggers": 0,
            "total_interventions_created": 0,
            "total_notifications_sent": 0,
            "results": [],
            "errors": []
        }

        for tutor_state, tutor_email in tutors:
            try:
                result = self.evaluate_and_notify(
                    tutor_state=tutor_state,
                    tutor_email=tutor_email,
                    create_interventions=create_interventions,
                    send_notifications=send_notifications,
                    notification_type=notification_type
                )

                if result["triggers_found"] > 0:
                    batch_result["tutors_with_interventions"] += 1

                batch_result["total_triggers"] += result["triggers_found"]
                batch_result["total_interventions_created"] += result["interventions_created"]
                batch_result["total_notifications_sent"] += result["notifications_sent"]
                batch_result["results"].append(result)

            except Exception as e:
                logger.error(f"Error processing tutor {tutor_state.tutor_id}: {e}", exc_info=True)
                batch_result["errors"].append({
                    "tutor_id": tutor_state.tutor_id,
                    "error": str(e)
                })

        logger.info(
            f"Batch evaluation complete: {batch_result['tutors_with_interventions']}/{batch_result['total_tutors']} "
            f"tutors with interventions, {batch_result['total_notifications_sent']} notifications sent"
        )

        return batch_result

    def _create_intervention_record(
        self,
        tutor_state: TutorState,
        trigger: InterventionTrigger
    ) -> str:
        """
        Create an intervention record in the database.

        Args:
            tutor_state: Tutor state
            trigger: Intervention trigger

        Returns:
            Intervention ID
        """
        if not self.db_session:
            raise ValueError("Database session required to create intervention records")

        # Import here to avoid circular dependency
        from ..database.models import Intervention, InterventionType as DBInterventionType, InterventionStatus

        # Generate intervention ID
        intervention_id = f"intv_{uuid.uuid4().hex[:12]}"

        # Calculate due date
        due_date = datetime.now() + timedelta(days=trigger.due_days)

        # Create intervention
        intervention = Intervention(
            intervention_id=intervention_id,
            tutor_id=tutor_state.tutor_id,
            intervention_type=DBInterventionType(trigger.intervention_type.value),
            trigger_reason=trigger.trigger_reason,
            recommended_date=datetime.now(),
            assigned_to=trigger.assigned_to,
            status=InterventionStatus.PENDING,
            due_date=due_date,
            notes=trigger.notes
        )

        # Add to session and commit
        self.db_session.add(intervention)
        self.db_session.commit()

        logger.info(f"Created intervention record {intervention_id} for tutor {tutor_state.tutor_id}")

        return intervention_id

    def get_intervention_summary(self, tutor_state: TutorState) -> str:
        """
        Get a formatted summary of interventions for a tutor.

        Args:
            tutor_state: Tutor state

        Returns:
            Formatted summary string
        """
        triggers = self.intervention_framework.evaluate_tutor_for_interventions(tutor_state)
        return self.intervention_framework.format_intervention_summary(tutor_state, triggers)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_orchestrator(
    db_session=None,
    enable_email: bool = True,
    enable_database: bool = True
) -> InterventionOrchestrator:
    """
    Create an intervention orchestrator with default configuration.

    Args:
        db_session: Database session
        enable_email: Enable email sending
        enable_database: Enable database operations

    Returns:
        Configured InterventionOrchestrator
    """
    from .notification_service import EmailConfig, NotificationConfig

    # Configure email
    email_config = EmailConfig(
        smtp_host="localhost",
        smtp_port=1025,  # MailHog default
        enabled=enable_email
    )

    notification_config = NotificationConfig(
        email_config=email_config,
        store_notifications=enable_database
    )

    return InterventionOrchestrator(
        db_session=db_session if enable_database else None,
        notification_config=notification_config
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Evaluate a high-risk tutor
    from .intervention_framework import TutorState, RiskLevel, PerformanceTier

    # Create orchestrator (no database, no email)
    orchestrator = create_orchestrator(
        db_session=None,
        enable_email=False,
        enable_database=False
    )

    # Create sample tutor state
    tutor_state = TutorState(
        tutor_id="T001",
        tutor_name="John Doe",
        churn_probability=0.72,
        churn_score=85,
        risk_level=RiskLevel.CRITICAL.value,
        avg_rating=3.5,
        first_session_success_rate=0.45,
        engagement_score=0.55,
        performance_tier=PerformanceTier.AT_RISK.value,
        no_show_rate=0.05,
        reschedule_rate=0.25,
        sessions_completed=20,
        sessions_per_week=3.5,
        engagement_decline=0.25,
        rating_decline=0.6,
        session_volume_decline=0.35,
        behavioral_risk_score=0.68,
        recent_interventions=[],
        tenure_days=120
    )

    # Evaluate and notify
    result = orchestrator.evaluate_and_notify(
        tutor_state=tutor_state,
        tutor_email="john.doe@example.com",
        create_interventions=False,
        send_notifications=True,
        notification_type="both"
    )

    # Print results
    print("\n" + "=" * 70)
    print("INTERVENTION EVALUATION RESULTS")
    print("=" * 70)
    print(f"Tutor: {result['tutor_name']} ({result['tutor_id']})")
    print(f"Triggers Found: {result['triggers_found']}")
    print(f"Notifications Sent: {result['notifications_sent']}")
    print("\nInterventions:")
    for intervention in result['interventions']:
        print(f"  - {intervention['type']} (Priority: {intervention['priority']})")
        if intervention['notification_sent']:
            print(f"    ✓ Notification sent: {intervention['notification_id']}")
        if intervention['errors']:
            print(f"    ✗ Errors: {', '.join(intervention['errors'])}")

    # Show notification queue
    notifications = orchestrator.notification_service.get_notification_queue()
    print(f"\nNotifications in queue: {len(notifications)}")
