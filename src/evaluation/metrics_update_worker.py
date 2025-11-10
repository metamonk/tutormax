"""
Real-Time Metrics Update Worker.

Listens for session completion events from Redis and updates
tutor performance metrics in near real-time (<60 seconds).

This worker:
1. Consumes session completion events from Redis enrichment queue
2. Calculates updated performance metrics for affected tutors
3. Persists metrics to tutor_performance_metrics table
4. Maintains low latency (<60s from event to database)
"""

import logging
import time
import signal
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..queue.client import RedisClient
from ..queue.consumer import MessageConsumer
from ..queue.channels import QueueChannels
from ..database.connection import get_session
from ..database.models import MetricWindow
from .performance_calculator import PerformanceCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsUpdateWorker:
    """
    Worker that updates performance metrics in real-time based on session events.

    Processing flow:
    1. Listen to session enrichment queue
    2. Extract tutor_id from session completion events
    3. Calculate updated metrics for affected tutor
    4. Save metrics to database
    5. Acknowledge processed events
    """

    # Target metric calculation windows
    METRIC_WINDOWS = [
        MetricWindow.SEVEN_DAY,
        MetricWindow.THIRTY_DAY,
        MetricWindow.NINETY_DAY,
    ]

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        consumer_group: str = "metrics-update-workers",
        batch_size: int = 5,
        poll_interval_ms: int = 1000,
        enable_debouncing: bool = True,
        debounce_window_seconds: int = 30,
    ):
        """
        Initialize metrics update worker.

        Args:
            redis_client: Redis client instance (creates new if None)
            consumer_group: Consumer group name
            batch_size: Number of events to process per batch
            poll_interval_ms: Polling interval in milliseconds
            enable_debouncing: Enable debouncing to batch updates per tutor
            debounce_window_seconds: Window for debouncing tutor updates
        """
        self.redis_client = redis_client or RedisClient()
        self.consumer_group = consumer_group
        self.batch_size = batch_size
        self.poll_interval_ms = poll_interval_ms
        self.enable_debouncing = enable_debouncing
        self.debounce_window_seconds = debounce_window_seconds

        # Initialize components
        self.consumer = MessageConsumer(
            self.redis_client,
            consumer_group=consumer_group
        )

        # Worker state
        self.running = False
        self.stats = {
            "events_processed": 0,
            "metrics_calculated": 0,
            "metrics_saved": 0,
            "errors": 0,
            "tutors_updated": set(),
            "start_time": None,
            "total_processing_time_ms": 0,
        }

        # Debouncing state: track tutors to update
        self._pending_tutor_updates: Dict[str, datetime] = {}

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

    def start(self):
        """
        Start the metrics update worker.

        Listens to the sessions enrichment queue for completed sessions.
        """
        logger.info("Starting Metrics Update Worker")
        logger.info(f"Consumer group: {self.consumer_group}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Poll interval: {self.poll_interval_ms}ms")
        logger.info(f"Debouncing: {self.enable_debouncing}")
        if self.enable_debouncing:
            logger.info(f"Debounce window: {self.debounce_window_seconds}s")

        self.running = True
        self.stats["start_time"] = datetime.now()

        # Queue to monitor: sessions enrichment queue
        # This queue receives sessions AFTER they've been enriched and persisted
        session_queue = "tutormax:sessions:enrichment"

        # Create consumer group
        try:
            self.consumer.create_consumer_group(session_queue, start_id="0")
        except Exception as e:
            logger.warning(f"Consumer group may already exist: {e}")

        # Main processing loop
        try:
            while self.running:
                processed = self._process_session_events(session_queue)

                # Process debounced updates if enabled
                if self.enable_debouncing:
                    self._process_debounced_updates()

                # Sleep if no messages were processed
                if processed == 0:
                    time.sleep(self.poll_interval_ms / 1000.0)

                # Log stats periodically (every 50 events)
                if self.stats["events_processed"] % 50 == 0 and self.stats["events_processed"] > 0:
                    self._log_stats()

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)

        finally:
            # Process any remaining debounced updates before shutdown
            if self.enable_debouncing:
                self._process_debounced_updates(force=True)
            self._shutdown()

    def _process_session_events(self, queue: str) -> int:
        """
        Process session completion events from the queue.

        Args:
            queue: Queue name

        Returns:
            Number of events processed
        """
        try:
            # Consume messages
            messages = self.consumer.consume(
                queue,
                count=self.batch_size,
                block_ms=None  # Non-blocking
            )

            if not messages:
                return 0

            logger.info(f"Processing {len(messages)} session events from {queue}")

            # Extract tutor IDs from session events
            tutor_ids = set()
            message_ids = []

            for message in messages:
                start_time = time.time()

                try:
                    # Extract session data
                    session_data = message.get("data", {})
                    tutor_id = session_data.get("tutor_id")
                    session_id = session_data.get("session_id")

                    if tutor_id:
                        if self.enable_debouncing:
                            # Add to debounce queue
                            self._pending_tutor_updates[tutor_id] = datetime.now()
                            logger.debug(
                                f"Session {session_id} completed for tutor {tutor_id}, "
                                f"queued for metrics update"
                            )
                        else:
                            # Process immediately
                            tutor_ids.add(tutor_id)

                        self.stats["events_processed"] += 1
                        message_ids.append(message.get("_redis_id"))

                    else:
                        logger.warning(f"Session event missing tutor_id: {session_id}")

                    processing_time = (time.time() - start_time) * 1000
                    self.stats["total_processing_time_ms"] += processing_time

                except Exception as e:
                    logger.error(f"Error processing session event: {e}", exc_info=True)
                    self.stats["errors"] += 1

            # If not using debouncing, update metrics immediately
            if not self.enable_debouncing and tutor_ids:
                asyncio.run(self._update_metrics_batch(list(tutor_ids)))

            # Acknowledge all processed messages
            for message_id in message_ids:
                try:
                    self.consumer.acknowledge(queue, message_id)
                except Exception as e:
                    logger.error(f"Failed to acknowledge message {message_id}: {e}")

            return len(messages)

        except Exception as e:
            logger.error(f"Error processing session events: {e}", exc_info=True)
            return 0

    def _process_debounced_updates(self, force: bool = False):
        """
        Process pending tutor updates from debounce queue.

        Args:
            force: If True, process all pending updates regardless of time
        """
        if not self._pending_tutor_updates:
            return

        now = datetime.now()
        tutors_to_update = []

        # Find tutors ready for update
        for tutor_id, queued_at in list(self._pending_tutor_updates.items()):
            time_elapsed = (now - queued_at).total_seconds()

            if force or time_elapsed >= self.debounce_window_seconds:
                tutors_to_update.append(tutor_id)
                del self._pending_tutor_updates[tutor_id]

        # Update metrics for ready tutors
        if tutors_to_update:
            logger.info(
                f"Processing debounced metrics updates for {len(tutors_to_update)} tutors"
            )
            asyncio.run(self._update_metrics_batch(tutors_to_update))

    async def _update_metrics_batch(self, tutor_ids: List[str]):
        """
        Update metrics for a batch of tutors.

        Args:
            tutor_ids: List of tutor IDs to update
        """
        for tutor_id in tutor_ids:
            try:
                await self._update_tutor_metrics(tutor_id)
                self.stats["tutors_updated"].add(tutor_id)
            except Exception as e:
                logger.error(
                    f"Failed to update metrics for tutor {tutor_id}: {e}",
                    exc_info=True
                )
                self.stats["errors"] += 1

    async def _update_tutor_metrics(self, tutor_id: str):
        """
        Calculate and save metrics for a specific tutor.

        Args:
            tutor_id: Tutor ID
        """
        start_time = time.time()

        async with get_session() as db_session:
            calculator = PerformanceCalculator(db_session)

            # Calculate metrics for all windows
            for window in self.METRIC_WINDOWS:
                try:
                    # Calculate metrics
                    metrics = await calculator.calculate_metrics(
                        tutor_id=tutor_id,
                        window=window,
                        reference_date=datetime.utcnow()
                    )

                    self.stats["metrics_calculated"] += 1

                    # Save to database
                    metric_id = await calculator.save_metrics(metrics)

                    self.stats["metrics_saved"] += 1

                    logger.debug(
                        f"Updated {window.value} metrics for tutor {tutor_id}: "
                        f"metric_id={metric_id}, "
                        f"avg_rating={metrics.avg_rating}, "
                        f"tier={metrics.performance_tier.value if metrics.performance_tier else 'N/A'}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to calculate {window.value} metrics for tutor {tutor_id}: {e}",
                        exc_info=True
                    )
                    self.stats["errors"] += 1

            # Commit all metrics for this tutor
            await db_session.commit()

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Updated all metrics for tutor {tutor_id} in {elapsed_ms:.2f}ms"
        )

    def _log_stats(self) -> None:
        """Log current statistics."""
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
            event_rate = self.stats["events_processed"] / uptime if uptime > 0 else 0

            avg_processing_time = 0
            if self.stats["events_processed"] > 0:
                avg_processing_time = (
                    self.stats["total_processing_time_ms"] / self.stats["events_processed"]
                )

            logger.info(
                f"Stats: "
                f"events={self.stats['events_processed']}, "
                f"metrics_calculated={self.stats['metrics_calculated']}, "
                f"metrics_saved={self.stats['metrics_saved']}, "
                f"errors={self.stats['errors']}, "
                f"tutors_updated={len(self.stats['tutors_updated'])}, "
                f"event_rate={event_rate:.2f}/s, "
                f"avg_processing_time={avg_processing_time:.2f}ms, "
                f"pending_updates={len(self._pending_tutor_updates)}"
            )

    def _shutdown(self) -> None:
        """Shutdown worker gracefully."""
        logger.info("Shutting down metrics update worker...")

        # Log final stats
        self._log_stats()

        logger.info("Metrics update worker stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        stats = self.stats.copy()
        stats["tutors_updated"] = len(self.stats["tutors_updated"])
        stats["pending_updates"] = len(self._pending_tutor_updates)
        return stats


def main():
    """Main entry point for metrics update worker."""
    logger.info("Starting TutorMax Real-Time Metrics Update Worker")
    logger.info("Monitoring session completion events for performance metric updates")

    # Create worker with debouncing enabled for efficiency
    worker = MetricsUpdateWorker(
        batch_size=5,
        poll_interval_ms=1000,
        enable_debouncing=True,
        debounce_window_seconds=30,
    )

    # Start processing
    worker.start()


if __name__ == "__main__":
    main()
