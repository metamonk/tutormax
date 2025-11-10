"""
Integration Tests for Notification System

Tests the complete notification workflow:
- Template generation
- Email delivery
- In-app notifications
- Integration with intervention framework
- Batch processing
"""

import pytest
from datetime import datetime

from src.evaluation.notification_service import (
    NotificationService,
    EmailConfig,
    NotificationConfig,
    create_notification_service
)
from src.evaluation.notification_templates import (
    get_notification_template,
    InterventionType as TemplateInterventionType
)
from src.evaluation.intervention_orchestrator import (
    InterventionOrchestrator,
    create_orchestrator
)
from src.evaluation.intervention_framework import (
    TutorState,
    InterventionTrigger,
    InterventionType,
    InterventionPriority,
    RiskLevel,
    PerformanceTier
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_tutor_state():
    """Create a sample tutor state for testing."""
    return TutorState(
        tutor_id="T001",
        tutor_name="John Doe",
        churn_probability=0.35,
        churn_score=45,
        risk_level=RiskLevel.MEDIUM.value,
        avg_rating=4.0,
        first_session_success_rate=0.70,
        engagement_score=0.72,
        learning_objectives_met_pct=0.75,
        performance_tier=PerformanceTier.DEVELOPING.value,
        no_show_rate=0.02,
        reschedule_rate=0.12,
        sessions_completed=20,
        sessions_per_week=4.0,
        engagement_decline=0.15,
        rating_decline=0.25,
        session_volume_decline=0.18,
        behavioral_risk_score=0.32,
        recent_interventions=[],
        tenure_days=90
    )


@pytest.fixture
def critical_risk_tutor():
    """Create a critical risk tutor state for testing."""
    return TutorState(
        tutor_id="T002",
        tutor_name="Alice Johnson",
        churn_probability=0.82,
        churn_score=92,
        risk_level=RiskLevel.CRITICAL.value,
        avg_rating=3.2,
        first_session_success_rate=0.40,
        engagement_score=0.45,
        learning_objectives_met_pct=0.55,
        performance_tier=PerformanceTier.AT_RISK.value,
        no_show_rate=0.08,
        reschedule_rate=0.32,
        sessions_completed=25,
        sessions_per_week=2.5,
        engagement_decline=0.35,
        rating_decline=0.75,
        session_volume_decline=0.45,
        behavioral_risk_score=0.82,
        recent_interventions=[],
        tenure_days=180
    )


@pytest.fixture
def sample_intervention():
    """Create a sample intervention trigger for testing."""
    return InterventionTrigger(
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


@pytest.fixture
def notification_service():
    """Create a notification service for testing."""
    return create_notification_service(
        enable_email=False,  # Disable email for testing
        smtp_host="localhost",
        smtp_port=1025
    )


@pytest.fixture
def orchestrator():
    """Create an orchestrator for testing."""
    return create_orchestrator(
        db_session=None,
        enable_email=False,
        enable_database=False
    )


# ============================================================================
# NOTIFICATION TEMPLATE TESTS
# ============================================================================

class TestNotificationTemplates:
    """Test notification template generation."""

    def test_automated_coaching_template(self):
        """Test automated coaching template generation."""
        template = get_notification_template(
            intervention_type=TemplateInterventionType.AUTOMATED_COACHING,
            tutor_name="John Doe",
            trigger_reason="Rating decline detected",
            recommended_actions=["Action 1", "Action 2"]
        )

        assert template.subject
        assert template.body_text
        assert template.body_html
        assert template.recipient_type == "tutor"
        assert "John" in template.body_text  # First name used
        assert "Rating decline detected" in template.body_text
        assert "Action 1" in template.body_text

    def test_staff_notification_template(self):
        """Test staff notification template generation."""
        template = get_notification_template(
            intervention_type=TemplateInterventionType.MANAGER_COACHING,
            tutor_name="John Doe",
            trigger_reason="High churn risk",
            recommended_actions=["Schedule coaching session"],
            tutor_id="T001"
        )

        assert template.recipient_type == "staff"
        assert "T001" in template.body_text
        assert "HIGH" in template.body_text  # Priority mentioned

    def test_all_intervention_types_have_templates(self):
        """Test that all intervention types have templates."""
        intervention_types = [
            TemplateInterventionType.AUTOMATED_COACHING,
            TemplateInterventionType.TRAINING_MODULE,
            TemplateInterventionType.FIRST_SESSION_CHECKIN,
            TemplateInterventionType.RESCHEDULING_ALERT,
            TemplateInterventionType.RECOGNITION,
        ]

        for intervention_type in intervention_types:
            template = get_notification_template(
                intervention_type=intervention_type,
                tutor_name="Test Tutor",
                trigger_reason="Test reason",
                recommended_actions=["Action 1"]
            )

            assert template.subject
            assert template.body_text
            assert template.body_html

    def test_html_content_is_valid(self):
        """Test that HTML content contains proper structure."""
        template = get_notification_template(
            intervention_type=TemplateInterventionType.TRAINING_MODULE,
            tutor_name="John Doe",
            trigger_reason="Low engagement",
            recommended_actions=["Complete training module"]
        )

        html = template.body_html
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<body>" in html
        assert "</body>" in html


# ============================================================================
# NOTIFICATION SERVICE TESTS
# ============================================================================

class TestNotificationService:
    """Test notification service functionality."""

    def test_service_initialization(self, notification_service):
        """Test service initializes correctly."""
        assert notification_service is not None
        assert notification_service.config is not None
        assert len(notification_service.notification_queue) == 0

    def test_send_notification(self, notification_service, sample_intervention, sample_tutor_state):
        """Test sending a notification."""
        result = notification_service.send_intervention_notification(
            intervention_trigger=sample_intervention,
            tutor_state=sample_tutor_state,
            tutor_email="john.doe@example.com",
            notification_type="both"
        )

        assert result["notification_id"]
        assert result["email_sent"]  # True because email is disabled (mock mode)
        assert not result["in_app_created"]  # False because no DB session

    def test_notification_queue(self, notification_service, sample_intervention, sample_tutor_state):
        """Test notification queue functionality."""
        notification_service.clear_notification_queue()

        notification_service.send_intervention_notification(
            intervention_trigger=sample_intervention,
            tutor_state=sample_tutor_state,
            tutor_email="john.doe@example.com"
        )

        queue = notification_service.get_notification_queue()
        assert len(queue) == 1
        assert queue[0]["notification_id"]
        assert queue[0]["recipient_email"] == "john.doe@example.com"

    def test_staff_notification_routing(self, notification_service, sample_tutor_state):
        """Test that staff notifications are routed correctly."""
        notification_service.clear_notification_queue()

        # Create staff notification (requires_human=True)
        staff_intervention = InterventionTrigger(
            intervention_type=InterventionType.MANAGER_COACHING,
            priority=InterventionPriority.HIGH,
            trigger_reason="High churn risk",
            requires_human=True,
            assigned_to="tutor_manager",
            recommended_actions=["Schedule coaching session"]
        )

        notification_service.send_intervention_notification(
            intervention_trigger=staff_intervention,
            tutor_state=sample_tutor_state,
            tutor_email="john.doe@example.com"
        )

        queue = notification_service.get_notification_queue()
        assert len(queue) == 1
        assert "tutor.manager@tutormax.com" in queue[0]["recipient_email"]


# ============================================================================
# INTERVENTION ORCHESTRATOR TESTS
# ============================================================================

class TestInterventionOrchestrator:
    """Test intervention orchestrator functionality."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator is not None
        assert orchestrator.intervention_framework is not None
        assert orchestrator.notification_service is not None

    def test_evaluate_and_notify(self, orchestrator, critical_risk_tutor):
        """Test complete evaluate and notify workflow."""
        result = orchestrator.evaluate_and_notify(
            tutor_state=critical_risk_tutor,
            tutor_email="alice.johnson@example.com",
            create_interventions=False,
            send_notifications=True
        )

        assert result["tutor_id"] == "T002"
        assert result["tutor_name"] == "Alice Johnson"
        assert result["triggers_found"] > 0
        assert result["notifications_sent"] > 0
        assert len(result["interventions"]) > 0

    def test_batch_evaluation(self, orchestrator, sample_tutor_state, critical_risk_tutor):
        """Test batch evaluation of multiple tutors."""
        tutors = [
            (sample_tutor_state, "john.doe@example.com"),
            (critical_risk_tutor, "alice.johnson@example.com")
        ]

        result = orchestrator.batch_evaluate_and_notify(
            tutors=tutors,
            create_interventions=False,
            send_notifications=True
        )

        assert result["total_tutors"] == 2
        assert result["tutors_with_interventions"] > 0
        assert result["total_triggers"] > 0
        assert result["total_notifications_sent"] > 0

    def test_intervention_priority_ordering(self, orchestrator, critical_risk_tutor):
        """Test that interventions are ordered by priority."""
        result = orchestrator.evaluate_and_notify(
            tutor_state=critical_risk_tutor,
            tutor_email="alice.johnson@example.com",
            create_interventions=False,
            send_notifications=True
        )

        interventions = result["interventions"]
        if len(interventions) > 1:
            # Check that critical/high priority comes before low priority
            priorities = [i["priority"] for i in interventions]
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            priority_values = [priority_order[p] for p in priorities]

            # Verify they're sorted
            assert priority_values == sorted(priority_values)

    def test_notification_content(self, orchestrator, sample_tutor_state):
        """Test notification content is generated correctly."""
        orchestrator.notification_service.clear_notification_queue()

        orchestrator.evaluate_and_notify(
            tutor_state=sample_tutor_state,
            tutor_email="john.doe@example.com",
            create_interventions=False,
            send_notifications=True
        )

        queue = orchestrator.notification_service.get_notification_queue()
        if len(queue) > 0:
            notification = queue[0]
            assert notification["subject"]
            assert notification["body"]
            assert notification["intervention_type"]
            assert notification["priority"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndIntegration:
    """Test complete end-to-end integration."""

    def test_complete_workflow(self, orchestrator):
        """Test complete workflow from evaluation to notification."""
        # Create a tutor with issues
        tutor = TutorState(
            tutor_id="T003",
            tutor_name="Bob Martinez",
            churn_probability=0.62,
            churn_score=72,
            risk_level=RiskLevel.HIGH.value,
            avg_rating=3.8,
            first_session_success_rate=0.52,
            engagement_score=0.62,
            learning_objectives_met_pct=0.68,
            performance_tier=PerformanceTier.NEEDS_ATTENTION.value,
            no_show_rate=0.04,
            reschedule_rate=0.28,
            sessions_completed=18,
            sessions_per_week=3.0,
            engagement_decline=0.22,
            rating_decline=0.45,
            session_volume_decline=0.25,
            behavioral_risk_score=0.58,
            recent_interventions=[],
            tenure_days=120
        )

        # Evaluate and notify
        result = orchestrator.evaluate_and_notify(
            tutor_state=tutor,
            tutor_email="bob.martinez@example.com",
            create_interventions=False,
            send_notifications=True
        )

        # Verify results
        assert result["tutor_id"] == "T003"
        assert result["triggers_found"] > 0
        assert result["notifications_sent"] == result["triggers_found"]

        # Verify notification queue
        queue = orchestrator.notification_service.get_notification_queue()
        assert len(queue) > 0

        # Verify each notification has required fields
        for notification in queue:
            assert notification["notification_id"]
            assert notification["recipient_email"]
            assert notification["subject"]
            assert notification["body"]
            assert notification["priority"] in ["critical", "high", "medium", "low"]

    def test_high_performer_recognition(self, orchestrator):
        """Test that high performers receive recognition."""
        # Create high performer
        tutor = TutorState(
            tutor_id="T004",
            tutor_name="David Park",
            churn_probability=0.08,
            churn_score=12,
            risk_level=RiskLevel.LOW.value,
            avg_rating=4.8,
            first_session_success_rate=0.92,
            engagement_score=0.92,
            learning_objectives_met_pct=0.95,
            performance_tier=PerformanceTier.EXEMPLARY.value,
            no_show_rate=0.00,
            reschedule_rate=0.02,
            sessions_completed=45,
            sessions_per_week=6.5,
            engagement_decline=-0.05,
            rating_decline=-0.15,
            session_volume_decline=0.05,
            behavioral_risk_score=0.08,
            recent_interventions=[],
            tenure_days=240
        )

        orchestrator.notification_service.clear_notification_queue()

        result = orchestrator.evaluate_and_notify(
            tutor_state=tutor,
            tutor_email="david.park@example.com",
            create_interventions=False,
            send_notifications=True
        )

        # Should trigger recognition
        assert result["triggers_found"] > 0

        # Verify recognition notification
        queue = orchestrator.notification_service.get_notification_queue()
        assert len(queue) > 0

        # Check for recognition intervention
        recognition_found = any(
            n["intervention_type"] == "recognition"
            for n in queue
        )
        assert recognition_found

    def test_batch_processing_performance(self, orchestrator):
        """Test batch processing can handle multiple tutors efficiently."""
        # Create 10 tutors
        tutors = []
        for i in range(10):
            tutor = TutorState(
                tutor_id=f"T{100+i}",
                tutor_name=f"Tutor {i}",
                churn_probability=0.3 + (i * 0.05),
                churn_score=30 + (i * 5),
                risk_level=RiskLevel.MEDIUM.value,
                avg_rating=4.0,
                sessions_completed=20,
                sessions_per_week=4.0,
                engagement_decline=0.1,
                rating_decline=0.2,
                session_volume_decline=0.15,
                tenure_days=90
            )
            tutors.append((tutor, f"tutor{i}@example.com"))

        # Process batch
        result = orchestrator.batch_evaluate_and_notify(
            tutors=tutors,
            create_interventions=False,
            send_notifications=True
        )

        assert result["total_tutors"] == 10
        assert result["total_notifications_sent"] > 0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in notification system."""

    def test_invalid_intervention_type(self):
        """Test handling of invalid intervention type."""
        with pytest.raises(ValueError):
            get_notification_template(
                intervention_type="invalid_type",  # type: ignore
                tutor_name="Test",
                trigger_reason="Test",
                recommended_actions=[]
            )

    def test_missing_tutor_id_for_staff_notification(self):
        """Test that staff notifications require tutor_id."""
        with pytest.raises(ValueError):
            get_notification_template(
                intervention_type=TemplateInterventionType.MANAGER_COACHING,
                tutor_name="Test",
                trigger_reason="Test",
                recommended_actions=[]
                # Missing tutor_id
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
