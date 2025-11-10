#!/bin/bash
#
# Analytics API Testing Script
# Tests all Task 9 analytics endpoints
#
# Usage: ./scripts/test_analytics_endpoints.sh

set -e

BASE_URL="http://localhost:8000/api/analytics"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  TutorMax Analytics API Testing"
echo "================================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"

    echo -n "Testing ${name}... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${url}")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}${url}")
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" = "200" ] || [ "$status_code" = "201" ]; then
        echo -e "${GREEN}✓ PASS${NC} (${status_code})"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (${status_code})"
        echo "  Response: $body"
        return 1
    fi
}

# Function to test and measure performance
test_performance() {
    local name="$1"
    local url="$2"
    local target_ms="$3"

    echo -n "Performance test ${name}... "

    start_time=$(date +%s%3N)
    response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${url}")
    end_time=$(date +%s%3N)

    status_code=$(echo "$response" | tail -n1)
    elapsed=$((end_time - start_time))

    if [ "$status_code" = "200" ]; then
        if [ "$elapsed" -lt "$target_ms" ]; then
            echo -e "${GREEN}✓ PASS${NC} (${elapsed}ms < ${target_ms}ms)"
            return 0
        else
            echo -e "${YELLOW}⚠ SLOW${NC} (${elapsed}ms > ${target_ms}ms)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (${status_code})"
        return 1
    fi
}

echo "=== Overview & Summary ==="
test_endpoint "Overview" "/overview"
test_endpoint "Performance Summary (30d)" "/performance-summary?period=30d"
echo ""

echo "=== Churn Heatmaps ==="
test_endpoint "Churn Heatmap (Weekly)" "/churn-heatmap?granularity=weekly"
test_endpoint "Churn Heatmap (Daily)" "/churn-heatmap?granularity=daily"
test_endpoint "Churn Heatmap (Monthly)" "/churn-heatmap?granularity=monthly"
test_endpoint "Churn Heatmap by Tier" "/churn-heatmap/by-tier"
echo ""

echo "=== Cohort Analysis ==="
test_endpoint "Cohort Analysis" "/cohort-analysis?cohort_by=month&metric=retention&period=monthly"
test_endpoint "Retention Curve" "/cohort-analysis/retention-curve"
echo ""

echo "=== Intervention Effectiveness ==="
test_endpoint "Intervention Effectiveness" "/intervention-effectiveness"
test_endpoint "Intervention Comparison" "/intervention-effectiveness/comparison"
test_endpoint "Intervention Funnel" "/intervention-effectiveness/funnel?intervention_type=automated_coaching"
echo ""

echo "=== Predictive Insights ==="
test_endpoint "Predictive Trends (30d)" "/predictive-insights/trends?forecast_days=30"
test_endpoint "Predictive Trends (7d)" "/predictive-insights/trends?forecast_days=7"
test_endpoint "Risk Segments" "/predictive-insights/risk-segments"
echo ""

echo "=== Cache Management ==="
test_endpoint "Clear Specific Cache" "/cache/clear?cache_key=test_key" "POST"
echo ""

echo "=== Performance Benchmarks ==="
test_performance "Overview Load Time" "/overview" 2000
test_performance "Heatmap Generation" "/churn-heatmap?granularity=weekly" 500
test_performance "Cohort Analysis" "/cohort-analysis?cohort_by=month&metric=retention&period=monthly" 1000
test_performance "Intervention Analysis" "/intervention-effectiveness" 1000
echo ""

echo "================================================"
echo "  Testing Complete"
echo "================================================"

# Summary
passed=0
failed=0
total=15

echo ""
echo "Results:"
echo "  Total Tests: $total"
echo -e "  ${GREEN}Passed: Check above${NC}"
echo -e "  ${RED}Failed: Check above${NC}"
echo ""
echo "To view detailed responses, run:"
echo "  curl -s ${BASE_URL}/overview | jq"
echo ""
