# Redis Setup Guide for TutorMax

Complete guide to set up and run the Redis message queue system.

## Quick Start (5 minutes)

### 1. Start Redis with Docker Compose

```bash
# Start Redis (runs in background)
docker-compose up -d redis

# Verify Redis is running
docker ps | grep redis

# Check Redis logs
docker logs tutormax-redis
```

### 2. Test Connection

```bash
# Using redis-cli
redis-cli ping
# Should return: PONG

# Or using Python
python -c "from src.queue import get_redis_client; print(get_redis_client().health_check())"
```

### 3. Run Example Script

```bash
# Run complete example
python examples/queue_example.py

# Monitor queues
python examples/monitor_queues.py --snapshot
```

### 4. Start Worker

```bash
# Run worker to process messages
python examples/worker.py
```

## Alternative Redis Setup Methods

### Option 1: Docker Compose (Recommended)

Includes Redis + Redis Commander (web UI):

```bash
docker-compose up -d
```

Access Redis Commander at: http://localhost:8081

### Option 2: Docker Only

```bash
docker run -d \
  --name tutormax-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes
```

### Option 3: Local Installation

**macOS (Homebrew):**
```bash
brew install redis
redis-server
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Windows:**
Download from: https://github.com/microsoftarchive/redis/releases

## Configuration

### Environment Variables

Copy and configure `.env.example`:

```bash
cp .env.example .env
```

Edit Redis settings in `.env`:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=              # Leave empty for no password
REDIS_MAX_CONNECTIONS=50
REDIS_MESSAGE_TTL_SECONDS=86400
REDIS_WORKER_BATCH_SIZE=10
```

### Redis Configuration File (Optional)

For production, create `redis.conf`:

```conf
# Network
bind 0.0.0.0
port 6379
protected-mode yes

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

Use with Docker:

```bash
docker run -d \
  --name tutormax-redis \
  -p 6379:6379 \
  -v $(pwd)/redis.conf:/usr/local/etc/redis/redis.conf \
  redis:7-alpine \
  redis-server /usr/local/etc/redis/redis.conf
```

## Usage Examples

### Publishing Messages

```python
from src.queue import get_redis_client, MessagePublisher, QueueChannels

# Get client
client = get_redis_client()
publisher = MessagePublisher(client)

# Publish tutor data
tutor_data = {
    "tutor_id": "T001",
    "name": "John Smith",
    "subject": "Mathematics",
    "rating": 4.8
}

msg_id = publisher.publish_tutor_data(tutor_data)
print(f"Published: {msg_id}")
```

### Processing Messages with Worker

```python
from src.queue import QueueWorker, QueueChannels

def process_tutor(data):
    print(f"Processing: {data['name']}")
    # Your processing logic here
    return True

worker = QueueWorker([QueueChannels.TUTORS])
worker.register_handler(QueueChannels.TUTORS, process_tutor)
worker.run()  # Runs until Ctrl+C
```

### Monitoring Queues

```bash
# Live monitoring (refreshes every 5 seconds)
python examples/monitor_queues.py

# One-time snapshot
python examples/monitor_queues.py --snapshot

# Custom interval (10 seconds)
python examples/monitor_queues.py --interval 10
```

## Testing

### Run Tests

```bash
# Make sure Redis is running
docker-compose up -d redis

# Run all queue tests
pytest tests/test_queue.py -v

# Run with coverage
pytest tests/test_queue.py --cov=src/queue --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Manual Testing

```bash
# Test connection
redis-cli ping

# Publish test message
redis-cli XADD tutormax:tutors "*" message '{"test": "data"}'

# Read stream
redis-cli XREAD STREAMS tutormax:tutors 0

# Get stream length
redis-cli XLEN tutormax:tutors

# Delete stream
redis-cli DEL tutormax:tutors
```

## Production Deployment

### Docker Swarm

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

volumes:
  redis-data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
```

### Redis Sentinel (High Availability)

For production high availability, use Redis Sentinel:

```bash
# Start master
docker run -d --name redis-master -p 6379:6379 redis:7-alpine

