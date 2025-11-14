#!/bin/bash

# Test All APIs and Show Outputs in Terminal
# Run this script to see all API calls and their responses

API_KEY="nxb_dev_key_12345"
BASE_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to display section header
section_header() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to test API endpoint
test_api() {
    local title="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local content_type="$5"

    echo -e "${CYAN}${BOLD}━━━ $title ━━━${NC}"
    echo ""

    # Show request
    echo -e "${YELLOW}Request:${NC}"
    if [ -z "$data" ]; then
        echo "curl -X $method \"$BASE_URL$endpoint\" \\"
        echo "  -H \"X-API-Key: $API_KEY\""
    else
        if [ "$content_type" = "json" ]; then
            echo "curl -X $method \"$BASE_URL$endpoint\" \\"
            echo "  -H \"X-API-Key: $API_KEY\" \\"
            echo "  -H \"Content-Type: application/json\" \\"
            echo "  -d '$data'"
        else
            echo "curl -X $method \"$BASE_URL$endpoint\" \\"
            echo "  -H \"X-API-Key: $API_KEY\" \\"
            echo "  -d '$data'"
        fi
    fi

    echo ""
    echo -e "${GREEN}Response:${NC}"

    # Execute curl and show response
    if [ -z "$data" ]; then
        response=$(curl -s -X "$method" "$BASE_URL$endpoint" -H "X-API-Key: $API_KEY" 2>&1)
    else
        if [ "$content_type" = "json" ]; then
            response=$(curl -s -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$data" 2>&1)
        else
            response=$(curl -s -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -d "$data" 2>&1)
        fi
    fi

    # Pretty print JSON or show raw response
    if echo "$response" | python3 -m json.tool 2>/dev/null; then
        :
    else
        echo "$response"
    fi

    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
    echo ""

    # Pause to read (optional - comment out for faster execution)
    # read -p "Press Enter to continue..."
}

clear
echo -e "${BOLD}${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           NEXBRIDGE API - COMPLETE TEST SUITE                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "API Base URL: $BASE_URL"
echo "API Key: $API_KEY"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop at any time${NC}"
echo ""
read -p "Press Enter to start testing..."

# ═══════════════════════════════════════════════════════════════
section_header "1. HEALTH ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Health Check" "GET" "/health"

test_api "Detailed Health" "GET" "/health/detailed"

test_api "Readiness Check" "GET" "/health/ready"

test_api "Liveness Check" "GET" "/health/live"

# ═══════════════════════════════════════════════════════════════
section_header "2. ROUTES ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Get Bridge Quotes" "POST" "/api/v1/routes/quote" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}' "json"

test_api "Batch Quote Requests" "POST" "/api/v1/routes/batch-quote" \
    '{"quotes":[{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}]}' "json"

test_api "Multi-Hop Routing" "POST" "/api/v1/routes/multi-hop?source_chain=ethereum&destination_chain=arbitrum&token=USDC&amount=1000000000&max_hops=2"

test_api "Timeout Estimate" "GET" \
    "/api/v1/routes/timeout-estimate?bridge_name=across&source_chain=ethereum&destination_chain=arbitrum&amount_usd=1000&confidence_level=90"

test_api "Batch Timeout Estimates" "POST" "/api/v1/routes/batch-timeout-estimates" \
    '[{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","amount_usd":1000,"confidence_level":90}]' "json"

# ═══════════════════════════════════════════════════════════════
section_header "3. BRIDGES ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Bridge Status" "GET" "/api/v1/bridges/status"

test_api "Supported Tokens" "GET" "/api/v1/bridges/tokens/supported"

# ═══════════════════════════════════════════════════════════════
section_header "4. TRANSACTIONS ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Track Transaction" "GET" "/api/v1/transactions/track/0x123456789abcdef"

test_api "Bridge Statistics" "GET" "/api/v1/transactions/statistics/bridges"

test_api "Chain Statistics" "GET" "/api/v1/transactions/statistics/chains"

# ═══════════════════════════════════════════════════════════════
section_header "5. UTILITIES ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Gas Prices (Ethereum)" "GET" "/api/v1/utilities/gas-prices/1"

test_api "All Gas Prices" "GET" "/api/v1/utilities/gas-prices"

