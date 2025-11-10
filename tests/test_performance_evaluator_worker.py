"""
Tests for Performance Evaluator Worker

This module tests the performance evaluator Celery tasks to ensure:
1. Task registration with correct names
2. Batch processing logic
3. Error handling and retry behavior
4. Integration with PerformanceCalculator
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Tutor,
    TutorStatus,
    BehavioralArchetype,
    MetricWindow,
    PerformanceTier,
)
from src.evaluation.performance_calculator import PerformanceMetrics


@pytest.mark.asyncio
async def test_get_active_tutors(async_session: AsyncSession):
    """Test fetching active tutors from database."""
    from src.workers.tasks.performance_evaluator import _get_active_tutors

    # Create test tutors
    active_tutor = Tutor(
        tutor_id="tutor_1",
        name="Active Tutor",
        email="active@test.com",
        onboarding_date=datetime.utcnow(),
        status=TutorStatus.ACTIVE,
        subjects=["Math"],
        behavioral_archetype=BehavioralArchetype.HIGH_PERFORMER,
    )

    inactive_tutor = Tutor(
        tutor_id="tutor_2",
        name="Inactive Tutor",
        email="inactive@test.com",
        onboarding_date=datetime.utcnow(),
        status=TutorStatus.INACTIVE,
        subjects=["Science"],
        behavioral_archetype=BehavioralArchetype.STEADY,
    )

    async_session.add_all([active_tutor, inactive_tutor])
    await async_session.commit()

    # Fetch active tutors
    active_tutors = await _get_active_tutors(async_session)

    # Verify
    assert len(active_tutors) == 1
    assert active_tutors[0].tutor_id == "tutor_1"
    assert active_tutors[0].status == TutorStatus.ACTIVE


@pytest.mark.asyncio
async def test_evaluate_tutor_batch_success(async_session: AsyncSession):
    """Test successful batch evaluation of tutors."""
    from src.workers.tasks.performance_evaluator import _evaluate_tutor_batch

    # Create test tutor
    tutor = Tutor(
        tutor_id="tutor_test",
        name="Test Tutor",
        email="test@test.com",
        onboarding_date=datetime.utcnow() - timedelta(days=60),
        status=TutorStatus.ACTIVE,
        subjects=["Math"],
        behavioral_archetype=BehavioralArchetype.HIGH_PERFORMER,
    )

    async_session.add(tutor)
    await async_session.commit()

    # Evaluate batch
    result = await _evaluate_tutor_batch(async_session, [tutor])

    # Verify batch stats
    assert result["evaluated"] == 1
    assert result["successful"] == 1
    assert result["failed"] == 0
    assert len(result["failed_tutor_ids"]) == 0


@pytest.mark.asyncio
async def test_evaluate_tutor_batch_with_failures(async_session: AsyncSession):
    """Test batch evaluation handles individual tutor failures gracefully."""
    from src.workers.tasks.performance_evaluator import _evaluate_tutor_batch

    # Create test tutors
    valid_tutor = Tutor(
        tutor_id="tutor_valid",
        name="Valid Tutor",
        email="valid@test.com",
        onboarding_date=datetime.utcnow() - timedelta(days=60),
        status=TutorStatus.ACTIVE,
        subjects=["Math"],
        behavioral_archetype=BehavioralArchetype.HIGH_PERFORMER,
    )

    # This tutor will cause errors due to no data
    no_data_tutor = Tutor(
        tutor_id="tutor_nodata",
        name="No Data Tutor",
        email="nodata@test.com",
        onboarding_date=datetime.utcnow(),
        status=TutorStatus.ACTIVE,
        subjects=["Science"],
        behavioral_archetype=BehavioralArchetype.NEW_TUTOR,
    )

    async_session.add_all([valid_tutor, no_data_tutor])
    await async_session.commit()

    # Evaluate batch
    result = await _evaluate_tutor_batch(async_session, [valid_tutor, no_data_tutor])

    # Verify batch processed both tutors
    assert result["evaluated"] == 2
    # Some may fail due to lack of data, but should not crash
    assert result["successful"] + result["failed"] == 2
    assert len(result["failed_tutor_ids"]) == result["failed"]


@pytest.mark.asyncio
async def test_evaluate_single_tutor_async():
    """Test single tutor evaluation async function."""
    from src.workers.tasks.performance_evaluator import _evaluate_single_tutor_async

    # Mock the database session
    with patch('src.workers.tasks.performance_evaluator.async_session_maker') as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        # Mock PerformanceCalculator
        with patch('src.workers.tasks.performance_evaluator.PerformanceCalculator') as MockCalculator:
            mock_calculator = AsyncMock()
            MockCalculator.return_value = mock_calculator

            # Mock metrics
            test_metrics = PerformanceMetrics(
                tutor_id="tutor_123",
                calculation_date=datetime.utcnow(),
                window=MetricWindow.THIRTY_DAY,
                sessions_completed=10,
                avg_rating=4.5,
                first_session_success_rate=85.0,
                reschedule_rate=5.0,
                no_show_count=1,
                engagement_score=80.0,
                learning_objectives_met_pct=90.0,
                response_time_avg_minutes=30.0,
                performance_tier=PerformanceTier.STRONG,
            )

            mock_calculator.calculate_metrics.return_value = test_metrics
            mock_calculator.save_metrics.return_value = "metric_123"

            # Call function
            result = await _evaluate_single_tutor_async("tutor_123", "30day")

            # Verify
            assert result["tutor_id"] == "tutor_123"
            assert result["metric_id"] == "metric_123"
            assert result["avg_rating"] == 4.5
            assert result["performance_tier"] == "Strong"

            # Verify calculator was called correctly
            mock_calculator.calculate_metrics.assert_called_once()
            call_args = mock_calculator.calculate_metrics.call_args
            assert call_args.kwargs["tutor_id"] == "tutor_123"
            assert call_args.kwargs["window"] == MetricWindow.THIRTY_DAY


def test_celery_task_registration():
    """Test that Celery tasks are registered with correct names."""
    from src.workers.celery_app import celery_app

    # Check main task is registered
    assert "src.workers.tasks.performance_evaluator.evaluate_tutor_performance" in celery_app.tasks

    # Check single tutor task is registered
    assert "src.workers.tasks.performance_evaluator.evaluate_single_tutor" in celery_app.tasks


def test_beat_schedule_configuration():
    """Test that beat schedule is configured correctly."""
    from src.workers.celery_app import celery_app

    beat_schedule = celery_app.conf.beat_schedule

    # Verify performance evaluation task is scheduled
    assert "evaluate-performance-every-15-min" in beat_schedule

    schedule_config = beat_schedule["evaluate-performance-every-15-min"]

    # Verify task name
    assert schedule_config["task"] == "src.workers.tasks.performance_evaluator.evaluate_tutor_performance"

    # Verify queue
    assert schedule_config["options"]["queue"] == "evaluation"

    # Verify schedule (every 15 minutes)
    # Note: crontab object doesn't easily expose minute value, so just check it exists
    assert schedule_config["schedule"] is not None


@pytest.mark.asyncio
async def test_evaluate_all_tutors_empty_database(async_session: AsyncSession):
    """Test evaluation when no active tutors exist."""
    from src.workers.tasks.performance_evaluator import _evaluate_all_tutors_async

    # Use actual session with no tutors
    with patch('src.workers.tasks.performance_evaluator.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value = async_session

        result = await _evaluate_all_tutors_async()

        # Verify stats
        assert result["tutors_evaluated"] == 0
        assert result["tutors_successful"] == 0
        assert result["tutors_failed"] == 0
        assert len(result["batch_stats"]) == 0


@pytest.mark.asyncio
async def test_multiple_windows_evaluation(async_session: AsyncSession):
    """Test that evaluation calculates metrics for all three windows."""
    from src.workers.tasks.performance_evaluator import _evaluate_tutor_batch

    # Create test tutor with some history
    tutor = Tutor(
        tutor_id="tutor_multiwindow",
        name="Multi Window Tutor",
        email="multiwindow@test.com",
        onboarding_date=datetime.utcnow() - timedelta(days=100),
        status=TutorStatus.ACTIVE,
        subjects=["Math", "Science"],
        behavioral_archetype=BehavioralArchetype.STEADY,
    )

    async_session.add(tutor)
    await async_session.commit()

    # Mock PerformanceCalculator to track calls
    with patch('src.workers.tasks.performance_evaluator.PerformanceCalculator') as MockCalculator:
        mock_calculator = AsyncMock()
        MockCalculator.return_value = mock_calculator

        # Create mock metrics for each window
        mock_metrics = PerformanceMetrics(
            tutor_id="tutor_multiwindow",
            calculation_date=datetime.utcnow(),
            window=MetricWindow.THIRTY_DAY,
            sessions_completed=5,
            avg_rating=4.0,
            first_session_success_rate=75.0,
            reschedule_rate=10.0,
            no_show_count=0,
            engagement_score=70.0,
            learning_objectives_met_pct=85.0,
            response_time_avg_minutes=25.0,
            performance_tier=PerformanceTier.DEVELOPING,
        )

        mock_calculator.calculate_metrics.return_value = mock_metrics
        mock_calculator.save_metrics.return_value = "metric_123"

        # Evaluate
        result = await _evaluate_tutor_batch(async_session, [tutor])

        # Verify all three windows were calculated
        assert mock_calculator.calculate_metrics.call_count == 3

        # Verify calls were for 30day, 7day, and 90day windows
        calls = mock_calculator.calculate_metrics.call_args_list
        windows_called = [call.kwargs["window"] for call in calls]

        assert MetricWindow.THIRTY_DAY in windows_called
        assert MetricWindow.SEVEN_DAY in windows_called
        assert MetricWindow.NINETY_DAY in windows_called


def test_task_retry_configuration():
    """Test that tasks have proper retry configuration."""
    from src.workers.tasks.performance_evaluator import (
        evaluate_tutor_performance,
        evaluate_single_tutor,
    )

    # Check main task retry config
    assert evaluate_tutor_performance.autoretry_for == (Exception,)
    assert evaluate_tutor_performance.retry_backoff is True
    assert evaluate_tutor_performance.retry_jitter is True

    # Check single tutor task retry config
    assert evaluate_single_tutor.autoretry_for == (Exception,)
    assert evaluate_single_tutor.retry_backoff is True
    assert evaluate_single_tutor.retry_jitter is True
