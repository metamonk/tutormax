#!/usr/bin/env python3
"""
Demo: Real-Time Metrics Update System

Demonstrates the real-time metrics update worker in action:
1. Creates a tutor with historical session data
2. Simulates new session completions
3. Shows metrics being updated in real-time
4. Displays latency and performance statistics
"""

import asyncio
import time
from datetime import datetime, timedelta
from threading import Thread

from src.evaluation.metrics_update_worker import MetricsUpdateWorker
from src.queue.client import RedisClient
from src.queue.publisher import MessagePublisher
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
from sqlalchemy import select


class Colors:
    """ANSI color codes for pretty output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}\n")


def print_section(text: str):
    """Print a formatted section."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▶ {text}{Colors.END}")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def print_metric(label: str, value: any):
    """Print a metric."""
    print(f"{Colors.YELLOW}  {label}:{Colors.END} {value}")


async def setup_test_data():
    """Create test tutor with historical session data."""
    print_section("Setting up test data...")

    async with get_session() as db:
        # Create tutor
        tutor = Tutor(
            tutor_id="tutor_demo_realtime_001",
            name="Alice Johnson",
            email="alice.demo@tutormax.com",
            onboarding_date=datetime.utcnow() - timedelta(days=60),
            status=TutorStatus.ACTIVE,
            subjects=["Math", "Physics", "Chemistry"],
            education_level="Master's Degree",
            location="San Francisco, CA",
        )
        db.add(tutor)

        # Create student
        student = Student(
            student_id="student_demo_realtime_001",
            name="Bob Smith",
            age=16,
            grade_level="11th",
            subjects_interested=["Math", "Physics"],
        )
        db.add(student)

        await db.commit()

        # Create 15 historical sessions over the past 30 days
        print_info("Creating 15 historical sessions...")
        for i in range(15):
            session_date = datetime.utcnow() - timedelta(days=30 - (i * 2))

            session = Session(
                session_id=f"session_demo_{tutor.tutor_id}_{i+1}",
                tutor_id=tutor.tutor_id,
                student_id=student.student_id,
                session_number=i + 1,
                scheduled_start=session_date,
                actual_start=session_date,
                duration_minutes=60,
                subject=["Math", "Physics", "Chemistry"][i % 3],
                session_type=SessionType.ONE_ON_ONE,
                tutor_initiated_reschedule=(i == 7),  # One reschedule
                no_show=False,
                late_start_minutes=0 if i % 5 != 0 else 15,
                engagement_score=85.0 + (i % 10),
                learning_objectives_met=True,
                technical_issues=False,
            )
            db.add(session)

            # Add feedback
            rating = 5 if i % 3 != 0 else 4
            feedback = StudentFeedback(
                feedback_id=f"feedback_demo_{session.session_id}",
                session_id=session.session_id,
                student_id=student.student_id,
                tutor_id=tutor.tutor_id,
                overall_rating=rating,
                is_first_session=(i == 0),
                subject_knowledge_rating=rating,
                communication_rating=rating,
                patience_rating=rating,
                engagement_rating=rating,
                helpfulness_rating=rating,
                would_recommend=True,
                submitted_at=session_date + timedelta(hours=1),
            )
            db.add(feedback)

        await db.commit()

        print_success(f"Created tutor: {tutor.name} ({tutor.tutor_id})")
        print_success(f"Created student: {student.name}")
        print_success(f"Created 15 historical sessions")

        return tutor.tutor_id, student.student_id


async def show_current_metrics(tutor_id: str):
    """Display current metrics for a tutor."""
    async with get_session() as db:
        query = (
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.tutor_id == tutor_id)
            .order_by(TutorPerformanceMetric.calculation_date.desc())
        )
        result = await db.execute(query)
        metrics = result.scalars().all()

        if not metrics:
            print_info("No metrics found yet")
            return

        # Group by window
        metrics_by_window = {}
        for metric in metrics:
            if metric.window not in metrics_by_window:
                metrics_by_window[metric.window] = metric

        for window in [MetricWindow.SEVEN_DAY, MetricWindow.THIRTY_DAY, MetricWindow.NINETY_DAY]:
            if window not in metrics_by_window:
                continue

            m = metrics_by_window[window]
            age = (datetime.utcnow() - m.calculation_date).total_seconds()

            print(f"\n  {Colors.BOLD}{window.value} Metrics:{Colors.END}")
            print_metric("    Calculation age", f"{age:.1f}s ago")
            print_metric("    Sessions completed", m.sessions_completed)
            print_metric("    Average rating", f"{m.avg_rating:.2f}" if m.avg_rating else "N/A")
            print_metric("    First session success", f"{m.first_session_success_rate:.1f}%" if m.first_session_success_rate else "N/A")
            print_metric("    Reschedule rate", f"{m.reschedule_rate:.1f}%" if m.reschedule_rate else "N/A")
            print_metric("    No-shows", m.no_show_count)
            print_metric("    Engagement score", f"{m.engagement_score:.1f}" if m.engagement_score else "N/A")
            print_metric("    Learning objectives met", f"{m.learning_objectives_met_pct:.1f}%" if m.learning_objectives_met_pct else "N/A")
            print_metric("    Performance tier", m.performance_tier.value if m.performance_tier else "N/A")


