#!/usr/bin/env python3
"""Generate a new API key"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.models import APIKey
from app.core.security import hash_api_key, generate_api_key


def create_api_key(name: str, email: str, tier: str = "free"):
    """Create a new API key"""
    db = SessionLocal()
    try:
        # Generate API key
        api_key = generate_api_key()

        # Set tier limits
        tier_limits = {
            "free": {"rpm": 60, "monthly": 100},
            "starter": {"rpm": 120, "monthly": 1000},
            "growth": {"rpm": 300, "monthly": 5000},
            "enterprise": {"rpm": 1000, "monthly": 999999},
        }

        limits = tier_limits.get(tier, tier_limits["free"])

        # Create API key record
        api_key_record = APIKey(
            key_hash=hash_api_key(api_key),
            name=name,
            tier=tier,
            requests_per_minute=limits["rpm"],
            monthly_transfer_limit=limits["monthly"],
            is_active=True,
            email=email
        )

        db.add(api_key_record)
        db.commit()

        print(f"\n✓ API Key created successfully!")
        print(f"\nName: {name}")
        print(f"Email: {email}")
        print(f"Tier: {tier}")
        print(f"Rate Limit: {limits['rpm']} requests/minute")
        print(f"Monthly Limit: {limits['monthly']} transfers")
        print(f"\n🔑 API Key: {api_key}")
        print("\n⚠️  Save this key securely - it won't be shown again!")

    except Exception as e:
        print(f"Error creating API key: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a new API key")
    parser.add_argument("--name", required=True, help="Name for the API key")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument(
        "--tier",
        default="free",
        choices=["free", "starter", "growth", "enterprise"],
        help="API tier"
    )

    args = parser.parse_args()
    create_api_key(args.name, args.email, args.tier)
