"""
Daily Metrics Aggregator - Batch processing service for tutor performance metrics.

This service:
1. Retrieves all active tutors from the database
2. Calculates performance metrics for each tutor across all time windows (7d, 30d, 90d)
3. Saves metrics to the database with transaction safety
4. Generates summary reports and statistics
5. Handles errors with retry logic and comprehensive logging

Designed to run as a scheduled job (cron) daily.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Tutor,
    TutorStatus,
    MetricWindow,
    TutorPerformanceMetric,
)
from src.database.connection import get_session
from src.evaluation.performance_calculator import PerformanceCalculator, PerformanceMetrics


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AggregationResult:
    """Results from a single tutor's metric aggregation."""

    tutor_id: str
    tutor_name: str
    success: bool
    metrics_saved: List[str] = field(default_factory=list)  # metric_ids
    error: Optional[str] = None
    windows_processed: List[MetricWindow] = field(default_factory=list)
    calculation_time_seconds: float = 0.0


@dataclass
class AggregationSummary:
    """Summary statistics for the entire aggregation run."""

    run_date: datetime
    total_tutors: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    total_metrics_saved: int = 0
    total_runtime_seconds: float = 0.0
    errors: List[Dict[str, str]] = field(default_factory=list)
    results: List[AggregationResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tutors == 0:
            return 0.0
        return round((self.successful / self.total_tutors) * 100, 2)

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/reporting."""
        return {
            "run_date": self.run_date.isoformat(),
            "total_tutors": self.total_tutors,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_metrics_saved": self.total_metrics_saved,
            "total_runtime_seconds": round(self.total_runtime_seconds, 2),
            "success_rate": self.success_rate,
            "errors": self.errors,
        }


class DailyMetricsAggregator:
    """
    Service for daily aggregation of tutor performance metrics.

    Processes all active tutors and calculates metrics across all time windows.
    Designed for scheduled execution (cron jobs).
    """

    def __init__(
        self,
        reference_date: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
        batch_size: int = 50,
    ):
        """
        Initialize the daily aggregator.

        Args:
            reference_date: Date to calculate metrics for (defaults to now)
            max_retries: Maximum retry attempts per tutor
            retry_delay_seconds: Delay between retries
            batch_size: Number of tutors to process per database commit
        """
        self.reference_date = reference_date or datetime.utcnow()
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.batch_size = batch_size

        # Time windows to calculate
        self.windows = [
            MetricWindow.SEVEN_DAY,
            MetricWindow.THIRTY_DAY,
            MetricWindow.NINETY_DAY,
        ]

        logger.info(
            f"DailyMetricsAggregator initialized for date: {self.reference_date.date()}"
        )

    async def run(
        self,
        tutor_ids: Optional[List[str]] = None,
        include_inactive: bool = False,
    ) -> AggregationSummary:
        """
        Run the daily aggregation process.

        Args:
            tutor_ids: Optional list of specific tutor IDs to process
            include_inactive: Whether to include inactive tutors

        Returns:
            AggregationSummary with results and statistics
        """
        start_time = datetime.utcnow()
        summary = AggregationSummary(run_date=self.reference_date)

        logger.info("Starting daily metrics aggregation...")

        try:
            async with get_session() as session:
                # Get list of tutors to process
                tutors = await self._get_tutors(
                    session,
                    tutor_ids=tutor_ids,
                    include_inactive=include_inactive
                )

                summary.total_tutors = len(tutors)
                logger.info(f"Found {summary.total_tutors} tutors to process")

                if summary.total_tutors == 0:
                    logger.warning("No tutors found to process")
                    return summary

                # Process tutors in batches
                for i in range(0, len(tutors), self.batch_size):
                    batch = tutors[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    total_batches = (len(tutors) + self.batch_size - 1) // self.batch_size

                    logger.info(
                        f"Processing batch {batch_num}/{total_batches} "
                        f"({len(batch)} tutors)"
                    )

                    # Process batch
                    batch_results = await self._process_batch(session, batch)

                    # Update summary
                    for result in batch_results:
                        summary.results.append(result)

                        if result.success:
                            summary.successful += 1
                            summary.total_metrics_saved += len(result.metrics_saved)
                        else:
                            summary.failed += 1
                            if result.error:
                                summary.errors.append({
                                    "tutor_id": result.tutor_id,
                                    "tutor_name": result.tutor_name,
                                    "error": result.error,
                                })

                    # Commit batch
                    await session.commit()
                    logger.info(f"Batch {batch_num}/{total_batches} committed")

        except Exception as e:
            logger.error(f"Fatal error during aggregation: {str(e)}", exc_info=True)
            summary.errors.append({
                "tutor_id": "SYSTEM",
                "tutor_name": "SYSTEM",
                "error": f"Fatal error: {str(e)}",
            })

        # Calculate total runtime
        end_time = datetime.utcnow()
        summary.total_runtime_seconds = (end_time - start_time).total_seconds()

        # Log final summary
        logger.info("=" * 80)
        logger.info("DAILY AGGREGATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Run date: {summary.run_date.date()}")
        logger.info(f"Total tutors: {summary.total_tutors}")
        logger.info(f"Successful: {summary.successful}")
        logger.info(f"Failed: {summary.failed}")
        logger.info(f"Skipped: {summary.skipped}")
        logger.info(f"Total metrics saved: {summary.total_metrics_saved}")
        logger.info(f"Success rate: {summary.success_rate}%")
        logger.info(f"Total runtime: {summary.total_runtime_seconds:.2f}s")

        if summary.errors:
            logger.warning(f"Encountered {len(summary.errors)} errors:")
            for error in summary.errors[:10]:  # Show first 10 errors
                logger.warning(f"  - {error['tutor_id']}: {error['error']}")

        logger.info("=" * 80)

        return summary

    async def _get_tutors(
        self,
        session: AsyncSession,
        tutor_ids: Optional[List[str]] = None,
        include_inactive: bool = False,
    ) -> List[Tutor]:
        """
        Retrieve tutors to process.

        Args:
            session: Database session
            tutor_ids: Optional specific tutor IDs
            include_inactive: Include inactive tutors

        Returns:
            List of Tutor objects
        """
        query = select(Tutor)

        # Filter by specific tutor IDs if provided
        if tutor_ids:
            query = query.where(Tutor.tutor_id.in_(tutor_ids))

        # Filter by status
        if not include_inactive:
            query = query.where(Tutor.status == TutorStatus.ACTIVE)

        # Order by tutor_id for consistent processing
        query = query.order_by(Tutor.tutor_id)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def _process_batch(
        self,
        session: AsyncSession,
        tutors: List[Tutor],
    ) -> List[AggregationResult]:
        """
        Process a batch of tutors.

        Args:
            session: Database session
            tutors: List of tutors to process

        Returns:
            List of AggregationResults
        """
        results = []

        for tutor in tutors:
            result = await self._process_tutor(session, tutor)
            results.append(result)

        return results

    async def _process_tutor(
        self,
        session: AsyncSession,
        tutor: Tutor,
    ) -> AggregationResult:
        """
        Process a single tutor with retry logic.

        Args:
            session: Database session
            tutor: Tutor to process

        Returns:
            AggregationResult
        """
        start_time = datetime.utcnow()
        result = AggregationResult(
            tutor_id=tutor.tutor_id,
            tutor_name=tutor.name,
            success=False,
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                # Calculate and save metrics for all windows
                calculator = PerformanceCalculator(session)

                for window in self.windows:
                    # Calculate metrics
                    metrics = await calculator.calculate_metrics(
                        tutor_id=tutor.tutor_id,
                        window=window,
                        reference_date=self.reference_date,
                    )

                    # Save to database
                    metric_id = await calculator.save_metrics(metrics)

                    result.metrics_saved.append(metric_id)
                    result.windows_processed.append(window)

                # Success!
                result.success = True

                # Log stats
                stats = calculator.get_stats()
                logger.debug(
                    f"Tutor {tutor.tutor_id} ({tutor.name}): "
                    f"{len(result.windows_processed)} windows processed, "
                    f"calculator stats: {stats}"
                )

                break  # Exit retry loop on success

            except Exception as e:
                error_msg = f"Attempt {attempt}/{self.max_retries} failed: {str(e)}"
                logger.warning(
                    f"Tutor {tutor.tutor_id} ({tutor.name}): {error_msg}"
                )

                result.error = str(e)

                # Retry if we have attempts left
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds)
                else:
                    logger.error(
                        f"Tutor {tutor.tutor_id} ({tutor.name}): "
                        f"All retry attempts exhausted"
                    )

        # Calculate processing time
        end_time = datetime.utcnow()
        result.calculation_time_seconds = (end_time - start_time).total_seconds()

        return result

    async def get_latest_metrics(
        self,
        session: AsyncSession,
        tutor_id: str,
        window: Optional[MetricWindow] = None,
    ) -> List[TutorPerformanceMetric]:
        """
        Retrieve the most recent metrics for a tutor.

        Args:
            session: Database session
            tutor_id: Tutor ID
            window: Optional specific window filter

        Returns:
            List of TutorPerformanceMetric records
        """
        query = select(TutorPerformanceMetric).where(
            TutorPerformanceMetric.tutor_id == tutor_id
        )

        if window:
            query = query.where(TutorPerformanceMetric.window == window)

        query = query.order_by(TutorPerformanceMetric.calculation_date.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    async def cleanup_old_metrics(
        self,
        session: AsyncSession,
        retention_days: int = 90,
    ) -> int:
        """
        Delete metrics older than retention period.

        Args:
            session: Database session
            retention_days: Number of days to retain metrics

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Find old metrics
        query = select(TutorPerformanceMetric).where(
            TutorPerformanceMetric.calculation_date < cutoff_date
        )
        result = await session.execute(query)
        old_metrics = list(result.scalars().all())

        # Delete them
        for metric in old_metrics:
            await session.delete(metric)

        await session.commit()

        logger.info(
            f"Cleaned up {len(old_metrics)} metrics older than "
            f"{retention_days} days (before {cutoff_date.date()})"
        )

        return len(old_metrics)


async def run_daily_aggregation(
    reference_date: Optional[datetime] = None,
    tutor_ids: Optional[List[str]] = None,
    include_inactive: bool = False,
    cleanup_old_metrics: bool = False,
    retention_days: int = 90,
) -> AggregationSummary:
    """
    Main entry point for daily metrics aggregation.

    Args:
        reference_date: Date to calculate metrics for (defaults to now)
        tutor_ids: Optional list of specific tutor IDs
        include_inactive: Include inactive tutors
        cleanup_old_metrics: Whether to cleanup old metrics after aggregation
        retention_days: Days to retain old metrics

    Returns:
        AggregationSummary with results
    """
    aggregator = DailyMetricsAggregator(reference_date=reference_date)

    # Run aggregation
    summary = await aggregator.run(
        tutor_ids=tutor_ids,
        include_inactive=include_inactive,
    )

    # Optional cleanup
    if cleanup_old_metrics and summary.successful > 0:
        logger.info("Running metrics cleanup...")
        async with get_session() as session:
            deleted_count = await aggregator.cleanup_old_metrics(
                session,
                retention_days=retention_days
            )
            logger.info(f"Cleanup complete: {deleted_count} old metrics deleted")

    return summary


if __name__ == "__main__":
    # Allow running directly for testing
    asyncio.run(run_daily_aggregation())
