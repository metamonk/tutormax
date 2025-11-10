#!/bin/bash
#
# Normal Load Test - Expected Production Load
# Simulates typical operating conditions
#
# Usage: ./scripts/load_tests/run_normal_load_test.sh

set -e

echo "========================================="
echo "  TutorMax Normal Load Test"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Users: 100"
echo "  Spawn rate: 10 users/second"
echo "  Duration: 10 minutes"
echo "  Host: http://localhost:8000"
echo ""
echo "This simulates normal production load:"
echo "  - 30,000 sessions/day target"
echo "  - 100 concurrent users"
echo "  - Mixed user behaviors"
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
echo "🚀 Starting normal load test..."
echo "⏱️  This will take 10 minutes..."
echo ""

locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html reports/normal-load-$(date +%Y%m%d-%H%M%S).html \
  --csv reports/normal-load-$(date +%Y%m%d-%H%M%S)

echo ""
echo "✅ Normal load test complete!"
echo "📊 Report saved to: reports/normal-load-*.html"
echo ""
echo "Next steps:"
echo "  1. Open the HTML report in your browser"
echo "  2. Check that p95 response time < 200ms"
echo "  3. Verify failure rate < 0.5%"
echo "  4. Review resource utilization"
echo ""
