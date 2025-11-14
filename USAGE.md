# How to Use the Cross-Chain Bridge Aggregator API

Complete guide for integrating and using the bridge aggregator in your application.

## Table of Contents
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Core Workflows](#core-workflows)
- [API Endpoints](#api-endpoints)
- [Integration Examples](#integration-examples)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)

---

## Quick Start

### 1. Get Your API Key

```bash
# If using Docker
docker-compose exec api python scripts/init_db.py

# If running locally
python scripts/init_db.py
```

Save the API key that's printed. You'll need it for all requests.

### 2. Make Your First Request

```bash
export API_KEY="your-api-key-here"

curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/bridges/status
```

### 3. Get a Route Quote

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount": "1000000000"
  }' \
  http://localhost:8000/api/v1/routes/quote
```

---

## Authentication

All API requests (except health checks) require authentication using an API key.

### Header Format

```
X-API-Key: your-api-key-here
```

### Generate New API Key

```bash
python scripts/generate_api_key.py \
  --name "Production Key" \
  --email "your@email.com" \
  --tier starter
```

### API Key Tiers

| Tier | Rate Limit | Monthly Transfers | Price |
|------|------------|-------------------|-------|
| Free | 60/min | 100 | $0 |
| Starter | 120/min | 1,000 | $299/mo |
| Growth | 300/min | 5,000 | $799/mo |
| Enterprise | Custom | Unlimited | Custom |

---

## Core Workflows

### Workflow 1: Simple Bridge Transfer

**Use Case**: Transfer USDC from Ethereum to Arbitrum

```javascript
// 1. Get route options
const routes = await fetch('http://localhost:8000/api/v1/routes/quote', {
  method: 'POST',
  headers: {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    source_chain: 'ethereum',
    destination_chain: 'arbitrum',
    source_token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    destination_token: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
    amount: '1000000000', // 1000 USDC (6 decimals)
    user_address: '0xYourAddress'
  })
}).then(r => r.json());

// 2. Select best route (routes are sorted by cost)
const bestRoute = routes.routes[0];
console.log(`Best route: ${bestRoute.bridge_name}`);
console.log(`Cost: $${bestRoute.cost_breakdown.total_cost_usd}`);
console.log(`Time: ${bestRoute.estimated_time_seconds / 60} minutes`);

// 3. Execute the route
const execution = await fetch('http://localhost:8000/api/v1/routes/execute', {
  method: 'POST',
  headers: {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    quote_id: routes.quote_id,
    route_index: 0,
    user_address: '0xYourAddress',
    slippage_tolerance: 0.5
  })
}).then(r => r.json());

// 4. Sign and send transactions (using ethers.js)
for (const tx of execution.transactions) {
  const signedTx = await wallet.sendTransaction({
    to: tx.to,
    data: tx.data,
    value: tx.value,
    gasLimit: tx.gas_limit
  });

  console.log(`Transaction sent: ${signedTx.hash}`);
  await signedTx.wait(); // Wait for confirmation
}

// 5. Monitor status
const checkStatus = async (txId) => {
  const status = await fetch(
    `http://localhost:8000/api/v1/routes/status/${txId}`,
    { headers: { 'X-API-Key': apiKey } }
  ).then(r => r.json());

  return status;
};

// Poll until completed
let status;
do {
  status = await checkStatus(execution.transaction_id);
  console.log(`Status: ${status.status} (${status.progress}%)`);
  await new Promise(r => setTimeout(r, 10000)); // Wait 10 seconds
} while (status.status !== 'completed' && status.status !== 'failed');
```

### Workflow 2: Compare Multiple Bridges

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

def get_route_quotes():
    """Get quotes from all available bridges"""

    response = requests.post(
        f"{BASE_URL}/api/v1/routes/quote",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "amount": "1000000000"
        }
    )

    routes = response.json()['routes']

    # Print comparison
    print("\\nBridge Comparison:\\n")
    print(f"{'Bridge':<20} {'Cost (USD)':<12} {'Time (min)':<12} {'Success Rate':<15}")
    print("-" * 70)

    for route in routes:
        cost = route['cost_breakdown']['total_cost_usd']
        time = route['estimated_time_seconds'] / 60
        success = route['success_rate']

        print(f"{route['bridge_name']:<20} ${cost:<11.2f} {time:<11.1f} {success:<14.1f}%")

    return routes

routes = get_route_quotes()
```

### Workflow 3: Check Bridge Health Before Transfer

