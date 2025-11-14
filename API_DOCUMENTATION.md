# Cross-Chain Bridge Aggregator API Documentation

## Overview

The Cross-Chain Bridge Aggregator API provides a unified interface to compare and select the best cross-chain bridge routes across multiple protocols. Currently integrated with 6 major bridge protocols:

- **Across Protocol** - Optimistic bridge with fast relayers
- **Stargate Finance** - LayerZero-powered unified liquidity
- **Hop Protocol** - AMM-based with bonder network
- **Connext** - Modular cross-chain protocol
- **Wormhole** - Generic messaging across 20+ chains
- **Synapse Protocol** - Swap and bridge in one transaction

## Base URL

```
http://localhost:8000
```

For production, replace with your actual domain.

## Authentication

All API endpoints require an API key in the request header:

```
X-API-Key: YOUR_API_KEY
```

### Getting an API Key

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "My Application"}'
```

**Response:**
```json
{
  "api_key": "sil2L8rsFyx_IRP8dBXEz5dHwN0IE2tdzCuxNgfYhtI",
  "name": "My Application",
  "created_at": "2025-11-10T12:00:00Z"
}
```

⚠️ **Important**: Save this API key - it will not be shown again!

---

## Endpoints

### 1. Health Check

Check if the API is operational.

**Endpoint:** `GET /health`

**Authentication:** None required

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00Z",
  "version": "1.0.0"
}
```

---

### 2. Get Bridge Status

Get real-time health status and performance metrics for all bridges.

**Endpoint:** `GET /api/v1/bridges/status`

**Authentication:** Required

**Example:**
```bash
curl http://localhost:8000/api/v1/bridges/status \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "bridges": [
    {
      "name": "Across Protocol",
      "protocol": "across",
      "is_healthy": true,
      "is_active": true,
      "success_rate": 97.5,
      "average_completion_time": 180,
      "uptime_percentage": 99.2,
      "last_health_check": "2025-11-10T12:00:00Z",
      "supported_chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"]
    }
  ],
  "total_bridges": 6,
  "healthy_bridges": 5,
  "checked_at": "2025-11-10T12:00:00Z"
}
```

---

### 3. Get Route Quotes

Get and compare quotes from all bridges for a specific route.

**Endpoint:** `POST /api/v1/routes/quote`

**Authentication:** Required

**Request Body:**
```json
{
  "source_chain": "ethereum",
  "destination_chain": "arbitrum",
  "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
  "amount": "100000000",
  "slippage_tolerance": "0.5",
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Parameters:**
- `source_chain` (string, required) - Source blockchain: ethereum, arbitrum, optimism, polygon, base
- `destination_chain` (string, required) - Destination blockchain
- `source_token` (string, required) - Source token contract address
- `destination_token` (string, required) - Destination token contract address
- `amount` (string, required) - Amount in smallest unit (e.g., 100000000 = 100 USDC with 6 decimals)
- `slippage_tolerance` (string, optional) - Max slippage tolerance (default: 0.5%)
- `user_address` (string, optional) - User's wallet address

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/routes/quote \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount": "100000000",
    "slippage_tolerance": "0.5"
  }'
```

**Response:**
```json
{
  "routes": [
    {
      "bridge_name": "Hop Protocol",
      "protocol": "hop",
      "route_type": "direct",
      "estimated_time_seconds": 240,
      "fee_breakdown": {
        "bridge_fee_usd": "0.08",
        "gas_cost_source_usd": "5.00",
        "gas_cost_destination_usd": "0.20",
        "total_cost_usd": "5.28",
        "slippage_percentage": "0.2"
      },
      "success_rate": "98.5",
      "steps": [
        {
          "action": "approve",
          "description": "Approve token spending"
        },
        {
          "action": "bridge",
          "description": "Bridge via AMM to arbitrum"
        }
      ],
      "requires_approval": true,
      "minimum_amount": "1000000",
      "maximum_amount": "1000000000000",
      "quote_id": "hop_1699632000"
    }
  ],
  "total_routes": 6,
  "best_by_cost": "hop",
  "best_by_speed": "across",
  "generated_at": "2025-11-10T12:00:00Z"
}
```

