# Testing Guide for New Features

This guide covers all the newly implemented features for the cross-chain bridge API.

## 🌱 1. Database Seeder

### Run the Seeder Script

```bash
# From project root
python scripts/seed_database.py
```

**What it does:**
- Creates 100 sample transactions across all bridges
- Generates realistic transaction history over the last 30 days
- Populates success/failure rates based on actual bridge performance
- Creates transaction hashes, timestamps, and completion times

**Options:**
- Clear existing transactions: `yes/no`
- Number of transactions to create: Default is `100`

**After seeding, you'll see:**
```
✅ Successfully created 100 sample transactions!

📊 Transaction Statistics:
  Across Protocol: 12 txs, 99.2% success rate
  Hop Protocol: 9 txs, 97.8% success rate
  ...
```

---

## 🔗 2. Blockchain RPC Integration

### Test Real Transaction Lookup

```bash
# Track any Ethereum transaction
curl -X GET "http://localhost:8000/api/v1/transactions/track/0x..." \
  -H "X-API-Key: nxb_dev_key_12345"
```

**What happens:**
1. Checks database first for transactions created via your API
2. If not found, searches across all supported chains using FREE public RPCs:
   - Ethereum
   - Arbitrum
   - Optimism
   - Polygon
   - Base

**Supported Chains:**
- Uses FREE public RPC endpoints (no API key needed!)
- Automatic failover across multiple providers
- Grove, Ankr, PublicNode, 1RPC

**Example Real Transaction:**
```bash
# Track a real Ethereum transaction
curl -X GET "http://localhost:8000/api/v1/transactions/track/0x5c8b9a1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b" \
  -H "X-API-Key: nxb_dev_key_12345"
```

---

## 📊 3. Real Database Statistics

### Test Bridge Statistics

```bash
# Get bridge statistics from real database
curl -X GET "http://localhost:8000/api/v1/transactions/statistics/bridges?days=30" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

**What it returns:**
- Real success rates from database (no longer >100%!)
- Actual completion times calculated from timestamps
- Total volume aggregated from all transactions
- Per-bridge performance metrics

**Before Seeding:**
```json
{
  "statistics": [
    {
      "bridge_name": "Across Protocol",
      "total_transactions": 0,  // Empty!
      "success_rate": "0"
    }
  ]
}
```

**After Seeding:**
```json
{
  "statistics": [
    {
      "bridge_name": "Across Protocol",
      "total_transactions": 15,  // Real data!
      "successful_transactions": 14,
      "failed_transactions": 1,
      "success_rate": "93.33",  // Realistic!
      "average_completion_time": 185,
      "total_volume_usd": "125000.50"
    }
  ]
}
```

---

## 🌐 4. Web3 Contract Integration

### Check Token Balance

```bash
# Install web3.py first
pip install web3

# Then use the API (if implemented in endpoints)
```

**Features:**
- Connect to Ethereum, Arbitrum, Optimism, Polygon, Base
- Read ERC20 token balances
- Check token allowances
- Estimate gas costs
- Build unsigned transactions

**Example (Python):**
```python
from app.services.web3_service import web3_service

# Get USDC balance
balance = await web3_service.get_token_balance(
    chain="ethereum",
    token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    user_address="0x..."
)
print(f"USDC Balance: {balance}")
```

---

## 🌉 5. Bridge-Specific APIs

### Test Across Protocol API

```bash
# Get real quote from Across
curl -X POST "http://localhost:8000/api/v1/routes/quote" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount": "1000000000"
  }' | jq
```

**Across API Integration:**
- Real-time fee quotes
- Estimated fill times
- Route availability check
- Deposit limits

**API Endpoint:** `https://across.to/api/suggested-fees`

---

## 📡 6. WebSocket Real-Time Monitoring

### Connect to WebSocket

**Using JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/track/0x...?api_key=nxb_dev_key_12345');

ws.onopen = () => {
  console.log('Connected to transaction monitoring');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);

  if (data.type === 'status_update') {
    console.log(`Status: ${data.status}, Progress: ${data.progress}%`);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send('ping');
}, 30000);
```

**Using Python:**
```python
import asyncio
import websockets
import json

async def track_transaction():
    uri = "ws://localhost:8000/api/v1/ws/track/0x123...?api_key=nxb_dev_key_12345"

    async with websockets.connect(uri) as websocket:
        # Receive messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

            if data['type'] == 'final_status':
                print("Transaction complete!")
                break