```javascript
async function selectHealthyBridge() {
  // 1. Check bridge status
  const bridgeStatus = await fetch(
    'http://localhost:8000/api/v1/bridges/status',
    { headers: { 'X-API-Key': apiKey } }
  ).then(r => r.json());

  // 2. Filter healthy bridges
  const healthyBridges = bridgeStatus.bridges.filter(b =>
    b.is_healthy && b.is_active && b.success_rate > 95
  );

  console.log(`${healthyBridges.length} healthy bridges available`);

  // 3. Get quotes (API will automatically exclude unhealthy bridges)
  const routes = await getRouteQuote({
    source_chain: 'ethereum',
    destination_chain: 'arbitrum',
    // ... other params
  });

  return routes;
}
```

### Workflow 4: Monitor All Active Transfers

```python
def monitor_active_transfers(api_key):
    """Monitor all active transfers for a customer"""

    # This would require storing transaction IDs
    active_transactions = get_stored_transaction_ids()

    for tx_id in active_transactions:
        status = requests.get(
            f"{BASE_URL}/api/v1/routes/status/{tx_id}",
            headers={"X-API-Key": api_key}
        ).json()

        print(f"TX {tx_id[:8]}... : {status['status']} ({status['progress']}%)")

        if status['status'] == 'completed':
            print(f"  ✓ Completed in {status.get('actual_time_seconds', 0) / 60:.1f} minutes")
        elif status['status'] == 'failed':
            print(f"  ✗ Failed: {status.get('message', 'Unknown error')}")
```

---

## API Endpoints

### Routes

#### POST `/api/v1/routes/quote`
Get optimal route quotes for a transfer

**Request Body**:
```json
{
  "source_chain": "ethereum",
  "destination_chain": "arbitrum",
  "source_token": "0xA0b...",
  "destination_token": "0xFF9...",
  "amount": "1000000000",
  "user_address": "0x742..." // optional
}
```

**Response**: List of route options sorted by cost

**Use When**:
- User wants to see transfer options
- Comparing costs across bridges
- Getting time estimates

#### POST `/api/v1/routes/execute`
Generate transaction data for execution

**Request Body**:
```json
{
  "quote_id": "quote_abc123",
  "route_index": 0,
  "user_address": "0x742...",
  "slippage_tolerance": 0.5
}
```

**Response**: Transaction data ready for signing

**Use When**:
- User has selected a route
- Ready to execute the transfer
- Need transaction data for wallet

#### GET `/api/v1/routes/status/{transaction_id}`
Check transfer status

**Response**:
```json
{
  "transaction_id": "tx_123",
  "status": "bridging",
  "progress": 60,
  "source_tx_hash": "0xabc...",
  "destination_tx_hash": null,
  "message": "Transfer in progress"
}
```

**Poll Frequency**: Every 10-15 seconds

### Bridges

#### GET `/api/v1/bridges/status`
Get health status of all bridges

**Use When**:
- Showing bridge status to users
- Checking if bridges are operational
- Monitoring system health

#### GET `/api/v1/bridges/tokens/supported?chain=ethereum`
List supported tokens

**Query Params**:
- `chain` (optional): Filter by chain name

**Use When**:
- Building token selector UI
- Validating user input
- Showing available options

### Health Checks

#### GET `/health`
Basic health check

#### GET `/health/detailed`
Detailed health with DB and Redis status

---

## Integration Examples

### React Integration

```typescript
import { useState, useEffect } from 'react';

function BridgeWidget() {
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(false);

  async function getQuotes(fromChain, toChain, token, amount) {
    setLoading(true);

    const response = await fetch('/api/v1/routes/quote', {
      method: 'POST',
      headers: {
        'X-API-Key': process.env.REACT_APP_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source_chain: fromChain,
        destination_chain: toChain,
        source_token: token,
        destination_token: token, // Same token
        amount: amount
      })
    });

    const data = await response.json();
    setRoutes(data.routes);
    setLoading(false);
  }

  return (
    <div>
      {loading ? (
        <div>Loading routes...</div>
      ) : (
        <div>
          {routes.map((route, i) => (
            <RouteCard key={i} route={route} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Python Backend Integration

```python
from typing import List, Dict
import requests
from decimal import Decimal

class BridgeAggregator:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def get_routes(
        self,
        source_chain: str,
        dest_chain: str,
        source_token: str,
        dest_token: str,
        amount: str
    ) -> List[Dict]:
        """Get route quotes"""

        response = requests.post(
            f"{self.base_url}/api/v1/routes/quote",
            headers=self.headers,
            json={
                "source_chain": source_chain,
                "destination_chain": dest_chain,
                "source_token": source_token,
                "destination_token": dest_token,
                "amount": amount
            }
        )

        response.raise_for_status()
        return response.json()['routes']

    def execute_route(self, quote_id: str, route_index: int, user_address: str):
        """Execute selected route"""

        response = requests.post(
            f"{self.base_url}/api/v1/routes/execute",
            headers=self.headers,
            json={
                "quote_id": quote_id,
                "route_index": route_index,
                "user_address": user_address,
                "slippage_tolerance": 0.5
            }
        )

        response.raise_for_status()
        return response.json()

    def get_status(self, tx_id: str) -> Dict:
        """Check transaction status"""

        response = requests.get(
            f"{self.base_url}/api/v1/routes/status/{tx_id}",
            headers=self.headers
        )

        response.raise_for_status()
        return response.json()

