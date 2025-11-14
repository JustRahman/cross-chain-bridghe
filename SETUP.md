# Setup Guide

This guide covers everything you need to get the Cross-Chain Bridge Aggregator API running.

## Required API Keys & Services

### 1. RPC Providers (REQUIRED)

You need RPC endpoints for blockchain access. Get free API keys from:

#### Option A: Alchemy (Recommended)
- **Website**: https://www.alchemy.com
- **Sign up**: Free tier includes 300M compute units/month
- **Chains available**: Ethereum, Arbitrum, Polygon, Base (⚠️ **Note**: Optimism not available)

Once you have your API key, you'll use URLs like:
```
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

#### Option B: Infura (MetaMask Developer)
- **Website**: https://infura.io
- **Sign up**: Free tier includes 100K requests/day
- **Chains available**: Ethereum, Polygon, Optimism, Arbitrum
- **URL format**: `https://mainnet.infura.io/v3/YOUR_API_KEY` (replace 'mainnet' with chain name)

Once you have your API key, you'll use URLs like:
```
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_API_KEY
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_API_KEY
OPTIMISM_RPC_URL=https://optimism-mainnet.infura.io/v3/YOUR_API_KEY
ARBITRUM_RPC_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_API_KEY
```

#### Option C: Public RPCs (Development Only)
For testing, you can use public RPCs:
```
ETHEREUM_RPC_URL=https://eth.llamarpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io
POLYGON_RPC_URL=https://polygon-rpc.com
BASE_RPC_URL=https://mainnet.base.org
```

⚠️ **Warning**: Public RPCs are unreliable and rate-limited. Only use for development!

### 2. DEX Aggregator APIs (OPTIONAL - For DEX Swaps)

#### Velora API
- **Website**: https://developers.velora.xyz
- **API Docs**: https://developers.velora.xyz/api/velora-api/velora-market-api/master/api-v6.2
- **Purpose**: DEX aggregation for multi-hop routes
- **Setup**:
  1. Review API documentation
  2. Add to `.env`:
     ```
     VELORA_API_URL=https://api.velora.xyz/v6.2
     ```

#### OpenOcean API
- **Website**: https://openocean.finance
- **API Docs**: https://apis.openocean.finance/developer/apis/swap-api/api-v4
- **Purpose**: DEX aggregation and swap routing
- **Setup**:
  1. Review API documentation
  2. Add to `.env`:
     ```
     OPENOCEAN_API_URL=https://open-api.openocean.finance/v4
     ```

### 3. Sentry (OPTIONAL - Error Tracking)

- **Website**: https://sentry.io
- **Purpose**: Real-time error monitoring and alerting
- **Pricing**: Free tier includes 5K errors/month
- **Setup**:
  1. Create new project
  2. **Select Platform**: Choose **FastAPI** when creating the project
  3. Copy DSN
  4. Add to `.env`:
     ```
     SENTRY_DSN=https://...@sentry.io/...
     ```

### 4. Database (PostgreSQL)

#### Option A: Docker (Recommended for Development)
Already included in `docker-compose.yml` - no setup needed!

#### Option B: External PostgreSQL (Supabase)
If using Supabase or other external database:

- **Supabase Setup**:
  1. Go to https://supabase.com
  2. Create new project with name: `Cross-Chain-Bridge`
  3. Set database password (save it securely)
  4. Get connection string from Settings > Database
  5. Use **Direct Connection** string (not Transaction pooler)

