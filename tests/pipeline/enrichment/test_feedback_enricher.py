"""
Tests for FeedbackEnricher.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.pipeline.enrichment.feedback_enricher import FeedbackEnricher


class TestFeedbackEnricher:
    """Test suite for FeedbackEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create FeedbackEnricher instance."""
        return FeedbackEnricher()

    @pytest.fixture
    def base_feedback_data(self):
        """Base feedback data for testing."""
        return {
            "feedback_id": "F001",
            "session_id": "S001",
            "student_id": "ST001",
            "tutor_id": "T001",
            "overall_rating": 4,
            "subject_knowledge_rating": 5,
            "communication_rating": 4,
            "patience_rating": 4,
            "engagement_rating": 5,
            "helpfulness_rating": 4,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_is_positive_true(self, enricher, base_feedback_data):
        """Test is_positive for rating >= 4."""
        test_cases = [4, 5]

        for rating in test_cases:
            base_feedback_data["overall_rating"] = rating
            result = enricher.enrich(base_feedback_data)

            assert result.success is True
            assert result.data["is_positive"] is True

    def test_is_positive_false(self, enricher, base_feedback_data):
        """Test is_positive for rating < 4."""
        test_cases = [1, 2, 3]

        for rating in test_cases:
            base_feedback_data["overall_rating"] = rating
            result = enricher.enrich(base_feedback_data)

            assert result.success is True
            assert result.data["is_positive"] is False

    def test_is_poor_true(self, enricher, base_feedback_data):
        """Test is_poor for rating < 3."""
        test_cases = [1, 2]

        for rating in test_cases:
            base_feedback_data["overall_rating"] = rating
            result = enricher.enrich(base_feedback_data)

            assert result.success is True
            assert result.data["is_poor"] is True

    def test_is_poor_false(self, enricher, base_feedback_data):
        """Test is_poor for rating >= 3."""
        test_cases = [3, 4, 5]

        for rating in test_cases:
            base_feedback_data["overall_rating"] = rating
            result = enricher.enrich(base_feedback_data)

            assert result.success is True
            assert result.data["is_poor"] is False

    def test_avg_category_rating(self, enricher, base_feedback_data):
        """Test avg_category_rating calculation."""
        # All ratings = 4, average should be 4.0
        base_feedback_data.update({
            "subject_knowledge_rating": 4,
            "communication_rating": 4,
            "patience_rating": 4,
            "engagement_rating": 4,
            "helpfulness_rating": 4,
        })

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["avg_category_rating"] == 4.0

    def test_avg_category_rating_mixed(self, enricher, base_feedback_data):
        """Test avg_category_rating with mixed values."""
        # Ratings: 5, 4, 3, 5, 3 -> average = 4.0
        base_feedback_data.update({
            "subject_knowledge_rating": 5,
            "communication_rating": 4,
            "patience_rating": 3,
            "engagement_rating": 5,
            "helpfulness_rating": 3,
        })

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["avg_category_rating"] == 4.0

    def test_avg_category_rating_with_nulls(self, enricher, base_feedback_data):
        """Test avg_category_rating with some null values."""
        # Only 3 ratings provided: 5, 4, 5 -> average = 4.67
        base_feedback_data.update({
            "subject_knowledge_rating": 5,
            "communication_rating": 4,
            "patience_rating": None,
            "engagement_rating": 5,
            "helpfulness_rating": None,
        })

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert abs(result.data["avg_category_rating"] - 4.67) < 0.01

    def test_category_variance_zero(self, enricher, base_feedback_data):
        """Test category_variance when all ratings are the same."""
        # All ratings = 4, variance should be 0
        base_feedback_data.update({
            "subject_knowledge_rating": 4,
            "communication_rating": 4,
            "patience_rating": 4,
            "engagement_rating": 4,
            "helpfulness_rating": 4,
        })

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["category_variance"] == 0.0

    def test_category_variance_nonzero(self, enricher, base_feedback_data):
        """Test category_variance with varying ratings."""
        # Ratings: 1, 3, 5 -> variance should be > 0
        base_feedback_data.update({
            "subject_knowledge_rating": 1,
            "communication_rating": 3,
            "patience_rating": 5,
            "engagement_rating": None,
            "helpfulness_rating": None,
        })

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["category_variance"] > 0

    def test_has_text_feedback_true(self, enricher, base_feedback_data):
        """Test has_text_feedback when text is provided."""
        base_feedback_data["free_text_feedback"] = "Great tutor, very helpful!"

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["has_text_feedback"] is True

    def test_has_text_feedback_false_empty(self, enricher, base_feedback_data):
        """Test has_text_feedback when text is empty."""
        base_feedback_data["free_text_feedback"] = ""

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["has_text_feedback"] is False

    def test_has_text_feedback_false_whitespace(self, enricher, base_feedback_data):
        """Test has_text_feedback when text is only whitespace."""
        base_feedback_data["free_text_feedback"] = "   "

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["has_text_feedback"] is False

    def test_has_text_feedback_false_none(self, enricher, base_feedback_data):
        """Test has_text_feedback when text is None."""
        base_feedback_data["free_text_feedback"] = None

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["has_text_feedback"] is False

    def test_feedback_delay_hours(self, enricher, base_feedback_data):
        """Test feedback_delay_hours calculation."""
        session_start = datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc)
        submitted_at = datetime(2024, 11, 7, 16, 30, 0, tzinfo=timezone.utc)  # 2.5 hours later

        base_feedback_data["session_scheduled_start"] = session_start.isoformat()
        base_feedback_data["submitted_at"] = submitted_at.isoformat()

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["feedback_delay_hours"] == 2.5

    def test_feedback_delay_hours_days_later(self, enricher, base_feedback_data):
        """Test feedback_delay_hours for feedback submitted days later."""
        session_start = datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc)
        submitted_at = datetime(2024, 11, 8, 14, 0, 0, tzinfo=timezone.utc)  # 24 hours later

        base_feedback_data["session_scheduled_start"] = session_start.isoformat()
        base_feedback_data["submitted_at"] = submitted_at.isoformat()

        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert result.data["feedback_delay_hours"] == 24.0

    def test_missing_required_fields(self, enricher):
        """Test handling of missing required fields."""
        incomplete_data = {
            "feedback_id": "F001",
            "session_id": "S001",
            # Missing student_id, tutor_id, overall_rating, submitted_at
        }

        result = enricher.enrich(incomplete_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Missing required fields" in result.errors[0]

    def test_derived_fields_metadata(self, enricher, base_feedback_data):
        """Test that derived fields are properly tracked."""
        result = enricher.enrich(base_feedback_data)

        assert result.success is True
        assert "is_positive" in result.derived_fields
        assert "is_poor" in result.derived_fields
        assert "avg_category_rating" in result.derived_fields
        assert "category_variance" in result.derived_fields
        assert "has_text_feedback" in result.derived_fields

    def test_enricher_stats(self, enricher, base_feedback_data):
        """Test enricher statistics tracking."""
        enricher.reset_stats()

        # Process valid data
        enricher.enrich(base_feedback_data)
        enricher.enrich(base_feedback_data)

        # Process invalid data
        enricher.enrich({})

        stats = enricher.get_stats()

        assert stats["enrichments_attempted"] == 3
        assert stats["enrichments_successful"] == 2
        assert stats["enrichments_failed"] == 1