# Usage
client = BridgeAggregator(api_key="your-key")
routes = client.get_routes(
    source_chain="ethereum",
    dest_chain="arbitrum",
    source_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    dest_token="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    amount="1000000000"
)
```

---

## Best Practices

### 1. Quote Caching
```javascript
// Cache quotes for 30 seconds to avoid rate limits
const quoteCache = new Map();

async function getCachedQuote(params) {
  const key = JSON.stringify(params);
  const cached = quoteCache.get(key);

  if (cached && Date.now() - cached.timestamp < 30000) {
    return cached.data;
  }

  const fresh = await getRouteQuote(params);
  quoteCache.set(key, { data: fresh, timestamp: Date.now() });

  return fresh;
}
```

### 2. Error Handling
```python
from requests.exceptions import HTTPError, Timeout

def safe_api_call(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Timeout:
            return {"error": "Request timeout - please try again"}
        except HTTPError as e:
            if e.response.status_code == 429:
                return {"error": "Rate limit exceeded - please wait"}
            elif e.response.status_code == 401:
                return {"error": "Invalid API key"}
            else:
                return {"error": f"API error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    return wrapper

@safe_api_call
def get_routes(...):
    # API call here
    pass
```

### 3. Progress Updates
```javascript
// Show user progress during bridging
async function monitorWithProgress(txId, onUpdate) {
  const statusMessages = {
    'pending': 'Waiting for confirmation...',
    'confirmed': 'Transaction confirmed!',
    'bridging': 'Bridging in progress...',
    'completed': 'Transfer completed!',
    'failed': 'Transfer failed'
  };

  while (true) {
    const status = await getStatus(txId);

    onUpdate({
      progress: status.progress,
      message: statusMessages[status.status],
      status: status.status
    });

    if (status.status === 'completed' || status.status === 'failed') {
      break;
    }

    await sleep(10000); // Wait 10 seconds
  }
}

// Usage
monitorWithProgress('tx_123', (update) => {
  console.log(`${update.progress}%: ${update.message}`);
});
```

### 4. Handle Rate Limits
```javascript
class RateLimitedAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.queue = [];
    this.processing = false;
    this.requestsPerSecond = 10; // Adjust based on your tier
  }

  async request(url, options) {
    return new Promise((resolve, reject) => {
      this.queue.push({ url, options, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;
    const { url, options, resolve, reject } = this.queue.shift();

    try {
      const response = await fetch(url, options);
      resolve(response);
    } catch (error) {
      reject(error);
    }

    // Wait before processing next request
    setTimeout(() => {
      this.processing = false;
      this.processQueue();
    }, 1000 / this.requestsPerSecond);
  }
}
```

---

## Error Handling

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Invalid API key | Check your API key |
| 403 | Forbidden | Check your tier limits |
| 422 | Invalid request data | Validate your input |
| 429 | Rate limit exceeded | Wait and retry |
| 500 | Server error | Contact support |
| 503 | Bridge unavailable | Try different bridge |

### Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "INSUFFICIENT_LIQUIDITY",
  "retry_after": 60
}
```

### Handling Specific Errors

```typescript
async function handleBridgeRequest() {
  try {
    const routes = await getRoutes(...);
    return routes;
  } catch (error) {
    if (error.status === 429) {
      // Rate limited
      const retryAfter = error.headers.get('Retry-After') || 60;
      await sleep(retryAfter * 1000);
      return handleBridgeRequest(); // Retry
    }

    if (error.status === 503) {
      // Bridge unavailable
      // Try with different route or show message to user
      showMessage("Bridge temporarily unavailable, please try again");
    }

    throw error;
  }
}
```

---

## Next Steps

1. ✅ Complete API integration
2. 📖 Read [FEATURES.md](FEATURES.md) for full capabilities
3. 📖 Check [API_EXAMPLES.md](API_EXAMPLES.md) for more examples
4. 🔧 See [SETUP.md](SETUP.md) if you need help with configuration
5. 🚀 Build your bridge UI!

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Examples**: See API_EXAMPLES.md
- **Setup Help**: See SETUP.md
- **Issues**: Open a GitHub issue
