"""
Tests for SessionEnricher.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.pipeline.enrichment.session_enricher import SessionEnricher


class TestSessionEnricher:
    """Test suite for SessionEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create SessionEnricher instance."""
        return SessionEnricher()

    @pytest.fixture
    def base_session_data(self):
        """Base session data for testing."""
        return {
            "session_id": "S001",
            "tutor_id": "T001",
            "student_id": "ST001",
            "session_number": 1,
            "scheduled_start": datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
            "duration_minutes": 60,
            "subject": "Math",
            "session_type": "1-on-1",
            "late_start_minutes": 3,
        }

    def test_is_weekend_saturday(self, enricher, base_session_data):
        """Test is_weekend for Saturday."""
        # Nov 9, 2024 is a Saturday
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 9, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["is_weekend"] is True

    def test_is_weekend_sunday(self, enricher, base_session_data):
        """Test is_weekend for Sunday."""
        # Nov 10, 2024 is a Sunday
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 10, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["is_weekend"] is True

    def test_is_weekend_weekday(self, enricher, base_session_data):
        """Test is_weekend for weekday."""
        # Nov 7, 2024 is a Thursday
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["is_weekend"] is False

    def test_time_of_day_morning(self, enricher, base_session_data):
        """Test time_of_day for morning session."""
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 9, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["time_of_day"] == "morning"

    def test_time_of_day_afternoon(self, enricher, base_session_data):
        """Test time_of_day for afternoon session."""
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["time_of_day"] == "afternoon"

    def test_time_of_day_evening(self, enricher, base_session_data):
        """Test time_of_day for evening session."""
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 19, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["time_of_day"] == "evening"

    def test_time_of_day_night(self, enricher, base_session_data):
        """Test time_of_day for night session."""
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 23, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["time_of_day"] == "night"

    def test_is_late_start_true(self, enricher, base_session_data):
        """Test is_late_start when late_start_minutes > 5."""
        base_session_data["late_start_minutes"] = 10

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["is_late_start"] is True

    def test_is_late_start_false(self, enricher, base_session_data):
        """Test is_late_start when late_start_minutes <= 5."""
        base_session_data["late_start_minutes"] = 3

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["is_late_start"] is False

    def test_week_of_year(self, enricher, base_session_data):
        """Test week_of_year calculation."""
        # Nov 7, 2024
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["week_of_year"] == 45  # Week 45 of 2024

    def test_month_of_year(self, enricher, base_session_data):
        """Test month_of_year calculation."""
        base_session_data["scheduled_start"] = datetime(
            2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc
        ).isoformat()

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["month_of_year"] == 11

    def test_actual_duration_minutes(self, enricher, base_session_data):
        """Test actual_duration_minutes calculation."""
        scheduled_start = datetime(2024, 11, 7, 14, 0, 0, tzinfo=timezone.utc)
        actual_start = datetime(2024, 11, 7, 14, 10, 0, tzinfo=timezone.utc)  # 10 min late

        base_session_data["scheduled_start"] = scheduled_start.isoformat()
        base_session_data["actual_start"] = actual_start.isoformat()
        base_session_data["duration_minutes"] = 60

        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert result.data["actual_duration_minutes"] == 60

    def test_missing_required_fields(self, enricher):
        """Test handling of missing required fields."""
        incomplete_data = {
            "session_id": "S001",
            "tutor_id": "T001",
            # Missing student_id, scheduled_start, duration_minutes, subject
        }

        result = enricher.enrich(incomplete_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Missing required fields" in result.errors[0]

    def test_derived_fields_metadata(self, enricher, base_session_data):
        """Test that derived fields are properly tracked."""
        result = enricher.enrich(base_session_data)

        assert result.success is True
        assert "is_weekend" in result.derived_fields
        assert "time_of_day" in result.derived_fields
        assert "is_late_start" in result.derived_fields
        assert "week_of_year" in result.derived_fields
        assert "month_of_year" in result.derived_fields

    def test_enricher_stats(self, enricher, base_session_data):
        """Test enricher statistics tracking."""
        enricher.reset_stats()

        # Process valid data
        enricher.enrich(base_session_data)
        enricher.enrich(base_session_data)

        # Process invalid data
        enricher.enrich({})

        stats = enricher.get_stats()

        assert stats["enrichments_attempted"] == 3
        assert stats["enrichments_successful"] == 2
        assert stats["enrichments_failed"] == 1
