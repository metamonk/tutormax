#!/usr/bin/env python3
"""
CLI script for running daily metrics aggregation.

This script can be executed manually or via cron to aggregate tutor performance
metrics on a daily basis.

Usage:
    # Run for today
    python scripts/run_daily_aggregation.py

    # Run for specific date
    python scripts/run_daily_aggregation.py --date 2025-11-01

    # Run for specific tutors only
    python scripts/run_daily_aggregation.py --tutors tutor_001,tutor_002

    # Include inactive tutors
    python scripts/run_daily_aggregation.py --include-inactive

    # With cleanup of old metrics
    python scripts/run_daily_aggregation.py --cleanup --retention-days 90

    # Dry run (no database writes)
    python scripts/run_daily_aggregation.py --dry-run

Example cron configuration:
    # Run daily at 2:00 AM
    0 2 * * * cd /path/to/tutormax && python scripts/run_daily_aggregation.py
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.daily_aggregator import run_daily_aggregation, logger


def parse_date(date_string: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_string}. Use YYYY-MM-DD"
        )


def parse_tutor_ids(tutor_ids_string: str) -> list[str]:
    """Parse comma-separated tutor IDs."""
    return [tid.strip() for tid in tutor_ids_string.split(",") if tid.strip()]


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run daily tutor performance metrics aggregation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Date options
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Reference date for metrics calculation (YYYY-MM-DD). Defaults to today.",
    )

    # Tutor selection
    parser.add_argument(
        "--tutors",
        type=parse_tutor_ids,
        default=None,
        help="Comma-separated list of tutor IDs to process (e.g., tutor_001,tutor_002)",
    )

    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive tutors in processing",
    )

    # Cleanup options
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup old metrics after aggregation",
    )

    parser.add_argument(
        "--retention-days",
        type=int,
        default=90,
        help="Number of days to retain old metrics (default: 90)",
    )

    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without writing to database (NOT YET IMPLEMENTED)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logger.setLevel("ERROR")
    elif args.verbose:
        logger.setLevel("DEBUG")

    # Display configuration
    if not args.quiet:
        print("=" * 80)
        print("DAILY METRICS AGGREGATION")
        print("=" * 80)
        print(f"Reference date: {args.date.date() if args.date else 'today'}")
        print(f"Tutors to process: {args.tutors if args.tutors else 'all active'}")
        print(f"Include inactive: {args.include_inactive}")
        print(f"Cleanup old metrics: {args.cleanup}")
        if args.cleanup:
            print(f"Retention days: {args.retention_days}")
        print(f"Dry run: {args.dry_run}")
        print("=" * 80)
        print()

    # Warn about dry-run
    if args.dry_run:
        logger.warning("DRY RUN MODE: Not yet implemented - will run normally")
        print()

    try:
        # Run aggregation
        summary = await run_daily_aggregation(
            reference_date=args.date,
            tutor_ids=args.tutors,
            include_inactive=args.include_inactive,
            cleanup_old_metrics=args.cleanup,
            retention_days=args.retention_days,
        )

        # Display results
        if not args.quiet:
            print()
            print("=" * 80)
            print("RESULTS")
            print("=" * 80)
            print(f"Total tutors processed: {summary.total_tutors}")
            print(f"Successful: {summary.successful}")
            print(f"Failed: {summary.failed}")
            print(f"Total metrics saved: {summary.total_metrics_saved}")
            print(f"Success rate: {summary.success_rate}%")
            print(f"Runtime: {summary.total_runtime_seconds:.2f} seconds")
            print("=" * 80)

            if summary.errors:
                print()
                print("ERRORS:")
                for error in summary.errors:
                    print(f"  - {error['tutor_id']}: {error['error']}")

        # Exit with appropriate code
        if summary.failed > 0:
            sys.exit(1)  # Indicate partial failure
        else:
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
