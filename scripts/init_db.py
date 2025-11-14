#!/usr/bin/env python3
"""Initialize database with sample data"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal, engine, Base
from app.models import Bridge, APIKey
from app.core.security import hash_api_key, generate_api_key
from datetime import datetime


def init_database():
    """Initialize database with tables and sample data"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")

    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Bridge).count() > 0:
            print("Database already initialized")
            return

        # Add sample bridges
        print("Adding sample bridges...")
        bridges = [
            Bridge(
                name="Across Protocol",
                protocol="across",
                api_url="https://across.to/api",
                supported_chains=[1, 10, 42161, 137, 8453],
                supported_tokens={
                    "1": ["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
                    "42161": ["0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"]
                },
                base_fee_percentage=0.005,
                min_fee_usd=0.5,
                is_active=True,
                is_healthy=True,
                success_rate=99.5,
                average_completion_time=180,
                uptime_percentage=99.8,
            ),
            Bridge(
                name="Stargate Finance",
                protocol="stargate",
                api_url="https://api.stargate.finance",
                supported_chains=[1, 10, 42161, 137],
                supported_tokens={
                    "1": ["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
                },
                base_fee_percentage=0.006,
                min_fee_usd=0.75,
                is_active=True,
                is_healthy=True,
                success_rate=98.8,
                average_completion_time=240,
                uptime_percentage=99.5,
            ),
            Bridge(
                name="Connext",
                protocol="connext",
                api_url="https://api.connext.network",
                supported_chains=[1, 10, 42161],
                supported_tokens={},
                base_fee_percentage=0.005,
                min_fee_usd=0.5,
                is_active=True,
                is_healthy=True,
                success_rate=97.5,
                average_completion_time=300,
                uptime_percentage=99.2,
            ),
            Bridge(
                name="Hop Protocol",
                protocol="hop",
                api_url="https://api.hop.exchange",
                supported_chains=[1, 10, 42161, 137],
                supported_tokens={},
                base_fee_percentage=0.007,
                min_fee_usd=1.0,
                is_active=True,
                is_healthy=True,
                success_rate=96.0,
                average_completion_time=420,
                uptime_percentage=98.0,
            ),
        ]

        for bridge in bridges:
            db.add(bridge)

        # Generate test API key
        print("Generating test API key...")
        test_api_key = generate_api_key()
        api_key_record = APIKey(
            key_hash=hash_api_key(test_api_key),
            name="Test API Key",
            tier="free",
            requests_per_minute=60,
            monthly_transfer_limit=100,
            is_active=True,
            email="test@example.com"
        )
        db.add(api_key_record)

        db.commit()

        print("\n✓ Database initialized successfully!")
        print(f"\n🔑 Test API Key: {test_api_key}")
        print("   Save this key - it won't be shown again!")
        print("\nUse this key in the X-API-Key header for API requests")

    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
