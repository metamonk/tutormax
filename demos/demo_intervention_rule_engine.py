"""
Demo: Intervention Rule Engine

Demonstrates the intervention rule engine with various tutor scenarios:
1. Critical risk tutor requiring immediate intervention
2. High risk tutor needing coaching
3. Baseline tutor with normal performance
4. High performer deserving recognition
5. Custom configuration and rule management
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.intervention_framework import (
    InterventionFramework,
    TutorState,
    RiskLevel,
    PerformanceTier,
)
from src.evaluation.intervention_config import (
    InterventionConfig,
    ConfigManager,
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_critical_risk_tutor():
    """Demo 1: Critical risk tutor requiring immediate intervention."""
    print_section("Demo 1: Critical Risk Tutor - Immediate Intervention Required")

    # Create framework
    framework = InterventionFramework()

    # Create critical risk tutor state
    tutor = TutorState(
        tutor_id="T001",
        tutor_name="Alice Johnson",
        churn_probability=0.78,
        churn_score=88,
        risk_level=RiskLevel.CRITICAL.value,
        avg_rating=3.2,
        first_session_success_rate=0.42,
        engagement_score=0.48,
        learning_objectives_met_pct=0.45,
        performance_tier=PerformanceTier.AT_RISK.value,
        no_show_rate=0.08,
        reschedule_rate=0.28,
        sessions_completed=18,
        sessions_per_week=2.8,
        engagement_decline=0.32,
        rating_decline=0.68,
        session_volume_decline=0.42,
        behavioral_risk_score=0.75,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=120,
    )

    print(f"Tutor: {tutor.tutor_name} ({tutor.tutor_id})")
    print(f"Churn Risk: {tutor.risk_level} ({tutor.churn_probability:.1%})")
    print(f"Performance Tier: {tutor.performance_tier}")
    print(f"Average Rating: {tutor.avg_rating:.2f}/5.0")
    print(f"Engagement Score: {tutor.engagement_score:.2f}")
    print()

    # Evaluate for interventions
    triggers = framework.evaluate_tutor_for_interventions(tutor)

    # Display results
    summary = framework.format_intervention_summary(tutor, triggers)
    print(summary)


def demo_high_risk_tutor():
    """Demo 2: High risk tutor needing coaching."""
    print_section("Demo 2: High Risk Tutor - Manager Coaching Needed")

    framework = InterventionFramework()

    tutor = TutorState(
        tutor_id="T002",
        tutor_name="Bob Smith",
        churn_probability=0.58,
        churn_score=65,
        risk_level=RiskLevel.HIGH.value,
        avg_rating=3.8,
        first_session_success_rate=0.55,
        engagement_score=0.62,
        learning_objectives_met_pct=0.60,
        performance_tier=PerformanceTier.DEVELOPING.value,
        no_show_rate=0.05,
        reschedule_rate=0.15,
        sessions_completed=22,
        sessions_per_week=4.2,
        engagement_decline=0.12,
        rating_decline=0.25,
        session_volume_decline=0.18,
        behavioral_risk_score=0.38,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=90,
    )

    print(f"Tutor: {tutor.tutor_name} ({tutor.tutor_id})")
    print(f"Churn Risk: {tutor.risk_level} ({tutor.churn_probability:.1%})")
    print(f"Performance Tier: {tutor.performance_tier}")
    print(f"Average Rating: {tutor.avg_rating:.2f}/5.0")
    print()

    triggers = framework.evaluate_tutor_for_interventions(tutor)
    summary = framework.format_intervention_summary(tutor, triggers)
    print(summary)


def demo_baseline_tutor():
    """Demo 3: Baseline tutor with normal performance."""
    print_section("Demo 3: Baseline Tutor - Normal Performance")

    framework = InterventionFramework()

    tutor = TutorState(
        tutor_id="T003",
        tutor_name="Carol Williams",
        churn_probability=0.25,
        churn_score=28,
        risk_level=RiskLevel.LOW.value,
        avg_rating=4.2,
        first_session_success_rate=0.72,
        engagement_score=0.75,
        learning_objectives_met_pct=0.72,
        performance_tier=PerformanceTier.STRONG.value,
        no_show_rate=0.03,
        reschedule_rate=0.08,
        sessions_completed=35,
        sessions_per_week=5.5,
        engagement_decline=0.02,
        rating_decline=0.05,
        session_volume_decline=0.05,
        behavioral_risk_score=0.12,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=150,
    )

    print(f"Tutor: {tutor.tutor_name} ({tutor.tutor_id})")
    print(f"Churn Risk: {tutor.risk_level} ({tutor.churn_probability:.1%})")
    print(f"Performance Tier: {tutor.performance_tier}")
    print(f"Average Rating: {tutor.avg_rating:.2f}/5.0")
    print()

    triggers = framework.evaluate_tutor_for_interventions(tutor)

    if triggers:
        summary = framework.format_intervention_summary(tutor, triggers)
        print(summary)
    else:
        print("✓ No interventions triggered - tutor performing well!")
        print("  Continue monitoring standard metrics.")


def demo_high_performer():
    """Demo 4: High performer deserving recognition."""
    print_section("Demo 4: High Performer - Recognition Deserved")

    framework = InterventionFramework()

    tutor = TutorState(
        tutor_id="T004",
        tutor_name="David Chen",
        churn_probability=0.08,
        churn_score=10,
        risk_level=RiskLevel.LOW.value,
        avg_rating=4.9,
        first_session_success_rate=0.92,
        engagement_score=0.91,
        learning_objectives_met_pct=0.88,
        performance_tier=PerformanceTier.EXEMPLARY.value,
        no_show_rate=0.01,
        reschedule_rate=0.02,
        sessions_completed=85,
        sessions_per_week=7.2,
        engagement_decline=-0.05,  # Negative = improvement
        rating_decline=-0.15,  # Negative = improvement
        session_volume_decline=-0.10,  # Negative = improvement
        behavioral_risk_score=0.05,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=240,
    )

    print(f"Tutor: {tutor.tutor_name} ({tutor.tutor_id})")
    print(f"Churn Risk: {tutor.risk_level} ({tutor.churn_probability:.1%})")
    print(f"Performance Tier: {tutor.performance_tier}")
    print(f"Average Rating: {tutor.avg_rating:.2f}/5.0")
    print(f"Engagement Score: {tutor.engagement_score:.2f}")
    print()

    triggers = framework.evaluate_tutor_for_interventions(tutor)
    summary = framework.format_intervention_summary(tutor, triggers)
    print(summary)


def demo_custom_configuration():
    """Demo 5: Custom configuration and rule management."""
    print_section("Demo 5: Custom Configuration & Rule Management")

    # Create custom configuration
    config = InterventionConfig()

    print("Original Configuration:")
    print(f"  Critical Churn Threshold: {config.thresholds.critical_churn_probability:.1%}")
    print(f"  High Churn Threshold: {config.thresholds.high_churn_probability:.1%}")
    print(f"  Poor First Session Rate: {config.thresholds.poor_first_session_rate:.1%}")
    print(f"  Intervention Cooldown: {config.timing.intervention_cooldown_days} days")
    print()

    # Modify configuration
    config.thresholds.critical_churn_probability = 0.75  # More lenient
    config.thresholds.high_churn_probability = 0.55
    config.timing.critical_due_days = 1  # More urgent
    config.max_interventions_per_tutor = 3  # Limit interventions

    print("Modified Configuration:")
    print(f"  Critical Churn Threshold: {config.thresholds.critical_churn_probability:.1%}")
    print(f"  High Churn Threshold: {config.thresholds.high_churn_probability:.1%}")
    print(f"  Critical Due Days: {config.timing.critical_due_days} day(s)")
    print(f"  Max Interventions per Tutor: {config.max_interventions_per_tutor}")
    print()

    # Create framework with custom config
    framework = InterventionFramework(config)

    # Test with same critical risk tutor from Demo 1
    tutor = TutorState(
        tutor_id="T001",
        tutor_name="Alice Johnson",
        churn_probability=0.72,  # Below new 0.75 threshold
        churn_score=82,
        risk_level=RiskLevel.HIGH.value,
        avg_rating=3.3,
        engagement_score=0.50,
        performance_tier=PerformanceTier.AT_RISK.value,
        sessions_completed=18,
        reschedule_rate=0.25,
    )

    print(f"Evaluating {tutor.tutor_name} with custom configuration:")
    print(f"  Churn Probability: {tutor.churn_probability:.1%} "
          f"(below new threshold of {config.thresholds.critical_churn_probability:.1%})")
    print()

    triggers = framework.evaluate_tutor_for_interventions(tutor)

    print(f"Triggered Interventions: {len(triggers)}")
    for i, trigger in enumerate(triggers, 1):
        print(f"  {i}. {trigger.intervention_type.value} ({trigger.priority.value})")
        print(f"     Due in {trigger.due_days} day(s)")


def demo_rule_enablement():
    """Demo 6: Enable/disable specific rules."""
    print_section("Demo 6: Rule Enablement Control")

    # Create config and disable recognition rules
    config = InterventionConfig()
    config.enablement.recognition_high_performer = False
    config.enablement.recognition_improvement = False

    print("Disabled Rules:")
    print("  - recognition_high_performer")
    print("  - recognition_improvement")
    print()

    framework = InterventionFramework(config)

    # High performer who would normally get recognition
    tutor = TutorState(
        tutor_id="T004",
        tutor_name="David Chen",
        churn_probability=0.08,
        churn_score=10,
        risk_level=RiskLevel.LOW.value,
        avg_rating=4.9,
        engagement_score=0.91,
        performance_tier=PerformanceTier.EXEMPLARY.value,
        sessions_completed=85,
    )

    print(f"Evaluating high performer: {tutor.tutor_name}")
    print(f"  Performance Tier: {tutor.performance_tier}")
    print(f"  Average Rating: {tutor.avg_rating}/5.0")
    print()

    triggers = framework.evaluate_tutor_for_interventions(tutor)

    if triggers:
        print(f"Triggered Interventions: {len(triggers)}")
        for trigger in triggers:
            print(f"  - {trigger.intervention_type.value}")
    else:
        print("✓ No interventions triggered (recognition rules disabled)")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "INTERVENTION RULE ENGINE DEMO" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        demo_critical_risk_tutor()
        demo_high_risk_tutor()
        demo_baseline_tutor()
        demo_high_performer()
        demo_custom_configuration()
        demo_rule_enablement()

        print_section("Demo Complete!")
        print("The intervention rule engine successfully:")
        print("  ✓ Evaluated tutors across different risk levels")
        print("  ✓ Triggered appropriate interventions based on metrics")
        print("  ✓ Applied custom configurations and thresholds")
        print("  ✓ Managed rule enablement/disablement")
        print("  ✓ Sorted interventions by priority")
        print()
        print("Next Steps:")
        print("  1. Integrate with email/notification systems (Task 5.3)")
        print("  2. Set up A/B testing for intervention effectiveness (Task 5.4)")
        print("  3. Deploy to production with monitoring")
        print()

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
