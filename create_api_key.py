#!/usr/bin/env python3
"""Create initial API key for development"""
import secrets
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://nexbridge_user:nexbridge_pass@localhost:5432/nexbridge_db"

def create_api_key(name="Development Key", email="dev@example.com"):
    """Create a new API key"""

    # Generate secure key
    key = f"nxb_{secrets.token_urlsafe(32)}"

    # Connect to database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Insert API key
        session.execute("""
            INSERT INTO api_keys (
                key, name, description, user_email, is_active,
                rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day,
                total_requests, successful_requests, failed_requests,
                created_at
            ) VALUES (
                :key, :name, 'Generated via create_api_key.py', :email, true,
                1000, 10000, 100000,
                0, 0, 0,
                :now
            )
        """, {
            'key': key,
            'name': name,
            'email': email,
            'now': datetime.utcnow()
        })

        session.commit()

        print("=" * 80)
        print("✅ API Key Created Successfully!")
        print("=" * 80)
        print(f"\nAPI Key: {key}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"\nRate Limits:")
        print(f"  - Per Minute: 1,000 requests")
        print(f"  - Per Hour: 10,000 requests")
        print(f"  - Per Day: 100,000 requests")
        print(f"\n⚠️  IMPORTANT: Save this key! It won't be shown again.")
        print(f"\nUsage Example:")
        print(f'curl -H "X-API-Key: {key}" http://localhost:8000/api/v1/bridges')
        print("=" * 80)

        return key

    except Exception as e:
        session.rollback()
        print(f"❌ Error creating API key: {e}")
        return None

    finally:
        session.close()

if __name__ == "__main__":
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "Development Key"
    email = sys.argv[2] if len(sys.argv) > 2 else "dev@example.com"

    create_api_key(name, email)
