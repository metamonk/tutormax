#!/bin/bash
#
# Run Celery Beat Scheduler
#
# This script starts the Celery beat scheduler that triggers periodic tasks,
# including the performance evaluator that runs every 15 minutes.
#
# Usage:
#   ./scripts/run_celery_beat.sh
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Celery Beat Scheduler${NC}"
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

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Beat configuration
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"
SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE:-celerybeat-schedule}"

echo -e "${BLUE}Starting Celery beat scheduler...${NC}"
echo "  Log level: ${LOG_LEVEL}"
echo "  Schedule file: ${SCHEDULE_FILE}"
echo ""
echo -e "${BLUE}Scheduled Tasks:${NC}"
echo "  • Performance Evaluator: Every 15 minutes"
echo "  • Churn Predictor: Daily at midnight"
echo "  • Model Trainer: Daily at 2 AM"
echo ""
echo -e "${GREEN}Beat scheduler is running. Press Ctrl+C to stop.${NC}"
echo ""

# Start beat scheduler
exec celery -A src.workers.celery_app beat \
    --loglevel=${LOG_LEVEL} \
    --schedule=${SCHEDULE_FILE}
