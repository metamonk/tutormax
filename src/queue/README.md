# TutorMax Message Queue System

Redis-based message queuing infrastructure for the TutorMax data processing pipeline.

## Overview

This package provides a robust, scalable message queue system for processing tutor, session, and feedback data. Built on Redis Streams, it supports:

- **Reliable message delivery** with consumer groups
- **Automatic retry** of failed messages
- **Dead letter queue** for permanently failed messages
- **Connection pooling** for efficient resource usage
- **Graceful shutdown** handling
- **Health monitoring** and statistics

## Architecture

```
┌─────────────┐
│   Producer  │──> Publish ──> [Redis Stream: tutormax:tutors]
└─────────────┘                          │
                                         ▼
┌─────────────┐                  [Consumer Group]
│   Worker    │<── Consume <──          │
│             │                          ▼
│  - Handler  │              ┌─────────────────┐
│  - Process  │              │ Message Queue   │
│  - ACK      │              │  - Pending      │
└─────────────┘              │  - Processing   │
                             │  - Retry        │
                             │  - Dead Letter  │
                             └─────────────────┘
```

## Queue Channels

| Channel | Purpose | Data Type |
|---------|---------|-----------|
| `tutormax:tutors` | Tutor profile data and updates | Tutor records |
| `tutormax:sessions` | Tutoring session records | Session data |
| `tutormax:feedback` | Student feedback data | Feedback/ratings |
| `tutormax:dead_letter` | Failed messages | Any |

## Quick Start

### 1. Start Redis

```bash
# Using Docker Compose
docker-compose up -d redis

# Or using Docker directly
docker run -d -p 6379:6379 --name tutormax-redis redis:7-alpine
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit Redis configuration (optional, defaults to localhost:6379)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=
```

### 3. Publish Messages

```python
from src.queue import get_redis_client, MessagePublisher, QueueChannels

# Get Redis client
client = get_redis_client()

# Create publisher
publisher = MessagePublisher(client)

# Publish tutor data
tutor_data = {
    "tutor_id": "T001",
    "name": "John Smith",
    "subject": "Mathematics",
    "rating": 4.8
}

message_id = publisher.publish(QueueChannels.TUTORS, tutor_data)
print(f"Published message: {message_id}")
```

### 4. Process Messages with Worker

```python
from src.queue import QueueWorker, QueueChannels

# Define handler function
def process_tutor(data: dict) -> bool:
    print(f"Processing tutor: {data['name']}")
    # Add your processing logic here
    return True

# Create worker
worker = QueueWorker([QueueChannels.TUTORS])

# Register handler
worker.register_handler(QueueChannels.TUTORS, process_tutor)

# Run worker (blocks until interrupted)
worker.run()
```

### 5. Run Standalone Worker

```bash
# Process all channels
python examples/worker.py

# Process specific channels
python examples/worker.py --channels tutormax:tutors,tutormax:sessions

# Custom batch size
python examples/worker.py --batch-size 20
```

## API Reference

### RedisClient

Connection manager with pooling and health checks.

```python
from src.queue import get_redis_client

# Get singleton client
client = get_redis_client()

# Check connection
if client.is_connected():
    print("Connected to Redis")

# Health check
health = client.health_check()
print(health)
```

### MessagePublisher

Publishes messages to queue channels.

```python
publisher = MessagePublisher(redis_client)

# Publish single message
msg_id = publisher.publish(channel, data, metadata)

# Publish batch
msg_ids = publisher.publish_batch(channel, [data1, data2, data3])

# Convenience methods
publisher.publish_tutor_data(tutor_data)
publisher.publish_session_data(session_data)
publisher.publish_feedback_data(feedback_data)

# Get queue info
length = publisher.get_stream_length(channel)
info = publisher.get_stream_info(channel)
```

### MessageConsumer

Consumes messages from queues using consumer groups.

```python
consumer = MessageConsumer(redis_client, consumer_group="my-group")

# Create consumer group
consumer.create_consumer_group(channel)

# Consume messages
messages = consumer.consume(channel, count=10, block_ms=1000)

# Process and acknowledge
for msg in messages:
    # Process message
    process_data(msg['data'])

    # Acknowledge
    consumer.acknowledge(channel, msg['_redis_id'])

# Handle failures
consumer.retry_message(channel, message, max_retries=3)

# Get pending messages
pending = consumer.get_pending_messages(channel)
```

### QueueWorker

Worker framework with automatic processing.

```python
worker = QueueWorker(
    channels=[QueueChannels.TUTORS, QueueChannels.SESSIONS],
    batch_size=10
)

# Register handlers
worker.register_handler(QueueChannels.TUTORS, process_tutor)
worker.register_handler(QueueChannels.SESSIONS, process_session)

# Run continuously
worker.run()

# Or process once (for cron jobs)
count = worker.run_once()

# Get statistics
stats = worker.get_stats()
```

### MessageSerializer

