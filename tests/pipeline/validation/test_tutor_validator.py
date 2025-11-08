"""
Tests for tutor validator.
"""

import pytest
from datetime import datetime, timedelta

from src.pipeline.validation.tutor_validator import TutorValidator


@pytest.fixture
def validator():
    """Create a tutor validator instance."""
    return TutorValidator()


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


class TestTutorValidator:
    """Test cases for TutorValidator."""

    def test_valid_tutor_data(self, validator, valid_tutor_data):
        """Test that valid tutor data passes validation."""
        result = validator.validate(valid_tutor_data)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.metadata["validator"] == "TutorValidator"
        assert result.metadata["tutor_id"] == "tutor_00001"

    def test_missing_required_fields(self, validator):
        """Test that missing required fields are caught."""
        data = {
            "tutor_id": "tutor_00001",
            "name": "John Doe"
            # Missing other required fields
        }

        result = validator.validate(data)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("email" in e.field for e in result.errors)

    def test_invalid_email(self, validator, valid_tutor_data):
        """Test that invalid email is caught."""
        valid_tutor_data["email"] = "not-an-email"

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("email" in e.field for e in result.errors)

    def test_age_below_minimum(self, validator, valid_tutor_data):
        """Test that age below 22 is rejected."""
        valid_tutor_data["age"] = 21

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("age" in e.field for e in result.errors)

    def test_age_above_maximum(self, validator, valid_tutor_data):
        """Test that age above 65 is rejected."""
        valid_tutor_data["age"] = 66

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("age" in e.field for e in result.errors)

    def test_invalid_behavioral_archetype(self, validator, valid_tutor_data):
        """Test that invalid behavioral archetype is rejected."""
        valid_tutor_data["behavioral_archetype"] = "invalid_archetype"

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("behavioral_archetype" in e.field for e in result.errors)

    def test_invalid_subject_type(self, validator, valid_tutor_data):
        """Test that invalid subject type is rejected."""
        valid_tutor_data["subject_type"] = "InvalidType"

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("subject_type" in e.field for e in result.errors)

    def test_invalid_subjects(self, validator, valid_tutor_data):
        """Test that invalid subjects are rejected."""
        valid_tutor_data["subjects"] = ["InvalidSubject"]

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("subjects" in e.field for e in result.errors)

    def test_empty_subjects_list(self, validator, valid_tutor_data):
        """Test that empty subjects list is rejected."""
        valid_tutor_data["subjects"] = []

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("subjects" in e.field for e in result.errors)

    def test_too_many_subjects(self, validator, valid_tutor_data):
        """Test that more than 10 subjects is rejected."""
        valid_tutor_data["subjects"] = [
            "Mathematics", "Algebra", "Calculus", "Geometry",
            "Physics", "Chemistry", "Biology", "Computer Science",
            "English", "Writing", "Literature"  # 11 subjects
        ]

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("subjects" in e.field for e in result.errors)

    def test_baseline_sessions_below_minimum(self, validator, valid_tutor_data):
        """Test that baseline sessions below 5 is rejected."""
        valid_tutor_data["baseline_sessions_per_week"] = 4

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("baseline_sessions_per_week" in e.field for e in result.errors)

    def test_baseline_sessions_above_maximum(self, validator, valid_tutor_data):
        """Test that baseline sessions above 30 is rejected."""
        valid_tutor_data["baseline_sessions_per_week"] = 31

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("baseline_sessions_per_week" in e.field for e in result.errors)

    def test_negative_tenure(self, validator, valid_tutor_data):
        """Test that negative tenure is rejected."""
        valid_tutor_data["tenure_days"] = -1

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("tenure_days" in e.field for e in result.errors)

    def test_invalid_status(self, validator, valid_tutor_data):
        """Test that invalid status is rejected."""
        valid_tutor_data["status"] = "invalid_status"

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("status" in e.field for e in result.errors)

    def test_invalid_date_format(self, validator, valid_tutor_data):
        """Test that invalid date format is rejected."""
        valid_tutor_data["onboarding_date"] = "not-a-date"

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("onboarding_date" in e.field for e in result.errors)

    def test_future_onboarding_date(self, validator, valid_tutor_data):
        """Test that future onboarding date is rejected."""
        future_date = (datetime.now() + timedelta(days=10)).isoformat()
        valid_tutor_data["onboarding_date"] = future_date

        result = validator.validate(valid_tutor_data)

        assert result.valid is False
        assert any("onboarding_date" in e.field for e in result.errors)

    def test_created_before_onboarding_warning(self, validator, valid_tutor_data):
        """Test that created_at before onboarding_date generates warning."""
        valid_tutor_data["onboarding_date"] = "2024-05-01T10:00:00"
        valid_tutor_data["created_at"] = "2024-04-01T10:00:00"

        result = validator.validate(valid_tutor_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("created_at" in w.field for w in result.warnings)

    def test_all_valid_behavioral_archetypes(self, validator, valid_tutor_data):
        """Test that all valid behavioral archetypes are accepted."""
        archetypes = [
            "high_performer", "at_risk", "new_tutor", "steady", "churner"
        ]

        for archetype in archetypes:
            valid_tutor_data["behavioral_archetype"] = archetype
            result = validator.validate(valid_tutor_data)
            assert result.valid is True, f"Archetype {archetype} should be valid"

    def test_all_valid_subject_types(self, validator, valid_tutor_data):
        """Test that all valid subject types are accepted."""
        subject_types = ["STEM", "Language", "TestPrep"]

        for subject_type in subject_types:
            valid_tutor_data["subject_type"] = subject_type
            result = validator.validate(valid_tutor_data)
            assert result.valid is True, f"Subject type {subject_type} should be valid"

    def test_validator_statistics(self, validator, valid_tutor_data):
        """Test that validator tracks statistics."""
        # Validate valid data
        validator.validate(valid_tutor_data)

        # Validate invalid data
        invalid_data = valid_tutor_data.copy()
        invalid_data["age"] = 100
        validator.validate(invalid_data)

        stats = validator.get_stats()
        assert stats["total_validated"] == 2
        assert stats["valid_count"] == 1
        assert stats["invalid_count"] == 1
