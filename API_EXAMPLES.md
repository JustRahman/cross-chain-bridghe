# API Examples

Example requests for testing the Cross-Chain Bridge Aggregator API.

## Setup

First, get your API key by initializing the database:

```bash
docker-compose up -d
docker-compose exec api python scripts/init_db.py
```

Copy the API key from the output and use it in the examples below.

## Authentication

All API requests (except health checks) require an API key:

```bash
export API_KEY="your-api-key-here"
```

## Health Checks

### Basic Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

### Detailed Health Check
```bash
curl http://localhost:8000/health/detailed
```

### Root Endpoint
```bash
curl http://localhost:8000/
```

## Bridge Status

### Get All Bridges Status
```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/bridges/status
```

Response:
```json
{
  "bridges": [
    {
      "name": "Across Protocol",
      "protocol": "across",
      "is_healthy": true,
      "is_active": true,
      "success_rate": 99.5,
      "average_completion_time": 180,
      "uptime_percentage": 99.8,
      "supported_chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"]
    }
  ],
  "total_bridges": 4,
  "healthy_bridges": 3,
  "checked_at": "2024-01-15T10:30:00Z"
}
```

### Get Supported Tokens
```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/bridges/tokens/supported
```

Filter by chain:
```bash
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/api/v1/bridges/tokens/supported?chain=ethereum"
```

## Route Management

### Get Route Quote

Transfer USDC from Ethereum to Arbitrum:

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount": "1000000000",
    "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }' \
  http://localhost:8000/api/v1/routes/quote
```

Response:
```json
{
  "routes": [
    {
      "bridge_name": "Across Protocol",
      "route_type": "direct",
      "estimated_time_seconds": 180,
      "cost_breakdown": {
        "bridge_fee_usd": 0.50,
        "gas_cost_source_usd": 5.20,
        "gas_cost_destination_usd": 0.10,
        "total_cost_usd": 5.80,
        "slippage_percentage": 0.1
      },
      "success_rate": 99.5,
      "steps": [
        {
          "action": "approve",
          "description": "Approve token spending"
        },
        {
          "action": "bridge",
          "description": "Bridge to arbitrum"
        }
      ],
      "requires_approval": true,
      "minimum_amount": "1000000",
      "maximum_amount": "10000000000"
    },
    {
      "bridge_name": "Stargate Finance",
      "route_type": "direct",
      "estimated_time_seconds": 240,
      "cost_breakdown": {
        "bridge_fee_usd": 0.75,
        "gas_cost_source_usd": 6.00,
        "gas_cost_destination_usd": 0.15,
        "total_cost_usd": 6.90,
        "slippage_percentage": 0.15
      },
      "success_rate": 98.8
    }
  ],
  "quote_id": "quote_abc123xyz",
  "expires_at": 1699564800
}
```

### Execute Route

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "quote_abc123xyz",
    "route_index": 0,
    "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "slippage_tolerance": 0.5
  }' \
  http://localhost:8000/api/v1/routes/execute
```

Response:
```json
{
  "transaction_id": "tx_def456uvw",
  "transactions": [
    {
      "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "data": "0x095ea7b3000000000000000000000000000000000000000000000000000000003b9aca00",
      "value": "0",
      "gas_limit": "50000",
      "chain_id": 1
    },
    {
      "to": "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5",
      "data": "0xabcdef123456...",
      "value": "0",
      "gas_limit": "200000",
      "chain_id": 1
    }
  ],
  "estimated_completion_time": 180,
  "status_url": "/api/v1/routes/status/tx_def456uvw"
}
```

### Check Transaction Status

```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/routes/status/tx_def456uvw
```

Response:
```json
{
  "transaction_id": "tx_def456uvw",
  "status": "processing",
  "source_tx_hash": "0xabc123def456...",
  "destination_tx_hash": null,
  "progress": 50,
  "message": "Bridge transfer in progress",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:00Z",
  "completed_at": null
}
```

## Common Token Addresses

### Ethereum Mainnet
- USDC: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- USDT: `0xdAC17F958D2ee523a2206206994597C13D831ec7`
- DAI: `0x6B175474E89094C44Da98b954EedeAC495271d0F`
- WETH: `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`

### Arbitrum One
- USDC: `0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8`
- USDT: `0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9`
- DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`

### Optimism
- USDC: `0x7F5c764cBc14f9669B88837ca1490cCa17c31607`
- USDT: `0x94b008aA00579c1307B0EF2c499aD98a8ce58e58`
- DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
- WETH: `0x4200000000000000000000000000000000000006`

### Polygon
- USDC: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- USDT: `0xc2132D05D31c914a87C6611C10748AEb04B58e8F`
- DAI: `0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063`
- WMATIC: `0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270`

## Testing with Python

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get bridge status
response = requests.get(f"{BASE_URL}/api/v1/bridges/status", headers=headers)
print(response.json())

# Get route quote
quote_data = {
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount": "1000000000"
}

response = requests.post(
    f"{BASE_URL}/api/v1/routes/quote",
    headers=headers,
    json=quote_data
)
print(response.json())
```

## Testing with JavaScript/Node.js

```javascript
const axios = require('axios');

const API_KEY = 'your-api-key-here';
const BASE_URL = 'http://localhost:8000';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Get bridge status
async function getBridgeStatus() {
  const response = await axios.get(`${BASE_URL}/api/v1/bridges/status`, { headers });
  console.log(response.data);
}

// Get route quote
async function getRouteQuote() {
  const data = {
    source_chain: 'ethereum',
    destination_chain: 'arbitrum',
    source_token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    destination_token: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
    amount: '1000000000'
  };

  const response = await axios.post(`${BASE_URL}/api/v1/routes/quote`, data, { headers });
  console.log(response.data);
}

getBridgeStatus();
getRouteQuote();
```

## Error Responses

### Missing API Key
```bash
curl http://localhost:8000/api/v1/bridges/status
```

Response:
```json
{
  "detail": "API Key required"
}
```
Status: 401

### Invalid Request Data
```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "invalid_chain",
    "destination_chain": "arbitrum"
  }' \
  http://localhost:8000/api/v1/routes/quote
```

Response:
```json
{
  "detail": [
    {
      "loc": ["body", "source_chain"],
      "msg": "Chain must be one of: ethereum, arbitrum, optimism, polygon, base",
      "type": "value_error"
    }
  ]
}
```
Status: 422

## Rate Limiting

The API enforces rate limits based on your tier:

- **Free**: 60 requests/minute
- **Starter**: 120 requests/minute
- **Growth**: 300 requests/minute
- **Enterprise**: 1000 requests/minute

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```
Status: 429

## Next Steps

1. Explore the interactive API docs at `http://localhost:8000/docs`
2. Try different token pairs and amounts
3. Check bridge status before making requests
4. Monitor transaction status after execution

For more information, see:
- `README.md` - Full documentation
- `QUICK_START.md` - Getting started guide
- `/docs` - Interactive API documentation
