#!/bin/bash

API_URL="https://printer-automation-frontend-production.up.railway.app"
AUTH_TOKEN="$1"  # Pass token as first argument

if [ -z "$AUTH_TOKEN" ]; then
  echo "❌ Error: Auth token required"
  echo ""
  echo "Usage: ./test_phase1.sh YOUR_AUTH_TOKEN"
  echo ""
  echo "To get your token:"
  echo "  1. Login to https://printer-automation-frontend-production.up.railway.app"
  echo "  2. Open DevTools (F12)"
  echo "  3. Go to Application → Local Storage"
  echo "  4. Copy the 'access_token' value"
  echo ""
  exit 1
fi

echo "🧪 Phase 1 Optimization Tests"
echo "=============================="
echo "API URL: $API_URL"
echo "Testing started at: $(date)"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_endpoint() {
  local name=$1
  local url=$2
  local expected_first=$3
  local expected_cached=$4

  echo "📍 Testing: $name"
  echo "   URL: $url"
  echo "---"

  # First call (cache miss)
  echo "  🔵 First call (cache miss):"
  start=$(date +%s.%N)

  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" "$url")

  end=$(date +%s.%N)
  time1=$(echo "$end - $start" | bc)

  if [ "$http_code" -eq 200 ]; then
    echo -e "    ✅ Status: ${GREEN}$http_code OK${NC}"
  else
    echo -e "    ❌ Status: ${RED}$http_code ERROR${NC}"
  fi

  echo "    ⏱️  Time: ${time1}s"

  # Check if within expected range
  if (( $(echo "$time1 < $expected_first" | bc -l) )); then
    echo -e "    ${GREEN}✅ Excellent! Below expected time (${expected_first}s)${NC}"
  elif (( $(echo "$time1 < $expected_first * 1.5" | bc -l) )); then
    echo -e "    ${YELLOW}⚠️  Acceptable (expected: ${expected_first}s)${NC}"
  else
    echo -e "    ${RED}❌ Slower than expected (expected: ${expected_first}s)${NC}"
  fi

  sleep 3

  # Second call (cache hit)
  echo "  🟢 Second call (cache hit):"
  start=$(date +%s.%N)

  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" "$url")

  end=$(date +%s.%N)
  time2=$(echo "$end - $start" | bc)

  if [ "$http_code" -eq 200 ]; then
    echo -e "    ✅ Status: ${GREEN}$http_code OK${NC}"
  else
    echo -e "    ❌ Status: ${RED}$http_code ERROR${NC}"
  fi

  echo "    ⏱️  Time: ${time2}s"

  if (( $(echo "$time2 < $expected_cached" | bc -l) )); then
    echo -e "    ${GREEN}✅ Excellent! Fast cache response${NC}"
  else
    echo -e "    ${YELLOW}⚠️  Cache might not be working properly${NC}"
  fi

  # Calculate improvement
  improvement=$(echo "scale=2; (($time1 - $time2) / $time1) * 100" | bc)
  echo -e "  📊 Cache improvement: ${GREEN}${improvement}%${NC}"
  echo ""
}

# Health check first
echo "🏥 Health Check"
echo "---"
health_response=$(curl -s "$API_URL/health")
status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$status" = "healthy" ]; then
  echo -e "✅ API Status: ${GREEN}$status${NC}"
else
  echo -e "❌ API Status: ${RED}$status${NC}"
  echo "Response: $health_response"
  exit 1
fi

env=$(echo "$health_response" | grep -o '"environment":"[^"]*"' | cut -d'"' -f4)
version=$(echo "$health_response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
echo "   Environment: $env"
echo "   Version: $version"
echo ""

# Test authentication
echo "🔐 Authentication Check"
echo "---"
user_response=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/users/me")

http_code=$(echo "$user_response" | tail -n1)
user_data=$(echo "$user_response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
  echo -e "✅ Auth Status: ${GREEN}Valid${NC}"
  email=$(echo "$user_data" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
  echo "   User: $email"
else
  echo -e "❌ Auth Status: ${RED}Invalid (${http_code})${NC}"
  echo "   Please get a new auth token and try again"
  exit 1
fi
echo ""

# Test endpoints with expected times
echo "📊 Performance Tests"
echo "===================="
echo ""

# Dashboard Analytics (most impactful optimization)
test_endpoint "Dashboard Analytics 2025" \
  "$API_URL/dashboard/analytics?year=2025" \
  10 \
  0.5

# Top Sellers
test_endpoint "Top Sellers 2025" \
  "$API_URL/dashboard/top-sellers?year=2025" \
  10 \
  0.5

# Active Orders
test_endpoint "Active Orders" \
  "$API_URL/orders?was_paid=true&was_shipped=false&was_canceled=false" \
  2 \
  0.5

# All Orders
test_endpoint "All Orders (100 limit)" \
  "$API_URL/orders/all-orders?limit=100&offset=0" \
  3 \
  0.5

echo "✅ Testing Complete!"
echo "===================="
echo ""
echo "📋 Summary of Expected Improvements (Phase 1):"
echo "   • Analytics: 60-70% faster (first call: 15-30s → 5-10s)"
echo "   • Orders: 70-75% faster (first call: 4-5s → 1-2s)"
echo "   • Cache TTL: Extended 3-6x (longer cache retention)"
echo "   • Frontend: Reduced API calls by 50-70%"
echo ""
echo "🎯 Next Steps:"
echo "   1. Review results above"
echo "   2. If successful, monitor for 1-2 days"
echo "   3. Proceed to Phase 2 for 70-85% total improvement"
echo ""
echo "Testing completed at: $(date)"
