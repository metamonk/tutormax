#!/bin/bash
#
# Run Performance Evaluator Celery Worker
#
# This script starts the Celery worker that processes performance evaluation tasks.
# It should be run alongside the beat scheduler for scheduled evaluations.
#
# Usage:
#   ./scripts/run_performance_worker.sh
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Performance Evaluator Celery Worker${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Redis is running
echo -e "${BLUE}Checking Redis connection...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Redis is not running or not accessible${NC}"
    echo "Please start Redis server first:"
    echo "  redis-server"
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"
echo ""

# Check if PostgreSQL is accessible
echo -e "${BLUE}Checking PostgreSQL connection...${NC}"
if ! pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} > /dev/null 2>&1; then
    echo -e "${RED}WARNING: PostgreSQL may not be running${NC}"
    echo "Database: ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"
fi
echo ""

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Worker configuration
WORKER_NAME="performance_evaluator@%h"
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"
CONCURRENCY="${CELERY_CONCURRENCY:-4}"
QUEUES="evaluation,default"

echo -e "${BLUE}Starting Celery worker...${NC}"
echo "  Worker name: ${WORKER_NAME}"
echo "  Log level: ${LOG_LEVEL}"
echo "  Concurrency: ${CONCURRENCY}"
echo "  Queues: ${QUEUES}"
echo ""
echo -e "${GREEN}Worker is running. Press Ctrl+C to stop.${NC}"
echo ""

# Start worker
exec celery -A src.workers.celery_app worker \
    --loglevel=${LOG_LEVEL} \
    --concurrency=${CONCURRENCY} \
    --queues=${QUEUES} \
    --hostname=${WORKER_NAME} \
    --time-limit=3600 \
    --soft-time-limit=3000 \
    --max-tasks-per-child=1000 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
