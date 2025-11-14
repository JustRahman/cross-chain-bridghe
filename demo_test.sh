#!/bin/bash

# Quick demo of the test script
API_KEY="nxb_dev_key_12345"
BASE_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

clear
echo -e "${BOLD}${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  NEXBRIDGE API TEST DEMO                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Test 1: Health Check
echo -e "${CYAN}${BOLD}━━━ Health Check ━━━${NC}"
echo ""
echo -e "${YELLOW}Request:${NC}"
echo "curl -X GET \"$BASE_URL/health\" \\"
echo "  -H \"X-API-Key: $API_KEY\""
echo ""
echo -e "${GREEN}Response:${NC}"
curl -s -X GET "$BASE_URL/health" -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo ""

# Test 2: Get Bridge Quotes
echo -e "${CYAN}${BOLD}━━━ Get Bridge Quotes ━━━${NC}"
echo ""
echo -e "${YELLOW}Request:${NC}"
echo "curl -X POST \"$BASE_URL/api/v1/routes/quote\" \\"
echo "  -H \"X-API-Key: $API_KEY\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"source_chain\":\"ethereum\",\"destination_chain\":\"arbitrum\",...}'"
echo ""
echo -e "${GREEN}Response (first 2 routes):${NC}"
curl -s -X POST "$BASE_URL/api/v1/routes/quote" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps({'routes': d['routes'][:2], 'total_routes': len(d['routes'])}, indent=2))"
echo ""
echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo ""

# Test 3: Bridge Status
echo -e "${CYAN}${BOLD}━━━ Bridge Status ━━━${NC}"
echo ""
echo -e "${YELLOW}Request:${NC}"
echo "curl \"$BASE_URL/api/v1/bridges/status\" \\"
echo "  -H \"X-API-Key: $API_KEY\""
echo ""
echo -e "${GREEN}Response (summary):${NC}"
curl -s "$BASE_URL/api/v1/bridges/status" -H "X-API-Key: $API_KEY" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps({'total_bridges': d['total_bridges'], 'healthy_bridges': d['healthy_bridges'], 'sample_bridge': d['bridges'][0]}, indent=2))"
echo ""
echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo ""

# Test 4: Analytics Dashboard
echo -e "${CYAN}${BOLD}━━━ Analytics Dashboard ━━━${NC}"
echo ""
echo -e "${YELLOW}Request:${NC}"
echo "curl \"$BASE_URL/api/v1/analytics/dashboard?hours=24\" \\"
echo "  -H \"X-API-Key: $API_KEY\""
echo ""
echo -e "${GREEN}Response (system health):${NC}"
curl -s "$BASE_URL/api/v1/analytics/dashboard?hours=24" -H "X-API-Key: $API_KEY" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps({'system_health': d['system_health']}, indent=2))"
echo ""
echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo ""

echo -e "${BOLD}${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     DEMO COMPLETE!                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}This was a quick demo showing 4 endpoints.${NC}"
echo ""
echo -e "${YELLOW}To test ALL endpoints (40+), run:${NC}"
echo "  ./test_all_apis_with_output.sh"
echo ""
echo -e "${YELLOW}Options:${NC}"
echo "  • View with pager:    ./test_all_apis_with_output.sh | less -R"
echo "  • Save to file:       ./test_all_apis_with_output.sh > results.txt"
echo "  • Run in background:  ./test_all_apis_with_output.sh &"
echo ""
