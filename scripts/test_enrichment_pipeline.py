#!/usr/bin/env python3
"""
Test script for enrichment pipeline end-to-end flow.

This script demonstrates the complete enrichment pipeline:
1. Generate sample data
2. Enrich data with derived fields
3. Prepare for database persistence
4. Display results
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.enrichment import (
    TutorEnricher,
    SessionEnricher,
    FeedbackEnricher,
    EnrichmentEngine,
)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print(f"{'=' * 60}\n")


def print_result(label: str, data: dict):
    """Print enrichment result."""
    print(f"{label}:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    print()


def test_tutor_enrichment():
    """Test tutor data enrichment."""
    print_section("TUTOR ENRICHMENT")

    enricher = TutorEnricher()

    # Test different tutor scenarios
    test_cases = [
        {
            "name": "New Tutor (15 days)",
            "data": {
                "tutor_id": "T001",
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
                "status": "active",
                "subjects": ["Math", "Physics"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "name": "Mid-level Tutor (180 days)",
            "data": {
                "tutor_id": "T002",
                "name": "Bob Smith",
                "email": "bob@example.com",
                "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=180)).isoformat(),
                "status": "active",
                "subjects": ["Chemistry", "Biology", "Physics", "Math"],
                "updated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            },
        },
        {
            "name": "Senior Tutor (500 days)",
            "data": {
                "tutor_id": "T003",
                "name": "Carol Williams",
                "email": "carol@example.com",
                "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(),
                "status": "active",
                "subjects": ["English", "History"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    ]

    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        result = enricher.enrich(test_case["data"])

        if result.success:
            print("✓ Enrichment successful")
            print_result("Derived Fields", result.derived_fields)
        else:
            print(f"✗ Enrichment failed: {result.errors}")

    # Print stats
    print_result("Enricher Statistics", enricher.get_stats())


def test_session_enrichment():
    """Test session data enrichment."""
    print_section("SESSION ENRICHMENT")

    enricher = SessionEnricher()

    # Test different session scenarios
    test_cases = [
        {
            "name": "Weekend Morning Session",
            "data": {
                "session_id": "S001",
                "tutor_id": "T001",
                "student_id": "ST001",
                "session_number": 1,
                "scheduled_start": datetime(2024, 11, 9, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
                "duration_minutes": 60,
                "subject": "Math",
                "late_start_minutes": 2,
            },
        },
        {
            "name": "Weekday Evening Session (Late)",
            "data": {
                "session_id": "S002",
                "tutor_id": "T002",
                "student_id": "ST002",
                "session_number": 5,
                "scheduled_start": datetime(2024, 11, 7, 18, 0, 0, tzinfo=timezone.utc).isoformat(),
                "duration_minutes": 90,
                "subject": "Physics",
                "late_start_minutes": 10,
            },
        },
        {
            "name": "Afternoon Session with Actual Start",
            "data": {
                "session_id": "S003",
                "tutor_id": "T003",
                "student_id": "ST003",
                "session_number": 10,
                "scheduled_start": datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
                "actual_start": datetime(2024, 11, 7, 14, 5, 0, tzinfo=timezone.utc).isoformat(),
                "duration_minutes": 60,
                "subject": "English",
                "late_start_minutes": 5,
            },
        },
    ]

    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        result = enricher.enrich(test_case["data"])

        if result.success:
            print("✓ Enrichment successful")
            print_result("Derived Fields", result.derived_fields)
        else:
            print(f"✗ Enrichment failed: {result.errors}")

    # Print stats
    print_result("Enricher Statistics", enricher.get_stats())


def test_feedback_enrichment():
    """Test feedback data enrichment."""
    print_section("FEEDBACK ENRICHMENT")

    enricher = FeedbackEnricher()

    # Test different feedback scenarios
    test_cases = [
        {
            "name": "Positive Feedback (No Text)",
            "data": {
                "feedback_id": "F001",
                "session_id": "S001",
                "student_id": "ST001",
                "tutor_id": "T001",
                "overall_rating": 5,
                "subject_knowledge_rating": 5,
                "communication_rating": 5,
                "patience_rating": 5,
                "engagement_rating": 5,
                "helpfulness_rating": 5,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "name": "Poor Feedback with Variance",
            "data": {
                "feedback_id": "F002",
                "session_id": "S002",
                "student_id": "ST002",
                "tutor_id": "T002",
                "overall_rating": 2,
                "subject_knowledge_rating": 3,
                "communication_rating": 2,
                "patience_rating": 1,
                "engagement_rating": 2,
                "helpfulness_rating": 2,
                "free_text_feedback": "Not very helpful, hard to understand.",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "name": "Mixed Feedback with Delay",
            "data": {
                "feedback_id": "F003",
                "session_id": "S003",
                "student_id": "ST003",
                "tutor_id": "T003",
                "overall_rating": 4,
                "subject_knowledge_rating": 5,
                "communication_rating": 4,
                "patience_rating": 3,
                "engagement_rating": 4,
                "helpfulness_rating": 4,
                "free_text_feedback": "Good session overall, could be more engaging.",
                "session_scheduled_start": (
                    datetime.now(timezone.utc) - timedelta(hours=12)
                ).isoformat(),
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    ]

    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        result = enricher.enrich(test_case["data"])

        if result.success:
            print("✓ Enrichment successful")
            print_result("Derived Fields", result.derived_fields)
        else:
            print(f"✗ Enrichment failed: {result.errors}")

    # Print stats
    print_result("Enricher Statistics", enricher.get_stats())


def test_enrichment_engine():
    """Test enrichment engine with all data types."""
    print_section("ENRICHMENT ENGINE")

    engine = EnrichmentEngine()

    # Prepare test data
    tutor_data = {
        "tutor_id": "T100",
        "name": "David Brown",
        "email": "david@example.com",
        "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
        "status": "active",
        "subjects": ["Math", "Statistics"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    session_data = {
        "session_id": "S100",
        "tutor_id": "T100",
        "student_id": "ST100",
        "session_number": 3,
        "scheduled_start": datetime(2024, 11, 7, 15, 0, 0, tzinfo=timezone.utc).isoformat(),
        "duration_minutes": 60,
        "subject": "Math",
        "late_start_minutes": 3,
    }

    feedback_data = {
        "feedback_id": "F100",
        "session_id": "S100",
        "student_id": "ST100",
        "tutor_id": "T100",
        "overall_rating": 4,
        "subject_knowledge_rating": 5,
        "communication_rating": 4,
        "patience_rating": 4,
        "engagement_rating": 4,
        "helpfulness_rating": 5,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Enrich all data types
    print("Enriching tutor...")
    tutor_result = engine.enrich(tutor_data, "tutor")
    print(f"✓ Success: {tutor_result.success}")

    print("\nEnriching session...")
    session_result = engine.enrich(session_data, "session")
    print(f"✓ Success: {session_result.success}")

    print("\nEnriching feedback...")
    feedback_result = engine.enrich(feedback_data, "feedback")
    print(f"✓ Success: {feedback_result.success}")

    # Test invalid data
    print("\nEnriching invalid data...")
    invalid_result = engine.enrich({}, "tutor")
    print(f"✗ Expected failure: {not invalid_result.success}")

    # Print overall stats
    print()
    print_result("Engine Statistics", engine.get_stats())


def main():
    """Run all enrichment tests."""
    print("\n" + "=" * 60)
    print("ENRICHMENT PIPELINE TEST SUITE".center(60))
    print("=" * 60)

    try:
        test_tutor_enrichment()
        test_session_enrichment()
        test_feedback_enrichment()
        test_enrichment_engine()

        print_section("TEST SUMMARY")
        print("✓ All enrichment tests completed successfully!")
        print("\nNext steps:")
        print("1. Start Redis: redis-server")
        print("2. Start PostgreSQL: ensure database is running")
        print("3. Run enrichment worker: python -m src.pipeline.enrichment.enrichment_worker")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
