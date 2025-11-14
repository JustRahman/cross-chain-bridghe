# Nexbridge API Reference

Complete API endpoint reference with test examples.

## First Time Setup

**Need an API key?** See `GET_STARTED.md` for instructions.

**Your Active API Key**:
```bash
X-API-Key: nxb_dev_key_12345
```

**Create additional keys:**
```bash
# See GET_STARTED.md for full instructions
docker exec bridge_postgres psql -U bridge_user -d bridge_aggregator -c "
-- Insert new API key (development only)
"
```

---

## Health

### Check API Health
```bash
curl http://localhost:8000/health
```
Returns API status and database connectivity.

---

## Routes

### Get Bridge Quotes
```bash
curl -X POST http://localhost:8000/api/v1/routes/quote \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "USDC",
    "destination_token": "USDC",
    "amount": "1000000000"
  }'
```
Compare quotes from all 10 bridge protocols, returns sorted by cost.

### Multi-Hop Routing
```bash
curl -X POST "http://localhost:8000/api/v1/routes/multi-hop?source_chain=ethereum&destination_chain=arbitrum&token=USDC&amount=1000000000&max_hops=2" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Find optimal routes including paths through intermediate chains (e.g., ETH→Polygon→ARB).

### Estimate Transaction Timeout
```bash
curl "http://localhost:8000/api/v1/routes/timeout-estimate?bridge_name=across&source_chain=ethereum&destination_chain=arbitrum&amount_usd=1000&confidence_level=90" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Predict completion time with confidence intervals (P50, P75, P90, P95, P99).

### Batch Quote Requests
```bash
curl -X POST http://localhost:8000/api/v1/routes/batch-quote \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "quotes": [
      {"source_chain": "ethereum", "destination_chain": "arbitrum", "source_token": "USDC", "destination_token": "USDC", "amount": "1000000000"},
      {"source_chain": "polygon", "destination_chain": "optimism", "source_token": "USDC", "destination_token": "USDC", "amount": "500000000"}
    ]
  }'
```
Process up to 10 quote requests concurrently.

### Batch Timeout Estimates
```bash
curl -X POST http://localhost:8000/api/v1/routes/batch-timeout-estimates \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '[
    {"bridge_name": "across", "source_chain": "ethereum", "destination_chain": "arbitrum", "amount_usd": 1000, "confidence_level": 90},
    {"bridge_name": "hop", "source_chain": "polygon", "destination_chain": "optimism", "amount_usd": 500, "confidence_level": 95}
  ]'
```
Get timeout estimates for multiple routes in one request.

---

## Bridges

### List All Bridges
```bash
curl http://localhost:8000/api/v1/bridges
```
Returns all 10 integrated bridge protocols with metadata.

### Get Bridge Details
```bash
curl http://localhost:8000/api/v1/bridges/across
```
Get detailed information about a specific bridge (supported chains, features).

### Bridge Health Status
```bash
curl http://localhost:8000/api/v1/bridges/status \
  -H "X-API-Key: nxb_dev_key_12345"
```
Real-time health check of all bridge APIs.

---

## Transactions
 
### Track Transaction
```bash
curl http://localhost:8000/api/v1/transactions/track/0x123... \
  -H "X-API-Key: nxb_dev_key_12345"
```
Track transaction status by hash.

### Get Transaction Statistics
```bash
curl http://localhost:8000/api/v1/transactions/statistics \
  -H "X-API-Key: nxb_dev_key_12345"
```
Aggregate statistics across all transactions.

---

## Utilities

### Get Gas Prices
```bash
curl http://localhost:8000/api/v1/utilities/gas-prices?chain_id=1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Current gas prices (slow, standard, fast) for specified chain.

### Get All Gas Prices
```bash
curl http://localhost:8000/api/v1/utilities/gas-prices/all \
  -H "X-API-Key: nxb_dev_key_12345"
```
Gas prices for all supported chains.

### Get Token Prices
```bash
curl http://localhost:8000/api/v1/utilities/token-prices \
  -H "X-API-Key: nxb_dev_key_12345"
