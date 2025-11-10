"""
API endpoints for worker monitoring.

Provides health checks, metrics, and status information for Celery workers.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from src.workers.monitoring import (
    HealthCheck,
    MetricsCollector,
    WorkerMonitor,
    get_monitoring_dashboard_data,
    AlertManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workers", tags=["workers"])


# ============================================================================
# Health Check Endpoints
# ============================================================================

@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """
    Get overall health status of workers and dependencies.

    Returns:
        Health check results for all services
    """
    try:
        health_check = HealthCheck()
        return health_check.get_overall_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/redis")
async def get_redis_health() -> Dict[str, Any]:
    """
    Get Redis broker health status.

    Returns:
        Redis health check results
    """
    try:
        health_check = HealthCheck()
        return health_check.check_redis()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/celery")
async def get_celery_health() -> Dict[str, Any]:
    """
    Get Celery worker health status.

    Returns:
        Celery worker health check results
    """
    try:
        health_check = HealthCheck()
        return health_check.check_celery_workers()
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/database")
async def get_database_health() -> Dict[str, Any]:
    """
    Get database health status.

    Returns:
        Database health check results
    """
    try:
        health_check = HealthCheck()
        return health_check.check_database()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Metrics Endpoints
# ============================================================================

@router.get("/metrics/tasks")
async def get_all_task_metrics() -> List[Dict[str, Any]]:
    """
    Get metrics for all tasks.

    Returns:
        List of task metrics including success rates and execution counts
    """
    try:
        metrics_collector = MetricsCollector()
        return metrics_collector.get_all_task_metrics()
    except Exception as e:
        logger.error(f"Failed to get task metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/tasks/{task_name}")
async def get_task_metrics(task_name: str, hours: int = 24) -> Dict[str, Any]:
    """
    Get metrics for a specific task.

    Args:
        task_name: Name of the task
        hours: Hours to look back (default: 24)

    Returns:
        Task metrics summary
    """
    try:
        metrics_collector = MetricsCollector()
        return metrics_collector.get_task_metrics(task_name, hours)
    except Exception as e:
        logger.error(f"Failed to get metrics for {task_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Worker Status Endpoints
# ============================================================================

@router.get("/status")
async def get_worker_status() -> Dict[str, Any]:
    """
    Get detailed worker status and statistics.

    Returns:
        Worker stats including active tasks, queues, and performance
    """
    try:
        worker_monitor = WorkerMonitor()
        return worker_monitor.get_worker_stats()
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queues")
async def get_queue_status() -> List[Dict[str, Any]]:
    """
    Get status of all task queues.

    Returns:
        Queue information including lengths and status
    """
    try:
        worker_monitor = WorkerMonitor()
        return worker_monitor.get_task_queue_info()
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queues/lengths")
async def get_queue_lengths() -> Dict[str, int]:
    """
    Get current length of all queues.

    Returns:
        Queue name to length mapping
    """
    try:
        worker_monitor = WorkerMonitor()
        return worker_monitor.get_queue_lengths()
    except Exception as e:
        logger.error(f"Failed to get queue lengths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive monitoring data for dashboard.

    Returns:
        Complete monitoring data including health, metrics, and worker status
    """
    try:
        return get_monitoring_dashboard_data()
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Alert Endpoints
# ============================================================================

@router.post("/alerts/check")
async def check_alerts() -> Dict[str, Any]:
    """
    Manually trigger alert checks.

    Returns:
        Alert check results
    """
    try:
        alert_manager = AlertManager()

        # Check queue backlog
        alert_manager.check_and_alert_queue_backlog(threshold=1000)

        # Check worker health
        alert_manager.check_and_alert_worker_health()

        return {
            "status": "success",
            "message": "Alert checks completed",
        }
    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Task Control Endpoints (Admin Only)
# ============================================================================

@router.post("/tasks/{task_name}/trigger")
async def trigger_task(task_name: str, kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Manually trigger a task.

    Args:
        task_name: Name of the task to trigger
        kwargs: Task keyword arguments

    Returns:
        Task ID and status
    """
    try:
        from src.workers.celery_app import celery_app

        # Get the task
        task = celery_app.tasks.get(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_name} not found")

        # Trigger the task
        result = task.delay(**(kwargs or {}))

        return {
            "status": "success",
            "task_id": result.id,
            "task_name": task_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger task {task_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a specific task execution.

    Args:
        task_id: Task ID

    Returns:
        Task status and result
    """
    try:
        from src.workers.celery_app import celery_app
        from celery.result import AsyncResult

        result = AsyncResult(task_id, app=celery_app)

        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info,
        }
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
