"""
Unit tests for Daily Metrics Aggregator.

Tests the batch processing functionality, error handling, and data persistence.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.evaluation.daily_aggregator import (
    DailyMetricsAggregator,
    AggregationResult,
    AggregationSummary,
)
from src.database.models import Tutor, TutorStatus, MetricWindow


class TestAggregationResult:
    """Test AggregationResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful aggregation result."""
        result = AggregationResult(
            tutor_id="tutor_001",
            tutor_name="John Doe",
            success=True,
            metrics_saved=["metric_1", "metric_2", "metric_3"],
            windows_processed=[
                MetricWindow.SEVEN_DAY,
                MetricWindow.THIRTY_DAY,
                MetricWindow.NINETY_DAY,
            ],
            calculation_time_seconds=1.5,
        )

        assert result.tutor_id == "tutor_001"
        assert result.success is True
        assert len(result.metrics_saved) == 3
        assert len(result.windows_processed) == 3

    def test_failed_result(self):
        """Test creating a failed aggregation result."""
        result = AggregationResult(
            tutor_id="tutor_002",
            tutor_name="Jane Smith",
            success=False,
            error="Database connection failed",
        )

        assert result.tutor_id == "tutor_002"
        assert result.success is False
        assert result.error == "Database connection failed"
        assert len(result.metrics_saved) == 0


class TestAggregationSummary:
    """Test AggregationSummary dataclass."""

    def test_summary_initialization(self):
        """Test summary initialization."""
        run_date = datetime.utcnow()
        summary = AggregationSummary(run_date=run_date)

        assert summary.run_date == run_date
        assert summary.total_tutors == 0
        assert summary.successful == 0
        assert summary.failed == 0
        assert summary.total_metrics_saved == 0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        summary = AggregationSummary(
            run_date=datetime.utcnow(),
            total_tutors=100,
            successful=95,
            failed=5,
        )

        assert summary.success_rate == 95.0

    def test_success_rate_zero_tutors(self):
        """Test success rate with zero tutors."""
        summary = AggregationSummary(
            run_date=datetime.utcnow(),
            total_tutors=0,
        )

        assert summary.success_rate == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        summary = AggregationSummary(
            run_date=datetime(2025, 11, 7, 12, 0, 0),
            total_tutors=50,
            successful=48,
            failed=2,
            total_metrics_saved=144,
            total_runtime_seconds=45.5,
        )

        result = summary.to_dict()

        assert result["total_tutors"] == 50
        assert result["successful"] == 48
        assert result["failed"] == 2
        assert result["total_metrics_saved"] == 144
        assert result["total_runtime_seconds"] == 45.5
        assert result["success_rate"] == 96.0


class TestDailyMetricsAggregator:
    """Test DailyMetricsAggregator class."""

    def test_initialization(self):
        """Test aggregator initialization."""
        reference_date = datetime(2025, 11, 7)
        aggregator = DailyMetricsAggregator(
            reference_date=reference_date,
            max_retries=5,
            retry_delay_seconds=10,
            batch_size=25,
        )

        assert aggregator.reference_date == reference_date
        assert aggregator.max_retries == 5
        assert aggregator.retry_delay_seconds == 10
        assert aggregator.batch_size == 25
        assert len(aggregator.windows) == 3

    def test_initialization_defaults(self):
        """Test aggregator initialization with defaults."""
        aggregator = DailyMetricsAggregator()

        assert aggregator.max_retries == 3
        assert aggregator.retry_delay_seconds == 5
        assert aggregator.batch_size == 50
        assert aggregator.reference_date is not None

    @pytest.mark.asyncio
    async def test_get_tutors_active_only(self):
        """Test getting active tutors only."""
        # Create mock session
        mock_session = AsyncMock()

        # Create mock tutors
        tutors = [
            Mock(tutor_id="tutor_001", status=TutorStatus.ACTIVE),
            Mock(tutor_id="tutor_002", status=TutorStatus.ACTIVE),
        ]

        # Mock the execute result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = tutors
        mock_session.execute.return_value = mock_result

        aggregator = DailyMetricsAggregator()

        result = await aggregator._get_tutors(
            mock_session,
            tutor_ids=None,
            include_inactive=False,
        )

        assert len(result) == 2
        assert result[0].tutor_id == "tutor_001"
        assert result[1].tutor_id == "tutor_002"

    @pytest.mark.asyncio
    async def test_get_tutors_specific_ids(self):
        """Test getting specific tutor IDs."""
        mock_session = AsyncMock()

        tutors = [
            Mock(tutor_id="tutor_001", status=TutorStatus.ACTIVE),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = tutors
        mock_session.execute.return_value = mock_result

        aggregator = DailyMetricsAggregator()

        result = await aggregator._get_tutors(
            mock_session,
            tutor_ids=["tutor_001"],
            include_inactive=False,
        )

        assert len(result) == 1
        assert result[0].tutor_id == "tutor_001"


class TestHelperFunctions:
    """Test helper functions and utility methods."""

    def test_aggregation_summary_with_errors(self):
        """Test summary with errors."""
        summary = AggregationSummary(
            run_date=datetime.utcnow(),
            total_tutors=10,
            successful=8,
            failed=2,
            errors=[
                {"tutor_id": "tutor_001", "error": "Database error"},
                {"tutor_id": "tutor_002", "error": "Timeout"},
            ],
        )

        assert len(summary.errors) == 2
        assert summary.failed == 2
        assert summary.success_rate == 80.0

    def test_aggregation_result_default_values(self):
        """Test aggregation result default values."""
        result = AggregationResult(
            tutor_id="tutor_123",
            tutor_name="Test Tutor",
            success=True,
        )

        assert result.metrics_saved == []
        assert result.windows_processed == []
        assert result.calculation_time_seconds == 0.0
        assert result.error is None


@pytest.mark.integration
class TestDailyAggregationIntegration:
    """Integration tests requiring database connection."""

    @pytest.mark.asyncio
    async def test_full_aggregation_flow(self):
        """
        Test full aggregation flow (requires database).

        This test is marked as integration and should only run
        when database is available.
        """
        # This test would require actual database setup
        # Skipping in unit test suite
        pytest.skip("Requires database connection")

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self):
        """
        Test cleanup of old metrics (requires database).

        This test is marked as integration and should only run
        when database is available.
        """
        pytest.skip("Requires database connection")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
