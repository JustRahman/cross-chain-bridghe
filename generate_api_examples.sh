#!/bin/bash

# Generate API Examples with Real Outputs
# This script calls all API endpoints and captures their responses

API_KEY="nxb_dev_key_12345"
BASE_URL="http://localhost:8000"
OUTPUT_FILE="API_EXAMPLES_WITH_OUTPUT.md"

echo "# Nexbridge API - Complete Examples with Real Outputs" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "This document shows all API endpoints with actual request/response examples." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to add API example with output
add_api_example() {
    local title="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local content_type="$5"

    echo "## $title" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Request:**" >> "$OUTPUT_FILE"
    echo '```bash' >> "$OUTPUT_FILE"

    if [ -z "$data" ]; then
        echo "curl -X $method \"$BASE_URL$endpoint\" \\" >> "$OUTPUT_FILE"
        echo "  -H \"X-API-Key: $API_KEY\"" >> "$OUTPUT_FILE"
    else
        if [ "$content_type" = "json" ]; then
            echo "curl -X $method \"$BASE_URL$endpoint\" \\" >> "$OUTPUT_FILE"
            echo "  -H \"X-API-Key: $API_KEY\" \\" >> "$OUTPUT_FILE"
            echo "  -H \"Content-Type: application/json\" \\" >> "$OUTPUT_FILE"
            echo "  -d '$data'" >> "$OUTPUT_FILE"
        else
            echo "curl -X $method \"$BASE_URL$endpoint\" \\" >> "$OUTPUT_FILE"
            echo "  -H \"X-API-Key: $API_KEY\" \\" >> "$OUTPUT_FILE"
            echo "  -d '$data'" >> "$OUTPUT_FILE"
        fi
    fi

    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Response:**" >> "$OUTPUT_FILE"
    echo '```json' >> "$OUTPUT_FILE"

    # Execute the curl command and capture output
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

    # Pretty print JSON
    if echo "$response" | python3 -m json.tool >> "$OUTPUT_FILE" 2>/dev/null; then
        : # Success, JSON was formatted
    else
        echo "$response" >> "$OUTPUT_FILE"
    fi

    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

echo "Generating API examples..."

# Health Endpoints
echo "# 1. Health Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Health Check" "GET" "/health"
add_api_example "Detailed Health" "GET" "/health/detailed"
add_api_example "Readiness Check" "GET" "/health/ready"
add_api_example "Liveness Check" "GET" "/health/live"

# Routes Endpoints
echo "# 2. Routes Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Get Bridge Quotes" "POST" "/api/v1/routes/quote" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}' "json"

add_api_example "Batch Quote Requests" "POST" "/api/v1/routes/batch-quote" \
    '{"quotes":[{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}]}' "json"

add_api_example "Timeout Estimate" "GET" \
    "/api/v1/routes/timeout-estimate?bridge_name=across&source_chain=ethereum&destination_chain=arbitrum&amount_usd=1000&confidence_level=90"

add_api_example "Batch Timeout Estimates" "POST" "/api/v1/routes/batch-timeout-estimates" \
    '[{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","amount_usd":1000,"confidence_level":90}]' "json"

# Bridges Endpoints
echo "# 3. Bridges Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Bridge Status" "GET" "/api/v1/bridges/status"
add_api_example "Supported Tokens" "GET" "/api/v1/bridges/tokens/supported"

# Transactions Endpoints
echo "# 4. Transactions Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Track Transaction" "GET" "/api/v1/transactions/track/0x123456789abcdef"
add_api_example "Bridge Statistics" "GET" "/api/v1/transactions/statistics/bridges"
add_api_example "Chain Statistics" "GET" "/api/v1/transactions/statistics/chains"

# Utilities Endpoints
echo "# 5. Utilities Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Gas Prices (Ethereum)" "GET" "/api/v1/utilities/gas-prices/1"
add_api_example "All Gas Prices" "GET" "/api/v1/utilities/gas-prices"
add_api_example "Token Price (USDC)" "GET" "/api/v1/utilities/token-price/USDC"
add_api_example "All Token Prices" "GET" "/api/v1/utilities/token-prices"
add_api_example "Calculate Savings" "POST" "/api/v1/utilities/calculate-savings" \
    '{"amount_usd":"1000.00","cheapest_route_cost":"10.50","expensive_route_cost":"25.75"}' "json"

# Transaction History Endpoints
echo "# 6. Transaction History Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "List Transactions" "GET" "/api/v1/transaction-history/?page=1&limit=10"
add_api_example "Simulate Transaction" "POST" "/api/v1/transaction-history/simulate" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","bridge":"across"}' "json"

# Webhooks Endpoints
echo "# 7. Webhooks Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "List Webhooks" "GET" "/api/v1/webhooks/"

# Slippage Endpoints
echo "# 8. Slippage Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Calculate Slippage" "POST" "/api/v1/slippage/calculate" \
    '{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","available_liquidity":"50000000000"}' "json"

add_api_example "Protection Parameters" "POST" "/api/v1/slippage/protection-parameters" \
    '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","risk_tolerance":"medium"}' "json"

add_api_example "Historical Slippage" "GET" "/api/v1/slippage/historical/across/ethereum/arbitrum?days=7"

# Gas Optimization Endpoints
echo "# 9. Gas Optimization Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Optimal Timing" "GET" "/api/v1/gas-optimization/optimal-timing/1"
add_api_example "Compare Timing" "GET" "/api/v1/gas-optimization/compare-timing/1?amount_usd=1000"

# API Keys Endpoints
echo "# 10. API Keys Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "List API Keys" "GET" "/api/v1/api-keys/?is_active=true"
add_api_example "Get API Key Usage" "GET" "/api/v1/api-keys/1/usage"
add_api_example "Get Rate Limits" "GET" "/api/v1/api-keys/1/rate-limits"
add_api_example "Get Violations" "GET" "/api/v1/api-keys/1/violations?limit=10"

# Analytics Endpoints
echo "# 11. Analytics Endpoints" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_api_example "Analytics Dashboard" "GET" "/api/v1/analytics/dashboard?hours=24"
add_api_example "Reliability Scores" "GET" "/api/v1/analytics/reliability-scores?hours=168"
add_api_example "Bridge Reliability" "GET" "/api/v1/analytics/bridge-reliability/across?hours=168"
add_api_example "Bridge Comparison" "GET" "/api/v1/analytics/bridge-comparison?bridges=across,hop,stargate&hours=168"

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "This file contains real request/response examples for all $(grep -c "^## " "$OUTPUT_FILE") API endpoints." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**API Key Used:** \`$API_KEY\`" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**Base URL:** \`$BASE_URL\`" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"

echo "✅ API examples generated successfully!"
echo "📁 Output file: $OUTPUT_FILE"
