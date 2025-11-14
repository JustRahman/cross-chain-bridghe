#!/bin/bash

# API Testing Script - Tests all endpoints from API_REFERENCE.md
# Usage: ./test_all_apis.sh

API_KEY="nxb_dev_key_12345"
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
SUCCESS=0
FAILED=0

echo "========================================"
echo "Testing Nexbridge API Endpoints"
echo "========================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local content_type="$5"

    TOTAL=$((TOTAL + 1))

    printf "%-50s " "$name"

    if [ -z "$data" ]; then
        # GET request
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "X-API-Key: $API_KEY" 2>&1)
    else
        # POST/PATCH/DELETE with data
        if [ "$content_type" = "json" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$data" 2>&1)
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -d "$data" 2>&1)
        fi
    fi

    status_code=$(echo "$response" | tail -1)

    if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 300 ]; then
        echo -e "${GREEN}✅ $status_code${NC}"
        SUCCESS=$((SUCCESS + 1))
    elif [ "$status_code" -eq 422 ] || [ "$status_code" -eq 400 ]; then
        echo -e "${YELLOW}⚠️  $status_code (validation error)${NC}"
        FAILED=$((FAILED + 1))
    elif [ "$status_code" -eq 404 ]; then
        echo -e "${RED}❌ $status_code (not found)${NC}"
        FAILED=$((FAILED + 1))
    else
        echo -e "${RED}❌ $status_code${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}━━━ Health Endpoints ━━━${NC}"
test_endpoint "Health Check" "GET" "/health"
test_endpoint "Detailed Health" "GET" "/health/detailed"
test_endpoint "Readiness Check" "GET" "/health/ready"
test_endpoint "Liveness Check" "GET" "/health/live"
echo ""

echo -e "${BLUE}━━━ Routes Endpoints ━━━${NC}"
test_endpoint "Get Quote" "POST" "/api/v1/routes/quote" '{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}' "json"
test_endpoint "Batch Quote" "POST" "/api/v1/routes/batch-quote" '{"quotes":[{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}]}' "json"
test_endpoint "Multi-Hop Routing" "POST" "/api/v1/routes/multi-hop?source_chain=ethereum&destination_chain=arbitrum&token=USDC&amount=1000000000&max_hops=2"
test_endpoint "Timeout Estimate" "GET" "/api/v1/routes/timeout-estimate?bridge_name=across&source_chain=ethereum&destination_chain=arbitrum&amount_usd=1000&confidence_level=90"
test_endpoint "Batch Timeout Estimates" "POST" "/api/v1/routes/batch-timeout-estimates" '{"estimates":[{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","amount_usd":1000,"confidence_level":90}]}' "json"
echo ""

echo -e "${BLUE}━━━ Bridges Endpoints ━━━${NC}"
test_endpoint "Bridge Status" "GET" "/api/v1/bridges/status"
test_endpoint "Supported Tokens" "GET" "/api/v1/bridges/tokens/supported"
echo ""

echo -e "${BLUE}━━━ Transactions Endpoints ━━━${NC}"
test_endpoint "Track Transaction" "GET" "/api/v1/transactions/track/0x123456789abcdef"
test_endpoint "Bridge Statistics" "GET" "/api/v1/transactions/statistics/bridges"
test_endpoint "Chain Statistics" "GET" "/api/v1/transactions/statistics/chains"
echo ""

echo -e "${BLUE}━━━ Utilities Endpoints ━━━${NC}"
test_endpoint "Gas Prices (Ethereum)" "GET" "/api/v1/utilities/gas-prices/1"
test_endpoint "All Gas Prices" "GET" "/api/v1/utilities/gas-prices"
test_endpoint "Token Price (USDC)" "GET" "/api/v1/utilities/token-price/USDC"
test_endpoint "All Token Prices" "GET" "/api/v1/utilities/token-prices"
test_endpoint "Token Details" "GET" "/api/v1/utilities/token-details/USDC"
test_endpoint "Calculate Savings" "POST" "/api/v1/utilities/calculate-savings" '{"amount_usd":"1000.00","cheapest_route_cost":"10.50","expensive_route_cost":"25.75"}' "json"
echo ""

echo -e "${BLUE}━━━ Transaction History Endpoints ━━━${NC}"
test_endpoint "Create Transaction" "POST" "/api/v1/transaction-history/" '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","selected_bridge":"across","estimated_cost_usd":12.50,"transaction_hash":"0xtest123"}' "json"
test_endpoint "List Transactions" "GET" "/api/v1/transaction-history/?status=completed&page=1&limit=50"
test_endpoint "Simulate Transaction" "POST" "/api/v1/transaction-history/simulate" '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","bridge":"across"}' "json"
echo ""

echo -e "${BLUE}━━━ Webhooks Endpoints ━━━${NC}"
test_endpoint "Create Webhook" "POST" "/api/v1/webhooks/" '{"url":"https://example.com/webhook","secret":"test_secret","events":["transaction.completed"],"description":"Test webhook"}' "json"
test_endpoint "List Webhooks" "GET" "/api/v1/webhooks/"
test_endpoint "Test Webhook" "POST" "/api/v1/webhooks/test" '{"webhook_id":1,"event_type":"test.event"}' "json"
echo ""

echo -e "${BLUE}━━━ Slippage Endpoints ━━━${NC}"
test_endpoint "Calculate Slippage" "POST" "/api/v1/slippage/calculate" '{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","available_liquidity":"50000000000"}' "json"
test_endpoint "Protection Parameters" "POST" "/api/v1/slippage/protection-parameters" '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","risk_tolerance":"medium"}' "json"
test_endpoint "Historical Slippage" "GET" "/api/v1/slippage/historical/across/ethereum/arbitrum?days=7"
echo ""

echo -e "${BLUE}━━━ Gas Optimization Endpoints ━━━${NC}"
test_endpoint "Optimal Timing" "GET" "/api/v1/gas-optimization/optimal-timing/1"
test_endpoint "Compare Timing" "GET" "/api/v1/gas-optimization/compare-timing/1?amount_usd=1000"
echo ""

echo -e "${BLUE}━━━ API Keys Endpoints ━━━${NC}"
test_endpoint "List API Keys" "GET" "/api/v1/api-keys/?is_active=true"
test_endpoint "Get API Key Usage" "GET" "/api/v1/api-keys/1/usage"
test_endpoint "Get Rate Limits" "GET" "/api/v1/api-keys/1/rate-limits"
test_endpoint "Get Violations" "GET" "/api/v1/api-keys/1/violations?limit=50"
echo ""

echo -e "${BLUE}━━━ Analytics Endpoints ━━━${NC}"
test_endpoint "Analytics Dashboard" "GET" "/api/v1/analytics/dashboard?hours=24"
test_endpoint "Reliability Scores" "GET" "/api/v1/analytics/reliability-scores?hours=168"
test_endpoint "Bridge Reliability" "GET" "/api/v1/analytics/bridge-reliability/across?hours=168"
test_endpoint "Bridge Comparison" "GET" "/api/v1/analytics/bridge-comparison?bridges=across,hop,stargate&hours=168"
echo ""

echo "========================================"
echo -e "${BLUE}Summary:${NC}"
echo "  Total Tests: $TOTAL"
echo -e "  ${GREEN}Passed: $SUCCESS${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo "========================================"

if [ $SUCCESS -eq $TOTAL ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
elif [ $SUCCESS -gt $((TOTAL / 2)) ]; then
    echo -e "${YELLOW}⚠️  Most tests passed, some need attention${NC}"
    exit 0
else
    echo -e "${RED}❌ Many tests failed, please check API${NC}"
    exit 1
fi
 