Handles message serialization with integrity checks.

```python
serializer = MessageSerializer()

# Serialize
message_json = serializer.serialize(channel, data, metadata)

# Deserialize
message = serializer.deserialize(message_json)

# Extract just the data
data = serializer.extract_data(message_json)
```

## Configuration

Environment variables (prefix: `REDIS_`):

```bash
# Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Connection pool
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Retry settings
REDIS_RETRY_ON_TIMEOUT=true
REDIS_MAX_RETRIES=3
REDIS_RETRY_BACKOFF_MS=100

# Message settings
REDIS_MESSAGE_TTL_SECONDS=86400
REDIS_MAX_MESSAGE_SIZE_BYTES=1048576

# Worker settings
REDIS_WORKER_BATCH_SIZE=10
REDIS_WORKER_POLL_INTERVAL_MS=100
REDIS_WORKER_MAX_PROCESSING_TIME_SECONDS=300

# Queue settings
REDIS_QUEUE_MAXLEN=100000
```

## Message Format

Messages are serialized as JSON with metadata and integrity checks:

```json
{
  "id": "uuid-v4",
  "timestamp": "2024-01-01T12:00:00",
  "channel": "tutormax:tutors",
  "data": {
    "tutor_id": "T001",
    "name": "John Smith"
  },
  "metadata": {
    "source": "api",
    "priority": "high"
  },
  "checksum": "sha256-hash"
}
```

## Error Handling

### Retry Logic

Failed messages are automatically retried up to `max_retries` times:

1. Message processing fails
2. Consumer calls `retry_message()`
3. Message moved to retry channel
4. Worker picks up retry message
5. If still failing after max retries → dead letter queue

### Dead Letter Queue

Messages that exceed retry limits are sent to `tutormax:dead_letter` for manual inspection:

```python
# Inspect dead letter queue
messages = consumer.consume(QueueChannels.DEAD_LETTER, count=10)

for msg in messages:
    print(f"Failed message: {msg['id']}")
    print(f"Reason: {msg['metadata']['reason']}")
    print(f"Retry count: {msg['metadata']['retry_count']}")
```

## Monitoring

### Queue Health

```python
# Check Redis health
health = redis_client.health_check()

# Check queue lengths
for channel in QueueChannels.all_channels():
    length = publisher.get_stream_length(channel)
    print(f"{channel}: {length} messages")

# Get detailed stream info
info = publisher.get_stream_info(QueueChannels.TUTORS)
```

### Worker Stats

```python
stats = worker.get_stats()
# {
#   'messages_processed': 1000,
#   'messages_succeeded': 980,
#   'messages_failed': 20,
#   'batches_processed': 100,
#   'errors': 2,
#   'consumer_stats': {...},
#   'is_running': True
# }
```

### Redis Commander (Web UI)

Access at http://localhost:8081 when using Docker Compose:

```bash
docker-compose up -d redis-commander
```

## Testing

Run tests with pytest:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all queue tests
pytest tests/test_queue.py -v

# Run with coverage
pytest tests/test_queue.py --cov=src/queue --cov-report=html
```

## Performance

### Throughput

- **3,000+ messages/day** easily handled
- Batch publishing for higher throughput
- Connection pooling reduces overhead
- Async-ready (can be extended for asyncio)

### Scalability

- **Horizontal scaling**: Run multiple workers
- **Consumer groups**: Multiple consumers share load
- **Channel-based**: Different workers for different channels
- **Stream trimming**: Automatic cleanup of old messages

### Resource Usage

- **Memory**: ~256MB recommended for Redis
- **CPU**: Minimal overhead
- **Network**: Local connections preferred
- **Disk**: AOF persistence for durability

## Best Practices

1. **Use consumer groups** for load distribution
2. **Set appropriate TTL** for messages
3. **Monitor dead letter queue** regularly
4. **Implement idempotent handlers** (messages may be redelivered)
5. **Log processing errors** with context
6. **Use batch operations** for efficiency
7. **Handle graceful shutdown** properly
8. **Set reasonable timeouts** to prevent blocking

## Troubleshooting

### Worker not processing messages

```python
# Check Redis connection
client = get_redis_client()
print(client.is_connected())

# Check queue length
length = publisher.get_stream_length(channel)
print(f"Queue has {length} messages")

# Check consumer group exists
consumer.create_consumer_group(channel)
```

### Messages stuck in pending

```python
# Get pending messages
pending = consumer.get_pending_messages(channel)
print(f"Pending: {len(pending)}")

# Claim stuck messages (dead consumer recovery)
claimed = consumer.claim_pending_messages(channel, min_idle_time_ms=60000)
```

### Connection errors

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping

# Check logs
docker logs tutormax-redis
```

## Examples

See `examples/` directory for complete examples:

- `queue_example.py` - Publishing and consuming examples
- `worker.py` - Standalone worker script

## License

Part of the TutorMax project.