asyncio.run(track_transaction())
```

**Using `wscat` (CLI tool):**
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/api/v1/ws/track/0x123...?api_key=nxb_dev_key_12345"
```

**Message Types:**
- `connected`: Initial connection confirmation
- `status_update`: Transaction status changed
- `final_status`: Transaction completed or failed
- `blockchain_update`: Update from blockchain RPC
- `pong`: Response to ping

---

## 🔄 7. Real-Time Statistics WebSocket

```javascript
// Connect to stats stream
const statsWs = new WebSocket('ws://localhost:8000/api/v1/ws/stats?api_key=nxb_dev_key_12345');

statsWs.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'stats_update') {
    console.log('Bridge Stats (last 1 hour):', data.data);
    // Updates every 10 seconds
  }
};
```

**Receives:**
```json
{
  "type": "stats_update",
  "timestamp": "2025-11-12T10:30:00Z",
  "data": [
    {
      "bridge_name": "Across Protocol",
      "transactions_1h": 25,
      "volume_1h": 125000
    }
  ]
}
```

---

## 🎮 8. Transaction Simulator

### Simulate Single Transaction

```bash
# Create a simulated transaction
curl -X POST "http://localhost:8000/api/v1/simulator/simulate" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "bridge_name": "Across Protocol",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "amount": "1000000000",
    "should_fail": false,
    "completion_time_seconds": 180
  }' | jq
```

**Response:**
```json
{
  "transaction_id": 123,
  "transaction_hash": "0xabc123...",
  "status": "pending",
  "message": "Simulated transaction created. Will complete in 180s",
  "estimated_completion": "2025-11-12T10:33:00Z"
}
```

**What happens:**
- Transaction progresses through states: `pending` → `processing` → `confirming` → `completed/failed`
- 25% time → processing
- 50% time → confirming
- 100% time → completed/failed
- Webhooks triggered at each status change
- WebSocket subscribers receive real-time updates

### Simulate Bulk Transactions

```bash
# Create 50 random transactions for testing
curl -X POST "http://localhost:8000/api/v1/simulator/simulate/bulk" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "bridge_name": null,
    "source_chain": null,
    "destination_chain": null
  }' | jq
```

**Features:**
- Creates 1-100 transactions at once
- Random bridges, chains, amounts
- 5% failure rate
- Completion times: 60-600 seconds
- Perfect for load testing

### Check Active Simulations

```bash
# Get all currently running simulations
curl -X GET "http://localhost:8000/api/v1/simulator/simulate/active" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

**Response:**
```json
{
  "active_count": 15,
  "transactions": [
    {
      "id": 123,
      "hash": "0xabc...",
      "status": "processing",
      "bridge": "Across Protocol",
      "route": "ethereum -> arbitrum",
      "created_at": "2025-11-12T10:30:00Z"
    }
  ]
}
```

---

## 🪝 9. Webhook Notifications

### Configure Webhook

First, set up a webhook endpoint to receive notifications:

```bash
# Create webhook
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "secret": "your_secret_key_123",
    "events": [
      "transaction.created",
      "transaction.processing",
      "transaction.confirming",
      "transaction.completed",
      "transaction.failed"
    ],
    "is_active": true
  }' | jq
```

### Webhook Payload Format

When a transaction status changes, your endpoint receives:

```json
{
  "event_type": "transaction.completed",
  "timestamp": "2025-11-12T10:35:00Z",
  "data": {
    "id": 123,
    "source_tx_hash": "0xabc...",
    "destination_tx_hash": "0xdef...",
    "status": "completed",
    "bridge": "Across Protocol",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "amount": "1000000000",
    "amount_received": "995000000",
    "created_at": "2025-11-12T10:30:00Z",
    "completed_at": "2025-11-12T10:35:00Z"
  }
}
```

### Verify Webhook Signature

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    """Verify webhook signature"""
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    expected_signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # Signature comes as "sha256=abc123..."
    signature_value = signature.split('=')[1]
    return hmac.compare_digest(expected_signature, signature_value)

# In your webhook handler
if verify_webhook(payload, request.headers['X-Webhook-Signature'], 'your_secret_key_123'):
    # Process webhook
    print("Webhook verified!")
```

### Test Webhook

