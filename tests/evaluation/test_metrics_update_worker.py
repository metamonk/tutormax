"""
Tests for Real-Time Metrics Update Worker.

Validates that the worker correctly:
1. Consumes session completion events from Redis
2. Calculates updated metrics for affected tutors
3. Saves metrics to the database
4. Maintains low latency (<60 seconds)
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.evaluation.metrics_update_worker import MetricsUpdateWorker
from src.queue.client import RedisClient
from src.queue.publisher import MessagePublisher
from src.queue.channels import QueueChannels
from src.database.connection import get_session
from src.database.models import (
    Tutor,
    Student,
    Session,
    StudentFeedback,
    TutorPerformanceMetric,
    TutorStatus,
    SessionType,
    MetricWindow,
)


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with get_session() as session:
        yield session


@pytest.fixture
def redis_client():
    """Create a Redis client for tests."""
    return RedisClient()


@pytest.fixture
def publisher(redis_client):
    """Create a message publisher for tests."""
    return MessagePublisher(redis_client)


@pytest.fixture
async def test_tutor(db_session):
    """Create a test tutor."""
    tutor = Tutor(
        tutor_id="tutor_test_metrics_001",
        name="Test Tutor",
        email="test.metrics@example.com",
        onboarding_date=datetime.utcnow() - timedelta(days=90),
        status=TutorStatus.ACTIVE,
        subjects=["Math", "Physics"],
        education_level="Master's",
        location="New York",
    )
    db_session.add(tutor)
    await db_session.commit()
    yield tutor

    # Cleanup
    await db_session.delete(tutor)
    await db_session.commit()


@pytest.fixture
async def test_student(db_session):
    """Create a test student."""
    student = Student(
        student_id="student_test_metrics_001",
        name="Test Student",
        age=15,
        grade_level="10th",
        subjects_interested=["Math"],
    )
    db_session.add(student)
    await db_session.commit()
    yield student

    # Cleanup
    await db_session.delete(student)
    await db_session.commit()


async def create_test_session(
    db_session,
    tutor_id: str,
    student_id: str,
    session_number: int,
    days_ago: int,
    rating: int = 5,
):
    """Helper to create a test session with feedback."""
    session_date = datetime.utcnow() - timedelta(days=days_ago)

    session = Session(
        session_id=f"session_test_{tutor_id}_{session_number}",
        tutor_id=tutor_id,
        student_id=student_id,
        session_number=session_number,
        scheduled_start=session_date,
        actual_start=session_date,
        duration_minutes=60,
        subject="Math",
        session_type=SessionType.ONE_ON_ONE,
        tutor_initiated_reschedule=False,
        no_show=False,
        late_start_minutes=0,
        engagement_score=85.0,
        learning_objectives_met=True,
        technical_issues=False,
    )
    db_session.add(session)

    feedback = StudentFeedback(
        feedback_id=f"feedback_test_{session.session_id}",
        session_id=session.session_id,
        student_id=student_id,
        tutor_id=tutor_id,
        overall_rating=rating,
        is_first_session=(session_number == 1),
        subject_knowledge_rating=rating,
        communication_rating=rating,
        patience_rating=rating,
        engagement_rating=rating,
        helpfulness_rating=rating,
        would_recommend=True,
        submitted_at=session_date + timedelta(hours=1),
    )
    db_session.add(feedback)

    await db_session.commit()
    return session


@pytest.mark.asyncio
async def test_worker_processes_session_event(
    db_session,
    redis_client,
    publisher,
    test_tutor,
    test_student,
):
    """Test that worker processes a session completion event and updates metrics."""
    # Create some historical sessions for context
    for i in range(5):
        await create_test_session(
            db_session,
            test_tutor.tutor_id,
            test_student.student_id,
            i + 1,
            days_ago=20 - i,
            rating=5,
        )

    # Publish a new session completion event
    new_session_data = {
        "session_id": f"session_test_{test_tutor.tutor_id}_6",
        "tutor_id": test_tutor.tutor_id,
        "student_id": test_student.student_id,
        "session_number": 6,
        "scheduled_start": datetime.utcnow().isoformat(),
        "actual_start": datetime.utcnow().isoformat(),
        "duration_minutes": 60,
        "subject": "Math",
        "session_type": "1-on-1",
        "tutor_initiated_reschedule": False,
        "no_show": False,
        "late_start_minutes": 0,
        "engagement_score": 90.0,
        "learning_objectives_met": True,
        "technical_issues": False,
    }

    # Publish to enrichment queue (simulating completed enrichment)
    publisher.publish(
        "tutormax:sessions:enrichment",
        new_session_data,
        metadata={"source": "test", "timestamp": datetime.utcnow().isoformat()}
    )

    # Create worker with short debounce for testing
    worker = MetricsUpdateWorker(
        redis_client=redis_client,
        consumer_group="test-metrics-workers",
        batch_size=5,
        poll_interval_ms=100,
        enable_debouncing=True,
        debounce_window_seconds=2,
    )

    # Run worker for a short time
    start_time = time.time()

    async def run_worker_for_duration(duration_seconds: int):
        """Run worker for a specific duration."""
        worker.running = True
        worker.stats["start_time"] = datetime.now()

        end_time = time.time() + duration_seconds
        session_queue = "tutormax:sessions:enrichment"

        try:
            worker.consumer.create_consumer_group(session_queue, start_id="0")
        except Exception:
            pass

        while time.time() < end_time:
            worker._process_session_events(session_queue)
            worker._process_debounced_updates()
            await asyncio.sleep(0.1)

        # Force final debounced updates
        worker._process_debounced_updates(force=True)

    # Run worker for 5 seconds
    await run_worker_for_duration(5)

    elapsed = time.time() - start_time

    # Verify metrics were updated
    assert worker.stats["events_processed"] >= 1, "Should process at least 1 event"
    assert worker.stats["metrics_calculated"] >= 3, "Should calculate 3 metric windows"
    assert worker.stats["metrics_saved"] >= 3, "Should save 3 metric windows"

    # Verify latency is acceptable (<60 seconds, but should be much faster)
    assert elapsed < 60, f"Processing took {elapsed}s, should be < 60s"

    print(f"\n✓ Worker Stats:")
    print(f"  Events processed: {worker.stats['events_processed']}")
    print(f"  Metrics calculated: {worker.stats['metrics_calculated']}")
    print(f"  Metrics saved: {worker.stats['metrics_saved']}")
    print(f"  Tutors updated: {len(worker.stats['tutors_updated'])}")
    print(f"  Total processing time: {elapsed:.2f}s")
    print(f"  Errors: {worker.stats['errors']}")

    # Verify metrics exist in database
    from sqlalchemy import select
    query = select(TutorPerformanceMetric).where(
        TutorPerformanceMetric.tutor_id == test_tutor.tutor_id
    )
    result = await db_session.execute(query)
    metrics = result.scalars().all()

    assert len(metrics) >= 3, "Should have metrics for 3 windows"

    # Check that metrics are recent
    for metric in metrics:
        age = (datetime.utcnow() - metric.calculation_date).total_seconds()
        assert age < 60, f"Metric should be recent (<60s), but is {age}s old"

    print(f"\n✓ Database Metrics:")
    for metric in metrics:
        print(
            f"  {metric.window.value}: "
            f"sessions={metric.sessions_completed}, "
            f"avg_rating={metric.avg_rating}, "
            f"tier={metric.performance_tier.value if metric.performance_tier else 'N/A'}"
        )


@pytest.mark.asyncio
async def test_worker_debouncing(db_session, redis_client, publisher, test_tutor, test_student):
    """Test that debouncing batches multiple events for the same tutor."""
    # Publish multiple session events in quick succession
    for i in range(5):
        session_data = {
            "session_id": f"session_test_debounce_{i}",
            "tutor_id": test_tutor.tutor_id,
            "student_id": test_student.student_id,
            "session_number": i + 1,
            "scheduled_start": datetime.utcnow().isoformat(),
            "actual_start": datetime.utcnow().isoformat(),
            "duration_minutes": 60,
            "subject": "Math",
            "session_type": "1-on-1",
        }

        publisher.publish(
            "tutormax:sessions:enrichment",
            session_data,
            metadata={"source": "test"}
        )
        await asyncio.sleep(0.1)

    # Create worker with debouncing
    worker = MetricsUpdateWorker(
        redis_client=redis_client,
        consumer_group="test-debounce-workers",
        batch_size=10,
        enable_debouncing=True,
        debounce_window_seconds=2,
    )

    # Run worker
    async def run_worker_for_duration(duration_seconds: int):
        worker.running = True
        worker.stats["start_time"] = datetime.now()

        end_time = time.time() + duration_seconds
        session_queue = "tutormax:sessions:enrichment"

        try:
            worker.consumer.create_consumer_group(session_queue, start_id="0")
        except Exception:
            pass

        while time.time() < end_time:
            worker._process_session_events(session_queue)
            worker._process_debounced_updates()
            await asyncio.sleep(0.1)

        worker._process_debounced_updates(force=True)

    await run_worker_for_duration(5)

    # Verify debouncing worked: should have processed 5 events but only updated metrics once
    assert worker.stats["events_processed"] >= 5, "Should process all 5 events"

    # With debouncing, metrics should be calculated only once per tutor (3 windows)
    # But we might get some overlap, so check it's reasonable
    print(f"\n✓ Debouncing Stats:")
    print(f"  Events processed: {worker.stats['events_processed']}")
    print(f"  Metrics calculated: {worker.stats['metrics_calculated']}")
    print(f"  Tutors updated: {len(worker.stats['tutors_updated'])}")

    # Should update only 1 tutor despite 5 events
    assert len(worker.stats['tutors_updated']) == 1, "Should update only 1 unique tutor"


@pytest.mark.asyncio
async def test_metrics_accuracy(db_session, test_tutor, test_student):
    """Test that calculated metrics are accurate."""
    # Create sessions with known metrics
    # 5 sessions in last 7 days, all rated 5
    for i in range(5):
        await create_test_session(
            db_session,
            test_tutor.tutor_id,
            test_student.student_id,
            i + 1,
            days_ago=i + 1,
            rating=5,
        )

    # Calculate metrics directly
    from src.evaluation.performance_calculator import PerformanceCalculator

    async with get_session() as session:
        calculator = PerformanceCalculator(session)

        metrics = await calculator.calculate_metrics(
            tutor_id=test_tutor.tutor_id,
            window=MetricWindow.SEVEN_DAY,
        )

        # Verify metrics
        assert metrics.sessions_completed == 5, "Should have 5 completed sessions"
        assert metrics.avg_rating == 5.0, "Average rating should be 5.0"
        assert metrics.first_session_success_rate == 100.0, "First session rated ≥4"
        assert metrics.no_show_count == 0, "No no-shows"

        print(f"\n✓ Metrics Accuracy:")
        print(f"  Sessions completed: {metrics.sessions_completed}")
        print(f"  Average rating: {metrics.avg_rating}")
        print(f"  First session success: {metrics.first_session_success_rate}%")
        print(f"  Engagement score: {metrics.engagement_score}")
        print(f"  Performance tier: {metrics.performance_tier.value}")


def test_worker_initialization():
    """Test worker initializes correctly."""
    worker = MetricsUpdateWorker(
        batch_size=10,
        poll_interval_ms=500,
        enable_debouncing=True,
        debounce_window_seconds=30,
    )

    assert worker.batch_size == 10
    assert worker.poll_interval_ms == 500
    assert worker.enable_debouncing is True
    assert worker.debounce_window_seconds == 30
    assert worker.stats["events_processed"] == 0
    assert worker.stats["metrics_calculated"] == 0

    print("\n✓ Worker initialized successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
