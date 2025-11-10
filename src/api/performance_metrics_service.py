"""
Performance Metrics Service

Tracks and aggregates performance metrics for the TutorMax system:
- API response times (p50, p95, p99)
- Database query performance
- Worker queue depths
- Redis hit rates and performance
- System resource utilization
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import statistics

import redis
from sqlalchemy import text

from src.api.config import settings
from src.workers.monitoring import WorkerMonitor, MetricsCollector
from src.database.database import get_db_session

logger = logging.getLogger(__name__)


class PerformanceMetricsService:
    """
    Service for tracking and aggregating performance metrics.

    Provides comprehensive performance monitoring for engineers:
    - Real-time API response time tracking
    - Database query performance analysis
    - Worker queue monitoring
    - Redis cache performance metrics
    """

    def __init__(self):
        """Initialize performance metrics service."""
        self.redis_client = redis.Redis.from_url(settings.redis_url)
        self.worker_monitor = WorkerMonitor()
        self.metrics_collector = MetricsCollector()
        self.metrics_prefix = "tutormax:perf:"

    async def get_api_response_times(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get API response time statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            API response time metrics with percentiles
        """
        # Get from SLA metrics
        from src.api.sla_tracking_service import get_sla_tracking_service
        sla_service = get_sla_tracking_service()

        stats = await sla_service.calculate_api_response_time_stats(hours=hours)

        # Add status code breakdown
        status_breakdown = await self._get_status_code_breakdown(hours)

        return {
            **stats,
            "status_codes": status_breakdown,
        }

    async def _get_status_code_breakdown(
        self,
        hours: int
    ) -> Dict[str, int]:
        """Get breakdown of HTTP status codes."""
        # This would typically come from access logs or metrics
        # For now, return a placeholder
        return {
            "2xx": 0,  # Success
            "4xx": 0,  # Client errors
            "5xx": 0,  # Server errors
        }

    async def get_database_performance(self) -> Dict[str, Any]:
        """
        Get database performance metrics.

        Returns:
            Database performance statistics
        """
        try:
            async with get_db_session() as session:
                # Get connection pool stats
                pool_stats = {
                    "pool_size": settings.db_pool_size,
                    "max_overflow": settings.db_max_overflow,
                    "pool_timeout": settings.db_pool_timeout,
                }

                # Get active connections
                result = await session.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
                )
                active_connections = result.scalar()

                # Get slow query count (queries > 1 second)
                result = await session.execute(
                    text("""
                        SELECT count(*)
                        FROM pg_stat_statements
                        WHERE mean_exec_time > 1000
                        LIMIT 1;
                    """)
                )
                slow_queries = result.scalar() or 0

                # Get database size
                result = await session.execute(
                    text(f"SELECT pg_database_size('{settings.postgres_db}') / 1024 / 1024 AS size_mb;")
                )
                db_size_mb = result.scalar()

                # Get cache hit ratio
                result = await session.execute(
                    text("""
                        SELECT
                            sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 AS cache_hit_ratio
                        FROM pg_statio_user_tables;
                    """)
                )
                cache_hit_ratio = result.scalar() or 0

                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "pool": pool_stats,
                    "active_connections": active_connections,
                    "slow_queries_count": slow_queries,
                    "database_size_mb": round(db_size_mb, 2) if db_size_mb else 0,
                    "cache_hit_ratio": round(cache_hit_ratio, 2) if cache_hit_ratio else 0,
                    "status": "healthy" if cache_hit_ratio > 90 else "degraded",
                }

        except Exception as e:
            logger.error(f"Failed to get database performance metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }

    def get_worker_queue_depths(self) -> Dict[str, Any]:
        """
        Get worker queue depths for all queues.

        Returns:
            Queue depth metrics
        """
        try:
            queue_lengths = self.worker_monitor.get_queue_lengths()
            queue_info = self.worker_monitor.get_task_queue_info()

            # Calculate total backlog
            total_backlog = sum(queue_lengths.values())

            # Identify queues with high backlog
            high_backlog_queues = [
                {"name": name, "length": length}
                for name, length in queue_lengths.items()
                if length > 100
            ]

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "queues": queue_info,
                "queue_lengths": queue_lengths,
                "total_backlog": total_backlog,
                "high_backlog_queues": high_backlog_queues,
                "status": "healthy" if total_backlog < 1000 else "degraded",
            }

        except Exception as e:
            logger.error(f"Failed to get worker queue depths: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }

    def get_redis_performance(self) -> Dict[str, Any]:
        """
        Get Redis performance metrics including hit rates.

        Returns:
            Redis performance statistics
        """
        try:
            info = self.redis_client.info()
            stats = self.redis_client.info("stats")

            # Calculate hit rate
            keyspace_hits = stats.get("keyspace_hits", 0)
            keyspace_misses = stats.get("keyspace_misses", 0)
            total_ops = keyspace_hits + keyspace_misses

            hit_rate = (keyspace_hits / total_ops * 100) if total_ops > 0 else 0

            # Memory usage
            used_memory_mb = info.get("used_memory", 0) / 1024 / 1024
            max_memory_mb = info.get("maxmemory", 0) / 1024 / 1024 if info.get("maxmemory", 0) > 0 else None
            memory_usage_pct = (used_memory_mb / max_memory_mb * 100) if max_memory_mb else 0

            # Connection stats
            connected_clients = info.get("connected_clients", 0)
            blocked_clients = info.get("blocked_clients", 0)

            # Operations per second
            ops_per_sec = stats.get("instantaneous_ops_per_sec", 0)

            # Evicted keys
            evicted_keys = stats.get("evicted_keys", 0)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "hit_rate_percentage": round(hit_rate, 2),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "memory": {
                    "used_mb": round(used_memory_mb, 2),
                    "max_mb": round(max_memory_mb, 2) if max_memory_mb else None,
                    "usage_percentage": round(memory_usage_pct, 2) if max_memory_mb else None,
                },
                "connections": {
                    "connected_clients": connected_clients,
                    "blocked_clients": blocked_clients,
                },
                "operations_per_second": ops_per_sec,
                "evicted_keys": evicted_keys,
                "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 2),
                "status": "healthy" if hit_rate > 80 else "degraded",
            }

        except Exception as e:
            logger.error(f"Failed to get Redis performance metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }

    def get_celery_task_metrics(self) -> Dict[str, Any]:
        """
        Get Celery task execution metrics.

        Returns:
            Task execution statistics
        """
        try:
            all_metrics = self.metrics_collector.get_all_task_metrics()

            # Aggregate statistics
            total_executions = sum(m["total_executions"] for m in all_metrics)
            total_successful = sum(m["successful"] for m in all_metrics)
            total_failed = sum(m["failed"] for m in all_metrics)

            overall_success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0

            # Find slowest tasks
            # This would require additional tracking, placeholder for now
            slowest_tasks = []

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_executions": total_executions,
                "successful": total_successful,
                "failed": total_failed,
                "overall_success_rate": round(overall_success_rate, 2),
                "tasks": all_metrics,
                "slowest_tasks": slowest_tasks,
                "status": "healthy" if overall_success_rate > 95 else "degraded",
            }

        except Exception as e:
            logger.error(f"Failed to get Celery task metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }

    async def get_performance_dashboard_data(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance dashboard data.

        Args:
            hours: Number of hours to analyze

        Returns:
            Complete performance dashboard data
        """
        try:
            # Gather all metrics
            api_metrics = await self.get_api_response_times(hours)
            db_metrics = await self.get_database_performance()
            queue_metrics = self.get_worker_queue_depths()
            redis_metrics = self.get_redis_performance()
            task_metrics = self.get_celery_task_metrics()

            # Determine overall health
            all_statuses = [
                api_metrics.get("meets_p95_sla", True),
                db_metrics.get("status") == "healthy",
                queue_metrics.get("status") == "healthy",
                redis_metrics.get("status") == "healthy",
                task_metrics.get("status") == "healthy",
            ]

            overall_health = "healthy" if all(all_statuses) else "degraded"

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "period_hours": hours,
                "overall_health": overall_health,
                "api_response_times": api_metrics,
                "database_performance": db_metrics,
                "worker_queues": queue_metrics,
                "redis_performance": redis_metrics,
                "celery_tasks": task_metrics,
            }

        except Exception as e:
            logger.error(f"Failed to get performance dashboard data: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }


# Singleton instance
performance_metrics_service = PerformanceMetricsService()


def get_performance_metrics_service() -> PerformanceMetricsService:
    """Get the singleton performance metrics service instance."""
    return performance_metrics_service