**Route Ranking:**
Routes are automatically sorted by a weighted score:
- **Cost (40%)** - Lower fees = better score
- **Speed (30%)** - Faster completion = better score
- **Reliability (20%)** - Higher success rate = better score
- **Liquidity (10%)** - Better liquidity = better score

---

### 4. Get Supported Tokens

Get list of supported tokens, optionally filtered by chain.

**Endpoint:** `GET /api/v1/bridges/tokens/supported`

**Authentication:** Required

**Query Parameters:**
- `chain` (string, optional) - Filter by chain name (ethereum, arbitrum, etc.)

**Example:**
```bash
curl "http://localhost:8000/api/v1/bridges/tokens/supported?chain=ethereum" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "tokens": [
    {
      "symbol": "USDC",
      "name": "USD Coin",
      "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "decimals": 6,
      "chain": "ethereum"
    },
    {
      "symbol": "USDT",
      "name": "Tether USD",
      "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
      "decimals": 6,
      "chain": "ethereum"
    }
  ],
  "total_tokens": 5
}
```

---

### 5. Track Transaction

Track the status of a cross-chain bridge transaction.

**Endpoint:** `GET /api/v1/transactions/track/{transaction_hash}`

**Authentication:** Required

**Example:**
```bash
curl http://localhost:8000/api/v1/transactions/track/0x1234567890abcdef \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "transaction": {
    "transaction_hash": "0x1234567890abcdef",
    "bridge_protocol": "across",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "status": "completed",
    "amount": "100000000",
    "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "created_at": "2025-11-10T11:55:00Z",
    "completed_at": "2025-11-10T11:58:00Z",
    "estimated_completion": null,
    "steps_completed": 4,
    "total_steps": 4,
    "error_message": null
  },
  "progress_percentage": 100.0,
  "current_step": "Transaction completed successfully"
}
```

**Transaction Statuses:**
- `pending` - Transaction in progress
- `completed` - Transaction successful
- `failed` - Transaction failed

---

### 6. Get Bridge Statistics

Get comprehensive performance statistics for all bridges.

**Endpoint:** `GET /api/v1/transactions/statistics/bridges`

**Authentication:** Required

**Query Parameters:**
- `days` (integer, optional) - Number of days for statistics (1-90, default: 7)

**Example:**
```bash
curl "http://localhost:8000/api/v1/transactions/statistics/bridges?days=30" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "statistics": [
    {
      "bridge_name": "Across Protocol",
      "protocol": "across",
      "total_transactions": 1000,
      "successful_transactions": 970,
      "failed_transactions": 30,
      "success_rate": "97.0",
      "average_completion_time": 240,
      "total_volume_usd": "5000000",
      "uptime_percentage": "98.5",
      "cheapest_route_count": 50,
      "fastest_route_count": 45
    }
  ],
  "total_transactions": 6900,
  "total_volume_usd": "37500000",
  "period_start": "2025-10-11T12:00:00Z",
  "period_end": "2025-11-10T12:00:00Z"
}
```

---

### 7. Get Chain Statistics

Get transaction statistics for all supported chains.

**Endpoint:** `GET /api/v1/transactions/statistics/chains`

**Authentication:** Required

**Example:**
```bash
curl http://localhost:8000/api/v1/transactions/statistics/chains \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "chains": [
    {
      "chain_name": "ethereum",
      "chain_id": 1,
      "outbound_transactions": 850,
      "inbound_transactions": 920,
      "total_volume_usd": "12500000",
      "most_popular_destination": "arbitrum",
      "average_transaction_size_usd": "15000"
    },
    {
      "chain_name": "arbitrum",
      "chain_id": 42161,
      "outbound_transactions": 720,
      "inbound_transactions": 850,
      "total_volume_usd": "8900000",
      "most_popular_destination": "ethereum",
      "average_transaction_size_usd": "12000"
    }
  ],
  "generated_at": "2025-11-10T12:00:00Z"
}
```

---

## Supported Chains

| Chain | Chain ID | Supported Bridges |
|-------|----------|-------------------|
| Ethereum | 1 | All (6) |
| Arbitrum | 42161 | All (6) |
| Optimism | 10 | All (6) |
| Polygon | 137 | All (6) |
| Base | 8453 | All (6) |

