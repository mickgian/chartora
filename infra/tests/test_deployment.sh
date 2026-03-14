#!/bin/bash
# Deployment verification tests
# Run after deployment to verify all services are operational
# Usage: ./test_deployment.sh [base_url]

set -euo pipefail

BASE_URL="${1:-http://localhost}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    if [ "$status" = "$expected_status" ]; then
        echo "  PASS: $name (HTTP $status)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (expected $expected_status, got $status)"
        FAIL=$((FAIL + 1))
    fi
}

check_contains() {
    local name="$1"
    local url="$2"
    local expected="$3"

    body=$(curl -s --max-time 10 "$url" || echo "")
    if echo "$body" | grep -q "$expected"; then
        echo "  PASS: $name (contains '$expected')"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (missing '$expected')"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Chartora Deployment Verification ==="
echo "Target: $BASE_URL"
echo ""

echo "--- Backend Health ---"
check "Health endpoint" "$BASE_URL/health"
check_contains "Health response body" "$BASE_URL/health" '"status":"healthy"'

echo ""
echo "--- API Endpoints ---"
check "Leaderboard API" "$BASE_URL/api/v1/leaderboard"
check "Rankings: patents" "$BASE_URL/api/v1/rankings/patents"
check "Rankings: stock-performance" "$BASE_URL/api/v1/rankings/stock-performance"
check "OpenAPI docs" "$BASE_URL/docs"

echo ""
echo "--- Frontend Pages ---"
check "Homepage" "$BASE_URL/"
check_contains "Homepage has title" "$BASE_URL/" "Chartora"

echo ""
echo "--- SEO Files ---"
check "Sitemap" "$BASE_URL/sitemap.xml"
check "Robots.txt" "$BASE_URL/robots.txt"

echo ""
echo "--- Security Headers ---"
headers=$(curl -s -I --max-time 10 "$BASE_URL/" || echo "")
if echo "$headers" | grep -qi "strict-transport-security"; then
    echo "  PASS: HSTS header present"
    PASS=$((PASS + 1))
else
    echo "  WARN: HSTS header missing (OK if HTTP-only dev)"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
