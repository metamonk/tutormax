"""
Demo script for the Synthetic Data Generator Worker.

This script demonstrates how to use the data generator tasks to create
synthetic data for the TutorMax system.

Run this after starting:
1. Redis server
2. PostgreSQL with TutorMax database
3. Celery worker (optional, for async demo)

Usage:
    python demos/demo_data_generator_worker.py
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def demo_synchronous_generation():
    """Demonstrate synchronous (blocking) data generation."""
    print("="*70)
    print("DEMO 1: Synchronous Data Generation")
    print("="*70)
    print("\nCalling generate_synthetic_data() directly (synchronous)...")
    print("This will block until completion.\n")

    from src.workers.tasks.data_generator import generate_synthetic_data

    # Generate small batch
    result = generate_synthetic_data(
        num_tutors=5,
        num_sessions=25,
        seed=42  # For reproducibility
    )

    print("\n✓ Generation Complete!")
    print("\nResults:")
    print(f"  Tutors Created:    {result['tutors_created']}")
    print(f"  Tutors Existing:   {result['tutors_existing']}")
    print(f"  Sessions Created:  {result['sessions_created']}")
    print(f"  Students Created:  {result['students_created']}")
    print(f"  Duration:          {result['duration_seconds']:.2f} seconds")
    print(f"  Errors:            {len(result['errors'])}")

    if result['errors']:
        print("\nErrors encountered:")
        for error in result['errors']:
            print(f"  - {error}")

    return result


def demo_asynchronous_generation():
    """Demonstrate asynchronous data generation via Celery."""
    print("\n\n" + "="*70)
    print("DEMO 2: Asynchronous Data Generation (via Celery)")
    print("="*70)
    print("\nNOTE: This requires a Celery worker to be running!")
    print("Start worker: celery -A src.workers.celery_app worker --loglevel=info")
    print()

    from src.workers.tasks.data_generator import generate_synthetic_data

    try:
        # Queue the task
        print("Queueing task with .delay()...")
        task = generate_synthetic_data.delay(
            num_tutors=3,
            num_sessions=15
        )

        print(f"\n✓ Task queued!")
        print(f"  Task ID:     {task.id}")
        print(f"  Task Status: {task.status}")

        # Wait for result with timeout
        print("\nWaiting for task to complete (timeout: 60 seconds)...")
        result = task.get(timeout=60)

        print("\n✓ Task Complete!")
        print("\nResults:")
        print(f"  Tutors Created:    {result['tutors_created']}")
        print(f"  Sessions Created:  {result['sessions_created']}")
        print(f"  Students Created:  {result['students_created']}")
        print(f"  Duration:          {result['duration_seconds']:.2f} seconds")

        return result

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  1. Redis is running (redis-server)")
        print("  2. Celery worker is running:")
        print("     celery -A src.workers.celery_app worker --loglevel=info")
        return None


def demo_continuous_generation():
    """Demonstrate continuous generation task."""
    print("\n\n" + "="*70)
    print("DEMO 3: Continuous Data Generation")
    print("="*70)
    print("\nThis task is designed for scheduled execution via Celery Beat.")
    print("Running it directly for demonstration...\n")

    from src.workers.tasks.data_generator import generate_data_continuous

    result = generate_data_continuous(batch_size=20)

    print("\n✓ Continuous Generation Complete!")
    print("\nResults:")
    print(f"  Tutors Created:    {result['tutors_created']}")
    print(f"  Sessions Created:  {result['sessions_created']}")
    print(f"  Students Created:  {result['students_created']}")

    return result


def demo_with_specific_date():
    """Demonstrate generating data for a specific date."""
    print("\n\n" + "="*70)
    print("DEMO 4: Generate Data for Specific Date")
    print("="*70)

    from src.workers.tasks.data_generator import generate_synthetic_data

    # Generate for yesterday
    target_date = "2024-11-07"

    print(f"\nGenerating data for date: {target_date}")

    result = generate_synthetic_data(
        num_tutors=2,
        num_sessions=10,
        target_date=target_date,
        seed=123
    )

    print("\n✓ Generation Complete!")
    print("\nResults:")
    print(f"  Target Date:       {target_date}")
    print(f"  Sessions Created:  {result['sessions_created']}")

    return result


def demo_task_inspection():
    """Demonstrate Celery task inspection."""
    print("\n\n" + "="*70)
    print("DEMO 5: Task Inspection and Metadata")
    print("="*70)

    from src.workers.tasks.data_generator import (
        generate_synthetic_data,
        generate_data_continuous,
        cleanup_old_data,
    )

    print("\nRegistered Tasks:")
    print(f"  1. {generate_synthetic_data.name}")
    print(f"     - Queue: {generate_synthetic_data.queue}")
    print(f"     - Max Retries: 3")
    print(f"     - Soft Time Limit: 1800s (30 min)")

    print(f"\n  2. {generate_data_continuous.name}")
    print(f"     - Queue: {generate_data_continuous.queue}")
    print(f"     - Purpose: Scheduled continuous generation")

    print(f"\n  3. {cleanup_old_data.name}")
    print(f"     - Queue: {cleanup_old_data.queue}")
    print(f"     - Purpose: Data retention management")

    # Show task signature
    print("\n\nTask Signatures:")
    print("\ngenerate_synthetic_data(")
    print("    num_tutors: int = 10,")
    print("    num_sessions: int = 100,")
    print("    target_date: str = None,  # ISO format")
    print("    seed: int = None")
    print(")")

    print("\ngenerate_data_continuous(")
    print("    batch_size: int = 100")
    print(")")

    print("\ncleanup_old_data(")
    print("    days_to_keep: int = 90")
    print(")")


def show_celery_beat_schedule():
    """Show example Celery Beat schedule configuration."""
    print("\n\n" + "="*70)
    print("DEMO 6: Celery Beat Schedule Configuration")
    print("="*70)

    print("\nTo enable scheduled data generation, add this to celery_app.py:")
    print("\n" + "-"*70)

    schedule_code = """
