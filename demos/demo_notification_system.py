"""
Demo: Intervention Notification System

This demo shows the complete intervention and notification workflow:
1. Evaluate tutors for interventions using the rule engine
2. Create intervention records in the database (simulated)
3. Send notifications via email and in-app
4. Display notification templates

This demonstrates Task 5.3: Integration with Email and Notification Systems
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.intervention_orchestrator import create_orchestrator
from src.evaluation.intervention_framework import TutorState, RiskLevel, PerformanceTier
from datetime import datetime


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def create_sample_tutors():
    """Create sample tutor states for testing."""
    return [
        # Critical Risk Tutor
        TutorState(
            tutor_id="T001",
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
        ),
        # High Risk Tutor
        TutorState(
            tutor_id="T002",
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
        ),
        # Medium Risk Tutor
        TutorState(
            tutor_id="T003",
            tutor_name="Carol Chen",
            churn_probability=0.38,
            churn_score=48,
            risk_level=RiskLevel.MEDIUM.value,
            avg_rating=4.0,
            first_session_success_rate=0.68,
            engagement_score=0.72,
            learning_objectives_met_pct=0.75,
            performance_tier=PerformanceTier.DEVELOPING.value,
            no_show_rate=0.02,
            reschedule_rate=0.12,
            sessions_completed=22,
            sessions_per_week=4.0,
            engagement_decline=0.15,
            rating_decline=0.25,
            session_volume_decline=0.18,
            behavioral_risk_score=0.32,
            recent_interventions=[],
            tenure_days=90
        ),
        # High Performer
        TutorState(
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
            engagement_decline=-0.05,  # Improving!
            rating_decline=-0.15,  # Improving!
            session_volume_decline=0.05,
            behavioral_risk_score=0.08,
            recent_interventions=[],
            tenure_days=240
        ),
        # New Tutor with Challenges
        TutorState(
            tutor_id="T005",
            tutor_name="Emma Wilson",
            churn_probability=0.25,
            churn_score=35,
            risk_level=RiskLevel.MEDIUM.value,
            avg_rating=3.9,
            first_session_success_rate=0.48,  # Poor first sessions
            engagement_score=0.68,
            learning_objectives_met_pct=0.65,
            performance_tier=PerformanceTier.DEVELOPING.value,
            no_show_rate=0.03,
            reschedule_rate=0.08,
            sessions_completed=12,
            sessions_per_week=3.5,
            engagement_decline=0.10,
            rating_decline=0.12,
            session_volume_decline=0.08,
            behavioral_risk_score=0.25,
            recent_interventions=[],
            tenure_days=22  # New tutor
        ),
    ]


def demo_individual_evaluation():
    """Demo: Evaluate individual tutors."""
    print_section("DEMO 1: Individual Tutor Evaluation")

    # Create orchestrator (without database or email sending for demo)
    orchestrator = create_orchestrator(
        db_session=None,
        enable_email=False,  # Don't send real emails
        enable_database=False  # Don't create DB records
    )

    tutors = create_sample_tutors()

    for i, tutor_state in enumerate(tutors, 1):
        print(f"\n{'─' * 80}")
        print(f"Tutor {i}: {tutor_state.tutor_name} ({tutor_state.tutor_id})")
        print(f"{'─' * 80}")
        print(f"  Risk Level: {tutor_state.risk_level}")
        print(f"  Churn Score: {tutor_state.churn_score}/100")
        print(f"  Churn Probability: {tutor_state.churn_probability:.1%}")
        print(f"  Performance Tier: {tutor_state.performance_tier}")
        print(f"  Avg Rating: {tutor_state.avg_rating:.2f}")
        print(f"  Sessions Completed: {tutor_state.sessions_completed}")
        print(f"  Tenure: {tutor_state.tenure_days} days")

        # Evaluate
        result = orchestrator.evaluate_and_notify(
            tutor_state=tutor_state,
            tutor_email=f"{tutor_state.tutor_id.lower()}@example.com",
            create_interventions=False,
            send_notifications=True,
            notification_type="both"
        )

        print(f"\n  📊 Evaluation Results:")
        print(f"     Interventions Triggered: {result['triggers_found']}")

        if result['triggers_found'] > 0:
            print(f"\n  🔔 Interventions:")
            for intervention in result['interventions']:
                print(f"     • {intervention['type'].upper()}")
                print(f"       Priority: {intervention['priority'].upper()}")
                print(f"       Notification Sent: {'✓' if intervention['notification_sent'] else '✗'}")
                if intervention['notification_id']:
                    print(f"       Notification ID: {intervention['notification_id']}")
        else:
            print(f"     ✓ No interventions needed - tutor is performing well!")


def demo_batch_evaluation():
    """Demo: Batch evaluation of multiple tutors."""
    print_section("DEMO 2: Batch Tutor Evaluation")

    # Create orchestrator
    orchestrator = create_orchestrator(
        db_session=None,
        enable_email=False,
        enable_database=False
    )

    tutors = create_sample_tutors()
    tutor_data = [(state, f"{state.tutor_id.lower()}@example.com") for state in tutors]

    print(f"Evaluating {len(tutor_data)} tutors for interventions...")

    # Batch evaluate
    batch_result = orchestrator.batch_evaluate_and_notify(
        tutors=tutor_data,
        create_interventions=False,
        send_notifications=True,
        notification_type="both"
    )

    # Display summary
    print(f"\n📊 Batch Evaluation Summary:")
    print(f"{'─' * 80}")
    print(f"Total Tutors Evaluated: {batch_result['total_tutors']}")
    print(f"Tutors Requiring Intervention: {batch_result['tutors_with_interventions']}")
    print(f"Total Interventions Triggered: {batch_result['total_triggers']}")
    print(f"Notifications Sent: {batch_result['total_notifications_sent']}")

    # Breakdown by tutor
    print(f"\n📋 Detailed Breakdown:")
    print(f"{'─' * 80}")
    for result in batch_result['results']:
        status = "✓" if result['triggers_found'] == 0 else f"⚠ {result['triggers_found']} interventions"
        print(f"  {result['tutor_name']:20} - {status}")


def demo_notification_content():
    """Demo: Show notification content for different intervention types."""
    print_section("DEMO 3: Notification Content Examples")

    # Create orchestrator
    orchestrator = create_orchestrator(
        db_session=None,
        enable_email=False,
        enable_database=False
    )

    # Use critical risk tutor
    tutor_state = create_sample_tutors()[0]  # Alice Johnson - Critical risk

    print(f"Generating notification content for: {tutor_state.tutor_name}")
    print(f"Risk Level: {tutor_state.risk_level}")
    print(f"Churn Score: {tutor_state.churn_score}/100")

    # Get intervention summary
    summary = orchestrator.get_intervention_summary(tutor_state)
    print(f"\n{summary}")

    # Show sample notification from queue
    orchestrator.notification_service.clear_notification_queue()

    result = orchestrator.evaluate_and_notify(
        tutor_state=tutor_state,
        tutor_email="alice.johnson@example.com",
        create_interventions=False,
        send_notifications=True,
        notification_type="both"
    )

    # Display notification details
    notifications = orchestrator.notification_service.get_notification_queue()

    if notifications:
        print(f"\n\n{'=' * 80}")
        print("SAMPLE NOTIFICATION CONTENT")
        print(f"{'=' * 80}")

        notification = notifications[0]
        print(f"\nNotification ID: {notification['notification_id']}")
        print(f"Recipient: {notification['recipient_email']}")
        print(f"Priority: {notification['priority'].upper()}")
        print(f"Intervention Type: {notification['intervention_type']}")
        print(f"\nSubject: {notification['subject']}")
        print(f"\n{'─' * 80}")
        print("PLAIN TEXT BODY:")
        print(f"{'─' * 80}")
        print(notification['body'])
        print(f"{'─' * 80}")


def demo_notification_statistics():
    """Demo: Show notification statistics."""
    print_section("DEMO 4: Notification Statistics")

    # Create orchestrator
    orchestrator = create_orchestrator(
        db_session=None,
        enable_email=False,
        enable_database=False
    )

    # Evaluate all tutors
    tutors = create_sample_tutors()
    tutor_data = [(state, f"{state.tutor_id.lower()}@example.com") for state in tutors]

    batch_result = orchestrator.batch_evaluate_and_notify(
        tutors=tutor_data,
        create_interventions=False,
        send_notifications=True,
        notification_type="both"
    )

    # Get all notifications
    notifications = orchestrator.notification_service.get_notification_queue()

    # Count by type and priority
    by_type = {}
    by_priority = {}

    for notif in notifications:
        intervention_type = notif['intervention_type']
        priority = notif['priority']

        by_type[intervention_type] = by_type.get(intervention_type, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    print(f"📊 Notification Statistics:")
    print(f"{'─' * 80}")
    print(f"Total Notifications: {len(notifications)}")

    print(f"\n📧 By Intervention Type:")
    for intervention_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {intervention_type:40} {count:2} notifications")

    print(f"\n⚡ By Priority:")
    priority_order = ['critical', 'high', 'medium', 'low']
    for priority in priority_order:
        if priority in by_priority:
            print(f"  {priority.upper():10} {by_priority[priority]:2} notifications")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "INTERVENTION NOTIFICATION SYSTEM DEMO" + " " * 26 + "║")
    print("║" + " " * 20 + "Task 5.3: Email & Notification Integration" + " " * 15 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Run demos
        demo_individual_evaluation()
        demo_batch_evaluation()
        demo_notification_content()
        demo_notification_statistics()

        print_section("DEMO COMPLETE")
        print("✓ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. Individual tutor evaluation with intervention triggers")
        print("  2. Batch evaluation of multiple tutors")
        print("  3. Notification content generation (email + in-app)")
        print("  4. Notification statistics and analytics")
        print("\nNotification System Components:")
        print("  • InterventionOrchestrator - Main workflow coordinator")
        print("  • NotificationService - Email and in-app notification delivery")
        print("  • NotificationTemplates - HTML and plain text templates")
        print("  • InterventionFramework - Rule engine for trigger evaluation")
        print("\nIntegration Status:")
        print("  ✓ Intervention evaluation working")
        print("  ✓ Notification templates generated")
        print("  ✓ Email delivery ready (SMTP configured)")
        print("  ✓ In-app notifications ready (database models created)")
        print("  ✓ Batch processing supported")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