```
Real-time cryptocurrency prices from CoinGecko.

### Estimate Transaction Fees
```bash
curl -X POST http://localhost:8000/api/v1/utilities/estimate-fees \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "chain_id": 1,
    "transaction_type": "erc20_transfer",
    "gas_price_tier": "standard"
  }'
```
Estimate transaction fees in USD.

---

## Transaction History

### Create Transaction Record
```bash
curl -X POST http://localhost:8000/api/v1/transaction-history/ \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "token": "USDC",
    "amount": "1000000000",
    "selected_bridge": "across",
    "estimated_cost_usd": 12.50,
    "transaction_hash": "0x123..."
  }'
```
Store transaction in history database.

### Get Transaction by ID
```bash
curl http://localhost:8000/api/v1/transaction-history/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Retrieve transaction record by database ID.

### Get Transaction by Hash
```bash
curl http://localhost:8000/api/v1/transaction-history/hash/0x123... \
  -H "X-API-Key: nxb_dev_key_12345"
```
Retrieve transaction record by blockchain hash.

### List Transactions
```bash
curl "http://localhost:8000/api/v1/transaction-history/?status=completed&page=1&limit=50" \
  -H "X-API-Key: nxb_dev_key_12345"
```
List transactions with filters (status, bridge, chain, date range).

### Update Transaction
```bash
curl -X PATCH http://localhost:8000/api/v1/transaction-history/1 \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_cost_usd": 11.75,
    "actual_time_minutes": 4
  }'
```
Update transaction status and actual metrics.

### Simulate Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transaction-history/simulate \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "token": "USDC",
    "amount": "1000000000",
    "bridge": "across"
  }'
```
Simulate transaction with risk analysis and success probability.

---

## Webhooks

### Create Webhook
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/ \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "secret": "your_secret_key",
    "events": ["transaction.completed", "transaction.failed"],
    "description": "Production webhook"
  }'
```
Register webhook for event notifications with HMAC signature verification.

### List Webhooks
```bash
curl http://localhost:8000/api/v1/webhooks/ \
  -H "X-API-Key: nxb_dev_key_12345"
```
List all registered webhooks.

### Get Webhook Details
```bash
curl http://localhost:8000/api/v1/webhooks/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Get specific webhook configuration and statistics.

### Update Webhook
```bash
curl -X PATCH http://localhost:8000/api/v1/webhooks/1 \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```
Update webhook configuration or disable it.

### Delete Webhook
```bash
curl -X DELETE http://localhost:8000/api/v1/webhooks/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Permanently delete webhook.

### Test Webhook
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/test \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 1,
    "event_type": "test.event"
  }'
```
Send test event to verify webhook configuration.

### Get Webhook Deliveries
```bash
curl http://localhost:8000/api/v1/webhooks/1/deliveries?limit=50 \
  -H "X-API-Key: nxb_dev_key_12345"
```
View delivery history with success/failure status.

---

## Slippage

### Calculate Slippage
```bash
curl -X POST http://localhost:8000/api/v1/slippage/calculate \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "bridge_name": "across",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "token": "USDC",
    "amount": "1000000000",
    "available_liquidity": "50000000000"
  }'
```
Calculate slippage with risk assessment (low/medium/high).

### Get Protection Parameters
```bash
curl -X POST http://localhost:8000/api/v1/slippage/protection-parameters \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "token": "USDC",
    "amount": "1000000000",
    "risk_tolerance": "medium"
  }'
```
Get recommended slippage tolerance and minimum output amounts.

### Get Historical Slippage
```bash
curl "http://localhost:8000/api/v1/slippage/historical/across/ethereum/arbitrum?days=7" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Historical slippage data for bridge/chain pair.

---

## Gas Optimization

### Get Optimal Timing
```bash
curl http://localhost:8000/api/v1/gas-optimization/optimal-timing/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Best time to execute transaction based on 24h gas price patterns.