# Start sentinel
docker run -d --name redis-sentinel \
  -p 26379:26379 \
  redis:7-alpine \
  redis-sentinel /path/to/sentinel.conf
```

## Performance Tuning

### For High Throughput (3,000+ messages/day)

1. **Increase connection pool:**
   ```bash
   REDIS_MAX_CONNECTIONS=100
   ```

2. **Adjust worker batch size:**
   ```bash
   REDIS_WORKER_BATCH_SIZE=50
   ```

3. **Use multiple workers:**
   ```bash
   # Terminal 1
   python examples/worker.py --channels tutormax:tutors

   # Terminal 2
   python examples/worker.py --channels tutormax:sessions

   # Terminal 3
   python examples/worker.py --channels tutormax:feedback
   ```

4. **Enable Redis pipelining in code** (already implemented)

### Memory Optimization

```conf
# Set memory limit
maxmemory 256mb

# Use LRU eviction
maxmemory-policy allkeys-lru

# Disable persistence for pure cache
save ""
appendonly no
```

## Monitoring and Maintenance

### Health Checks

```bash
# Redis health
redis-cli ping

# Queue statistics
python examples/monitor_queues.py --snapshot

# Check memory usage
redis-cli INFO memory

# Check connected clients
redis-cli CLIENT LIST
```

### Cleanup Old Messages

```bash
# Trim stream to last 1000 messages
redis-cli XTRIM tutormax:tutors MAXLEN ~ 1000

# Delete all messages
redis-cli DEL tutormax:tutors
redis-cli DEL tutormax:sessions
redis-cli DEL tutormax:feedback
```

### Backup and Restore

```bash
# Create backup
docker exec tutormax-redis redis-cli SAVE
docker cp tutormax-redis:/data/dump.rdb ./backup/

# Restore backup
docker cp ./backup/dump.rdb tutormax-redis:/data/
docker restart tutormax-redis
```

## Troubleshooting

### Connection Refused

```bash
# Check if Redis is running
docker ps | grep redis

# Check Redis logs
docker logs tutormax-redis

# Restart Redis
docker-compose restart redis
```

### Out of Memory

```bash
# Check memory usage
redis-cli INFO memory

# Clear all data (CAUTION!)
redis-cli FLUSHALL

# Or set maxmemory policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Slow Performance

```bash
# Check slow log
redis-cli SLOWLOG GET 10

# Monitor commands in real-time
redis-cli MONITOR

# Check latency
redis-cli --latency
```

### Messages Stuck in Queue

```python
from src.queue import get_redis_client, MessageConsumer

consumer = MessageConsumer(get_redis_client())

# Check pending messages
pending = consumer.get_pending_messages("tutormax:tutors")
print(f"Pending: {len(pending)}")

# Claim stuck messages (dead consumer recovery)
claimed = consumer.claim_pending_messages("tutormax:tutors")
print(f"Claimed: {len(claimed)}")
```

## Security

### Production Security Checklist

- [ ] Enable Redis password authentication
- [ ] Bind to specific IP (not 0.0.0.0)
- [ ] Use SSL/TLS for connections
- [ ] Disable dangerous commands
- [ ] Enable protected mode
- [ ] Use firewall rules
- [ ] Regular backups

### Example Secure Configuration

```conf
# Require password
requirepass your-strong-password-here

# Bind to specific interface
bind 127.0.0.1

# Protected mode
protected-mode yes

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

Update `.env`:

```bash
REDIS_PASSWORD=your-strong-password-here
```

## Resources

- **Redis Documentation**: https://redis.io/documentation
- **Redis Streams**: https://redis.io/topics/streams-intro
- **Redis Python Client**: https://redis-py.readthedocs.io/
- **TutorMax Queue README**: src/queue/README.md

## Support

For issues or questions:
1. Check Redis logs: `docker logs tutormax-redis`
2. Check worker logs: `tail -f worker.log`
3. Review test output: `pytest tests/test_queue.py -v`
4. Monitor queue status: `python examples/monitor_queues.py --snapshot`