- **Other Providers**:
  - [Neon](https://neon.tech) - Free tier with 1GB storage
  - [Railway](https://railway.app) - $5/month
  - AWS RDS, Google Cloud SQL (production)

**Supabase Connection String Format**:
```
DATABASE_URL=postgresql://postgres.{project_ref}:{password}@aws-0-{region}.pooler.supabase.com:5432/postgres
```

**Example with your credentials**:
```
DATABASE_URL=postgresql://postgres:jebvez-zIxfo0-gutgug@{your-project-host}:5432/postgres
```

### 5. Redis

#### Option A: Docker (Recommended for Development)
Already included in `docker-compose.yml` - no setup needed!

#### Option B: External Redis
- **Providers**:
  - [Upstash](https://upstash.com) - Free tier with 10K requests/day
  - [Redis Cloud](https://redis.com/cloud) - Free 30MB
  - AWS ElastiCache (production)

**Connection string format**:
```
REDIS_URL=redis://username:password@host:port/0
```

---

## Environment Setup

### 1. Clone and Create Virtual Environment

```bash
# Clone repository
cd cross-chain-bridge

# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your values
nano .env  # or use any text editor
```

**Minimum Required Configuration**:
```bash
# Application
SECRET_KEY=generate-a-secure-32-character-string-here
DATABASE_URL=postgresql://bridge_user:bridge_password@localhost:5432/bridge_aggregator
REDIS_URL=redis://localhost:6379/0

# RPC Endpoints (REQUIRED)
# Using Alchemy (for Ethereum, Arbitrum, Polygon, Base)
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY

# Using Infura (for Optimism and fallbacks)
OPTIMISM_RPC_URL=https://optimism-mainnet.infura.io/v3/YOUR_INFURA_KEY
```

**Optional but Recommended**:
```bash
# Error Tracking
SENTRY_DSN=your-sentry-dsn

# DEX Integration
VELORA_API_URL=https://api.velora.xyz/v6.2
OPENOCEAN_API_URL=https://open-api.openocean.finance/v4

# Fallback RPC (for redundancy)
ETHEREUM_RPC_FALLBACK_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
POLYGON_RPC_FALLBACK_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY
ARBITRUM_RPC_FALLBACK_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_KEY
```

### 3. Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and set it as `SECRET_KEY` in `.env`

---

## Installation Methods

### Method 1: Docker (Easiest)

**Prerequisites**: Docker and Docker Compose installed

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python scripts/init_db.py

# Check logs
docker-compose logs -f api

# API is now running at http://localhost:8000
```

**Docker Compose includes**:
- PostgreSQL database
- Redis cache
- FastAPI application
- Celery worker (background tasks)
- Celery beat (scheduled tasks)

### Method 2: Local Development

**Prerequisites**:
- Python 3.11+
- PostgreSQL 15+ (running on port 5432)
- Redis 7+ (running on port 6379)

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Initialize database with sample data
python scripts/init_db.py

# Start the API server
uvicorn app.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.services.celery_app worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.services.celery_app beat --loglevel=info
```

---

## Verification

### 1. Test API Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### 2. Test Database Connection

```bash
curl http://localhost:8000/health/detailed
```

Should show database and Redis as "healthy"

### 3. Get Your API Key

After running `init_db.py`, you'll see output like:
```
🔑 Test API Key: sk_test_abc123xyz...
```

Save this key! Use it in the `X-API-Key` header for all requests.

### 4. Test API Endpoint

```bash
export API_KEY="your-api-key-from-init"

curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/bridges/status
```

---

## Production Deployment

### Additional Requirements for Production

1. **Domain & SSL Certificate**
   - Purchase domain name
   - Set up SSL with Let's Encrypt (free)
   - Configure DNS records

2. **Production Database**
   - Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Enable automated backups
   - Set up read replicas for scaling

3. **Production Redis**
   - Use managed Redis (AWS ElastiCache, Redis Cloud)
   - Enable persistence
   - Set up replication

4. **Monitoring**
   - Sentry for error tracking (REQUIRED)
   - Prometheus + Grafana for metrics (recommended)
   - Log aggregation (Datadog, Grafana Loki, CloudWatch)

5. **Scaling**
   - Load balancer (nginx, AWS ALB)
   - Multiple API instances
   - Separate Celery workers

### Production Environment Variables

Additional variables for production:
```bash
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# CORS - limit to your domains
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=100

# Enable monitoring
ENABLE_METRICS=True
ENABLE_BRIDGE_HEALTH_MONITORING=True
ENABLE_CIRCUIT_BREAKER=True
```

---

## Troubleshooting

### "Connection refused" to database
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check database logs
docker-compose logs postgres
```

### "Connection refused" to Redis
```bash
# Check if Redis is running
docker-compose ps

# Check Redis logs
docker-compose logs redis
```

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### RPC errors
```bash
# Test your RPC endpoint
curl https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### Database migration errors
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec api python scripts/init_db.py
```

---

## Cost Estimate

### Free Tier (Development)
- Alchemy/Infura: Free
- Database: Docker (local)
- Redis: Docker (local)
- Total: **$0/month**

### Basic Production
- Alchemy: $49/month (or Infura $50/month)
- Database: Neon Free tier or Railway $5/month
- Redis: Upstash Free tier
- Sentry: Free tier
- Server: $5-20/month (DigitalOcean, Railway)
- Total: **~$60-75/month**

### Scaled Production
- Alchemy: $199/month (or dedicated nodes)
- Database: AWS RDS $50-200/month
- Redis: AWS ElastiCache $50/month
- Monitoring: Datadog $15/month
- Servers: $100-500/month (multiple instances)
- Total: **~$400-1000/month**

---

## Next Steps

1. ✅ Complete this setup guide
2. ✅ Get API running locally
3. 📖 Read [USAGE.md](USAGE.md) to learn how to use the API
4. 📖 Read [FEATURES.md](FEATURES.md) to see what's available
5. 📖 Check [API_EXAMPLES.md](API_EXAMPLES.md) for code examples
6. 🚀 Start building your integration!

---

## Support

- **Documentation**: See all `.md` files in project root
- **API Reference**: http://localhost:8000/docs
- **Issues**: Check troubleshooting section above
- **Community**: [Open an issue on GitHub]

---

## Security Notes

⚠️ **Never commit these to version control**:
- `.env` file
- API keys
- Database passwords
- Secret keys

✅ **Do commit**:
- `.env.example` (with placeholder values)
- Documentation
- Code

🔒 **Production Security Checklist**:
- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS only
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