```bash
# Test webhook endpoint
curl -X POST "http://localhost:8000/api/v1/webhooks/{webhook_id}/test" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

### Webhook Delivery Tracking

```bash
# Check webhook delivery history
curl -X GET "http://localhost:8000/api/v1/webhooks/{webhook_id}/deliveries" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

**Features:**
- Automatic retry with exponential backoff (up to 5 retries)
- Delivery tracking (success/failure)
- Response time monitoring
- HMAC signature authentication

---

## 🎨 10. Frontend Dashboard

### Access Dashboard

Open in browser:
```
http://localhost:8000/static/dashboard.html?api_key=nxb_dev_key_12345
```

### Features

**Real-Time Statistics:**
- Bridge performance metrics
- Transaction throughput
- Success rates
- Volume tracking
- Updates every 10 seconds via WebSocket

**Transaction Tracking:**
- Enter transaction hash
- Live status updates
- Progress visualization
- Error messages
- Completion notifications

**Bridge Comparison:**
- Side-by-side metrics
- Historical data (1h, 24h, 7d)
- Visual charts
- Performance rankings

### Dashboard Testing Flow

1. **Open Dashboard:**
   ```
   http://localhost:8000/static/dashboard.html?api_key=nxb_dev_key_12345
   ```

2. **Simulate Transactions:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/simulator/simulate/bulk" \
     -H "X-API-Key: nxb_dev_key_12345" \
     -H "Content-Type: application/json" \
     -d '{"count": 10}'
   ```

3. **Watch Real-Time Updates:**
   - Statistics update automatically
   - Transaction statuses change live
   - Progress bars move
   - Completion notifications appear

4. **Track Specific Transaction:**
   - Copy transaction hash from simulator response
   - Enter in dashboard tracking field
   - Watch status progression

---

## 🌉 11. Bridge API Integrations

### Hop Protocol

```bash
# Get real quote from Hop
curl -X POST "http://localhost:8000/api/v1/routes/quote" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "optimism",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
    "amount": "1000000000"
  }' | jq
```

**Hop API Features:**
- Real-time quotes
- Bonder fees
- Price impact
- Estimated time: ~5 minutes

### Stargate Finance

```bash
# Stargate uses 0.06% fee structure
# Returns estimated output based on known fees
```

**Stargate Features:**
- LayerZero integration
- 0.06% bridge fee
- ~4 minute transfers
- Multi-chain liquidity pools

### Synapse Protocol

```bash
# Get quote from Synapse
# Supports swap + bridge combinations
```

**Synapse Features:**
- Swap + bridge routing
- Multiple token support
- ~6 minute avg time
- Wide chain support

---

## 🧪 Complete Testing Flow

### 1. **Seed the Database**
```bash
python scripts/seed_database.py
# Choose: yes to clear existing, 100 transactions
```

### 2. **Check Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/statistics/bridges" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

### 3. **Open Frontend Dashboard**
```bash
# Open in browser
open http://localhost:8000/static/dashboard.html?api_key=nxb_dev_key_12345
```

### 4. **Simulate Transactions**
```bash
# Simulate bulk transactions to see real-time updates
curl -X POST "http://localhost:8000/api/v1/simulator/simulate/bulk" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"count": 20}' | jq

# Watch dashboard update in real-time!
```

### 5. **Track Simulated Transaction**
```bash
# Simulate single transaction
TX_HASH=$(curl -s -X POST "http://localhost:8000/api/v1/simulator/simulate" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "bridge_name": "Across Protocol",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "amount": "1000000000",
    "should_fail": false,
    "completion_time_seconds": 120
  }' | jq -r '.transaction_hash')

echo "Transaction Hash: $TX_HASH"

# Track via API
curl -X GET "http://localhost:8000/api/v1/transactions/track/$TX_HASH" \
  -H "X-API-Key: nxb_dev_key_12345" | jq

# Or enter hash in dashboard to watch live updates
```

### 6. **Monitor via WebSocket**
```bash
# Install wscat if needed
npm install -g wscat

# Connect and watch status updates
wscat -c "ws://localhost:8000/api/v1/ws/track/$TX_HASH?api_key=nxb_dev_key_12345"
```

### 7. **Configure Webhook (Optional)**
```bash
# Set up webhook.site to receive test webhooks
# Visit https://webhook.site to get a unique URL

WEBHOOK_URL="https://webhook.site/YOUR-UNIQUE-ID"

curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$WEBHOOK_URL\",
    \"secret\": \"test_secret_123\",
    \"events\": [\"transaction.created\", \"transaction.completed\", \"transaction.failed\"],
    \"is_active\": true
  }" | jq

# Now simulate a transaction and watch webhook.site!
curl -X POST "http://localhost:8000/api/v1/simulator/simulate" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "bridge_name": "Hop Protocol",
    "source_chain": "ethereum",
    "destination_chain": "optimism",
    "amount": "500000000",
    "completion_time_seconds": 60
  }'
```

### 8. **Test Bridge APIs**
```bash
# Test Hop Protocol quote
curl -X POST "http://localhost:8000/api/v1/routes/quote" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "optimism",
    "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_token": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
    "amount": "1000000000"
  }' | jq
```

### 9. **Track Real Blockchain Transaction**
```bash
# Use any real Ethereum transaction hash
curl -X GET "http://localhost:8000/api/v1/transactions/track/0x5c8b9a1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

### 10. **Check Active Simulations**
```bash
# See all running simulations
curl -X GET "http://localhost:8000/api/v1/simulator/simulate/active" \
  -H "X-API-Key: nxb_dev_key_12345" | jq
```

---

## 📦 Dependencies

Make sure you have these installed:

```bash
# Python packages
pip install web3 websockets aiohttp

# Node packages (for testing)
npm install -g wscat
```

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart if needed
docker-compose restart db
```

### WebSocket Connection Refused
```bash
# Make sure FastAPI is running
docker-compose logs app

# Rebuild if main.py was updated
docker-compose down
docker-compose build
docker-compose up -d
```

### "web3.py not installed" Warning
```bash
# Install in Docker container
docker-compose exec app pip install web3

# Or add to requirements.txt and rebuild
```

### RPC Timeout Errors
- Public RPCs can be slow/rate limited
- The service automatically tries multiple providers
- Wait and retry if all providers fail

---

## 🎉 Success Indicators

You'll know everything is working when:

✅ **Database Seeder:**
  - Creates 100 transactions successfully
  - Shows transaction statistics with realistic success rates

✅ **API Statistics:**
  - Bridge statistics show real data (not 0 or >100%)
  - Success rates are between 95-99%
  - Completion times match bridge characteristics

✅ **Transaction Tracking:**
  - Finds transactions from database
  - Finds real blockchain transactions
  - Returns proper status and details

✅ **WebSocket Monitoring:**
  - Transaction tracking connects successfully
  - Receives real-time status updates
  - Stats WebSocket sends periodic updates (every 10s)
  - Ping/pong works for keepalive

✅ **Transaction Simulator:**
  - Single transaction simulation works
  - Bulk simulation creates multiple transactions
  - Transactions progress through states: pending → processing → confirming → completed
  - Active simulations endpoint shows running transactions
  - Dashboard shows real-time updates

✅ **Webhook Notifications:**
  - Webhook creation succeeds
  - Webhooks triggered on transaction status changes
  - Webhook signatures are valid
  - Webhook.site receives test notifications
  - Delivery tracking shows success/failure

✅ **Frontend Dashboard:**
  - Dashboard loads without errors
  - Statistics update every 10 seconds
  - Transaction tracking shows live progress
  - Charts and metrics display correctly
  - WebSocket connection indicator shows "Connected"

✅ **Bridge APIs:**
  - Hop Protocol returns real quotes
  - Stargate returns fee estimates
  - Synapse returns route data
  - No timeout errors

✅ **System Health:**
  - No errors in `docker-compose logs app`
  - Database connections stable
  - WebSocket connections maintained
  - Background tasks executing properly

---

## 📚 Next Steps

1. **Populate More Data:**
   - Run seeder multiple times with different date ranges
   - Create transactions through your actual API

2. **Monitor in Production:**
   - Use WebSocket to build real-time dashboard
   - Track bridge performance over time

3. **Integrate Bridge APIs:**
   - Across Protocol: Real fees and limits
   - Hop Protocol: Coming soon
   - Stargate: Coming soon

4. **Add More Chains:**
   - BSC, Avalanche, Fantom support exists
   - Just need to test and enable

---

## 🤝 Support

If you encounter issues:
1. Check Docker logs: `docker-compose logs -f app`
2. Verify database: `docker-compose exec db psql -U postgres -d bridge_db`
3. Test endpoints individually
4. Check this guide for examples

Happy testing! 🚀
