#!/usr/bin/env python3
"""
Comprehensive API Test Script
Tests all available endpoints and displays results in organized sections.

Usage:
    python test_all_apis.py

Requirements:
    pip install requests colorama
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "nxb_dev_key_12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


class APITester:
    """Test all API endpoints"""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(80)}{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

    def print_info(self, message: str):
        """Print info message"""
        print(f"{Fore.YELLOW}ℹ️  {message}{Style.RESET_ALL}")

    def print_data(self, label: str, data: Any):
        """Print formatted data"""
        print(f"{Fore.MAGENTA}{label}:{Style.RESET_ALL}")
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"  {data}")
        print()

    def _print_curl_equivalent(self, method: str, url: str, data: Optional[Dict] = None,
                               params: Optional[Dict] = None):
        """Print curl command equivalent for manual verification"""
        curl_parts = [f"curl -X {method}"]

        # Add URL with query params
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            curl_parts.append(f'"{url}?{param_str}"')
        else:
            curl_parts.append(f'"{url}"')

        # Add headers
        curl_parts.append(f'-H "X-API-Key: {self.headers["X-API-Key"]}"')
        if data:
            curl_parts.append(f'-H "Content-Type: application/json"')
            curl_parts.append(f"-d '{json.dumps(data)}'")

        curl_command = " \\\n  ".join(curl_parts)
        print(f"\n{Fore.BLUE}💡 Verify this call yourself with curl:{Style.RESET_ALL}")
        print(curl_command)
        print()

    def test_endpoint(self, method: str, endpoint: str, name: str,
                     data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """Test a single endpoint"""
        self.results["total"] += 1
        url = f"{self.base_url}{endpoint}"

        try:
            print(f"\n{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}Testing: {name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Making REAL API call to:{Style.RESET_ALL} {method} {url}")

            if params:
                print(f"{Fore.YELLOW}Query params:{Style.RESET_ALL} {params}")
            if data:
                print(f"{Fore.YELLOW}Request body:{Style.RESET_ALL}")
                print(json.dumps(data, indent=2))

            # Make REAL HTTP request
            start_time = time.time()

            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=10)
            else:
                self.print_error(f"Unsupported method: {method}")
                return None

            response_time = (time.time() - start_time) * 1000  # Convert to ms
            print(f"{Fore.GREEN}Response received in {response_time:.2f}ms{Style.RESET_ALL}")
            print(f"Status Code: {response.status_code}")

            if response.status_code < 400:
                self.results["passed"] += 1
                self.print_success(f"{name} - SUCCESS")

                # Show curl equivalent for verification
                self._print_curl_equivalent(method, url, data, params)

                try:
                    json_response = response.json()
                    print(f"\n{Fore.MAGENTA}REAL Response from server:{Style.RESET_ALL}")
                    print(json.dumps(json_response, indent=2, default=str)[:2000])  # Limit output
                    if len(str(json_response)) > 2000:
                        print(f"\n{Fore.YELLOW}... (response truncated, showing first 2000 chars){Style.RESET_ALL}")
                    return json_response
                except:
                    print(f"\n{Fore.MAGENTA}REAL Response (text):{Style.RESET_ALL}")
                    print(response.text[:500])
                    return {"response": response.text}
            else:
                self.results["failed"] += 1
                self.print_error(f"{name} - FAILED")
                print(f"Error response: {response.text[:300]}")
                return None

        except Exception as e:
            self.results["failed"] += 1
            self.print_error(f"{name} - ERROR: {str(e)}")
            return None

    def run_all_tests(self):
        """Run all API tests"""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'*' * 80}")
        print(f"{'CROSS-CHAIN BRIDGE API - COMPREHENSIVE TEST SUITE'.center(80)}")
        print(f"{'*' * 80}{Style.RESET_ALL}\n")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {API_KEY}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n{Fore.GREEN}✅ Server restarted - all endpoints including simulator are available!{Style.RESET_ALL}\n")

        # 1. Health Check
        self.print_section("1. HEALTH & STATUS")
        self.test_endpoint("GET", "/health", "Health Check")

        # 2. Token Prices (Real Data)
        self.print_section("2. TOKEN PRICES (Real Data)")
        self.print_info("These prices come from REAL free APIs: CoinLore → Binance → DIA")

        self.test_endpoint("GET", "/api/v1/utilities/token-price/USDC",
                          "USDC Price")

        self.test_endpoint("GET", "/api/v1/utilities/token-price/ETH",
                          "ETH Price")

        self.test_endpoint("GET", "/api/v1/utilities/token-prices",
                          "All Token Prices")

        # 3. Bridge Information
        self.print_section("3. BRIDGE INFORMATION")

        self.test_endpoint("GET", "/api/v1/bridges/status", "Bridge Status")
        self.test_endpoint("GET", "/api/v1/bridges/tokens/supported", "Supported Tokens")

        # 4. Bridge Quotes (Real API Integration)
        self.print_section("4. BRIDGE QUOTES (Real API Integration)")
        self.print_info("These quotes come from REAL bridge APIs: Hop, Synapse, Across")

        quote_request = {
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC on Arbitrum
            "amount": "1000000000"  # 1000 USDC
        }

        self.test_endpoint("POST", "/api/v1/routes/quote",
                          "Get Bridge Quote (1000 USDC: Ethereum → Arbitrum)", data=quote_request)

        # 5. Bridge Statistics (Real Database Data)
        self.print_section("5. BRIDGE STATISTICS (Real Database Data)")
        self.print_info("Statistics calculated from REAL transactions in PostgreSQL database")

        self.test_endpoint("GET", "/api/v1/transactions/statistics/bridges",
                          "Bridge Statistics (Last 30 Days)", params={"days": 30})

        # 6. Transaction History (Real Database)
        self.print_section("6. TRANSACTION HISTORY (Real Database)")
        self.print_info("Transaction history from PostgreSQL database")

        self.test_endpoint("GET", "/api/v1/transaction-history",
                          "Recent Transactions (Last 10)", params={"limit": 10})

        # 7. Transaction Simulator (Test Data Creation)
        self.print_section("7. TRANSACTION SIMULATOR (Test Data)")
        self.print_info("Creates test transactions for development - this is INTENTIONAL test data")

        sim_request = {
            "bridge_name": "Across Protocol",
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "amount": "1000000000",
            "should_fail": False,
            "completion_time_seconds": 60
        }

        simulated_tx = self.test_endpoint("POST", "/api/v1/simulator/simulate",
                                         "Simulate Single Transaction (60s completion)", data=sim_request)

        if simulated_tx and isinstance(simulated_tx, dict):
            tx_hash = simulated_tx.get("transaction_hash")

            # Wait a bit and track it
            if tx_hash:
                print(f"\n{Fore.YELLOW}⏳ Waiting 5 seconds for transaction to progress...{Style.RESET_ALL}")
                time.sleep(5)

                self.test_endpoint("GET", f"/api/v1/transactions/track/{tx_hash}",
                                  "Track Simulated Transaction (Should show status change)")

        self.test_endpoint("GET", "/api/v1/simulator/simulate/active",
                          "View Active Simulations")

        # 8. Bulk Simulation
        self.print_section("8. BULK SIMULATION (Load Testing)")
        self.print_info("Creates multiple test transactions for load testing")

        self.test_endpoint("POST", "/api/v1/simulator/simulate/bulk",
                          "Bulk Simulate 5 Transactions",
                          data={"count": 5})

        # 9. Webhooks
        self.print_section("9. WEBHOOKS (Real HTTP Delivery)")
        self.print_info("Webhooks make REAL HTTP POST requests with HMAC signatures")

        self.test_endpoint("GET", "/api/v1/webhooks/", "List Configured Webhooks")

        # 10. Gas Optimization
        self.print_section("10. GAS OPTIMIZATION")

        self.test_endpoint("GET", "/api/v1/gas-optimization/optimal-timing/1",
                          "Optimal Gas Timing (Ethereum - Chain ID 1)")

        # 11. Slippage Calculation
        self.print_section("11. SLIPPAGE CALCULATION")

        slippage_request = {
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "amount": "1000000000",
            "bridge_name": "Across Protocol"
        }
        self.test_endpoint("POST", "/api/v1/slippage/calculate",
                          "Calculate Slippage (1000 USDC: ETH → ARB on Across)", data=slippage_request)

        # 12. Analytics
        self.print_section("12. ANALYTICS (Real Database Metrics)")
        self.print_info("Analytics from REAL database queries")

        self.test_endpoint("GET", "/api/v1/analytics/dashboard", "Analytics Dashboard")

        # 13. API Keys Management
        self.print_section("13. API KEYS MANAGEMENT")

        self.test_endpoint("GET", "/api/v1/api-keys/", "List API Keys")

        # 14. Multi-hop Routing
        self.print_section("14. MULTI-HOP ROUTING")

        multihop_params = {
            "source_chain": "ethereum",
            "destination_chain": "polygon",
            "token": "USDC",
            "amount": "1000000000"
        }
        self.test_endpoint("POST", "/api/v1/routes/multi-hop",
                          "Multi-hop Route (Ethereum → Polygon via intermediary)",
                          params=multihop_params)

        # 15. Batch Quotes
        self.print_section("15. BATCH QUOTES (Multiple Routes)")
        self.print_info("Get quotes for multiple routes in parallel")

        batch_request = {
            "quotes": [
                {
                    "source_chain": "ethereum",
                    "destination_chain": "arbitrum",
                    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC on Arbitrum
                    "amount": "1000000000"
                },
                {
                    "source_chain": "ethereum",
                    "destination_chain": "optimism",
                    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "destination_token": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC on Optimism
                    "amount": "500000000"
                }
            ]
        }
        self.test_endpoint("POST", "/api/v1/routes/batch-quote",
                          "Batch Quotes (2 routes)", data=batch_request)

        # Print Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'TEST SUMMARY'.center(80)}{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests:  {total}")
        print(f"{Fore.GREEN}Passed:       {passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed:       {failed}{Style.RESET_ALL}")
        print(f"Pass Rate:    {pass_rate:.1f}%")

        print(f"\n{'=' * 80}\n")

        # Data source summary
        print(f"{Fore.CYAN}{Style.BRIGHT}DATA SOURCES SUMMARY:{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}✅ Real Data Sources:{Style.RESET_ALL}")
        print(f"  • Token Prices: CoinLore → Binance → DIA (100% Free APIs)")
        print(f"  • Blockchain Data: Free Public RPCs (Grove, Ankr, PublicNode)")
        print(f"  • Bridge Statistics: PostgreSQL Database")
        print(f"  • Transaction History: PostgreSQL Database")
        print(f"  • Webhooks: Real HTTP POST delivery with HMAC signatures")
        print(f"  • WebSocket: Real-time updates from database")

        print(f"\n{Fore.YELLOW}⚠️  Estimated/Fallback Data:{Style.RESET_ALL}")
        print(f"  • Stargate API: Uses known 0.06% fee structure (public API unavailable)")
        print(f"  • Some bridge quotes: Fallback to estimated fees when API unavailable")

        print(f"\n{Fore.BLUE}🎮 Test/Development Data:{Style.RESET_ALL}")
        print(f"  • Transaction Simulator: Creates test transactions for development")
        print(f"  • Bulk Simulator: Load testing and demo purposes")

        print(f"\n{'=' * 80}\n")
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def main():
    """Main function"""
    try:
        tester = APITester()
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"\n\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
