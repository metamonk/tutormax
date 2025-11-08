"""
Tests for validation engine.
"""

import pytest

from src.pipeline.validation.validation_engine import ValidationEngine


@pytest.fixture
def engine():
    """Create a validation engine instance."""
    return ValidationEngine()


@pytest.fixture
def valid_tutor_data():
    """Create valid tutor data."""
    return {
        "tutor_id": "tutor_00001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 28,
        "location": "New York",
        "education_level": "Master's Degree",
        "subjects": ["Mathematics"],
        "subject_type": "STEM",
        "onboarding_date": "2024-01-15T10:00:00",
        "tenure_days": 120,
        "behavioral_archetype": "high_performer",
        "baseline_sessions_per_week": 20,
        "status": "active",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-05-14T10:00:00"
    }


@pytest.fixture
def valid_session_data():
    """Create valid session data."""
    return {
        "session_id": "test-session",
        "tutor_id": "tutor_00001",
        "student_id": "student_00042",
        "session_number": 1,
        "is_first_session": True,
        "scheduled_start": "2024-05-14T15:00:00",
        "actual_start": "2024-05-14T15:00:00",
        "duration_minutes": 60,
        "subject": "Algebra",
        "session_type": "1-on-1",
        "tutor_initiated_reschedule": False,
        "no_show": False,
        "late_start_minutes": 0,
        "engagement_score": 0.92,
        "learning_objectives_met": True,
        "technical_issues": False,
        "created_at": "2024-05-14T15:00:00",
        "updated_at": "2024-05-14T16:05:00"
    }


@pytest.fixture
def valid_feedback_data():
    """Create valid feedback data."""
    return {
        "feedback_id": "test-feedback",
        "session_id": "test-session",
        "student_id": "student_00042",
        "tutor_id": "tutor_00001",
        "overall_rating": 5,
        "is_first_session": True,
        "subject_knowledge_rating": 5,
        "communication_rating": 5,
        "patience_rating": 5,
        "engagement_rating": 5,
        "helpfulness_rating": 5,
        "free_text_feedback": "Great!",
        "submitted_at": "2024-05-14T18:30:00",
        "created_at": "2024-05-14T18:30:00",
        "would_recommend": True,
        "improvement_areas": []
    }


class TestValidationEngine:
    """Test cases for ValidationEngine."""

    def test_validate_tutor(self, engine, valid_tutor_data):
        """Test validating tutor data."""
        result = engine.validate_tutor(valid_tutor_data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_session(self, engine, valid_session_data):
        """Test validating session data."""
        result = engine.validate_session(valid_session_data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_feedback(self, engine, valid_feedback_data):
        """Test validating feedback data."""
        result = engine.validate_feedback(valid_feedback_data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_with_explicit_type(self, engine, valid_tutor_data):
        """Test validate method with explicit data type."""
        result = engine.validate(valid_tutor_data, "tutor")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_unknown_type(self, engine, valid_tutor_data):
        """Test that unknown data type is rejected."""
        result = engine.validate(valid_tutor_data, "unknown_type")

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("_type" in e.field for e in result.errors)

    def test_engine_statistics(
        self, engine, valid_tutor_data, valid_session_data, valid_feedback_data
    ):
        """Test that engine tracks statistics across all validators."""
        # Validate various data types
        engine.validate_tutor(valid_tutor_data)
        engine.validate_session(valid_session_data)
        engine.validate_feedback(valid_feedback_data)

        # Validate invalid data
        invalid_tutor = valid_tutor_data.copy()
        invalid_tutor["age"] = 100
        engine.validate_tutor(invalid_tutor)

        stats = engine.get_stats()

        # Check overall stats
        assert stats["total_validated"] == 4
        assert stats["valid_count"] == 3
        assert stats["invalid_count"] == 1

        # Check per-type stats
        assert stats["by_type"]["tutor"]["valid"] == 1
        assert stats["by_type"]["tutor"]["invalid"] == 1
        assert stats["by_type"]["session"]["valid"] == 1
        assert stats["by_type"]["feedback"]["valid"] == 1

    def test_reset_stats(self, engine, valid_tutor_data):
        """Test that reset_stats clears all statistics."""
        # Generate some stats
        engine.validate_tutor(valid_tutor_data)

        # Reset
        engine.reset_stats()

        stats = engine.get_stats()
        assert stats["total_validated"] == 0
        assert stats["valid_count"] == 0
        assert stats["invalid_count"] == 0

    def test_case_insensitive_type(self, engine, valid_tutor_data):
        """Test that data type is case-insensitive."""
        result1 = engine.validate(valid_tutor_data, "tutor")
        result2 = engine.validate(valid_tutor_data, "TUTOR")
        result3 = engine.validate(valid_tutor_data, "Tutor")

        assert result1.valid is True
        assert result2.valid is True
        assert result3.valid is True

    def test_multiple_validation_calls(self, engine, valid_tutor_data):
        """Test that multiple validation calls work correctly."""
        for _ in range(10):
            result = engine.validate_tutor(valid_tutor_data)
            assert result.valid is True

        stats = engine.get_stats()
        assert stats["total_validated"] == 10
        assert stats["valid_count"] == 10

    def test_mixed_valid_invalid(self, engine, valid_tutor_data):
        """Test mixture of valid and invalid data."""
        # Valid
        engine.validate_tutor(valid_tutor_data)

        # Invalid
        invalid = valid_tutor_data.copy()
        invalid["email"] = "not-an-email"
        engine.validate_tutor(invalid)

        # Valid
        engine.validate_tutor(valid_tutor_data)

        stats = engine.get_stats()
        assert stats["total_validated"] == 3
        assert stats["valid_count"] == 2
        assert stats["invalid_count"] == 1
