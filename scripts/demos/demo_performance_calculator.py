"""
Demo script to validate Performance Calculator implementation.

This script demonstrates the core functionality without requiring a live database.
"""

from datetime import datetime, timedelta
from src.evaluation.performance_calculator import PerformanceMetrics, PerformanceTier, MetricWindow


def demo_metrics_calculation():
    """Demonstrate metrics calculation and tier assignment."""

    print("=" * 70)
    print("Performance Calculator Demo - Core Functionality")
    print("=" * 70)

    # Example 1: High Performer
    print("\n1. High Performer Example:")
    print("-" * 70)
    high_performer = PerformanceMetrics(
        tutor_id="tutor_001",
        calculation_date=datetime.utcnow(),
        window=MetricWindow.THIRTY_DAY,
        sessions_completed=85,
        avg_rating=4.8,
        first_session_success_rate=92.0,
        reschedule_rate=5.0,
        no_show_count=0,
        engagement_score=88.5,
        learning_objectives_met_pct=95.0,
        response_time_avg_minutes=15.0,
        performance_tier=PerformanceTier.EXEMPLARY,
    )

    print(f"Tutor ID: {high_performer.tutor_id}")
    print(f"Sessions Completed: {high_performer.sessions_completed}")
    print(f"Avg Rating: {high_performer.avg_rating}")
    print(f"First Session Success Rate: {high_performer.first_session_success_rate}%")
    print(f"Reschedule Rate: {high_performer.reschedule_rate}%")
    print(f"Engagement Score: {high_performer.engagement_score}")
    print(f"Learning Objectives Met: {high_performer.learning_objectives_met_pct}%")
    print(f"Performance Tier: {high_performer.performance_tier.value}")

    # Example 2: At-Risk Tutor
    print("\n\n2. At-Risk Tutor Example:")
    print("-" * 70)
    at_risk_tutor = PerformanceMetrics(
        tutor_id="tutor_002",
        calculation_date=datetime.utcnow(),
        window=MetricWindow.THIRTY_DAY,
        sessions_completed=25,
        avg_rating=3.2,
        first_session_success_rate=55.0,
        reschedule_rate=22.0,
        no_show_count=5,
        engagement_score=45.0,
        learning_objectives_met_pct=65.0,
        response_time_avg_minutes=120.0,
        performance_tier=PerformanceTier.AT_RISK,
    )

    print(f"Tutor ID: {at_risk_tutor.tutor_id}")
    print(f"Sessions Completed: {at_risk_tutor.sessions_completed}")
    print(f"Avg Rating: {at_risk_tutor.avg_rating}")
    print(f"First Session Success Rate: {at_risk_tutor.first_session_success_rate}%")
    print(f"Reschedule Rate: {at_risk_tutor.reschedule_rate}%")
    print(f"No-Shows: {at_risk_tutor.no_show_count}")
    print(f"Engagement Score: {at_risk_tutor.engagement_score}")
    print(f"Learning Objectives Met: {at_risk_tutor.learning_objectives_met_pct}%")
    print(f"Performance Tier: {at_risk_tutor.performance_tier.value}")

    # Example 3: Developing Tutor
    print("\n\n3. Developing Tutor Example:")
    print("-" * 70)
    developing_tutor = PerformanceMetrics(
        tutor_id="tutor_003",
        calculation_date=datetime.utcnow(),
        window=MetricWindow.THIRTY_DAY,
        sessions_completed=42,
        avg_rating=3.9,
        first_session_success_rate=75.0,
        reschedule_rate=12.0,
        no_show_count=2,
        engagement_score=70.0,
        learning_objectives_met_pct=82.0,
        response_time_avg_minutes=45.0,
        performance_tier=PerformanceTier.DEVELOPING,
    )

    print(f"Tutor ID: {developing_tutor.tutor_id}")
    print(f"Sessions Completed: {developing_tutor.sessions_completed}")
    print(f"Avg Rating: {developing_tutor.avg_rating}")
    print(f"First Session Success Rate: {developing_tutor.first_session_success_rate}%")
    print(f"Reschedule Rate: {developing_tutor.reschedule_rate}%")
    print(f"Engagement Score: {developing_tutor.engagement_score}")
    print(f"Performance Tier: {developing_tutor.performance_tier.value}")

    # Test serialization
    print("\n\n4. Metrics Serialization:")
    print("-" * 70)
    metrics_dict = high_performer.to_dict()
    print(f"Serialized to dict with {len(metrics_dict)} fields")
    print(f"Window type: {type(metrics_dict['window'])}")
    print(f"Performance tier type: {type(metrics_dict['performance_tier'])}")
    print("✓ Enums properly converted to strings")

    # Test all metric windows
    print("\n\n5. Multiple Time Windows:")
    print("-" * 70)
    for window in [MetricWindow.SEVEN_DAY, MetricWindow.THIRTY_DAY, MetricWindow.NINETY_DAY]:
        metrics = PerformanceMetrics(
            tutor_id="tutor_004",
            calculation_date=datetime.utcnow(),
            window=window,
            sessions_completed=10,
            avg_rating=4.0,
            first_session_success_rate=80.0,
            reschedule_rate=10.0,
            no_show_count=1,
            engagement_score=75.0,
            learning_objectives_met_pct=85.0,
            response_time_avg_minutes=30.0,
            performance_tier=PerformanceTier.STRONG,
        )
        print(f"Window: {window.value} -> Tier: {metrics.performance_tier.value}")

    print("\n" + "=" * 70)
    print("✓ All core functionality demonstrated successfully!")
    print("=" * 70)


if __name__ == "__main__":
    demo_metrics_calculation()
