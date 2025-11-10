#!/bin/bash
# Start all Celery workers for TutorMax
# This script starts workers for each queue and the beat scheduler

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting TutorMax Celery Workers...${NC}"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Redis is not running. Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Log directory
LOG_DIR="$PROJECT_ROOT/logs/workers"
mkdir -p "$LOG_DIR"

# PID directory
PID_DIR="$PROJECT_ROOT/logs/pids"
mkdir -p "$PID_DIR"

# Start workers for each queue
echo -e "${GREEN}Starting data generation worker...${NC}"
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=data_generation \
    --concurrency=2 \
    --logfile="$LOG_DIR/data_generation.log" \
    --pidfile="$PID_DIR/data_generation.pid" \
    --detach

echo -e "${GREEN}Starting evaluation worker...${NC}"
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=evaluation \
    --concurrency=2 \
    --logfile="$LOG_DIR/evaluation.log" \
    --pidfile="$PID_DIR/evaluation.pid" \
    --detach

echo -e "${GREEN}Starting prediction worker...${NC}"
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=prediction \
    --concurrency=2 \
    --logfile="$LOG_DIR/prediction.log" \
    --pidfile="$PID_DIR/prediction.pid" \
    --detach

echo -e "${GREEN}Starting training worker...${NC}"
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=training \
    --concurrency=1 \
    --logfile="$LOG_DIR/training.log" \
    --pidfile="$PID_DIR/training.pid" \
    --detach

echo -e "${GREEN}Starting default queue worker...${NC}"
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=default \
    --concurrency=2 \
    --logfile="$LOG_DIR/default.log" \
    --pidfile="$PID_DIR/default.pid" \
    --detach

echo -e "${GREEN}Starting Celery Beat scheduler...${NC}"
celery -A src.workers.celery_app beat \
    --loglevel=info \
    --logfile="$LOG_DIR/beat.log" \
    --pidfile="$PID_DIR/beat.pid" \
    --detach

echo -e "${GREEN}Starting Flower monitoring...${NC}"
celery -A src.workers.celery_app flower \
    --port=5555 \
    --logfile="$LOG_DIR/flower.log" \
    --detach

sleep 2

echo ""
echo -e "${GREEN}✓ All workers started successfully!${NC}"
echo ""
echo "Worker logs: $LOG_DIR"
echo "PIDs: $PID_DIR"
echo ""
echo "Monitoring:"
echo "  - Flower: http://localhost:5555"
echo "  - API Health: http://localhost:8000/api/workers/health"
echo "  - API Dashboard: http://localhost:8000/api/workers/dashboard"
echo ""
echo "To stop all workers:"
echo "  ./scripts/stop_all_workers.sh"
echo ""
