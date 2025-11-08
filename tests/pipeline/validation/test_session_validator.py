"""
Tests for session validator.
"""

import pytest
from datetime import datetime, timedelta

from src.pipeline.validation.session_validator import SessionValidator


@pytest.fixture
def validator():
    """Create a session validator instance."""
    return SessionValidator()


@pytest.fixture
def valid_session_data():
    """Create valid session data."""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "tutor_id": "tutor_00001",
        "student_id": "student_00042",
        "session_number": 3,
        "is_first_session": False,
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


class TestSessionValidator:
    """Test cases for SessionValidator."""

    def test_valid_session_data(self, validator, valid_session_data):
        """Test that valid session data passes validation."""
        result = validator.validate(valid_session_data)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.metadata["validator"] == "SessionValidator"
        assert result.metadata["session_id"] == "550e8400-e29b-41d4-a716-446655440000"

    def test_missing_required_fields(self, validator):
        """Test that missing required fields are caught."""
        data = {
            "session_id": "test-session",
            "tutor_id": "tutor_00001"
            # Missing other required fields
        }

        result = validator.validate(data)

        assert result.valid is False
        assert len(result.errors) > 0

    def test_invalid_session_number(self, validator, valid_session_data):
        """Test that session number < 1 is rejected."""
        valid_session_data["session_number"] = 0

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("session_number" in e.field for e in result.errors)

    def test_invalid_subject(self, validator, valid_session_data):
        """Test that invalid subject is rejected."""
        valid_session_data["subject"] = "InvalidSubject"

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("subject" in e.field for e in result.errors)

    def test_invalid_session_type(self, validator, valid_session_data):
        """Test that invalid session type is rejected."""
        valid_session_data["session_type"] = "invalid_type"

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("session_type" in e.field for e in result.errors)

    def test_engagement_score_below_minimum(self, validator, valid_session_data):
        """Test that engagement score < 0.0 is rejected."""
        valid_session_data["engagement_score"] = -0.1

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("engagement_score" in e.field for e in result.errors)

    def test_engagement_score_above_maximum(self, validator, valid_session_data):
        """Test that engagement score > 1.0 is rejected."""
        valid_session_data["engagement_score"] = 1.1

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("engagement_score" in e.field for e in result.errors)

    def test_scheduled_too_far_in_future(self, validator, valid_session_data):
        """Test that scheduled date more than 30 days in future is rejected."""
        future_date = (datetime.now() + timedelta(days=31)).isoformat()
        valid_session_data["scheduled_start"] = future_date

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("scheduled_start" in e.field for e in result.errors)

    def test_future_actual_start(self, validator, valid_session_data):
        """Test that future actual_start is rejected."""
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        valid_session_data["actual_start"] = future_date

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("actual_start" in e.field for e in result.errors)

    def test_no_show_with_actual_start(self, validator, valid_session_data):
        """Test that no-show session with actual_start is rejected."""
        valid_session_data["no_show"] = True
        # actual_start should be None for no-shows

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("actual_start" in e.field for e in result.errors)

    def test_no_show_without_actual_start(self, validator, valid_session_data):
        """Test that no-show session without actual_start is valid."""
        valid_session_data["no_show"] = True
        valid_session_data["actual_start"] = None

        result = validator.validate(valid_session_data)

        assert result.valid is True

    def test_non_no_show_without_actual_start_warning(self, validator, valid_session_data):
        """Test that non-no-show without actual_start generates warning."""
        valid_session_data["no_show"] = False
        valid_session_data["actual_start"] = None

        result = validator.validate(valid_session_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("actual_start" in w.field for w in result.warnings)

    def test_late_start_exceeds_duration(self, validator, valid_session_data):
        """Test that late_start > duration is rejected."""
        valid_session_data["duration_minutes"] = 60
        valid_session_data["late_start_minutes"] = 65

        result = validator.validate(valid_session_data)

        assert result.valid is False
        assert any("late_start_minutes" in e.field for e in result.errors)

    def test_duration_not_standard_warning(self, validator, valid_session_data):
        """Test that non-standard duration generates warning."""
        valid_session_data["duration_minutes"] = 55  # Not in [30, 45, 60, 90]

        result = validator.validate(valid_session_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("duration_minutes" in w.field for w in result.warnings)

    def test_first_session_with_session_number_1(self, validator, valid_session_data):
        """Test that first session with session_number=1 is valid."""
        valid_session_data["is_first_session"] = True
        valid_session_data["session_number"] = 1

        result = validator.validate(valid_session_data)

        assert result.valid is True

    def test_first_session_with_wrong_session_number_warning(self, validator, valid_session_data):
        """Test that first session with session_number != 1 generates warning."""
        valid_session_data["is_first_session"] = True
        valid_session_data["session_number"] = 3

        result = validator.validate(valid_session_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("session_number" in w.field for w in result.warnings)

    def test_no_show_high_engagement_warning(self, validator, valid_session_data):
        """Test that no-show with high engagement generates warning."""
        valid_session_data["no_show"] = True
        valid_session_data["actual_start"] = None
        valid_session_data["engagement_score"] = 0.8

        result = validator.validate(valid_session_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("engagement_score" in w.field for w in result.warnings)

    def test_all_valid_durations(self, validator, valid_session_data):
        """Test that all standard durations are accepted without warning."""
        durations = [30, 45, 60, 90]

        for duration in durations:
            valid_session_data["duration_minutes"] = duration
            result = validator.validate(valid_session_data)
            assert result.valid is True
            # Should not have duration warning
            assert not any("duration_minutes" in w.field for w in result.warnings)

    def test_all_valid_session_types(self, validator, valid_session_data):
        """Test that all valid session types are accepted."""
        session_types = ["1-on-1", "group", "workshop"]

        for session_type in session_types:
            valid_session_data["session_type"] = session_type
            result = validator.validate(valid_session_data)
            assert result.valid is True

    def test_validator_statistics(self, validator, valid_session_data):
        """Test that validator tracks statistics."""
        # Validate valid data
        validator.validate(valid_session_data)

        # Validate invalid data
        invalid_data = valid_session_data.copy()
        invalid_data["engagement_score"] = 2.0
        validator.validate(invalid_data)

        stats = validator.get_stats()
        assert stats["total_validated"] == 2
        assert stats["valid_count"] == 1
        assert stats["invalid_count"] == 1
