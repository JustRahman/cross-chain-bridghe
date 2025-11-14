# Getting Started with Nexbridge API

## Create Your First API Key

Since API key management requires authentication, here's how to bootstrap your first key:

### Option 1: Use the Health Endpoint (No Auth Required)

Test that the API is running:
```bash
curl http://localhost:8000/health
```

### Option 2: Temporarily Disable Authentication

For development, you can bypass authentication on specific endpoints.

**Quick Development Key:**

Run this command to insert a test key directly:

```bash
docker exec bridge_postgres psql -U bridge_user -d bridge_aggregator << EOF
-- Check if new api_keys table exists
DO \$\$
BEGIN
    -- Try to insert into the new structure
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'api_keys' AND column_name = 'key') THEN
        INSERT INTO api_keys (key, name, description, user_email, is_active, rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day, total_requests, successful_requests, failed_requests, created_at)
        VALUES ('nxb_dev_key_12345', 'Development Key', 'Testing key', 'dev@example.com', true, 1000, 10000, 100000, 0, 0, 0, NOW())
        ON CONFLICT DO NOTHING;

        RAISE NOTICE 'API Key created: nxb_dev_key_12345';
    ELSE
        RAISE NOTICE 'Using legacy table structure - keys need to be hashed';
    END IF;
END \$\$;
EOF
```

### Option 3: Use a Default Test Key

For quick testing, use this pre-configured key:

**Test API Key**: `nxb_test_123`

This works with most endpoints for testing purposes.

## Test Your API Key

Once you have a key, test it:

```bash
# Test authentication
curl http://localhost:8000/api/v1/bridges \
  -H "X-API-Key: YOUR_KEY_HERE"

# Get a bridge quote
curl -X POST http://localhost:8000/api/v1/routes/quote \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "token": "USDC",
    "amount": "1000000000"
  }'
```

## Production Setup

For production, use the API key management endpoints:

```bash
# Create a new key (requires admin key)
curl -X POST http://localhost:8000/api/v1/api-keys/ \
  -H "X-API-Key: ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "user_email": "user@example.com",
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 5000,
    "rate_limit_per_day": 50000
  }'
```

## Common Issues

**401 Unauthorized**: Your API key is missing or invalid
- Make sure you include the `X-API-Key` header
- Verify the key hasn't been revoked or expired

**429 Too Many Requests**: You've exceeded your rate limit
- Check the `Retry-After` header
- View your limits: `GET /api/v1/api-keys/{id}/rate-limits`

**403 Forbidden**: Your key is valid but doesn't have access
- Key may be revoked, expired, or IP-restricted
- Check key status: `GET /api/v1/api-keys/{id}`

## Next Steps

1. Read the full API Reference: `API_REFERENCE.md`
2. Explore the interactive docs: http://localhost:8000/docs
3. Check system health: http://localhost:8000/health
4. View the landing page: http://localhost:8000/
