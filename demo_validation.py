#!/usr/bin/env python3
"""
Validation System Demo

Demonstrates the data validation module for TutorMax.
Shows validation of tutors, sessions, and feedback data with various scenarios.
"""

import logging
from datetime import datetime
from src.pipeline.validation import (
    ValidationEngine,
    TutorValidator,
    SessionValidator,
    FeedbackValidator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_tutor_validation():
    """Demonstrate tutor data validation."""
    logger.info("=" * 60)
    logger.info("TUTOR VALIDATION DEMO")
    logger.info("=" * 60)

    validator = TutorValidator()

    # Valid tutor
    valid_tutor = {
        "tutor_id": "tutor_00001",
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "age": 28,
        "location": "New York",
        "education_level": "Master's Degree",
        "subjects": ["Mathematics", "Algebra"],
        "subject_type": "STEM",
        "onboarding_date": "2024-01-15T10:00:00",
        "tenure_days": 120,
        "behavioral_archetype": "high_performer",
        "baseline_sessions_per_week": 20,
        "status": "active",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-05-14T10:00:00"
    }

    logger.info("\n1. Validating VALID tutor data:")
    result = validator.validate(valid_tutor)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")
    logger.info(f"   Warnings: {len(result.warnings)}")

    # Invalid tutor - age out of range
    invalid_tutor = valid_tutor.copy()
    invalid_tutor["age"] = 70

    logger.info("\n2. Validating INVALID tutor (age > 65):")
    result = validator.validate(invalid_tutor)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")

    # Invalid tutor - bad email
    invalid_tutor2 = valid_tutor.copy()
    invalid_tutor2["email"] = "not-an-email"

    logger.info("\n3. Validating INVALID tutor (bad email):")
    result = validator.validate(invalid_tutor2)
    logger.info(f"   Valid: {result.valid}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")

    # Invalid tutor - invalid subject
    invalid_tutor3 = valid_tutor.copy()
    invalid_tutor3["subjects"] = ["InvalidSubject"]

    logger.info("\n4. Validating INVALID tutor (invalid subject):")
    result = validator.validate(invalid_tutor3)
    logger.info(f"   Valid: {result.valid}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")


def demo_session_validation():
    """Demonstrate session data validation."""
    logger.info("\n" + "=" * 60)
    logger.info("SESSION VALIDATION DEMO")
    logger.info("=" * 60)

    validator = SessionValidator()

    # Valid session
    valid_session = {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "tutor_id": "tutor_00001",
        "student_id": "student_00042",
        "session_number": 1,
        "is_first_session": True,
        "scheduled_start": "2024-05-14T15:00:00",
        "actual_start": "2024-05-14T15:02:00",
        "duration_minutes": 60,
        "subject": "Algebra",
        "session_type": "1-on-1",
        "tutor_initiated_reschedule": False,
        "no_show": False,
        "late_start_minutes": 2,
        "engagement_score": 0.92,
        "learning_objectives_met": True,
        "technical_issues": False,
        "created_at": "2024-05-14T15:00:00",
        "updated_at": "2024-05-14T16:05:00"
    }

    logger.info("\n1. Validating VALID session data:")
    result = validator.validate(valid_session)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")
    logger.info(f"   Warnings: {len(result.warnings)}")

    # No-show session
    no_show_session = valid_session.copy()
    no_show_session["no_show"] = True
    no_show_session["actual_start"] = None
    no_show_session["engagement_score"] = 0.0

    logger.info("\n2. Validating NO-SHOW session:")
    result = validator.validate(no_show_session)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")

    # Invalid session - engagement score out of range
    invalid_session = valid_session.copy()
    invalid_session["engagement_score"] = 1.5

    logger.info("\n3. Validating INVALID session (engagement > 1.0):")
    result = validator.validate(invalid_session)
    logger.info(f"   Valid: {result.valid}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")

    # Invalid session - late start exceeds duration
    invalid_session2 = valid_session.copy()
    invalid_session2["late_start_minutes"] = 70
    invalid_session2["duration_minutes"] = 60

    logger.info("\n4. Validating INVALID session (late_start > duration):")
    result = validator.validate(invalid_session2)
    logger.info(f"   Valid: {result.valid}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")


def demo_feedback_validation():
    """Demonstrate feedback data validation."""
    logger.info("\n" + "=" * 60)
    logger.info("FEEDBACK VALIDATION DEMO")
    logger.info("=" * 60)

    validator = FeedbackValidator()

    # Valid feedback
    valid_feedback = {
        "feedback_id": "660e8400-e29b-41d4-a716-446655440000",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "student_id": "student_00042",
        "tutor_id": "tutor_00001",
        "overall_rating": 5,
        "is_first_session": False,
        "subject_knowledge_rating": 5,
        "communication_rating": 5,
        "patience_rating": 4,
        "engagement_rating": 5,
        "helpfulness_rating": 5,
        "free_text_feedback": "Great session, very helpful!",
        "submitted_at": "2024-05-14T18:30:00",
        "created_at": "2024-05-14T18:30:00",
        "would_recommend": None,
        "improvement_areas": None
    }

    logger.info("\n1. Validating VALID feedback data:")
    result = validator.validate(valid_feedback)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")
    logger.info(f"   Warnings: {len(result.warnings)}")

    # First session feedback
    first_session_feedback = valid_feedback.copy()
    first_session_feedback["is_first_session"] = True
    first_session_feedback["would_recommend"] = True
    first_session_feedback["improvement_areas"] = ["pacing"]

    logger.info("\n2. Validating FIRST SESSION feedback:")
    result = validator.validate(first_session_feedback)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Errors: {len(result.errors)}")

    # Invalid feedback - rating out of range
    invalid_feedback = valid_feedback.copy()
    invalid_feedback["overall_rating"] = 6

    logger.info("\n3. Validating INVALID feedback (rating > 5):")
    result = validator.validate(invalid_feedback)
    logger.info(f"   Valid: {result.valid}")
    for error in result.errors:
        logger.info(f"   - {error.field}: {error.message}")

    # Feedback with warning - inconsistent ratings
    warning_feedback = valid_feedback.copy()
    warning_feedback["overall_rating"] = 2
    warning_feedback["subject_knowledge_rating"] = 5
    warning_feedback["communication_rating"] = 5
    warning_feedback["patience_rating"] = 5
    warning_feedback["engagement_rating"] = 5
    warning_feedback["helpfulness_rating"] = 5

    logger.info("\n4. Validating feedback with WARNING (inconsistent ratings):")
    result = validator.validate(warning_feedback)
    logger.info(f"   Valid: {result.valid}")
    logger.info(f"   Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        logger.info(f"   - {warning.field}: {warning.message}")


def demo_validation_engine():
    """Demonstrate the validation engine."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION ENGINE DEMO")
    logger.info("=" * 60)

    engine = ValidationEngine()

    # Test data
    tutor_data = {
        "tutor_id": "tutor_00001",
        "name": "Alice",
        "email": "alice@example.com",
        "age": 28,
        "location": "NY",
        "education_level": "Master's",
        "subjects": ["Math"],
        "subject_type": "STEM",
        "onboarding_date": "2024-01-15T10:00:00",
        "tenure_days": 120,
        "behavioral_archetype": "high_performer",
        "baseline_sessions_per_week": 20,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-05-14T10:00:00"
    }

    session_data = {
        "session_id": "test-session",
        "tutor_id": "tutor_00001",
        "student_id": "student_001",
        "session_number": 1,
        "is_first_session": True,
        "scheduled_start": "2024-05-14T15:00:00",
        "actual_start": "2024-05-14T15:00:00",
        "duration_minutes": 60,
        "subject": "Mathematics",
        "session_type": "1-on-1",
        "tutor_initiated_reschedule": False,
        "no_show": False,
        "late_start_minutes": 0,
        "engagement_score": 0.9,
        "learning_objectives_met": True,
        "technical_issues": False,
        "created_at": "2024-05-14T15:00:00",
        "updated_at": "2024-05-14T16:00:00"
    }

    feedback_data = {
        "feedback_id": "test-feedback",
        "session_id": "test-session",
        "student_id": "student_001",
        "tutor_id": "tutor_00001",
        "overall_rating": 5,
        "is_first_session": True,
        "subject_knowledge_rating": 5,
        "communication_rating": 5,
        "patience_rating": 5,
        "engagement_rating": 5,
        "helpfulness_rating": 5,
        "free_text_feedback": "Excellent!",
        "submitted_at": "2024-05-14T18:00:00",
        "created_at": "2024-05-14T18:00:00",
        "would_recommend": True,
        "improvement_areas": []
    }

    logger.info("\n1. Validating all data types:")
    result1 = engine.validate_tutor(tutor_data)
    result2 = engine.validate_session(session_data)
    result3 = engine.validate_feedback(feedback_data)

    logger.info(f"   Tutor valid: {result1.valid}")
    logger.info(f"   Session valid: {result2.valid}")
    logger.info(f"   Feedback valid: {result3.valid}")

    logger.info("\n2. Engine statistics:")
    stats = engine.get_stats()
    logger.info(f"   Total validated: {stats['total_validated']}")
    logger.info(f"   Valid count: {stats['valid_count']}")
    logger.info(f"   Invalid count: {stats['invalid_count']}")
    logger.info(f"   By type: {stats['by_type']}")


def main():
    """Run all demos."""
    logger.info("TutorMax Data Validation System Demo")
    logger.info("=" * 60)

    demo_tutor_validation()
    demo_session_validation()
    demo_feedback_validation()
    demo_validation_engine()

    logger.info("\n" + "=" * 60)
    logger.info("DEMO COMPLETED")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
