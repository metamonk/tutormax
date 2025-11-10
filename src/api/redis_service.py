"""
Redis service for message queuing.

Handles Redis connection and message queue operations for the data ingestion pipeline.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis service for queuing incoming data for downstream processing.

    Supports async operations for non-blocking I/O in FastAPI.
    """

    # Queue names for different data types
    TUTOR_QUEUE = "tutormax:queue:tutors"
    SESSION_QUEUE = "tutormax:queue:sessions"
    FEEDBACK_QUEUE = "tutormax:queue:feedbacks"

    # Cache key prefixes
    PREDICTION_CACHE_PREFIX = "tutormax:cache:prediction:"
    DASHBOARD_CACHE_PREFIX = "tutormax:cache:dashboard:"
    METRICS_CACHE_PREFIX = "tutormax:cache:metrics:"
    TUTOR_LIST_CACHE_KEY = "tutormax:cache:tutor_list"
    INTERVENTION_STATS_CACHE_KEY = "tutormax:cache:intervention_stats"

    # Cache TTL (time to live in seconds)
    PREDICTION_CACHE_TTL = 3600  # 1 hour
    DASHBOARD_CACHE_TTL = 300  # 5 minutes
    METRICS_CACHE_TTL = 600  # 10 minutes
    TUTOR_LIST_CACHE_TTL = 180  # 3 minutes

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis service.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish connection to Redis.

        Should be called during application startup.
        """
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"Successfully connected to Redis at {self.redis_url}")
        except RedisError as e:
            self._connected = False
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Close Redis connection.

        Should be called during application shutdown.
        """
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def is_connected(self) -> bool:
        """
        Check if Redis is connected and responsive.

        Returns:
            True if connected and responsive, False otherwise
        """
        if not self._connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except RedisError:
            self._connected = False
            return False

    async def queue_tutor(self, tutor_data: Dict[str, Any]) -> bool:
        """
        Queue tutor profile data for processing.

        Args:
            tutor_data: Tutor profile dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.TUTOR_QUEUE, tutor_data)

    async def queue_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Queue session data for processing.

        Args:
            session_data: Session data dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.SESSION_QUEUE, session_data)

    async def queue_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Queue feedback data for processing.

        Args:
            feedback_data: Feedback data dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.FEEDBACK_QUEUE, feedback_data)

    async def _enqueue(self, queue_name: str, data: Dict[str, Any]) -> bool:
        """
        Enqueue data to specified Redis queue.

        Uses Redis LPUSH to add to the left side of the list (queue).
        Processors will use RPOP to dequeue from the right side (FIFO).

        Args:
            queue_name: Name of the Redis queue
            data: Data dictionary to enqueue

        Returns:
            True if successfully queued, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            # Add metadata
            message = {
                "data": data,
                "queued_at": datetime.now().isoformat(),
                "queue": queue_name,
            }

            # Serialize to JSON
            message_json = json.dumps(message)

            # Push to queue (LPUSH adds to left, RPOP removes from right = FIFO)
            await self.redis_client.lpush(queue_name, message_json)

            logger.debug(f"Successfully queued message to {queue_name}")
            return True

        except RedisError as e:
            logger.error(f"Failed to queue message to {queue_name}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize message for {queue_name}: {e}")
            return False

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get the current length of a queue.

        Args:
            queue_name: Name of the Redis queue

        Returns:
            Queue length, or -1 on error
        """
        if not self.redis_client:
            return -1

        try:
            length = await self.redis_client.llen(queue_name)
            return length
        except RedisError as e:
            logger.error(f"Failed to get queue length for {queue_name}: {e}")
            return -1

    async def get_queue_stats(self) -> Dict[str, int]:
        """
        Get statistics for all queues.

        Returns:
            Dictionary mapping queue names to their lengths
        """
        return {
            "tutors": await self.get_queue_length(self.TUTOR_QUEUE),
            "sessions": await self.get_queue_length(self.SESSION_QUEUE),
            "feedbacks": await self.get_queue_length(self.FEEDBACK_QUEUE),
        }

    async def cache_prediction(
        self,
        tutor_id: str,
        prediction_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a churn prediction result.

        Args:
            tutor_id: Tutor ID
            prediction_data: Prediction result dictionary
            ttl: Time to live in seconds (default: PREDICTION_CACHE_TTL)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            cache_key = f"{self.PREDICTION_CACHE_PREFIX}{tutor_id}"
            ttl_seconds = ttl or self.PREDICTION_CACHE_TTL

            # Serialize prediction data
            prediction_json = json.dumps(prediction_data)

            # Set with expiration
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                prediction_json
            )

            logger.debug(f"Cached prediction for tutor {tutor_id} (TTL: {ttl_seconds}s)")
            return True

        except RedisError as e:
            logger.error(f"Failed to cache prediction for {tutor_id}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize prediction for {tutor_id}: {e}")
            return False

    async def get_cached_prediction(self, tutor_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached prediction for a tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            Cached prediction data if exists, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            cache_key = f"{self.PREDICTION_CACHE_PREFIX}{tutor_id}"

            # Get from cache
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                prediction = json.loads(cached_data)
                logger.debug(f"Cache hit for tutor {tutor_id}")
                return prediction
            else:
                logger.debug(f"Cache miss for tutor {tutor_id}")
                return None

        except RedisError as e:
            logger.error(f"Failed to retrieve cached prediction for {tutor_id}: {e}")
            return None
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to deserialize cached prediction for {tutor_id}: {e}")
            return None

    async def invalidate_prediction_cache(self, tutor_id: str) -> bool:
        """
        Invalidate cached prediction for a tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            True if successfully invalidated, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            cache_key = f"{self.PREDICTION_CACHE_PREFIX}{tutor_id}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated prediction cache for tutor {tutor_id}")
            return True

        except RedisError as e:
            logger.error(f"Failed to invalidate prediction cache for {tutor_id}: {e}")
            return False

    # Dashboard caching methods
    async def cache_dashboard_data(
        self,
        dashboard_key: str,
        dashboard_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache dashboard data.

        Args:
            dashboard_key: Unique key for the dashboard (e.g., 'main', 'tutor_123')
            dashboard_data: Dashboard data dictionary
            ttl: Time to live in seconds (default: DASHBOARD_CACHE_TTL)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            cache_key = f"{self.DASHBOARD_CACHE_PREFIX}{dashboard_key}"
            ttl_seconds = ttl or self.DASHBOARD_CACHE_TTL

            # Serialize dashboard data
            data_json = json.dumps(dashboard_data)

            # Set with expiration
            await self.redis_client.setex(cache_key, ttl_seconds, data_json)

            logger.debug(f"Cached dashboard data for {dashboard_key} (TTL: {ttl_seconds}s)")
            return True

        except RedisError as e:
            logger.error(f"Failed to cache dashboard data for {dashboard_key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize dashboard data for {dashboard_key}: {e}")
            return False

    async def get_cached_dashboard_data(self, dashboard_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached dashboard data.

        Args:
            dashboard_key: Unique key for the dashboard

        Returns:
            Cached dashboard data if exists, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            cache_key = f"{self.DASHBOARD_CACHE_PREFIX}{dashboard_key}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit for dashboard {dashboard_key}")
                return data
            else:
                logger.debug(f"Cache miss for dashboard {dashboard_key}")
                return None

        except RedisError as e:
            logger.error(f"Failed to retrieve cached dashboard data for {dashboard_key}: {e}")
            return None
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to deserialize cached dashboard data for {dashboard_key}: {e}")
            return None

    async def invalidate_dashboard_cache(self, dashboard_key: str) -> bool:
        """
        Invalidate cached dashboard data.

        Args:
            dashboard_key: Unique key for the dashboard

        Returns:
            True if successfully invalidated, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            cache_key = f"{self.DASHBOARD_CACHE_PREFIX}{dashboard_key}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated dashboard cache for {dashboard_key}")
            return True

        except RedisError as e:
            logger.error(f"Failed to invalidate dashboard cache for {dashboard_key}: {e}")
            return False

    # Aggregated metrics caching
    async def cache_metrics(
        self,
        metric_key: str,
        metrics_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache aggregated metrics.

        Args:
            metric_key: Unique key for the metrics (e.g., 'churn_rates', 'performance_summary')
            metrics_data: Metrics data dictionary
            ttl: Time to live in seconds (default: METRICS_CACHE_TTL)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            cache_key = f"{self.METRICS_CACHE_PREFIX}{metric_key}"
            ttl_seconds = ttl or self.METRICS_CACHE_TTL

            # Serialize metrics data
            data_json = json.dumps(metrics_data)

            # Set with expiration
            await self.redis_client.setex(cache_key, ttl_seconds, data_json)

            logger.debug(f"Cached metrics for {metric_key} (TTL: {ttl_seconds}s)")
            return True

        except RedisError as e:
            logger.error(f"Failed to cache metrics for {metric_key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize metrics for {metric_key}: {e}")
            return False

    async def get_cached_metrics(self, metric_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached metrics.

        Args:
            metric_key: Unique key for the metrics

        Returns:
            Cached metrics if exists, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            cache_key = f"{self.METRICS_CACHE_PREFIX}{metric_key}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit for metrics {metric_key}")
                return data
            else:
                logger.debug(f"Cache miss for metrics {metric_key}")
                return None

        except RedisError as e:
            logger.error(f"Failed to retrieve cached metrics for {metric_key}: {e}")
            return None
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to deserialize cached metrics for {metric_key}: {e}")
            return None

    async def invalidate_metrics_cache(self, metric_key: str) -> bool:
        """
        Invalidate cached metrics.

        Args:
            metric_key: Unique key for the metrics

        Returns:
            True if successfully invalidated, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            cache_key = f"{self.METRICS_CACHE_PREFIX}{metric_key}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated metrics cache for {metric_key}")
            return True

        except RedisError as e:
            logger.error(f"Failed to invalidate metrics cache for {metric_key}: {e}")
            return False

    # Cache warming
    async def warm_cache(self, session) -> Dict[str, bool]:
        """
        Warm cache with frequently accessed data.

        This method should be called during application startup or periodically
        to pre-load commonly accessed data into the cache.

        Args:
            session: Database session for fetching data to warm cache

        Returns:
            Dictionary indicating success/failure for each cache warming operation
        """
        results = {}
        logger.info("Starting cache warming...")

        try:
            # Warm tutor list cache (if we have a method to fetch all tutors)
            # This would need to be implemented based on your data access layer
            # For now, just mark as pending
            results['tutor_list'] = False
            logger.debug("Tutor list cache warming not yet implemented")

            # Warm intervention stats cache
            results['intervention_stats'] = False
            logger.debug("Intervention stats cache warming not yet implemented")

            # Warm dashboard data cache for main dashboard
            results['main_dashboard'] = False
            logger.debug("Main dashboard cache warming not yet implemented")

            logger.info(f"Cache warming completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error during cache warming: {e}", exc_info=True)
            return results

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics including hit/miss rates and memory usage.

        Returns:
            Dictionary with cache statistics
        """
        if not self.redis_client:
            return {"error": "Redis client not initialized"}

        try:
            # Get Redis info
            info = await self.redis_client.info('stats')

            # Get key counts for different cache types
            prediction_keys = len(await self.redis_client.keys(f"{self.PREDICTION_CACHE_PREFIX}*"))
            dashboard_keys = len(await self.redis_client.keys(f"{self.DASHBOARD_CACHE_PREFIX}*"))
            metrics_keys = len(await self.redis_client.keys(f"{self.METRICS_CACHE_PREFIX}*"))

            return {
                "prediction_cache_keys": prediction_keys,
                "dashboard_cache_keys": dashboard_keys,
                "metrics_cache_keys": metrics_keys,
                "total_cache_keys": prediction_keys + dashboard_keys + metrics_keys,
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": (
                    info.get('keyspace_hits', 0) /
                    (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
                    if (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) > 0
                    else 0
                )
            }

        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


# Global Redis service instance
redis_service = RedisService()


async def get_redis_service() -> RedisService:
    """
    Dependency injection function for FastAPI.

    Returns:
        RedisService instance
    """
    return redis_service