---

## Supported Tokens

Currently supported stablecoins:
- **USDC** - USD Coin (6 decimals)
- **USDT** - Tether USD (6 decimals)
- **DAI** - Dai Stablecoin (18 decimals)
- **WETH** - Wrapped Ether (18 decimals)

More tokens coming soon!

---

## Error Responses

All endpoints return standard HTTP status codes:

**Success (2xx):**
- `200 OK` - Request successful

**Client Errors (4xx):**
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded

**Server Errors (5xx):**
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

**Error Response Format:**
```json
{
  "detail": "Invalid API key"
}
```

---

## Rate Limits

- **Default:** 100 requests per minute per API key
- **Burst:** 10 requests per second

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699632060
```

---

## Best Practices

1. **Cache Quotes**: Bridge quotes are cached for 30 seconds. Don't refresh unnecessarily.

2. **Handle Timeouts**: Bridge API calls have a 3-second timeout. Some bridges may not respond in time.

3. **Check Bridge Health**: Before requesting quotes, check bridge status to avoid unhealthy bridges.

4. **Use Slippage Tolerance**: Set appropriate slippage (0.5-1%) to avoid failed transactions.

5. **Monitor Transactions**: Use the tracking endpoint to monitor transaction progress.

6. **Error Handling**: Always implement proper error handling for bridge failures.

---

## Integration Example (JavaScript)

```javascript
const API_KEY = 'YOUR_API_KEY';
const API_BASE = 'http://localhost:8000';

// Get best route quote
async function getBestRoute(sourceChain, destChain, token, amount) {
  const response = await fetch(`${API_BASE}/api/v1/routes/quote`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      source_chain: sourceChain,
      destination_chain: destChain,
      source_token: token,
      destination_token: token,
      amount: amount,
      slippage_tolerance: '0.5'
    })
  });

  const data = await response.json();
  return data.routes[0]; // Best route (already sorted)
}

// Track transaction
async function trackTransaction(txHash) {
  const response = await fetch(
    `${API_BASE}/api/v1/transactions/track/${txHash}`,
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );

  return await response.json();
}

// Usage
const bestRoute = await getBestRoute(
  'ethereum',
  'arbitrum',
  '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
  '100000000'
);

console.log(`Best route: ${bestRoute.bridge_name}`);
console.log(`Cost: $${bestRoute.fee_breakdown.total_cost_usd}`);
console.log(`Time: ${bestRoute.estimated_time_seconds}s`);
```

---

## Integration Example (Python)

```python
import requests

API_KEY = 'YOUR_API_KEY'
API_BASE = 'http://localhost:8000'

def get_best_route(source_chain, dest_chain, token, amount):
    """Get the best bridge route"""
    response = requests.post(
        f'{API_BASE}/api/v1/routes/quote',
        headers={
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        json={
            'source_chain': source_chain,
            'destination_chain': dest_chain,
            'source_token': token,
            'destination_token': token,
            'amount': amount,
            'slippage_tolerance': '0.5'
        }
    )
    data = response.json()
    return data['routes'][0]  # Best route

def track_transaction(tx_hash):
    """Track transaction status"""
    response = requests.get(
        f'{API_BASE}/api/v1/transactions/track/{tx_hash}',
        headers={'X-API-Key': API_KEY}
    )
    return response.json()

# Usage
best_route = get_best_route(
    'ethereum',
    'arbitrum',
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    '100000000'
)

print(f"Best route: {best_route['bridge_name']}")
print(f"Cost: ${best_route['fee_breakdown']['total_cost_usd']}")
print(f"Time: {best_route['estimated_time_seconds']}s")
```

---

## WebSocket Support (Coming Soon)

Real-time updates for:
- Transaction status changes
- Bridge health status
- New route availability
- Price updates

---

## Support

- **Documentation**: http://localhost:8000/docs (Interactive API docs)
- **GitHub**: [Your repository URL]
- **Email**: support@yourdomain.com
- **Discord**: [Your Discord invite]

---

## Changelog

### Version 1.0.0 (2025-11-10)
- Initial release
- 6 bridge integrations
- Real-time health monitoring
- Transaction tracking
- Bridge and chain statistics
- Professional landing page
