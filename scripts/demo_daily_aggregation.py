#!/usr/bin/env python3
"""
Demo script for Daily Metrics Aggregation.

This script demonstrates the daily aggregation functionality by:
1. Running aggregation for all active tutors
2. Displaying detailed results
3. Querying saved metrics from the database
4. Showing summary statistics

Usage:
    python scripts/demo_daily_aggregation.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.daily_aggregator import DailyMetricsAggregator
from src.database.connection import get_session
from src.database.models import Tutor, TutorPerformanceMetric, MetricWindow
from sqlalchemy import select, func


async def display_tutor_summary(session):
    """Display summary of tutors in the database."""
    print("\n" + "=" * 80)
    print("TUTOR DATABASE SUMMARY")
    print("=" * 80)

    # Count tutors by status
    query = select(Tutor.status, func.count(Tutor.tutor_id)).group_by(Tutor.status)
    result = await session.execute(query)
    status_counts = result.all()

    print("\nTutors by Status:")
    for status, count in status_counts:
        print(f"  {status.value}: {count}")

    # Get total count
    total_query = select(func.count(Tutor.tutor_id))
    total_result = await session.execute(total_query)
    total = total_result.scalar()

    print(f"\nTotal Tutors: {total}")
    print()


async def display_existing_metrics(session):
    """Display existing metrics in the database."""
    print("\n" + "=" * 80)
    print("EXISTING METRICS SUMMARY")
    print("=" * 80)

    # Count metrics by window
    query = select(
        TutorPerformanceMetric.window,
        func.count(TutorPerformanceMetric.metric_id)
    ).group_by(TutorPerformanceMetric.window)

    result = await session.execute(query)
    window_counts = result.all()

    print("\nMetrics by Time Window:")
    for window, count in window_counts:
        print(f"  {window.value}: {count}")

    # Get total count
    total_query = select(func.count(TutorPerformanceMetric.metric_id))
    total_result = await session.execute(total_query)
    total = total_result.scalar()

    print(f"\nTotal Metrics: {total}")
    print()


async def display_sample_metrics(session, limit=5):
    """Display sample metrics from the database."""
    print("\n" + "=" * 80)
    print(f"SAMPLE METRICS (showing up to {limit})")
    print("=" * 80)

    query = (
        select(TutorPerformanceMetric)
        .order_by(TutorPerformanceMetric.calculation_date.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    metrics = result.scalars().all()

    if not metrics:
        print("\nNo metrics found in database.")
        return

    # Prepare table data
    table_data = []
    for metric in metrics:
        table_data.append([
            metric.tutor_id[:15],  # Truncate for display
            metric.calculation_date.strftime("%Y-%m-%d %H:%M"),
            metric.window.value,
            metric.sessions_completed,
            f"{metric.avg_rating:.2f}" if metric.avg_rating else "N/A",
            f"{metric.first_session_success_rate:.1f}%" if metric.first_session_success_rate else "N/A",
            metric.performance_tier.value if metric.performance_tier else "N/A",
        ])

    headers = [
        "Tutor ID",
        "Calc Date",
        "Window",
        "Sessions",
        "Avg Rating",
        "1st Session %",
        "Tier"
    ]

    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    print()


async def run_demo():
    """Run the demo aggregation."""
    print("=" * 80)
    print("DAILY METRICS AGGREGATION DEMO")
    print("=" * 80)
    print()

    # Display initial state
    async with get_session() as session:
        await display_tutor_summary(session)
        await display_existing_metrics(session)

    # Run aggregation
    print("\n" + "=" * 80)
    print("RUNNING DAILY AGGREGATION")
    print("=" * 80)
    print()

    aggregator = DailyMetricsAggregator()
    summary = await aggregator.run()

    # Display detailed results
    print("\n" + "=" * 80)
    print("AGGREGATION RESULTS")
    print("=" * 80)
    print()

    print(f"Run Date: {summary.run_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Tutors: {summary.total_tutors}")
    print(f"Successful: {summary.successful}")
    print(f"Failed: {summary.failed}")
    print(f"Total Metrics Saved: {summary.total_metrics_saved}")
    print(f"Success Rate: {summary.success_rate}%")
    print(f"Total Runtime: {summary.total_runtime_seconds:.2f} seconds")

    # Show per-tutor breakdown
    if summary.results:
        print("\n" + "-" * 80)
        print("PER-TUTOR BREAKDOWN")
        print("-" * 80)

        table_data = []
        for result in summary.results[:10]:  # Show first 10
            status = "SUCCESS" if result.success else "FAILED"
            table_data.append([
                result.tutor_id[:20],
                result.tutor_name[:25],
                status,
                len(result.metrics_saved),
                f"{result.calculation_time_seconds:.2f}s",
                result.error[:30] if result.error else "-",
            ])

        headers = ["Tutor ID", "Name", "Status", "Metrics", "Time", "Error"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))

        if len(summary.results) > 10:
            print(f"\n... and {len(summary.results) - 10} more tutors")

    # Show errors if any
    if summary.errors:
        print("\n" + "-" * 80)
        print("ERRORS ENCOUNTERED")
        print("-" * 80)
        for error in summary.errors[:5]:
            print(f"\nTutor: {error['tutor_id']}")
            print(f"Error: {error['error']}")

    # Display updated state
    async with get_session() as session:
        await display_existing_metrics(session)
        await display_sample_metrics(session, limit=10)

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()

    # Return appropriate exit code
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_demo())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
