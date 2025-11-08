"""
TutorMax Queue Worker

Standalone worker script for processing messages from Redis queues.

Usage:
    python examples/worker.py [--channels CHANNEL1,CHANNEL2] [--batch-size N]

Examples:
    # Process all channels
    python examples/worker.py

    # Process only tutors and sessions
    python examples/worker.py --channels tutormax:tutors,tutormax:sessions

    # Custom batch size
    python examples/worker.py --batch-size 20
"""
import argparse
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.queue import (
    QueueWorker,
    QueueChannels,
    get_redis_client,
    shutdown_redis_client
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('worker.log')
    ]
)
logger = logging.getLogger(__name__)


def process_tutor_data(data: dict) -> bool:
    """
    Process tutor data from queue.

    Args:
        data: Tutor data dictionary

    Returns:
        True if processing succeeded
    """
    try:
        tutor_id = data.get('tutor_id', 'Unknown')
        logger.info(f"Processing tutor: {tutor_id}")

        # TODO: Add your tutor data processing logic here
        # Examples:
        # - Validate data
        # - Store in database
        # - Update analytics
        # - Trigger downstream processes

        return True

    except Exception as e:
        logger.error(f"Error processing tutor data: {e}", exc_info=True)
        return False


def process_session_data(data: dict) -> bool:
    """
    Process session data from queue.

    Args:
        data: Session data dictionary

    Returns:
        True if processing succeeded
    """
    try:
        session_id = data.get('session_id', 'Unknown')
        logger.info(f"Processing session: {session_id}")

        # TODO: Add your session data processing logic here
        # Examples:
        # - Calculate session metrics
        # - Update tutor statistics
        # - Store session records
        # - Trigger billing processes

        return True

    except Exception as e:
        logger.error(f"Error processing session data: {e}", exc_info=True)
        return False


def process_feedback_data(data: dict) -> bool:
    """
    Process feedback data from queue.

    Args:
        data: Feedback data dictionary

    Returns:
        True if processing succeeded
    """
    try:
        feedback_id = data.get('feedback_id', 'Unknown')
        rating = data.get('rating', 0)
        logger.info(f"Processing feedback: {feedback_id} (rating: {rating})")

        # TODO: Add your feedback data processing logic here
        # Examples:
        # - Sentiment analysis
        # - Update tutor ratings
        # - Flag problematic feedback
        # - Generate alerts for low ratings

        return True

    except Exception as e:
        logger.error(f"Error processing feedback data: {e}", exc_info=True)
        return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='TutorMax Queue Worker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--channels',
        type=str,
        default=None,
        help='Comma-separated list of channels to process (default: all channels)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of messages to process per batch (default: 10)'
    )

    parser.add_argument(
        '--consumer-group',
        type=str,
        default='tutormax-workers',
        help='Consumer group name (default: tutormax-workers)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    return parser.parse_args()


def main():
    """Run the queue worker."""
    args = parse_args()

    # Set log level
    logging.getLogger().setLevel(args.log_level)

    # Determine channels to process
    if args.channels:
        channels = [ch.strip() for ch in args.channels.split(',')]
    else:
        channels = QueueChannels.all_channels()

    logger.info("=" * 60)
    logger.info("TutorMax Queue Worker Starting")
    logger.info("=" * 60)
    logger.info(f"Channels: {channels}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Consumer group: {args.consumer_group}")
    logger.info("=" * 60)

    try:
        # Create worker
        worker = QueueWorker(
            channels=channels,
            consumer_group=args.consumer_group,
            batch_size=args.batch_size
        )

        # Register handlers
        worker.register_handler(QueueChannels.TUTORS, process_tutor_data)
        worker.register_handler(QueueChannels.SESSIONS, process_session_data)
        worker.register_handler(QueueChannels.FEEDBACK, process_feedback_data)

        # Run worker (blocks until interrupted)
        worker.run()

    except KeyboardInterrupt:
        logger.info("\nWorker interrupted by user")

    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Cleanup
        shutdown_redis_client()
        logger.info("Worker shut down successfully")


if __name__ == "__main__":
    main()
