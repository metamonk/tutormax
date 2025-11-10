#!/bin/bash
#
# Baseline Load Test - Light Load
# Tests basic functionality with minimal load
#
# Usage: ./scripts/load_tests/run_baseline_test.sh

set -e

echo "========================================="
echo "  TutorMax Baseline Load Test"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Users: 25"
echo "  Spawn rate: 5 users/second"
echo "  Duration: 3 minutes"
echo "  Host: http://localhost:8000"
echo ""

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: API server is not running on http://localhost:8000"
    echo "Please start the API server first:"
    echo "  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ API server is running"
echo ""

# Create reports directory
mkdir -p reports

# Run test
echo "🚀 Starting baseline load test..."
echo ""

locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 25 \
  --spawn-rate 5 \
  --run-time 3m \
  --headless \
  --html reports/baseline-test-$(date +%Y%m%d-%H%M%S).html \
  --csv reports/baseline-test-$(date +%Y%m%d-%H%M%S)

echo ""
echo "✅ Baseline test complete!"
echo "📊 Report saved to: reports/baseline-test-*.html"
echo ""
