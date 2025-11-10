"""
Advanced caching service with cache warming and invalidation strategies.

Implements multi-tier caching for:
- Dashboard data (5 min TTL)
- Prediction results (1 hour TTL)
- Aggregated metrics (15 min TTL)
- Cache warming for frequently accessed data
"""

import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps

import redis.asyncio as redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class CacheService:
    """
    Advanced caching service with warming and invalidation capabilities.
    """

    # Cache key prefixes
    DASHBOARD_PREFIX = "tutormax:cache:dashboard:"
    PREDICTION_PREFIX = "tutormax:cache:prediction:"
    METRICS_PREFIX = "tutormax:cache:metrics:"
    TUTOR_PROFILE_PREFIX = "tutormax:cache:tutor_profile:"
    SESSION_STATS_PREFIX = "tutormax:cache:session_stats:"

    # Cache TTLs (in seconds)
    DASHBOARD_TTL = 300  # 5 minutes
    PREDICTION_TTL = 3600  # 1 hour
    METRICS_TTL = 900  # 15 minutes
    TUTOR_PROFILE_TTL = 1800  # 30 minutes
    SESSION_STATS_TTL = 600  # 10 minutes

    # Cache warming configuration
    WARM_CACHE_ON_STARTUP = True
    WARM_CACHE_BATCH_SIZE = 100

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"Cache service connected to Redis at {self.redis_url}")
        except RedisError as e:
            self._connected = False
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Cache service disconnected from Redis")

    async def is_connected(self) -> bool:
        """Check if Redis is connected and responsive."""
        if not self._connected or not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except RedisError:
            self._connected = False
            return False

    # ==================== Core Cache Operations ====================

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                self._cache_stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached_data)
            else:
                self._cache_stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return None
        except RedisError as e:
            self._cache_stats["errors"] += 1
            logger.error(f"Cache get error for {key}: {e}")
            return None
        except (TypeError, ValueError) as e:
            logger.error(f"Cache deserialization error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)

            self._cache_stats["sets"] += 1
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except RedisError as e:
            self._cache_stats["errors"] += 1
            logger.error(f"Cache set error for {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Cache serialization error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            self._cache_stats["deletes"] += 1
            logger.debug(f"Cache delete: {key}")
            return True
        except RedisError as e:
            self._cache_stats["errors"] += 1
            logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "tutormax:cache:dashboard:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            deleted = 0
            async for key in self.redis_client.scan_iter(match=pattern, count=100):
                await self.redis_client.delete(key)
                deleted += 1

            self._cache_stats["deletes"] += deleted
            logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            return deleted
        except RedisError as e:
            self._cache_stats["errors"] += 1
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    # ==================== Dashboard Caching ====================

    async def cache_dashboard_data(
        self,
        dashboard_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Cache dashboard data with 5-minute TTL.

        Args:
            dashboard_id: Dashboard identifier
            data: Dashboard data

        Returns:
            True if cached successfully
        """
        key = f"{self.DASHBOARD_PREFIX}{dashboard_id}"
        return await self.set(key, data, self.DASHBOARD_TTL)

    async def get_dashboard_data(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get cached dashboard data."""
        key = f"{self.DASHBOARD_PREFIX}{dashboard_id}"
        return await self.get(key)

    async def invalidate_dashboard(self, dashboard_id: str) -> bool:
        """Invalidate cached dashboard data."""
        key = f"{self.DASHBOARD_PREFIX}{dashboard_id}"
        return await self.delete(key)

    # ==================== Prediction Caching ====================

    async def cache_prediction(
        self,
        tutor_id: str,
        prediction_data: Dict[str, Any]
    ) -> bool:
        """
        Cache prediction result with 1-hour TTL.

        Args:
            tutor_id: Tutor ID
            prediction_data: Prediction result

        Returns:
            True if cached successfully
        """
        key = f"{self.PREDICTION_PREFIX}{tutor_id}"
        return await self.set(key, prediction_data, self.PREDICTION_TTL)

    async def get_prediction(self, tutor_id: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction for a tutor."""
        key = f"{self.PREDICTION_PREFIX}{tutor_id}"
        return await self.get(key)

    async def invalidate_prediction(self, tutor_id: str) -> bool:
        """Invalidate cached prediction for a tutor."""
        key = f"{self.PREDICTION_PREFIX}{tutor_id}"
        return await self.delete(key)

    # ==================== Metrics Caching ====================

    async def cache_metrics(
        self,
        metric_key: str,
        metrics_data: Dict[str, Any]
    ) -> bool:
        """
        Cache aggregated metrics with 15-minute TTL.

        Args:
            metric_key: Metric identifier (e.g., "daily_summary_2024-01-01")
            metrics_data: Metrics data

        Returns:
            True if cached successfully
        """
        key = f"{self.METRICS_PREFIX}{metric_key}"
        return await self.set(key, metrics_data, self.METRICS_TTL)

    async def get_metrics(self, metric_key: str) -> Optional[Dict[str, Any]]:
        """Get cached metrics."""
        key = f"{self.METRICS_PREFIX}{metric_key}"
        return await self.get(key)

    async def invalidate_metrics(self, metric_key: str) -> bool:
        """Invalidate cached metrics."""
        key = f"{self.METRICS_PREFIX}{metric_key}"
        return await self.delete(key)

    async def invalidate_all_metrics(self) -> int:
        """Invalidate all cached metrics."""
        pattern = f"{self.METRICS_PREFIX}*"
        return await self.delete_pattern(pattern)

    # ==================== Tutor Profile Caching ====================

    async def cache_tutor_profile(
        self,
        tutor_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """
        Cache tutor profile with 30-minute TTL.

        Args:
            tutor_id: Tutor ID
            profile_data: Profile data

        Returns:
            True if cached successfully
        """
        key = f"{self.TUTOR_PROFILE_PREFIX}{tutor_id}"
        return await self.set(key, profile_data, self.TUTOR_PROFILE_TTL)

    async def get_tutor_profile(self, tutor_id: str) -> Optional[Dict[str, Any]]:
        """Get cached tutor profile."""
        key = f"{self.TUTOR_PROFILE_PREFIX}{tutor_id}"
        return await self.get(key)

    async def invalidate_tutor_profile(self, tutor_id: str) -> bool:
        """Invalidate cached tutor profile."""
        key = f"{self.TUTOR_PROFILE_PREFIX}{tutor_id}"
        return await self.delete(key)

    # ==================== Session Stats Caching ====================

    async def cache_session_stats(
        self,
        tutor_id: str,
        window: str,
        stats_data: Dict[str, Any]
    ) -> bool:
        """
        Cache session statistics with 10-minute TTL.

        Args:
            tutor_id: Tutor ID
            window: Time window (e.g., "7day", "30day")
            stats_data: Statistics data

        Returns:
            True if cached successfully
        """
        key = f"{self.SESSION_STATS_PREFIX}{tutor_id}:{window}"
        return await self.set(key, stats_data, self.SESSION_STATS_TTL)

    async def get_session_stats(
        self,
        tutor_id: str,
        window: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached session statistics."""
        key = f"{self.SESSION_STATS_PREFIX}{tutor_id}:{window}"
        return await self.get(key)

    # ==================== Cache Warming ====================

    async def warm_dashboard_cache(
        self,
        dashboard_ids: List[str],
        data_fetcher: Callable
    ) -> int:
        """
        Warm dashboard cache for frequently accessed dashboards.

        Args:
            dashboard_ids: List of dashboard IDs to warm
            data_fetcher: Async function to fetch dashboard data

        Returns:
            Number of dashboards cached
        """
        warmed = 0
        for dashboard_id in dashboard_ids:
            try:
                data = await data_fetcher(dashboard_id)
                if data and await self.cache_dashboard_data(dashboard_id, data):
                    warmed += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for dashboard {dashboard_id}: {e}")

        logger.info(f"Warmed cache for {warmed}/{len(dashboard_ids)} dashboards")
        return warmed

    async def warm_tutor_cache(
        self,
        tutor_ids: List[str],
        profile_fetcher: Callable,
        prediction_fetcher: Callable
    ) -> int:
        """
        Warm cache for frequently accessed tutors.

        Args:
            tutor_ids: List of tutor IDs
            profile_fetcher: Function to fetch tutor profile
            prediction_fetcher: Function to fetch tutor prediction

        Returns:
            Number of tutors cached
        """
        warmed = 0
        for tutor_id in tutor_ids:
            try:
                # Cache profile
                profile = await profile_fetcher(tutor_id)
                if profile:
                    await self.cache_tutor_profile(tutor_id, profile)

                # Cache prediction
                prediction = await prediction_fetcher(tutor_id)
                if prediction:
                    await self.cache_prediction(tutor_id, prediction)

                warmed += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for tutor {tutor_id}: {e}")

        logger.info(f"Warmed cache for {warmed}/{len(tutor_ids)} tutors")
        return warmed

    # ==================== Cache Statistics ====================

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss ratios and counts
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "sets": self._cache_stats["sets"],
            "deletes": self._cache_stats["deletes"],
            "errors": self._cache_stats["errors"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self._connected
        }

    def reset_cache_stats(self) -> None:
        """Reset cache statistics."""
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        logger.info("Cache statistics reset")


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """
    Dependency injection function for FastAPI.

    Returns:
        CacheService instance
    """
    return cache_service


# ==================== Cache Decorator ====================

def cached(
    prefix: str,
    ttl: int,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments

    Example:
        @cached(prefix="tutor_stats", ttl=600, key_func=lambda tutor_id: tutor_id)
        async def get_tutor_stats(tutor_id: str):
            # Expensive operation
            return stats
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key_suffix = key_func(*args, **kwargs)
            else:
                # Use all arguments as key
                key_suffix = ":".join(str(arg) for arg in args)

            cache_key = f"{prefix}:{key_suffix}"

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_service.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
