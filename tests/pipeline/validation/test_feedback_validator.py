"""
Tests for feedback validator.
"""

import pytest
from datetime import datetime

from src.pipeline.validation.feedback_validator import FeedbackValidator


@pytest.fixture
def validator():
    """Create a feedback validator instance."""
    return FeedbackValidator()


@pytest.fixture
def valid_feedback_data():
    """Create valid feedback data."""
    return {
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


@pytest.fixture
def valid_first_session_feedback():
    """Create valid first session feedback data."""
    return {
        "feedback_id": "660e8400-e29b-41d4-a716-446655440001",
        "session_id": "550e8400-e29b-41d4-a716-446655440001",
        "student_id": "student_00043",
        "tutor_id": "tutor_00002",
        "overall_rating": 4,
        "is_first_session": True,
        "subject_knowledge_rating": 5,
        "communication_rating": 4,
        "patience_rating": 4,
        "engagement_rating": 4,
        "helpfulness_rating": 4,
        "free_text_feedback": "Good first session",
        "submitted_at": "2024-05-14T18:30:00",
        "created_at": "2024-05-14T18:30:00",
        "would_recommend": True,
        "improvement_areas": ["pacing"]
    }


class TestFeedbackValidator:
    """Test cases for FeedbackValidator."""

    def test_valid_feedback_data(self, validator, valid_feedback_data):
        """Test that valid feedback data passes validation."""
        result = validator.validate(valid_feedback_data)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.metadata["validator"] == "FeedbackValidator"
        assert result.metadata["feedback_id"] == "660e8400-e29b-41d4-a716-446655440000"

    def test_valid_first_session_feedback(self, validator, valid_first_session_feedback):
        """Test that valid first session feedback passes validation."""
        result = validator.validate(valid_first_session_feedback)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.metadata["is_first_session"] is True

    def test_missing_required_fields(self, validator):
        """Test that missing required fields are caught."""
        data = {
            "feedback_id": "test-feedback",
            "session_id": "test-session"
            # Missing other required fields
        }

        result = validator.validate(data)

        assert result.valid is False
        assert len(result.errors) > 0

    def test_rating_below_minimum(self, validator, valid_feedback_data):
        """Test that rating < 1 is rejected."""
        valid_feedback_data["overall_rating"] = 0

        result = validator.validate(valid_feedback_data)

        assert result.valid is False
        assert any("overall_rating" in e.field for e in result.errors)

    def test_rating_above_maximum(self, validator, valid_feedback_data):
        """Test that rating > 5 is rejected."""
        valid_feedback_data["overall_rating"] = 6

        result = validator.validate(valid_feedback_data)

        assert result.valid is False
        assert any("overall_rating" in e.field for e in result.errors)

    def test_all_ratings_in_range(self, validator, valid_feedback_data):
        """Test all rating fields with valid values."""
        rating_fields = [
            "overall_rating",
            "subject_knowledge_rating",
            "communication_rating",
            "patience_rating",
            "engagement_rating",
            "helpfulness_rating"
        ]

        for field in rating_fields:
            # Test valid ratings
            for rating in [1, 2, 3, 4, 5]:
                valid_feedback_data[field] = rating
                result = validator.validate(valid_feedback_data)
                assert result.valid is True, f"{field}={rating} should be valid"

    def test_first_session_missing_would_recommend(self, validator, valid_first_session_feedback):
        """Test that first session feedback missing would_recommend is rejected."""
        valid_first_session_feedback["would_recommend"] = None

        result = validator.validate(valid_first_session_feedback)

        assert result.valid is False
        assert any("would_recommend" in e.field for e in result.errors)

    def test_first_session_missing_improvement_areas_warning(
        self, validator, valid_first_session_feedback
    ):
        """Test that first session feedback missing improvement_areas gets warning."""
        valid_first_session_feedback["improvement_areas"] = None

        result = validator.validate(valid_first_session_feedback)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("improvement_areas" in w.field for w in result.warnings)

    def test_free_text_too_long(self, validator, valid_feedback_data):
        """Test that free text exceeding max length is rejected."""
        valid_feedback_data["free_text_feedback"] = "x" * 5001

        result = validator.validate(valid_feedback_data)

        assert result.valid is False
        assert any("free_text_feedback" in e.field for e in result.errors)

    def test_overall_rating_inconsistent_with_individual_warning(
        self, validator, valid_feedback_data
    ):
        """Test that inconsistent overall rating generates warning."""
        # Set all individual ratings to 5
        valid_feedback_data["subject_knowledge_rating"] = 5
        valid_feedback_data["communication_rating"] = 5
        valid_feedback_data["patience_rating"] = 5
        valid_feedback_data["engagement_rating"] = 5
        valid_feedback_data["helpfulness_rating"] = 5
        # But overall rating is 2
        valid_feedback_data["overall_rating"] = 2

        result = validator.validate(valid_feedback_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("overall_rating" in w.field for w in result.warnings)

    def test_low_rating_without_feedback_warning(self, validator, valid_feedback_data):
        """Test that low rating without feedback text generates warning."""
        valid_feedback_data["overall_rating"] = 2
        valid_feedback_data["free_text_feedback"] = ""

        result = validator.validate(valid_feedback_data)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("free_text_feedback" in w.field for w in result.warnings)

    def test_first_session_low_rating_without_improvement_areas_warning(
        self, validator, valid_first_session_feedback
    ):
        """Test that first session with low rating and no improvement areas gets warning."""
        valid_first_session_feedback["overall_rating"] = 2
        valid_first_session_feedback["improvement_areas"] = []

        result = validator.validate(valid_first_session_feedback)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("improvement_areas" in w.field for w in result.warnings)

    def test_would_recommend_true_with_low_rating_warning(
        self, validator, valid_first_session_feedback
    ):
        """Test that would_recommend=True with low rating generates warning."""
        valid_first_session_feedback["overall_rating"] = 2
        valid_first_session_feedback["would_recommend"] = True

        result = validator.validate(valid_first_session_feedback)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("would_recommend" in w.field for w in result.warnings)

    def test_would_recommend_false_with_high_rating_warning(
        self, validator, valid_first_session_feedback
    ):
        """Test that would_recommend=False with high rating generates warning."""
        valid_first_session_feedback["overall_rating"] = 5
        valid_first_session_feedback["would_recommend"] = False

        result = validator.validate(valid_first_session_feedback)

        # Should be valid but have warning
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("would_recommend" in w.field for w in result.warnings)

    def test_submitted_before_created(self, validator, valid_feedback_data):
        """Test that submitted_at before created_at is rejected."""
        valid_feedback_data["created_at"] = "2024-05-14T18:30:00"
        valid_feedback_data["submitted_at"] = "2024-05-14T18:00:00"

        result = validator.validate(valid_feedback_data)

        assert result.valid is False
        assert any("submitted_at" in e.field for e in result.errors)

    def test_improvement_areas_too_many(self, validator, valid_first_session_feedback):
        """Test that too many improvement areas is rejected."""
        valid_first_session_feedback["improvement_areas"] = [
            f"area_{i}" for i in range(11)
        ]

        result = validator.validate(valid_first_session_feedback)

        assert result.valid is False
        assert any("improvement_areas" in e.field for e in result.errors)

    def test_validator_statistics(self, validator, valid_feedback_data):
        """Test that validator tracks statistics."""
        # Validate valid data
        validator.validate(valid_feedback_data)

        # Validate invalid data
        invalid_data = valid_feedback_data.copy()
        invalid_data["overall_rating"] = 10
        validator.validate(invalid_data)

        stats = validator.get_stats()
        assert stats["total_validated"] == 2
        assert stats["valid_count"] == 1
        assert stats["invalid_count"] == 1
