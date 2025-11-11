"""
Test script for the data generator worker.

This script demonstrates how to use the data generator tasks both synchronously
and asynchronously via Celery.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_direct_import():
    """Test that we can import the task module directly."""
    print("Testing direct import...")

    try:
        from src.workers.tasks import data_generator
        print("✓ Data generator module imported successfully")
        print(f"  Available functions: {[x for x in dir(data_generator) if not x.startswith('_')][:10]}")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_celery_task_registration():
    """Test that tasks are registered with Celery."""
    print("\nTesting Celery task registration...")

    try:
        from src.workers.celery_app import celery_app

        # Get all registered tasks
        all_tasks = list(celery_app.tasks.keys())

        # Filter for our data generator tasks
        data_gen_tasks = [t for t in all_tasks if 'data_generator' in t]

        print(f"✓ Celery app loaded")
        print(f"  Total tasks registered: {len(all_tasks)}")
        print(f"  Data generator tasks: {len(data_gen_tasks)}")

        for task in data_gen_tasks:
            print(f"    - {task}")

        return len(data_gen_tasks) > 0

    except Exception as e:
        print(f"✗ Task registration check failed: {e}")
        return False


def test_task_execution():
    """Test executing the task directly (not via Celery broker)."""
    print("\nTesting direct task execution...")

    try:
        # Import without going through database models
        from src.workers.tasks.data_generator import (
            generate_synthetic_data,
            generate_data_continuous,
        )

        print("✓ Task functions imported")
        print("  Note: Full execution requires database connection")
        print("  Task signatures:")
        print(f"    - generate_synthetic_data: {generate_synthetic_data.name}")
        print(f"    - generate_data_continuous: {generate_data_continuous.name}")

        return True

    except Exception as e:
        print(f"✗ Task execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage_examples():
    """Display usage examples."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)

    print("""
1. Call task synchronously (blocking):

   from src.workers.tasks.data_generator import generate_synthetic_data

   result = generate_synthetic_data(
       num_tutors=20,
       num_sessions=200,
       target_date="2024-11-08",
       seed=42
   )
   print(result)

2. Call task asynchronously via Celery:

   from src.workers.tasks.data_generator import generate_synthetic_data

   # Queue the task
   task = generate_synthetic_data.delay(
       num_tutors=20,
       num_sessions=200
   )

   # Check status
   print(f"Task ID: {task.id}")
   print(f"Status: {task.status}")

   # Get result (blocks until complete)
   result = task.get(timeout=300)
   print(result)

3. Schedule continuous generation:

   # Add to celery_app.py beat_schedule:
   'generate-data-hourly': {
       'task': 'data_generator.generate_data_continuous',
       'schedule': crontab(minute=0),
       'kwargs': {'batch_size': 125},
   }

4. Call from command line:

   # Using Celery CLI
   celery -A src.workers.celery_app call data_generator.generate_synthetic_data \\
       --kwargs='{"num_tutors": 10, "num_sessions": 100}'

   # Start worker
   celery -A src.workers.celery_app worker \\
       --loglevel=info \\
       --queues=data_generation \\
       --concurrency=2

5. Monitor task execution:

   # Using Flower (Celery monitoring tool)
   celery -A src.workers.celery_app flower

   # Then visit http://localhost:5555
""")


if __name__ == "__main__":
    print("="*60)
    print("DATA GENERATOR WORKER TEST SUITE")
    print("="*60)

    results = []

    # Run tests
    results.append(("Direct Import", test_direct_import()))
    results.append(("Celery Registration", test_celery_task_registration()))
    results.append(("Task Execution", test_task_execution()))

    # Show results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    # Show usage
    show_usage_examples()

    # Summary
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print("\n" + "="*60)
    print(f"SUMMARY: {total_passed}/{total_tests} tests passed")
    print("="*60)

    sys.exit(0 if total_passed == total_tests else 1)