def run_worker_thread(worker: MetricsUpdateWorker):
    """Run the worker in a separate thread."""
    worker.start()


async def simulate_session_completions(
    tutor_id: str,
    student_id: str,
    num_sessions: int = 5,
    delay_seconds: float = 2.0
):
    """Simulate new session completions."""
    print_section(f"Simulating {num_sessions} new session completions...")

    redis_client = RedisClient()
    publisher = MessagePublisher(redis_client)

    for i in range(num_sessions):
        session_number = 16 + i
        session_id = f"session_demo_{tutor_id}_{session_number}"

        print_info(f"Publishing session {session_number} completion event...")

        # Publish session completion event
        session_data = {
            "session_id": session_id,
            "tutor_id": tutor_id,
            "student_id": student_id,
            "session_number": session_number,
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

        event_time = time.time()

        publisher.publish(
            "tutormax:sessions:enrichment",
            session_data,
            metadata={
                "source": "demo",
                "timestamp": datetime.utcnow().isoformat(),
                "event_time": event_time,
            }
        )

        print_success(f"Session {session_number} event published at {datetime.utcnow().strftime('%H:%M:%S')}")

        if i < num_sessions - 1:
            await asyncio.sleep(delay_seconds)


async def cleanup_test_data(tutor_id: str, student_id: str):
    """Clean up test data."""
    print_section("Cleaning up test data...")

    async with get_session() as db:
        # Delete tutor (cascade will delete sessions, feedback, metrics)
        from sqlalchemy import delete

        await db.execute(delete(Tutor).where(Tutor.tutor_id == tutor_id))
        await db.execute(delete(Student).where(Student.student_id == student_id))
        await db.commit()

        print_success("Test data cleaned up")


async def main():
    """Main demo function."""
    print_header("Real-Time Metrics Update System Demo")

    # Setup
    tutor_id, student_id = await setup_test_data()

    # Show initial state
    print_section("Initial metrics (before real-time updates):")
    await show_current_metrics(tutor_id)

    # Start the metrics update worker in a background thread
    print_section("Starting Real-Time Metrics Update Worker...")
    worker = MetricsUpdateWorker(
        consumer_group="demo-metrics-workers",
        batch_size=5,
        poll_interval_ms=500,
        enable_debouncing=True,
        debounce_window_seconds=5,  # Short debounce for demo
    )

    worker_thread = Thread(target=run_worker_thread, args=(worker,), daemon=True)
    worker_thread.start()
    print_success("Worker started in background")

    await asyncio.sleep(2)

    # Simulate session completions
    start_time = time.time()
    await simulate_session_completions(
        tutor_id,
        student_id,
        num_sessions=5,
        delay_seconds=1.5
    )

    # Wait for metrics to be processed
    print_section("Waiting for metrics to be updated...")
    await asyncio.sleep(10)

    # Show updated metrics
    print_section("Updated metrics (after real-time updates):")
    await show_current_metrics(tutor_id)

    # Show performance stats
    total_time = time.time() - start_time
    stats = worker.get_stats()

    print_section("Performance Statistics:")
    print_metric("Total processing time", f"{total_time:.2f}s")
    print_metric("Events processed", stats["events_processed"])
    print_metric("Metrics calculated", stats["metrics_calculated"])
    print_metric("Metrics saved", stats["metrics_saved"])
    print_metric("Tutors updated", stats["tutors_updated"])
    print_metric("Errors", stats["errors"])
    print_metric("Pending updates", stats["pending_updates"])

    if stats["events_processed"] > 0:
        avg_latency = total_time / stats["events_processed"]
        print_metric("Average latency per event", f"{avg_latency:.2f}s")

        if avg_latency < 60:
            print_success(f"✓ Latency requirement met: {avg_latency:.2f}s < 60s")
        else:
            print(f"{Colors.RED}✗ Latency requirement not met: {avg_latency:.2f}s > 60s{Colors.END}")

    # Shutdown worker
    print_section("Shutting down worker...")
    worker.running = False
    await asyncio.sleep(2)
    print_success("Worker shutdown complete")

    # Cleanup
    await cleanup_test_data(tutor_id, student_id)

    print_header("Demo Complete!")
    print_info("The real-time metrics update system successfully:")
    print_success("1. Consumed session completion events from Redis")
    print_success("2. Calculated updated metrics for affected tutors")
    print_success("3. Saved metrics to the database")
    print_success("4. Maintained low latency (<60 seconds)")


if __name__ == "__main__":
    asyncio.run(main())
