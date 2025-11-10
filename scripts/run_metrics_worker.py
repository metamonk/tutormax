#!/usr/bin/env python3
"""
Run the Real-Time Metrics Update Worker.

This script starts the metrics update worker as a standalone service.
It can be run manually or via process management tools (systemd, supervisor, etc.).

Usage:
    python scripts/run_metrics_worker.py [--batch-size=10] [--poll-interval=1000]

Options:
    --batch-size: Number of events to process per batch (default: 10)
    --poll-interval: Polling interval in milliseconds (default: 1000)
    --no-debounce: Disable debouncing (process immediately)
    --debounce-window: Debounce window in seconds (default: 30)
    --consumer-group: Consumer group name (default: metrics-update-workers)
"""

import sys
import argparse
import logging
from src.evaluation.metrics_update_worker import MetricsUpdateWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/metrics_worker.log') if True else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run the Real-Time Metrics Update Worker'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of events to process per batch (default: 10)'
    )

    parser.add_argument(
        '--poll-interval',
        type=int,
        default=1000,
        help='Polling interval in milliseconds (default: 1000)'
    )

    parser.add_argument(
        '--no-debounce',
        action='store_true',
        help='Disable debouncing (process immediately)'
    )

    parser.add_argument(
        '--debounce-window',
        type=int,
        default=30,
        help='Debounce window in seconds (default: 30)'
    )

    parser.add_argument(
        '--consumer-group',
        type=str,
        default='metrics-update-workers',
        help='Consumer group name (default: metrics-update-workers)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("TutorMax Real-Time Metrics Update Worker")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  Consumer group: {args.consumer_group}")
    logger.info(f"  Batch size: {args.batch_size}")
    logger.info(f"  Poll interval: {args.poll_interval}ms")
    logger.info(f"  Debouncing: {not args.no_debounce}")
    if not args.no_debounce:
        logger.info(f"  Debounce window: {args.debounce_window}s")
    logger.info("=" * 80)

    # Create and start worker
    try:
        worker = MetricsUpdateWorker(
            consumer_group=args.consumer_group,
            batch_size=args.batch_size,
            poll_interval_ms=args.poll_interval,
            enable_debouncing=not args.no_debounce,
            debounce_window_seconds=args.debounce_window,
        )

        logger.info("Starting worker... (Press Ctrl+C to stop)")
        worker.start()

    except KeyboardInterrupt:
        logger.info("\nReceived shutdown signal, stopping worker...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Worker failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
