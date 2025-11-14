# Quick Start Guide

Get the Cross-Chain Bridge Aggregator API running in 5 minutes!

## Option 1: Docker (Recommended)

The fastest way to get started:

```bash
# 1. Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# 2. Wait for services to be ready (~30 seconds)
docker-compose logs -f api

# 3. Initialize the database
docker-compose exec api python scripts/init_db.py

# 4. Test the API
curl http://localhost:8000/health
```

That's it! The API is now running at `http://localhost:8000`

View API docs at: `http://localhost:8000/docs`

## Option 2: Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (running on port 5432)
- Redis 7+ (running on port 6379)

### Steps

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env

# Edit .env and set your database URL:
# DATABASE_URL=postgresql://user:password@localhost:5432/bridge_aggregator

# 4. Initialize database
python scripts/init_db.py

# 5. Run migrations
alembic upgrade head

# 6. Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Testing the API

### Get a test API key

The `init_db.py` script generates a test API key. Copy it from the output!

### Make your first request

```bash
# Get bridge status
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/bridges/status

# Get a route quote
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
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

## Using the Makefile

If you prefer using make commands:

```bash
# Start Docker services
make docker-up

# Initialize database
make init-db

# Generate API key
make api-key

# Run tests
make test

# View all available commands
make help
```

## Next Steps

1. **Configure RPC endpoints**: Edit `.env` with your Alchemy/Infura API keys
2. **Explore API docs**: Visit `http://localhost:8000/docs` for interactive documentation
3. **Read the README**: Check out `README.md` for detailed documentation
4. **Implement bridges**: Start integrating real bridge protocols in `app/services/`

## Troubleshooting

### Port already in use
```bash
# Check what's using port 8000
lsof -i :8000

# Or use a different port
uvicorn app.main:app --reload --port 8080
```

### Database connection error
```bash
# Make sure PostgreSQL is running
docker-compose ps

# Check database logs
docker-compose logs postgres
```

### Redis connection error
```bash
# Make sure Redis is running
docker-compose ps

# Check Redis logs
docker-compose logs redis
```

## Development Workflow

```bash
# 1. Make code changes in app/

# 2. Run tests
make test

# 3. Format code
make format

# 4. Check code quality
make lint

# 5. Restart server (auto-reloads if using --reload flag)
```

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- View API documentation at `/docs`
- Open an issue on GitHub

Happy building! 🚀
