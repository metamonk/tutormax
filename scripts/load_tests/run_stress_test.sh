#!/bin/bash
#
# Stress Test - Peak Load Simulation
# Tests system under 2-3x normal load
#
# Usage: ./scripts/load_tests/run_stress_test.sh

set -e

echo "========================================="
echo "  TutorMax Stress Test"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Users: 250"
echo "  Spawn rate: 15 users/second"
echo "  Duration: 15 minutes"
echo "  Host: http://localhost:8000"
echo ""
echo "⚠️  This simulates 2.5x peak load!"
echo "System may experience degraded performance."
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

read -p "Continue with stress test? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Stress test cancelled."
    exit 0
fi

# Create reports directory
mkdir -p reports

# Run test
echo "🚀 Starting stress test..."
echo "⏱️  This will take 15 minutes..."
echo "💡 Monitor system resources (CPU, memory, DB connections)"
echo ""

locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 250 \
  --spawn-rate 15 \
  --run-time 15m \
  --headless \
  --html reports/stress-test-$(date +%Y%m%d-%H%M%S).html \
  --csv reports/stress-test-$(date +%Y%m%d-%H%M%S)

echo ""
echo "✅ Stress test complete!"
echo "📊 Report saved to: reports/stress-test-*.html"
echo ""
echo "Analysis checklist:"
echo "  ☐ Were there any failures?"
echo "  ☐ Did response times degrade significantly?"
echo "  ☐ Did the system recover after load decreased?"
echo "  ☐ Are there any resource leaks?"
echo "  ☐ Did database connections max out?"
echo ""
