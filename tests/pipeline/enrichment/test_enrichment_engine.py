"""
Tests for EnrichmentEngine.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.pipeline.enrichment.enrichment_engine import EnrichmentEngine


class TestEnrichmentEngine:
    """Test suite for EnrichmentEngine."""

    @pytest.fixture
    def engine(self):
        """Create EnrichmentEngine instance."""
        return EnrichmentEngine()

    @pytest.fixture
    def tutor_data(self):
        """Sample tutor data."""
        return {
            "tutor_id": "T001",
            "name": "John Doe",
            "email": "john@example.com",
            "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
            "status": "active",
            "subjects": ["Math", "Physics"],
        }

    @pytest.fixture
    def session_data(self):
        """Sample session data."""
        return {
            "session_id": "S001",
            "tutor_id": "T001",
            "student_id": "ST001",
            "session_number": 1,
            "scheduled_start": datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
            "duration_minutes": 60,
            "subject": "Math",
            "late_start_minutes": 3,
        }

    @pytest.fixture
    def feedback_data(self):
        """Sample feedback data."""
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

    def test_enrich_tutor(self, engine, tutor_data):
        """Test enriching tutor data."""
        result = engine.enrich(tutor_data, "tutor")

        assert result.success is True
        assert "is_new_tutor" in result.data
        assert "experience_level" in result.data
        assert "subject_count" in result.data

    def test_enrich_session(self, engine, session_data):
        """Test enriching session data."""
        result = engine.enrich(session_data, "session")

        assert result.success is True
        assert "is_weekend" in result.data
        assert "time_of_day" in result.data
        assert "is_late_start" in result.data
        assert "week_of_year" in result.data
        assert "month_of_year" in result.data

    def test_enrich_feedback(self, engine, feedback_data):
        """Test enriching feedback data."""
        result = engine.enrich(feedback_data, "feedback")

        assert result.success is True
        assert "is_positive" in result.data
        assert "is_poor" in result.data
        assert "avg_category_rating" in result.data
        assert "category_variance" in result.data
        assert "has_text_feedback" in result.data

    def test_enrich_unknown_type(self, engine):
        """Test enriching with unknown data type."""
        result = engine.enrich({}, "unknown_type")

        assert result.success is False
        assert len(result.errors) > 0
        assert "Unknown data type" in result.errors[0]

    def test_stats_tracking_success(self, engine, tutor_data, session_data):
        """Test statistics tracking for successful enrichments."""
        engine.reset_stats()

        # Enrich tutor
        engine.enrich(tutor_data, "tutor")
        engine.enrich(tutor_data, "tutor")

        # Enrich session
        engine.enrich(session_data, "session")

        stats = engine.get_stats()

        assert stats["total_enriched"] == 3
        assert stats["total_failed"] == 0
        assert stats["by_type"]["tutor"]["success"] == 2
        assert stats["by_type"]["session"]["success"] == 1

    def test_stats_tracking_failure(self, engine):
        """Test statistics tracking for failed enrichments."""
        engine.reset_stats()

        # Invalid data (missing required fields)
        engine.enrich({}, "tutor")
        engine.enrich({}, "session")
        engine.enrich({}, "feedback")

        stats = engine.get_stats()

        assert stats["total_enriched"] == 0
        assert stats["total_failed"] == 3
        assert stats["by_type"]["tutor"]["failed"] == 1
        assert stats["by_type"]["session"]["failed"] == 1
        assert stats["by_type"]["feedback"]["failed"] == 1

    def test_stats_tracking_mixed(self, engine, tutor_data):
        """Test statistics tracking with mixed results."""
        engine.reset_stats()

        # Valid
        engine.enrich(tutor_data, "tutor")

        # Invalid
        engine.enrich({}, "tutor")

        stats = engine.get_stats()

        assert stats["total_enriched"] == 1
        assert stats["total_failed"] == 1
        assert stats["by_type"]["tutor"]["success"] == 1
        assert stats["by_type"]["tutor"]["failed"] == 1

    def test_reset_stats(self, engine, tutor_data):
        """Test resetting statistics."""
        # Generate some stats
        engine.enrich(tutor_data, "tutor")
        engine.enrich({}, "tutor")

        # Verify stats exist
        stats_before = engine.get_stats()
        assert stats_before["total_enriched"] > 0 or stats_before["total_failed"] > 0

        # Reset
        engine.reset_stats()

        # Verify stats are cleared
        stats_after = engine.get_stats()
        assert stats_after["total_enriched"] == 0
        assert stats_after["total_failed"] == 0

    def test_enricher_stats_included(self, engine, tutor_data):
        """Test that enricher-specific stats are included."""
        engine.reset_stats()

        engine.enrich(tutor_data, "tutor")

        stats = engine.get_stats()

        assert "enricher_stats" in stats["by_type"]["tutor"]
        enricher_stats = stats["by_type"]["tutor"]["enricher_stats"]
        assert "enrichments_attempted" in enricher_stats
        assert enricher_stats["enrichments_attempted"] > 0
