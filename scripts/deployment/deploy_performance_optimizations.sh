#!/bin/bash

# Performance Optimization Deployment Script
# Applies all Task 11 optimizations to TutorMax

set -e  # Exit on error

echo "================================================================================"
echo "TutorMax Performance Optimization Deployment"
echo "================================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check dependencies
echo "Step 1: Checking dependencies..."
echo "--------------------------------"

if ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python 3.11+"
    exit 1
fi
print_status "Python found: $(python --version)"

if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL client not found (optional for pg_stat_statements)"
else
    print_status "PostgreSQL client found"
fi

if ! command -v redis-cli &> /dev/null; then
    print_warning "Redis CLI not found (optional for cache verification)"
else
    print_status "Redis CLI found"
fi

echo ""

# Step 2: Install Python dependencies
echo "Step 2: Installing Python dependencies..."
echo "-------------------------------------------"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

echo ""

# Step 3: Check database connection
echo "Step 3: Checking database connection..."
echo "-----------------------------------------"

# Load .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_status ".env file loaded"
else
    print_warning ".env file not found. Using default settings."
fi

# Test database connection (optional)
if command -v psql &> /dev/null; then
    if psql -U "${POSTGRES_USER:-tutormax}" -d "${POSTGRES_DB:-tutormax}" -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -c "SELECT 1" > /dev/null 2>&1; then
        print_status "Database connection successful"
    else
        print_warning "Database connection failed. Continuing anyway..."
    fi
fi

echo ""

# Step 4: Apply database migrations
echo "Step 4: Applying database migrations..."
echo "-----------------------------------------"

if [ -f "alembic.ini" ]; then
    alembic upgrade head
    print_status "Database migrations applied"
else
    print_error "alembic.ini not found"
    exit 1
fi

echo ""

# Step 5: Enable PostgreSQL extensions (optional)
echo "Step 5: Enabling PostgreSQL extensions..."
echo "-------------------------------------------"

if command -v psql &> /dev/null; then
    echo "Attempting to enable pg_stat_statements..."
    if psql -U "${POSTGRES_USER:-tutormax}" -d "${POSTGRES_DB:-tutormax}" -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" > /dev/null 2>&1; then
        print_status "pg_stat_statements enabled"
    else
        print_warning "Failed to enable pg_stat_statements (requires superuser privileges)"
        print_warning "Run manually: psql -U postgres -d tutormax -c \"CREATE EXTENSION IF NOT EXISTS pg_stat_statements;\""
    fi
else
    print_warning "Skipping pg_stat_statements (psql not available)"
fi

echo ""

# Step 6: Verify Redis connection
echo "Step 6: Verifying Redis connection..."
echo "---------------------------------------"

if command -v redis-cli &> /dev/null; then
    if redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" ping > /dev/null 2>&1; then
        print_status "Redis connection successful"
    else
        print_error "Redis connection failed. Please ensure Redis is running."
        exit 1
    fi
else
    print_warning "Skipping Redis verification (redis-cli not available)"
fi

echo ""

# Step 7: Run validation
echo "Step 7: Running performance validation..."
echo "-------------------------------------------"

if [ -f "scripts/performance_report.py" ]; then
    python scripts/performance_report.py || true
    print_status "Validation complete (see output above)"
else
    print_warning "Performance validation script not found"
fi

echo ""

# Step 8: Build frontend (optional)
echo "Step 8: Building frontend (optional)..."
echo "-----------------------------------------"

if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            echo "Installing frontend dependencies..."
            npm install
            print_status "Frontend dependencies installed"

            echo "Building frontend..."
            npm run build
            print_status "Frontend built successfully"
        else
            print_warning "npm not found. Skipping frontend build."
        fi
    else
        print_warning "package.json not found in frontend directory"
    fi
    cd "$PROJECT_ROOT"
else
    print_warning "Frontend directory not found. Skipping."
fi

echo ""

# Final summary
echo "================================================================================"
echo "Deployment Summary"
echo "================================================================================"
echo ""
print_status "Python dependencies installed"
print_status "Database migrations applied"
print_status "Performance optimizations deployed"
echo ""

echo "Next steps:"
echo "  1. Start the API:"
echo "     uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  2. Monitor performance:"
echo "     curl http://localhost:8000/api/performance/summary"
echo ""
echo "  3. Run load tests:"
echo "     locust -f tests/load_testing/locustfile.py --host=http://localhost:8000"
echo ""
echo "  4. View documentation:"
echo "     cat docs/PERFORMANCE_QUICK_START.md"
echo ""

echo "================================================================================"
print_status "Performance optimization deployment complete!"
echo "================================================================================"
