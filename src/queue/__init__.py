"""
Message queue infrastructure for TutorMax data processing pipeline.

This package provides Redis-based message queuing for:
- Tutor data processing
- Session data processing
- Feedback data processing
"""

from .client import RedisClient, get_redis_client
from .publisher import MessagePublisher
from .consumer import MessageConsumer
from .worker import QueueWorker
from .channels import QueueChannels
from .serializer import MessageSerializer

__all__ = [
    "RedisClient",
    "get_redis_client",
    "MessagePublisher",
    "MessageConsumer",
    "QueueWorker",
    "QueueChannels",
    "MessageSerializer",
]
