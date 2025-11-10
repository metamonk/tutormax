"""
Performance monitoring and optimization endpoints.

Provides endpoints for:
- Cache statistics
- Query performance metrics
- Database optimization recommendations
- Performance dashboard
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_async_session
from ..database.query_optimizer import query_optimizer, get_query_optimizer, QueryOptimizer
from .cache_service import cache_service, get_cache_service, CacheService
from .performance_middleware import PerformanceMiddleware


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/performance",
    tags=["Performance Monitoring"]
)


@router.get("/cache/stats")
async def get_cache_stats(
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """
    Get cache performance statistics.

    Returns:
        Cache hit/miss ratios and counts
    """
    stats = cache.get_cache_stats()
    return {
        "timestamp": datetime.now().isoformat(),
        "cache_stats": stats
    }


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = "*",
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """
    Clear cache by pattern.

    Args:
        pattern: Cache key pattern to clear (default: "*" for all)

    Returns:
        Number of keys cleared
    """
    if pattern == "*":
        # Clear all cache prefixes
        total_deleted = 0
        for prefix in [
            cache.DASHBOARD_PREFIX,
            cache.PREDICTION_PREFIX,
            cache.METRICS_PREFIX,
            cache.TUTOR_PROFILE_PREFIX,
            cache.SESSION_STATS_PREFIX
        ]:
            deleted = await cache.delete_pattern(f"{prefix}*")
            total_deleted += deleted
    else:
        total_deleted = await cache.delete_pattern(pattern)

    return {
        "success": True,
        "deleted_keys": total_deleted,
        "pattern": pattern,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/query/stats")
async def get_query_stats(
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get query performance statistics.

    Returns:
        Query timing and slow query information
    """
    stats = optimizer.get_query_stats()
    return {
        "timestamp": datetime.now().isoformat(),
        "query_stats": stats
    }


@router.get("/database/slow-queries")
async def get_slow_queries(
    min_duration_ms: int = 100,
    session: AsyncSession = Depends(get_async_session),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get slow queries from pg_stat_statements.

    Args:
        min_duration_ms: Minimum query duration in milliseconds

    Returns:
        List of slow queries with timing information
    """
    slow_queries = await optimizer.analyze_slow_queries(session, min_duration_ms)

    return {
        "timestamp": datetime.now().isoformat(),
        "min_duration_ms": min_duration_ms,
        "slow_queries": slow_queries,
        "count": len(slow_queries)
    }


@router.get("/database/table/{table_name}/stats")
async def get_table_stats(
    table_name: str,
    session: AsyncSession = Depends(get_async_session),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get statistics for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        Table size, row count, and maintenance statistics
    """
    stats = await optimizer.get_table_stats(session, table_name)

    return {
        "timestamp": datetime.now().isoformat(),
        "table_stats": stats
    }


@router.get("/database/table/{table_name}/indexes")
async def get_table_indexes(
    table_name: str,
    session: AsyncSession = Depends(get_async_session),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get all indexes for a table.

    Args:
        table_name: Name of the table

    Returns:
        List of indexes with definitions and sizes
    """
    indexes = await optimizer.get_table_indexes(session, table_name)

    return {
        "timestamp": datetime.now().isoformat(),
        "table": table_name,
        "indexes": indexes,
        "count": len(indexes)
    }


@router.get("/database/table/{table_name}/index-suggestions")
async def get_index_suggestions(
    table_name: str,
    session: AsyncSession = Depends(get_async_session),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get index suggestions for a table.

    Args:
        table_name: Name of the table

    Returns:
        Suggested index DDL statements
    """
    suggestions = await optimizer.suggest_indexes(session, table_name)

    return {
        "timestamp": datetime.now().isoformat(),
        "table": table_name,
        "suggestions": suggestions,
        "count": len(suggestions)
    }


@router.post("/database/query/explain")
async def explain_query(
    query: str,
    analyze: bool = False,
    session: AsyncSession = Depends(get_async_session),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Run EXPLAIN on a query.

    Args:
        query: SQL query to analyze
        analyze: Include ANALYZE for actual execution timing

    Returns:
        Query execution plan
    """
    try:
        result = await optimizer.explain_query(session, query, analyze)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to explain query: {str(e)}"
        )


@router.get("/summary")
async def get_performance_summary(
    cache: CacheService = Depends(get_cache_service),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get overall performance summary.

    Returns:
        Combined cache and query performance metrics
    """
    cache_stats = cache.get_cache_stats()
    query_stats = optimizer.get_query_stats()

    # Calculate overall health score (0-100)
    health_score = 100

    # Penalize low cache hit rate
    if cache_stats["hit_rate_percent"] < 80:
        health_score -= (80 - cache_stats["hit_rate_percent"]) / 2

    # Penalize high slow query rate
    if query_stats.get("slow_query_rate", 0) > 10:
        health_score -= query_stats["slow_query_rate"]

    # Penalize high average response time
    avg_time = query_stats.get("avg_time_ms", 0)
    if avg_time > 100:
        health_score -= min(20, (avg_time - 100) / 10)

    health_score = max(0, min(100, health_score))

    return {
        "timestamp": datetime.now().isoformat(),
        "health_score": round(health_score, 2),
        "cache": cache_stats,
        "queries": query_stats,
        "recommendations": _generate_recommendations(cache_stats, query_stats)
    }


def _generate_recommendations(
    cache_stats: Dict[str, Any],
    query_stats: Dict[str, Any]
) -> list:
    """
    Generate performance recommendations based on metrics.

    Args:
        cache_stats: Cache statistics
        query_stats: Query statistics

    Returns:
        List of recommendations
    """
    recommendations = []

    # Cache recommendations
    if cache_stats["hit_rate_percent"] < 80:
        recommendations.append({
            "type": "cache",
            "severity": "warning",
            "message": f"Cache hit rate is {cache_stats['hit_rate_percent']:.2f}%, should be > 80%",
            "suggestion": "Consider warming cache for frequently accessed data"
        })

    if cache_stats["errors"] > 0:
        recommendations.append({
            "type": "cache",
            "severity": "error",
            "message": f"{cache_stats['errors']} cache errors detected",
            "suggestion": "Check Redis connection and logs for errors"
        })

    # Query recommendations
    if query_stats.get("slow_query_rate", 0) > 10:
        recommendations.append({
            "type": "database",
            "severity": "warning",
            "message": f"{query_stats['slow_query_rate']:.2f}% of queries are slow",
            "suggestion": "Review slow queries and add missing indexes"
        })

    if query_stats.get("avg_time_ms", 0) > 100:
        recommendations.append({
            "type": "database",
            "severity": "warning",
            "message": f"Average query time is {query_stats['avg_time_ms']:.2f}ms, should be < 100ms",
            "suggestion": "Optimize slow queries and consider read replicas"
        })

    # General recommendations
    if not recommendations:
        recommendations.append({
            "type": "general",
            "severity": "info",
            "message": "Performance metrics are healthy",
            "suggestion": "Continue monitoring for degradation"
        })

    return recommendations