# In celery_app.py beat_schedule dictionary:

'generate-data-hourly': {
    'task': 'data_generator.generate_data_continuous',
    'schedule': crontab(minute=0),  # Every hour at :00
    'kwargs': {'batch_size': 125},  # ~3000 sessions per day
    'options': {'queue': 'data_generation'},
},

'cleanup-old-data-weekly': {
    'task': 'data_generator.cleanup_old_data',
    'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
    'kwargs': {'days_to_keep': 90},
    'options': {'queue': 'data_generation'},
},
"""

    print(schedule_code)
    print("-"*70)

    print("\nThen start Celery Beat:")
    print("  celery -A src.workers.celery_app beat --loglevel=info")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("SYNTHETIC DATA GENERATOR WORKER - DEMO")
    print("="*70)
    print("\nThis demo showcases the data generator worker capabilities.")
    print("\nPrerequisites:")
    print("  ✓ Redis running on localhost:6379")
    print("  ✓ PostgreSQL with TutorMax database")
    print("  ✓ Python dependencies installed")
    print()

    input("Press Enter to start Demo 1 (Synchronous Generation)...")

    # Demo 1: Synchronous
    try:
        demo_synchronous_generation()
    except Exception as e:
        print(f"\n✗ Error in Demo 1: {e}")
        import traceback
        traceback.print_exc()

    # Demo 2: Asynchronous (optional - requires worker)
    print("\n\nDemo 2 requires a running Celery worker.")
    choice = input("Do you want to run Demo 2? (y/n): ").lower()

    if choice == 'y':
        try:
            demo_asynchronous_generation()
        except Exception as e:
            print(f"\n✗ Error in Demo 2: {e}")

    # Demo 3: Continuous
    input("\n\nPress Enter to run Demo 3 (Continuous Generation)...")
    try:
        demo_continuous_generation()
    except Exception as e:
        print(f"\n✗ Error in Demo 3: {e}")

    # Demo 4: Specific Date
    input("\n\nPress Enter to run Demo 4 (Generate for Specific Date)...")
    try:
        demo_with_specific_date()
    except Exception as e:
        print(f"\n✗ Error in Demo 4: {e}")

    # Demo 5: Task Inspection
    input("\n\nPress Enter to show Demo 5 (Task Inspection)...")
    try:
        demo_task_inspection()
    except Exception as e:
        print(f"\n✗ Error in Demo 5: {e}")

    # Demo 6: Beat Schedule
    input("\n\nPress Enter to show Demo 6 (Celery Beat Schedule)...")
    try:
        show_celery_beat_schedule()
    except Exception as e:
        print(f"\n✗ Error in Demo 6: {e}")

    # Summary
    print("\n\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Review generated data in PostgreSQL")
    print("  2. Start Celery worker for async execution")
    print("  3. Configure Celery Beat for scheduled generation")
    print("  4. Monitor with Flower: celery -A src.workers.celery_app flower")
    print()
    print("Documentation:")
    print("  - Task 15.2 Summary: docs/TASK_15.2_DATA_GENERATOR_WORKER.md")
    print("  - Worker Quick Start: README_CELERY_WORKER.md")
    print("="*70)


if __name__ == "__main__":
    main()
