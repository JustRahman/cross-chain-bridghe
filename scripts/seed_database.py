"""
Database seeder script to populate with sample transaction data.

This creates realistic transaction history for testing and demonstration purposes.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from decimal import Decimal

from app.db.base import SessionLocal
from app.models.transaction import Transaction
from app.models.api_key import APIKey


def create_sample_transactions(db, num_transactions: int = 100):
    """Create sample transactions for testing"""

    print(f"Creating {num_transactions} sample transactions...")

    # Get or create default API key
    api_key = db.query(APIKey).first()
    if not api_key:
        api_key = APIKey(
            key_hash="sample_key_hash",
            name="Sample API Key",
            tier="free",
            is_active=True
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

    # Bridge configurations
    bridges = [
        {"name": "Across Protocol", "protocol": "across", "avg_time": 180, "success_rate": 0.995},
        {"name": "Hop Protocol", "protocol": "hop", "avg_time": 300, "success_rate": 0.975},
        {"name": "Stargate Finance", "protocol": "stargate", "avg_time": 240, "success_rate": 0.988},
        {"name": "Synapse Protocol", "protocol": "synapse", "avg_time": 360, "success_rate": 0.965},
        {"name": "Celer cBridge", "protocol": "celer", "avg_time": 180, "success_rate": 0.988},
        {"name": "Connext", "protocol": "connext", "avg_time": 300, "success_rate": 0.975},
        {"name": "Orbiter Finance", "protocol": "orbiter", "avg_time": 300, "success_rate": 0.992},
        {"name": "LayerZero", "protocol": "layerzero", "avg_time": 300, "success_rate": 0.980},
        {"name": "deBridge", "protocol": "debridge", "avg_time": 420, "success_rate": 0.978},
        {"name": "Wormhole", "protocol": "wormhole", "avg_time": 600, "success_rate": 0.950},
    ]

    # Chain pairs
    chain_pairs = [
        ("ethereum", "arbitrum"),
        ("ethereum", "optimism"),
        ("ethereum", "polygon"),
        ("ethereum", "base"),
        ("arbitrum", "optimism"),
        ("optimism", "polygon"),
        ("polygon", "base"),
        ("base", "arbitrum"),
    ]

    # Token addresses (USDC on different chains)
    tokens = {
        "ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "arbitrum": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "optimism": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    }

    # Generate transactions over the last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)

    transactions_created = 0

    for i in range(num_transactions):
        # Random bridge
        bridge = random.choice(bridges)

        # Random chain pair
        source_chain, destination_chain = random.choice(chain_pairs)

        # Random amount (between $100 and $10,000)
        amount_usd = random.uniform(100, 10000)
        amount_usdc = str(int(amount_usd * 1_000_000))  # 6 decimals

        # Random creation time in last 30 days
        days_ago = random.uniform(0, 30)
        created_at = start_date + timedelta(days=days_ago)

        # Determine if transaction succeeded
        is_successful = random.random() < bridge["success_rate"]

        if is_successful:
            status = "completed"
            # Completion time: avg_time +/- 30%
            completion_seconds = int(bridge["avg_time"] * random.uniform(0.7, 1.3))
            completed_at = created_at + timedelta(seconds=completion_seconds)
            error_message = None
        else:
            status = "failed"
            # Failed transactions complete quickly
            completion_seconds = random.randint(30, 120)
            completed_at = created_at + timedelta(seconds=completion_seconds)
            error_messages = [
                "Insufficient liquidity",
                "Transaction reverted",
                "Gas estimation failed",
                "Timeout waiting for confirmations",
                "Bridge contract error",
            ]
            error_message = random.choice(error_messages)

        # Generate realistic transaction hashes
        source_tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
        destination_tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}" if is_successful else None

        # Create transaction
        transaction = Transaction(
            api_key_id=api_key.id,
            source_chain=source_chain,
            destination_chain=destination_chain,
            source_token=tokens.get(source_chain, tokens["ethereum"]),
            destination_token=tokens.get(destination_chain, tokens["ethereum"]),
            amount=amount_usdc,
            bridge_name=bridge["name"],
            status=status,
            user_address_hash=f"hash_{random.randint(1000, 9999)}",
            estimated_time_seconds=bridge["avg_time"],
            source_tx_hash=source_tx_hash,
            destination_tx_hash=destination_tx_hash,
            created_at=created_at,
            updated_at=completed_at,
            completed_at=completed_at,
            error_message=error_message
        )

        db.add(transaction)
        transactions_created += 1

        # Commit in batches
        if (i + 1) % 20 == 0:
            db.commit()
            print(f"  Created {i + 1}/{num_transactions} transactions...")

    # Final commit
    db.commit()
    print(f"✅ Successfully created {transactions_created} sample transactions!")

    # Print statistics
    print("\n📊 Transaction Statistics:")
    for bridge in bridges:
        count = db.query(Transaction).filter(Transaction.bridge_name == bridge["name"]).count()
        completed = db.query(Transaction).filter(
            Transaction.bridge_name == bridge["name"],
            Transaction.status == "completed"
        ).count()
        success_rate = (completed / count * 100) if count > 0 else 0
        print(f"  {bridge['name']}: {count} txs, {success_rate:.1f}% success rate")


def main():
    """Main seeder function"""
    print("🌱 Database Seeder")
    print("=" * 50)

    # Create database session
    db = SessionLocal()

    try:
        # Check existing transactions
        existing_count = db.query(Transaction).count()
        print(f"Existing transactions in database: {existing_count}")

        if existing_count > 0:
            response = input("\nDatabase already has transactions. Clear them? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                db.query(Transaction).delete()
                db.commit()
                print("✅ Cleared existing transactions")
            else:
                print("Keeping existing transactions...")

        # Ask how many transactions to create
        num_transactions = input("\nHow many sample transactions to create? [100]: ").strip()
        num_transactions = int(num_transactions) if num_transactions else 100

        # Create transactions
        create_sample_transactions(db, num_transactions)

        # Show summary
        print("\n" + "=" * 50)
        print("✅ Database seeding completed successfully!")
        print(f"Total transactions: {db.query(Transaction).count()}")

        # Show recent transactions
        print("\n📝 Recent Transactions:")
        recent = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(5).all()
        for tx in recent:
            print(f"  {tx.bridge_name}: {tx.source_chain} → {tx.destination_chain} ({tx.status})")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