### Compare Timing Options
```bash
curl "http://localhost:8000/api/v1/gas-optimization/compare-timing/1?amount_usd=1000" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Compare executing now vs waiting for optimal time with savings calculation.

---

## API Keys

### Create API Key
```bash
curl -X POST http://localhost:8000/api/v1/api-keys/ \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "description": "Main production key",
    "user_email": "user@example.com",
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 5000,
    "rate_limit_per_day": 50000,
    "expires_days": 365
  }'
```
Generate new API key (returned once only - save it!).

### List API Keys
```bash
curl "http://localhost:8000/api/v1/api-keys/?is_active=true" \
  -H "X-API-Key: nxb_dev_key_12345"
```
List all API keys with optional filters.

### Get API Key Details
```bash
curl http://localhost:8000/api/v1/api-keys/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Get specific API key configuration.

### Update API Key
```bash
curl -X PATCH http://localhost:8000/api/v1/api-keys/1 \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "rate_limit_per_minute": 200,
    "is_active": true
  }'
```
Update API key settings.

### Revoke API Key
```bash
curl -X POST http://localhost:8000/api/v1/api-keys/1/revoke \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Security breach - key compromised"
  }'
```
Permanently revoke API key (cannot be reactivated).

### Delete API Key
```bash
curl -X DELETE http://localhost:8000/api/v1/api-keys/1 \
  -H "X-API-Key: nxb_dev_key_12345"
```
Permanently delete API key and all history.

### Get API Key Usage
```bash
curl http://localhost:8000/api/v1/api-keys/1/usage \
  -H "X-API-Key: nxb_dev_key_12345"
```
Detailed usage statistics, success rates, most used endpoints, recent errors.

### Get Rate Limit Status
```bash
curl http://localhost:8000/api/v1/api-keys/1/rate-limits \
  -H "X-API-Key: nxb_dev_key_12345"
```
Current rate limit usage (minute/hour/day) with remaining capacity.

### Reset Rate Limits
```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/1/rate-limits/reset?window=minute" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Reset rate limit counters (admin only, for testing).

### Get Rate Limit Violations
```bash
curl "http://localhost:8000/api/v1/api-keys/1/violations?limit=50" \
  -H "X-API-Key: nxb_dev_key_12345"
```
View recent rate limit violations.

---

## Analytics

### Get Analytics Dashboard
```bash
curl "http://localhost:8000/api/v1/analytics/dashboard?hours=24" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Comprehensive dashboard: system health, top endpoints, chain stats, bridge popularity, time series data.

### Get Reliability Scores
```bash
curl "http://localhost:8000/api/v1/analytics/reliability-scores?hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Reliability scores (0-100) for all bridges with cost/speed ratings.

### Get Bridge Reliability
```bash
curl "http://localhost:8000/api/v1/analytics/bridge-reliability/across?hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Detailed reliability analysis for specific bridge with component scores breakdown.

### Compare Bridges
```bash
curl "http://localhost:8000/api/v1/analytics/bridge-comparison?bridges=across,hop,stargate&hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```
Side-by-side comparison of multiple bridges with best choice recommendation.

---

## Quick Reference

**Base URL**: `http://localhost:8000`

**Authentication**: Include `X-API-Key` header with all requests (except /health)

**Common Query Parameters**:
- `hours` - Analysis period (1-720 hours)
- `page` - Pagination page number
- `limit` - Results per page
- `status` - Filter by status (pending/completed/failed)

**Response Codes**:
- `200` - Success
- `201` - Created
- `204` - No Content (delete success)
- `400` - Bad Request
- `401` - Unauthorized (missing/invalid API key)
- `403` - Forbidden (key revoked/expired/IP restricted)
- `404` - Not Found
- `429` - Rate Limit Exceeded (check Retry-After header)
- `500` - Internal Server Error

**Rate Limits**: Enforced per API key (default: 60/min, 1000/hour, 10000/day)

**Webhooks**: HMAC-SHA256 signature in `X-Webhook-Signature` header

**Documentation**: http://localhost:8000/docs
