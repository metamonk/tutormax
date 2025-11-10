"""
Performance Evaluator Worker - Celery Task

This module implements the scheduled performance evaluation worker that:
1. Runs every 15 minutes via Celery Beat
2. Evaluates tutor performance using the PerformanceCalculator
3. Stores results in the database
4. Handles batch processing for efficiency
5. Implements retry logic and error handling
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..celery_app import celery_app
from ..config import worker_settings
from ...database.database import async_session_maker
from ...database.models import (
    Tutor,
    TutorStatus,
    MetricWindow,
)
from ...evaluation.performance_calculator import PerformanceCalculator

# Configure logging
logger = logging.getLogger(__name__)


class PerformanceEvaluatorTask(Task):
    """
    Custom Celery task class with retry logic and error handling.
    """
    autoretry_for = (Exception,)
    retry_kwargs = {
        'max_retries': worker_settings.max_task_retries,
        'countdown': worker_settings.retry_backoff
    }
    retry_backoff = True
    retry_backoff_max = worker_settings.retry_backoff_max
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=PerformanceEvaluatorTask,
    name="src.workers.tasks.performance_evaluator.evaluate_tutor_performance"
)
def evaluate_tutor_performance(self) -> Dict[str, Any]:
    """
    Scheduled task to evaluate performance for all active tutors.

    This task is triggered every 15 minutes by Celery Beat and:
    1. Fetches all active tutors from the database
    2. Calculates performance metrics for each tutor
    3. Stores metrics in the database
    4. Reports statistics

    Returns:
        Dictionary with execution statistics:
        - tutors_evaluated: Number of tutors processed
        - tutors_successful: Number of successful evaluations
        - tutors_failed: Number of failed evaluations
        - execution_time_seconds: Time taken
        - timestamp: Evaluation timestamp
    """
    logger.info(f"Starting performance evaluation task: {self.request.id}")
    start_time = datetime.utcnow()

    stats = {
        "tutors_evaluated": 0,
        "tutors_successful": 0,
        "tutors_failed": 0,
        "execution_time_seconds": 0,
        "timestamp": start_time.isoformat(),
        "task_id": self.request.id,
    }

    try:
        # Use asyncio to run the async evaluation
        import asyncio
        result = asyncio.run(_evaluate_all_tutors_async())

        stats.update(result)

        # Calculate execution time
        end_time = datetime.utcnow()
        stats["execution_time_seconds"] = (end_time - start_time).total_seconds()

        logger.info(
            f"Performance evaluation completed: "
            f"{stats['tutors_successful']}/{stats['tutors_evaluated']} successful, "
            f"{stats['tutors_failed']} failed, "
            f"took {stats['execution_time_seconds']:.2f}s"
        )

        return stats

    except Exception as e:
        logger.error(f"Performance evaluation task failed: {str(e)}", exc_info=True)
        stats["error"] = str(e)
        raise


async def _evaluate_all_tutors_async() -> Dict[str, Any]:
    """
    Async function to evaluate all active tutors.

    Returns:
        Dictionary with evaluation statistics
    """
    stats = {
        "tutors_evaluated": 0,
        "tutors_successful": 0,
        "tutors_failed": 0,
        "batch_stats": [],
    }

    async with async_session_maker() as session:
        try:
            # Fetch all active tutors
            tutors = await _get_active_tutors(session)
            logger.info(f"Found {len(tutors)} active tutors to evaluate")

            if not tutors:
                logger.warning("No active tutors found for evaluation")
                return stats

            # Process tutors in batches
            batch_size = worker_settings.perf_eval_batch_size
            batch_num = 0

            for i in range(0, len(tutors), batch_size):
                batch_num += 1
                batch = tutors[i:i + batch_size]

                logger.info(
                    f"Processing batch {batch_num} "
                    f"({len(batch)} tutors, indices {i}-{i+len(batch)-1})"
                )

                batch_result = await _evaluate_tutor_batch(session, batch)

                stats["tutors_evaluated"] += batch_result["evaluated"]
                stats["tutors_successful"] += batch_result["successful"]
                stats["tutors_failed"] += batch_result["failed"]
                stats["batch_stats"].append({
                    "batch_number": batch_num,
                    "batch_size": len(batch),
                    **batch_result
                })

                # Commit after each batch
                await session.commit()
                logger.info(
                    f"Batch {batch_num} completed: "
                    f"{batch_result['successful']}/{batch_result['evaluated']} successful"
                )

            return stats

        except Exception as e:
            logger.error(f"Error in tutor evaluation: {str(e)}", exc_info=True)
            await session.rollback()
            raise


async def _get_active_tutors(session: AsyncSession) -> List[Tutor]:
    """
    Fetch all active tutors from the database.

    Args:
        session: Database session

    Returns:
        List of active Tutor objects
    """
    query = select(Tutor).where(Tutor.status == TutorStatus.ACTIVE)
    result = await session.execute(query)
    return list(result.scalars().all())


async def _evaluate_tutor_batch(
    session: AsyncSession,
    tutors: List[Tutor]
) -> Dict[str, Any]:
    """
    Evaluate a batch of tutors and save their performance metrics.

    Args:
        session: Database session
        tutors: List of tutors to evaluate

    Returns:
        Dictionary with batch statistics
    """
    batch_stats = {
        "evaluated": len(tutors),
        "successful": 0,
        "failed": 0,
        "failed_tutor_ids": [],
    }

    calculator = PerformanceCalculator(session)

    for tutor in tutors:
        try:
            # Calculate metrics for all windows
            # Primary window: 30-day (as per PRD requirements)
            metrics_30day = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.THIRTY_DAY,
            )

            # Save primary metrics
            metric_id = await calculator.save_metrics(metrics_30day)

            # Also calculate 7-day and 90-day for comprehensive tracking
            metrics_7day = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.SEVEN_DAY,
            )
            await calculator.save_metrics(metrics_7day)

            metrics_90day = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.NINETY_DAY,
            )
            await calculator.save_metrics(metrics_90day)

            batch_stats["successful"] += 1

            logger.debug(
                f"Successfully evaluated tutor {tutor.tutor_id}: "
                f"tier={metrics_30day.performance_tier}, "
                f"avg_rating={metrics_30day.avg_rating}, "
                f"sessions={metrics_30day.sessions_completed}"
            )

        except Exception as e:
            batch_stats["failed"] += 1
            batch_stats["failed_tutor_ids"].append(tutor.tutor_id)
            logger.error(
                f"Failed to evaluate tutor {tutor.tutor_id}: {str(e)}",
                exc_info=True
            )
            # Continue with next tutor instead of failing entire batch
            continue

    return batch_stats


@celery_app.task(
    bind=True,
    base=PerformanceEvaluatorTask,
    name="src.workers.tasks.performance_evaluator.evaluate_single_tutor"
)
def evaluate_single_tutor(self, tutor_id: str, window: str = "30day") -> Dict[str, Any]:
    """
    Evaluate performance for a single tutor.

    This task can be called on-demand (e.g., from API endpoints or other tasks)
    to evaluate a specific tutor's performance.

    Args:
        tutor_id: ID of the tutor to evaluate
        window: Time window for evaluation (7day, 30day, 90day)

    Returns:
        Dictionary with evaluation results
    """
    logger.info(f"Starting single tutor evaluation: {tutor_id} ({window} window)")

    try:
        import asyncio
        result = asyncio.run(_evaluate_single_tutor_async(tutor_id, window))

        logger.info(
            f"Single tutor evaluation completed for {tutor_id}: "
            f"tier={result.get('performance_tier')}, "
            f"avg_rating={result.get('avg_rating')}"
        )

        return {
            "success": True,
            "tutor_id": tutor_id,
            "window": window,
            "metrics": result,
        }

    except Exception as e:
        logger.error(
            f"Single tutor evaluation failed for {tutor_id}: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "tutor_id": tutor_id,
            "window": window,
            "error": str(e),
        }


async def _evaluate_single_tutor_async(tutor_id: str, window: str) -> Dict[str, Any]:
    """
    Async function to evaluate a single tutor.

    Args:
        tutor_id: ID of the tutor to evaluate
        window: Time window (7day, 30day, 90day)

    Returns:
        Dictionary with calculated metrics
    """
    async with async_session_maker() as session:
        try:
            # Validate window
            window_enum = MetricWindow(window)

            # Calculate metrics
            calculator = PerformanceCalculator(session)
            metrics = await calculator.calculate_metrics(
                tutor_id=tutor_id,
                window=window_enum,
            )

            # Save metrics
            metric_id = await calculator.save_metrics(metrics)
            await session.commit()

            # Return metrics as dict
            result = metrics.to_dict()
            result["metric_id"] = metric_id

            return result

        except Exception as e:
            await session.rollback()
            logger.error(f"Error evaluating tutor {tutor_id}: {str(e)}", exc_info=True)
            raise
