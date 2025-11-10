"""
Demo: Performance Evaluator Worker

This script demonstrates the performance evaluator worker by:
1. Triggering a manual evaluation
2. Monitoring task execution
3. Displaying results

Prerequisites:
- Redis server running
- PostgreSQL database accessible
- Celery worker running (run_performance_worker.sh)
- Some tutors in the database

Usage:
    python demos/demo_performance_worker.py
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workers.tasks.performance_evaluator import (
    evaluate_tutor_performance,
    evaluate_single_tutor,
)
from src.database.database import async_session_maker
from src.database.models import Tutor, TutorStatus
from sqlalchemy import select, func


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


async def get_active_tutor_count():
    """Get count of active tutors in database."""
    async with async_session_maker() as session:
        query = select(func.count()).select_from(Tutor).where(
            Tutor.status == TutorStatus.ACTIVE
        )
        result = await session.execute(query)
        return result.scalar()


async def get_sample_tutor():
    """Get a sample tutor for single evaluation demo."""
    async with async_session_maker() as session:
        query = select(Tutor).where(Tutor.status == TutorStatus.ACTIVE).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()


def demo_batch_evaluation():
    """Demo: Trigger batch evaluation of all tutors."""
    print_header("Demo 1: Batch Evaluation (All Tutors)")

    # Get tutor count
    tutor_count = asyncio.run(get_active_tutor_count())
    print(f"Active tutors in database: {tutor_count}")

    if tutor_count == 0:
        print("\n⚠️  No active tutors found. Please run data generation first.")
        print("   python scripts/demo_data_generation.py")
        return

    print("\nTriggering performance evaluation task...")
    print("(This will run asynchronously in the Celery worker)")

    # Trigger task
    result = evaluate_tutor_performance.delay()

    print(f"\nTask ID: {result.id}")
    print(f"Task State: {result.state}")

    # Wait for result (with timeout)
    print("\nWaiting for task to complete (max 60 seconds)...")
    try:
        task_result = result.get(timeout=60)

        print("\n" + "─" * 60)
        print("RESULTS:")
        print("─" * 60)
        print(f"Tutors Evaluated:  {task_result['tutors_evaluated']}")
        print(f"Successful:        {task_result['tutors_successful']}")
        print(f"Failed:            {task_result['tutors_failed']}")
        print(f"Execution Time:    {task_result['execution_time_seconds']:.2f} seconds")
        print(f"Timestamp:         {task_result['timestamp']}")

        if task_result.get('batch_stats'):
            print(f"\nBatch Count:       {len(task_result['batch_stats'])}")
            for batch in task_result['batch_stats']:
                print(f"  Batch {batch['batch_number']}: "
                      f"{batch['successful']}/{batch['evaluated']} successful")

    except Exception as e:
        print(f"\n❌ Error waiting for task: {str(e)}")
        print("\nNote: Make sure Celery worker is running:")
        print("  ./scripts/run_performance_worker.sh")


def demo_single_tutor_evaluation():
    """Demo: Evaluate a single tutor."""
    print_header("Demo 2: Single Tutor Evaluation")

    # Get a sample tutor
    tutor = asyncio.run(get_sample_tutor())

    if not tutor:
        print("⚠️  No tutors found in database.")
        return

    print(f"Evaluating tutor: {tutor.tutor_id}")
    print(f"Name: {tutor.name}")
    print(f"Email: {tutor.email}")
    print(f"Status: {tutor.status.value}")

    # Evaluate for 30-day window
    print("\nTriggering evaluation for 30-day window...")
    result = evaluate_single_tutor.delay(tutor.tutor_id, "30day")

    print(f"\nTask ID: {result.id}")

    # Wait for result
    print("Waiting for task to complete...")
    try:
        task_result = result.get(timeout=30)

        print("\n" + "─" * 60)
        print("RESULTS:")
        print("─" * 60)
        print(f"Success:           {task_result['success']}")

        if task_result['success']:
            metrics = task_result['metrics']
            print(f"Metric ID:         {metrics.get('metric_id')}")
            print(f"Performance Tier:  {metrics.get('performance_tier')}")
            print(f"Sessions Completed: {metrics.get('sessions_completed')}")
            print(f"Avg Rating:        {metrics.get('avg_rating')}")
            print(f"First Session Success: {metrics.get('first_session_success_rate')}%")
            print(f"Reschedule Rate:   {metrics.get('reschedule_rate')}%")
            print(f"No-Show Count:     {metrics.get('no_show_count')}")
            print(f"Engagement Score:  {metrics.get('engagement_score')}")
        else:
            print(f"Error:             {task_result.get('error')}")

    except Exception as e:
        print(f"\n❌ Error waiting for task: {str(e)}")


def demo_async_execution():
    """Demo: Trigger async execution and check later."""
    print_header("Demo 3: Asynchronous Execution")

    tutor_count = asyncio.run(get_active_tutor_count())
    if tutor_count == 0:
        print("⚠️  No active tutors found.")
        return

    print("Triggering evaluation task asynchronously...")
    result = evaluate_tutor_performance.delay()

    print(f"\nTask ID: {result.id}")
    print("\nYou can check the task status later using:")
    print(f"  celery -A src.workers.celery_app result {result.id}")
    print("\nOr check active tasks:")
    print("  celery -A src.workers.celery_app inspect active")

    print("\nNote: The task will run in the background.")
    print("Check worker logs for execution details:")
    print("  tail -f celery_worker.log")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  Performance Evaluator Worker Demo")
    print("=" * 60)
    print("\nThis demo shows how to use the performance evaluator worker.")

    # Check prerequisites
    print("\nChecking prerequisites...")

    try:
        from redis import Redis
        r = Redis()
        r.ping()
        print("✓ Redis is running")
    except Exception as e:
        print(f"❌ Redis is not running: {str(e)}")
        print("\nPlease start Redis first:")
        print("  redis-server")
        return

    try:
        tutor_count = asyncio.run(get_active_tutor_count())
        print(f"✓ Database accessible ({tutor_count} active tutors)")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return

    # Run demos
    try:
        # Demo 1: Batch evaluation
        demo_batch_evaluation()

        time.sleep(2)

        # Demo 2: Single tutor evaluation
        demo_single_tutor_evaluation()

        time.sleep(2)

        # Demo 3: Async execution
        demo_async_execution()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  Demo Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
