#!/bin/bash
# Stop all Celery workers for TutorMax

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping TutorMax Celery Workers...${NC}"

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# PID directory
PID_DIR="$PROJECT_ROOT/logs/pids"

# Function to stop a worker
stop_worker() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill -TERM "$pid"

            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done

            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}Forcefully killing $name...${NC}"
                kill -KILL "$pid"
            fi

            rm "$pid_file"
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}$name not running (stale PID file)${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}$name PID file not found${NC}"
    fi
}

# Stop all workers
stop_worker "data_generation"
stop_worker "evaluation"
stop_worker "prediction"
stop_worker "training"
stop_worker "default"
stop_worker "beat"

# Stop Flower
echo -e "${YELLOW}Stopping Flower...${NC}"
pkill -f "celery.*flower" || echo -e "${YELLOW}Flower not running${NC}"

echo ""
echo -e "${GREEN}✓ All workers stopped${NC}"
