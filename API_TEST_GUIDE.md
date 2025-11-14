# API Testing Guide

## Quick Start

Test all APIs with one command:

```bash
# Install dependencies
pip install requests colorama

# Run test script
python test_all_apis.py
```

## What Gets Tested

The script tests all available APIs in organized sections:

### 1. **Health & Status**
- ✅ Health check endpoint
- Server status and uptime

### 2. **Token Prices** (Real Data)
- ✅ Single token price (CoinLore → Binance → DIA)
- ✅ Multiple token prices
- **Data Source**: 100% FREE public APIs, no mock data

### 3. **Bridge Information**
- ✅ List all available bridges
- ✅ Supported chains
- 10 bridges: Across, Hop, Stargate, Synapse, Celer, Connext, Orbiter, LayerZero, deBridge, Wormhole

### 4. **Bridge Quotes** (Real API Integration)
- ✅ Get quotes from bridge APIs
- **Hop Protocol**: Real API integration
- **Stargate**: Estimated fees (0.06% known structure)
- **Synapse**: Real API integration
- **Across**: Real API integration

### 5. **Bridge Statistics** (Real Database)
- ✅ Success rates from actual transactions
- ✅ Average completion times
- ✅ Total volume
- **Data Source**: PostgreSQL database

### 6. **Transaction History** (Real Database)
- ✅ Recent transactions
- ✅ Filter by status, bridge, chain
- **Data Source**: PostgreSQL database

### 7. **Transaction Simulator** (Test Data)
- ✅ Simulate single transaction
- ✅ Track simulated transaction
- ✅ View active simulations
- **Purpose**: Testing and development

### 8. **Bulk Simulation** (Load Testing)
- ✅ Create multiple transactions at once
- ✅ Stress test the system
- **Purpose**: Load testing

### 9. **Webhooks** (Real HTTP Delivery)
- ✅ List configured webhooks
- ✅ Real HTTP POST with HMAC signatures
- **Data Source**: Real webhook deliveries

### 10. **Gas Optimization**
- ✅ Gas price estimates
- ✅ Transaction cost calculations

### 11. **Slippage Calculation**
- ✅ Calculate slippage for bridge transfers
- ✅ Price impact estimation

### 12. **Analytics** (Real Database Metrics)
- ✅ Usage statistics
- ✅ Performance metrics
- **Data Source**: PostgreSQL database

### 13. **API Keys Management**
- ✅ API key usage statistics
- ✅ Rate limit tracking

### 14. **Multi-hop Routing**
- ✅ Find optimal multi-hop routes
- ✅ Compare direct vs. indirect routes

### 15. **Batch Quotes**
- ✅ Get quotes for multiple routes simultaneously
- ✅ Parallel quote fetching

## Sample Output

```
================================================================================
                 CROSS-CHAIN BRIDGE API - COMPREHENSIVE TEST SUITE
================================================================================

Base URL: http://localhost:8000
API Key: nxb_dev_key_12345
Started: 2025-11-12 10:30:00

================================================================================
                              1. HEALTH & STATUS
================================================================================

Testing: Health Check
  GET /health
  Status: 200
✅ Health Check - SUCCESS

Health Status:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-12T10:30:00Z"
}

================================================================================
                        2. TOKEN PRICES (Real Data)
================================================================================

Testing: USDC Price
  GET /api/v1/utilities/token-price?symbol=USDC
  Status: 200
✅ USDC Price - SUCCESS

USDC Price (Real from CoinLore/Binance/DIA):
{
  "symbol": "USDC",
  "price_usd": 0.9998,
  "source": "coinlore",
  "timestamp": "2025-11-12T10:30:05Z"
}

...

================================================================================
                                 TEST SUMMARY
================================================================================

Total Tests:  25
Passed:       23
Failed:       2
Pass Rate:    92.0%

================================================================================

DATA SOURCES SUMMARY:

✅ Real Data Sources:
  • Token Prices: CoinLore → Binance → DIA (100% Free APIs)
  • Blockchain Data: Free Public RPCs (Grove, Ankr, PublicNode)
  • Bridge Statistics: PostgreSQL Database
  • Transaction History: PostgreSQL Database
  • Webhooks: Real HTTP POST delivery with HMAC signatures
  • WebSocket: Real-time updates from database

⚠️  Estimated/Fallback Data:
  • Stargate API: Uses known 0.06% fee structure (public API unavailable)
  • Some bridge quotes: Fallback to estimated fees when API unavailable

🎮 Test/Development Data:
  • Transaction Simulator: Creates test transactions for development
  • Bulk Simulator: Load testing and demo purposes
```

