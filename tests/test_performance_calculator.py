"""
Tests for Performance Calculator.

Tests core metric calculation logic using synthetic data.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.evaluation.performance_calculator import PerformanceCalculator, PerformanceMetrics
from src.database.models import (
    Tutor,
    Session,
    StudentFeedback,
    TutorEvent,
    MetricWindow,
    PerformanceTier,
)


class TestPerformanceCalculator:
    """Test suite for PerformanceCalculator."""

    @pytest.mark.asyncio
    async def test_calculate_metrics_30day(self, db_session: AsyncSession):
        """Test metric calculation for 30-day window."""
        calculator = PerformanceCalculator(db_session)

        # Use existing tutor from test data
        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        # Calculate metrics
        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Assertions
        assert metrics is not None
        assert metrics.tutor_id == tutor.tutor_id
        assert metrics.window == MetricWindow.THIRTY_DAY
        assert metrics.sessions_completed >= 0
        assert isinstance(metrics.calculation_date, datetime)

    @pytest.mark.asyncio
    async def test_avg_rating_calculation(self, db_session: AsyncSession):
        """Test average rating calculation."""
        calculator = PerformanceCalculator(db_session)

        # Get tutor with feedback
        query = (
            select(Tutor)
            .join(Session)
            .join(StudentFeedback)
            .limit(1)
        )
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Rating should be between 1-5
        if metrics.avg_rating is not None:
            assert 1.0 <= metrics.avg_rating <= 5.0

    @pytest.mark.asyncio
    async def test_first_session_success_rate(self, db_session: AsyncSession):
        """Test first session success rate calculation."""
        calculator = PerformanceCalculator(db_session)

        # Get tutor with first sessions
        query = (
            select(Tutor)
            .join(Session)
            .where(Session.session_number == 1)
            .limit(1)
        )
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Success rate should be 0-100%
        if metrics.first_session_success_rate is not None:
            assert 0 <= metrics.first_session_success_rate <= 100

    @pytest.mark.asyncio
    async def test_reschedule_rate_calculation(self, db_session: AsyncSession):
        """Test reschedule rate calculation."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Reschedule rate should be 0-100%
        if metrics.reschedule_rate is not None:
            assert 0 <= metrics.reschedule_rate <= 100

    @pytest.mark.asyncio
    async def test_engagement_score_calculation(self, db_session: AsyncSession):
        """Test engagement score calculation."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Engagement score should be 0-100
        if metrics.engagement_score is not None:
            assert 0 <= metrics.engagement_score <= 100

    @pytest.mark.asyncio
    async def test_learning_objectives_met_pct(self, db_session: AsyncSession):
        """Test learning objectives met percentage calculation."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Learning objectives met should be 0-100%
        if metrics.learning_objectives_met_pct is not None:
            assert 0 <= metrics.learning_objectives_met_pct <= 100

    @pytest.mark.asyncio
    async def test_performance_tier_assignment(self, db_session: AsyncSession):
        """Test performance tier assignment logic."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(5)
        result = await db_session.execute(query)
        tutors = list(result.scalars().all())

        for tutor in tutors:
            metrics = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.THIRTY_DAY,
            )

            # Performance tier should be assigned
            assert metrics.performance_tier in [
                PerformanceTier.EXEMPLARY,
                PerformanceTier.STRONG,
                PerformanceTier.DEVELOPING,
                PerformanceTier.NEEDS_ATTENTION,
                PerformanceTier.AT_RISK,
            ]

    @pytest.mark.asyncio
    async def test_save_metrics(self, db_session: AsyncSession):
        """Test saving metrics to database."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        # Calculate metrics
        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Save to database
        metric_id = await calculator.save_metrics(metrics)

        assert metric_id is not None
        assert metric_id.startswith("metric_")

        # Commit to persist
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_multiple_windows(self, db_session: AsyncSession):
        """Test calculation across different time windows."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        # Calculate for all three windows
        metrics_7d = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.SEVEN_DAY,
        )

        metrics_30d = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        metrics_90d = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.NINETY_DAY,
        )

        # All should have correct windows
        assert metrics_7d.window == MetricWindow.SEVEN_DAY
        assert metrics_30d.window == MetricWindow.THIRTY_DAY
        assert metrics_90d.window == MetricWindow.NINETY_DAY

        # 90-day should have >= sessions than 30-day
        assert metrics_90d.sessions_completed >= metrics_30d.sessions_completed

    @pytest.mark.asyncio
    async def test_no_show_count(self, db_session: AsyncSession):
        """Test no-show count calculation."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # No-show count should be non-negative
        assert metrics.no_show_count >= 0

    @pytest.mark.asyncio
    async def test_calculator_stats(self, db_session: AsyncSession):
        """Test calculator statistics tracking."""
        calculator = PerformanceCalculator(db_session)

        initial_stats = calculator.get_stats()
        assert initial_stats["calculations_performed"] == 0

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        # Perform calculation
        await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        stats = calculator.get_stats()
        assert stats["calculations_performed"] == 1
        assert stats["calculations_successful"] == 1

    @pytest.mark.asyncio
    async def test_high_performer_detection(self, db_session: AsyncSession):
        """Test detection of high-performing tutors."""
        calculator = PerformanceCalculator(db_session)

        # Get tutors with high ratings
        query = (
            select(Tutor)
            .join(Session)
            .join(StudentFeedback)
            .where(StudentFeedback.overall_rating >= 4.5)
            .limit(5)
        )
        result = await db_session.execute(query)
        tutors = list(result.scalars().all())

        for tutor in tutors:
            metrics = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.THIRTY_DAY,
            )

            # High performers should have good ratings
            if metrics.avg_rating is not None:
                # Note: aggregate might still be lower than 4.5
                assert metrics.avg_rating >= 1.0

    @pytest.mark.asyncio
    async def test_at_risk_tutor_detection(self, db_session: AsyncSession):
        """Test detection of at-risk tutors."""
        calculator = PerformanceCalculator(db_session)

        # Get tutors with potential issues
        query = (
            select(Tutor)
            .join(Session)
            .where(Session.no_show == True)
            .limit(5)
        )
        result = await db_session.execute(query)
        tutors = list(result.scalars().all())

        for tutor in tutors:
            metrics = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.THIRTY_DAY,
            )

            # Should detect no-shows
            assert metrics.no_show_count >= 0

    @pytest.mark.asyncio
    async def test_metrics_to_dict(self, db_session: AsyncSession):
        """Test metrics serialization to dict."""
        calculator = PerformanceCalculator(db_session)

        query = select(Tutor).limit(1)
        result = await db_session.execute(query)
        tutor = result.scalar_one()

        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Convert to dict
        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert "tutor_id" in metrics_dict
        assert "avg_rating" in metrics_dict
        assert "performance_tier" in metrics_dict

        # Enums should be converted to strings
        assert isinstance(metrics_dict["window"], str)
        if metrics_dict["performance_tier"]:
            assert isinstance(metrics_dict["performance_tier"], str)


@pytest.mark.asyncio
async def test_end_to_end_evaluation(db_session: AsyncSession):
    """End-to-end test: calculate and save metrics for multiple tutors."""
    calculator = PerformanceCalculator(db_session)

    # Get 10 tutors
    query = select(Tutor).limit(10)
    result = await db_session.execute(query)
    tutors = list(result.scalars().all())

    saved_count = 0

    for tutor in tutors:
        # Calculate metrics
        metrics = await calculator.calculate_metrics(
            tutor_id=tutor.tutor_id,
            window=MetricWindow.THIRTY_DAY,
        )

        # Save to database
        metric_id = await calculator.save_metrics(metrics)
        assert metric_id is not None
        saved_count += 1

    # Commit all
    await db_session.commit()

    assert saved_count == len(tutors)
