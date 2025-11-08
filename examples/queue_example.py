"""
Example usage of TutorMax message queue system.

This script demonstrates:
1. Publishing messages to different channels
2. Consuming messages with a worker
3. Processing messages with custom handlers
4. Monitoring queue health
"""
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.queue import (
    get_redis_client,
    MessagePublisher,
    MessageConsumer,
    QueueWorker,
    QueueChannels,
    shutdown_redis_client
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_publish_messages():
    """Example: Publishing messages to queues."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Publishing Messages")
    logger.info("=" * 60)

    # Get Redis client
    redis_client = get_redis_client()

    # Create publisher
    publisher = MessagePublisher(redis_client)

    # Example tutor data
    tutor_data = {
        "tutor_id": "T001",
        "name": "John Smith",
        "subject": "Mathematics",
        "rating": 4.8,
        "sessions_count": 150
    }

    # Publish tutor data
    msg_id = publisher.publish_tutor_data(tutor_data)
    logger.info(f"Published tutor data, message ID: {msg_id}")

    # Example session data
    session_data = {
        "session_id": "S001",
        "tutor_id": "T001",
        "student_id": "ST001",
        "duration_minutes": 60,
        "subject": "Algebra",
        "completion_status": "completed"
    }

    # Publish session data
    msg_id = publisher.publish_session_data(session_data)
    logger.info(f"Published session data, message ID: {msg_id}")

    # Example feedback data
    feedback_data = {
        "feedback_id": "F001",
        "session_id": "S001",
        "rating": 5,
        "comment": "Excellent tutoring session!",
        "sentiment": "positive"
    }

    # Publish feedback data
    msg_id = publisher.publish_feedback_data(feedback_data)
    logger.info(f"Published feedback data, message ID: {msg_id}")

    # Batch publish example
    batch_messages = [
        {"tutor_id": f"T{i:03d}", "name": f"Tutor {i}", "rating": 4.0 + (i % 10) / 10}
        for i in range(2, 12)
    ]

    msg_ids = publisher.publish_batch(QueueChannels.TUTORS, batch_messages)
    logger.info(f"Published {len(msg_ids)} messages in batch")

    # Check queue lengths
    logger.info("\nQueue Lengths:")
    for channel in QueueChannels.all_channels():
        length = publisher.get_stream_length(channel)
        logger.info(f"  {channel}: {length} messages")


def example_consume_messages():
    """Example: Consuming messages from queues."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Consuming Messages")
    logger.info("=" * 60)

    # Get Redis client
    redis_client = get_redis_client()

    # Create consumer
    consumer = MessageConsumer(redis_client)

    # Consume from tutors channel
    logger.info(f"\nConsuming from {QueueChannels.TUTORS}:")
    messages = consumer.consume(QueueChannels.TUTORS, count=5)

    for i, msg in enumerate(messages, 1):
        logger.info(f"  Message {i}:")
        logger.info(f"    ID: {msg['id']}")
        logger.info(f"    Data: {msg['data']}")

        # Acknowledge message
        consumer.acknowledge(QueueChannels.TUTORS, msg['_redis_id'])

    # Check consumer stats
    logger.info(f"\nConsumer Stats: {consumer.get_stats()}")


def example_worker_with_handlers():
    """Example: Using worker with custom handlers."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 3: Worker with Custom Handlers")
    logger.info("=" * 60)

    # Define message handlers
    def process_tutor(data: dict) -> bool:
        """Process tutor data."""
        logger.info(f"Processing tutor: {data.get('name', 'Unknown')}")
        # Add your processing logic here
        return True

    def process_session(data: dict) -> bool:
        """Process session data."""
        logger.info(f"Processing session: {data.get('session_id', 'Unknown')}")
        # Add your processing logic here
        return True

    def process_feedback(data: dict) -> bool:
        """Process feedback data."""
        logger.info(f"Processing feedback: {data.get('rating', 0)} stars")
        # Add your processing logic here
        return True

    # Create worker
    worker = QueueWorker(
        channels=[
            QueueChannels.TUTORS,
            QueueChannels.SESSIONS,
            QueueChannels.FEEDBACK
        ]
    )

    # Register handlers
    worker.register_handler(QueueChannels.TUTORS, process_tutor)
    worker.register_handler(QueueChannels.SESSIONS, process_session)
    worker.register_handler(QueueChannels.FEEDBACK, process_feedback)

    # Process one batch (for demo purposes)
    logger.info("\nProcessing one batch from each channel...")
    total_processed = worker.run_once()
    logger.info(f"Processed {total_processed} messages")

    # Show stats
    logger.info(f"\nWorker Stats: {worker.get_stats()}")


def example_health_check():
    """Example: Checking Redis connection health."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 4: Health Check")
    logger.info("=" * 60)

    redis_client = get_redis_client()
    health = redis_client.health_check()

    logger.info("\nRedis Health Status:")
    for key, value in health.items():
        logger.info(f"  {key}: {value}")


def main():
    """Run all examples."""
    try:
        # Run examples
        example_publish_messages()
        example_consume_messages()
        example_worker_with_handlers()
        example_health_check()

        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)

    finally:
        # Cleanup
        shutdown_redis_client()
        logger.info("\nRedis client shut down.")


if __name__ == "__main__":
    main()