test_api "Token Price (USDC)" "GET" "/api/v1/utilities/token-price/USDC"

test_api "All Token Prices" "GET" "/api/v1/utilities/token-prices"

test_api "Token Details" "GET" "/api/v1/utilities/token-details/USDC"

test_api "Calculate Savings" "POST" "/api/v1/utilities/calculate-savings" \
    '{"amount_usd":"1000.00","cheapest_route_cost":"10.50","expensive_route_cost":"25.75"}' "json"

# ═══════════════════════════════════════════════════════════════
section_header "6. TRANSACTION HISTORY ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Create Transaction" "POST" "/api/v1/transaction-history/" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","selected_bridge":"across","estimated_cost_usd":12.50,"estimated_time_minutes":5,"estimated_gas_cost":5.0,"transaction_hash":"0xtest123"}' "json"

test_api "List Transactions" "GET" "/api/v1/transaction-history/?page=1&limit=10"

test_api "Get Transaction by ID" "GET" "/api/v1/transaction-history/1"

test_api "Simulate Transaction" "POST" "/api/v1/transaction-history/simulate" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","bridge":"across"}' "json"

# ═══════════════════════════════════════════════════════════════
section_header "7. WEBHOOKS ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Create Webhook" "POST" "/api/v1/webhooks/" \
    '{"url":"https://example.com/webhook","secret":"test_secret","events":["transaction.completed"],"description":"Test webhook"}' "json"

test_api "List Webhooks" "GET" "/api/v1/webhooks/"

test_api "Get Webhook Details" "GET" "/api/v1/webhooks/1"

test_api "Test Webhook" "POST" "/api/v1/webhooks/test" \
    '{"webhook_id":1,"event_type":"test.event"}' "json"

# ═══════════════════════════════════════════════════════════════
section_header "8. SLIPPAGE ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Calculate Slippage" "POST" "/api/v1/slippage/calculate" \
    '{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","available_liquidity":"50000000000"}' "json"

test_api "Protection Parameters" "POST" "/api/v1/slippage/protection-parameters" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","risk_tolerance":"medium"}' "json"

test_api "Historical Slippage" "GET" "/api/v1/slippage/historical/across/ethereum/arbitrum?days=7"

# ═══════════════════════════════════════════════════════════════
section_header "9. GAS OPTIMIZATION ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Optimal Timing" "GET" "/api/v1/gas-optimization/optimal-timing/1"

test_api "Compare Timing" "GET" "/api/v1/gas-optimization/compare-timing/1?amount_usd=1000"

# ═══════════════════════════════════════════════════════════════
section_header "10. API KEYS ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "List API Keys" "GET" "/api/v1/api-keys/?is_active=true"

test_api "Get API Key Details" "GET" "/api/v1/api-keys/1"

test_api "Get API Key Usage" "GET" "/api/v1/api-keys/1/usage"

test_api "Get Rate Limits" "GET" "/api/v1/api-keys/1/rate-limits"

test_api "Get Violations" "GET" "/api/v1/api-keys/1/violations?limit=10"

# ═══════════════════════════════════════════════════════════════
section_header "11. ANALYTICS ENDPOINTS"
# ═══════════════════════════════════════════════════════════════

test_api "Analytics Dashboard" "GET" "/api/v1/analytics/dashboard?hours=24"

test_api "Reliability Scores" "GET" "/api/v1/analytics/reliability-scores?hours=168"

test_api "Bridge Reliability (Across)" "GET" "/api/v1/analytics/bridge-reliability/across?hours=168"

test_api "Bridge Comparison" "GET" "/api/v1/analytics/bridge-comparison?bridges=across,hop,stargate&hours=168"

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    TESTING COMPLETED!                         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo "  • Tested all major API endpoints"
echo "  • API Key: $API_KEY"
echo "  • Base URL: $BASE_URL"
echo ""
echo -e "${YELLOW}Tip: Run with 'less' for easier scrolling:${NC}"
echo "  ./test_all_apis_with_output.sh | less -R"
echo ""
echo -e "${YELLOW}Or save to file:${NC}"
echo "  ./test_all_apis_with_output.sh > api_test_results.txt"
echo ""