## Configuration

Edit the script to change settings:

```python
# At the top of test_all_apis.py
BASE_URL = "http://localhost:8000"  # Change if using different host
API_KEY = "nxb_dev_key_12345"       # Your API key
```

## Prerequisites

1. **API Server Running:**
   ```bash
   # Start with Docker
   docker-compose up -d

   # OR start directly
   python app/main.py
   ```

2. **Database Seeded (Recommended):**
   ```bash
   python scripts/seed_database.py
   ```
   This creates sample transactions for statistics and history endpoints.

3. **Dependencies:**
   ```bash
   pip install requests colorama
   ```

## Run Without Colorama

If you don't want to install colorama:

```bash
# Remove colorama import and color codes
sed 's/Fore\.[A-Z]*//g; s/Style\.[A-Z_]*//g' test_all_apis.py > test_simple.py
python test_simple.py
```

Or just run with errors ignored:
```bash
python test_all_apis.py 2>/dev/null
```

## Common Issues

### Connection Refused
```
❌ Health Check - ERROR: Connection refused
```
**Solution**: Start the API server first:
```bash
docker-compose up -d
# OR
python app/main.py
```

### No Transactions Found
```
✅ Transaction History - SUCCESS
Transaction History (Database):
{
  "transactions": [],
  "total": 0
}
```
**Solution**: Seed the database:
```bash
python scripts/seed_database.py
```

### API Key Invalid
```
❌ Bridge Statistics - FAILED: Invalid API key
```
**Solution**: Update API_KEY in the script or create a valid key.

## Advanced Usage

### Test Specific Section

Modify the script to test only specific endpoints:

```python
# Comment out sections you don't want to test
# self.print_section("1. HEALTH & STATUS")
# health = self.test_endpoint("GET", "/health", "Health Check")
```

### Save Results to File

```bash
python test_all_apis.py > api_test_results.txt 2>&1
```

### Run Continuously

```bash
# Test every 60 seconds
watch -n 60 python test_all_apis.py
```

### Integration with CI/CD

```yaml
# .github/workflows/api-tests.yml
- name: Test APIs
  run: |
    pip install requests colorama
    python test_all_apis.py
```

## What's Real vs. Mock?

### 100% Real Data ✅
- **Token Prices**: CoinLore, Binance, DIA APIs
- **Blockchain Transactions**: Public RPC nodes
- **Database Statistics**: PostgreSQL queries
- **Webhook Deliveries**: Actual HTTP requests
- **WebSocket Updates**: Real-time from DB

### Estimated Data ⚠️
- **Stargate Quotes**: Uses known fee structure (API not public)
- **Fallback Quotes**: When primary API unavailable

### Test Data 🎮
- **Transaction Simulator**: Creates test transactions
- **Bulk Simulator**: Load testing tool

**Bottom Line**: All production endpoints use real data from free public APIs and your database. Only the simulator creates test data, which is its purpose.

## Next Steps

After running tests:

1. **Check failed tests** - Fix any configuration issues
2. **Review data sources** - Confirm all real APIs are working
3. **Test WebSocket** - Use dashboard for real-time updates
4. **Configure webhooks** - Set up webhook.site for testing
5. **Run load tests** - Use bulk simulator

## Support

If tests fail:
1. Check `docker-compose logs app`
2. Verify database connection
3. Confirm API server is running
4. Review firewall/network settings

Happy testing! 🚀
