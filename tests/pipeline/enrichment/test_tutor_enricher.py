"""
Tests for TutorEnricher.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.pipeline.enrichment.tutor_enricher import TutorEnricher


class TestTutorEnricher:
    """Test suite for TutorEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create TutorEnricher instance."""
        return TutorEnricher()

    @pytest.fixture
    def base_tutor_data(self):
        """Base tutor data for testing."""
        return {
            "tutor_id": "T001",
            "name": "John Doe",
            "email": "john@example.com",
            "onboarding_date": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
            "status": "active",
            "subjects": ["Math", "Physics", "Chemistry"],
            "education_level": "PhD",
            "location": "New York",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_enrich_new_tutor(self, enricher, base_tutor_data):
        """Test enrichment of new tutor (< 30 days)."""
        # Set onboarding date to 15 days ago
        base_tutor_data["onboarding_date"] = (
            datetime.now(timezone.utc) - timedelta(days=15)
        ).isoformat()

        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_new_tutor"] is True
        assert result.data["experience_level"] == "junior"
        assert result.data["tenure_days"] >= 15
        assert result.data["subject_count"] == 3
        assert "is_active_today" in result.data

    def test_enrich_junior_tutor(self, enricher, base_tutor_data):
        """Test enrichment of junior tutor (30-89 days)."""
        # Set onboarding date to 60 days ago
        base_tutor_data["onboarding_date"] = (
            datetime.now(timezone.utc) - timedelta(days=60)
        ).isoformat()

        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_new_tutor"] is False
        assert result.data["experience_level"] == "junior"
        assert result.data["tenure_days"] >= 60

    def test_enrich_mid_tutor(self, enricher, base_tutor_data):
        """Test enrichment of mid-level tutor (90-364 days)."""
        # Set onboarding date to 180 days ago
        base_tutor_data["onboarding_date"] = (
            datetime.now(timezone.utc) - timedelta(days=180)
        ).isoformat()

        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_new_tutor"] is False
        assert result.data["experience_level"] == "mid"
        assert result.data["tenure_days"] >= 180

    def test_enrich_senior_tutor(self, enricher, base_tutor_data):
        """Test enrichment of senior tutor (365+ days)."""
        # Set onboarding date to 400 days ago
        base_tutor_data["onboarding_date"] = (
            datetime.now(timezone.utc) - timedelta(days=400)
        ).isoformat()

        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_new_tutor"] is False
        assert result.data["experience_level"] == "senior"
        assert result.data["tenure_days"] >= 400

    def test_subject_count(self, enricher, base_tutor_data):
        """Test subject count calculation."""
        test_cases = [
            ([], 0),
            (["Math"], 1),
            (["Math", "Physics"], 2),
            (["Math", "Physics", "Chemistry", "Biology"], 4),
        ]

        for subjects, expected_count in test_cases:
            base_tutor_data["subjects"] = subjects
            result = enricher.enrich(base_tutor_data)

            assert result.success is True
            assert result.data["subject_count"] == expected_count

    def test_is_active_today(self, enricher, base_tutor_data):
        """Test is_active_today calculation."""
        # Active today
        base_tutor_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_active_today"] is True

        # Not active today
        base_tutor_data["updated_at"] = (
            datetime.now(timezone.utc) - timedelta(days=2)
        ).isoformat()
        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert result.data["is_active_today"] is False

    def test_missing_required_fields(self, enricher):
        """Test handling of missing required fields."""
        incomplete_data = {
            "tutor_id": "T001",
            "name": "John Doe",
            # Missing email, onboarding_date, status, subjects
        }

        result = enricher.enrich(incomplete_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Missing required fields" in result.errors[0]

    def test_derived_fields_metadata(self, enricher, base_tutor_data):
        """Test that derived fields are properly tracked."""
        result = enricher.enrich(base_tutor_data)

        assert result.success is True
        assert "tenure_days" in result.derived_fields
        assert "is_new_tutor" in result.derived_fields
        assert "experience_level" in result.derived_fields
        assert "subject_count" in result.derived_fields

    def test_enricher_stats(self, enricher, base_tutor_data):
        """Test enricher statistics tracking."""
        # Reset stats
        enricher.reset_stats()

        # Process valid data
        enricher.enrich(base_tutor_data)
        enricher.enrich(base_tutor_data)

        # Process invalid data
        enricher.enrich({})

        stats = enricher.get_stats()

        assert stats["enrichments_attempted"] == 3
        assert stats["enrichments_successful"] == 2
        assert stats["enrichments_failed"] == 1

    def test_timezone_handling(self, enricher, base_tutor_data):
        """Test handling of timezone-aware and naive datetimes."""
        # Timezone-aware
        base_tutor_data["onboarding_date"] = datetime.now(timezone.utc).isoformat()
        result = enricher.enrich(base_tutor_data)
        assert result.success is True

        # Naive datetime
        base_tutor_data["onboarding_date"] = datetime.now().isoformat()
        result = enricher.enrich(base_tutor_data)
        assert result.success is True
