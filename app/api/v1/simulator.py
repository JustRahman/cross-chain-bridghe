"""
Transaction simulator for testing bridge functionality.

Allows creating simulated transactions that progress through different states
for testing WebSocket monitoring, webhooks, and dashboard features.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
import hashlib
import random

from app.db.base import get_db
from app.models.transaction import Transaction
from app.core.security import get_api_key
from app.core.logging import log
from app.services.webhook_service import webhook_service


router = APIRouter()


def _transaction_to_webhook_data(tx: Transaction) -> dict:
    """Convert transaction to webhook data format"""
    return {
        "id": tx.id,
        "source_tx_hash": tx.source_tx_hash,
        "destination_tx_hash": tx.destination_tx_hash,
        "status": tx.status,
        "bridge": tx.bridge_name,
        "source_chain": tx.source_chain,
        "destination_chain": tx.destination_chain,
        "source_token": tx.source_token,
        "destination_token": tx.destination_token,
        "amount": tx.amount,
        "estimated_time_seconds": tx.estimated_time_seconds,
        "error_message": tx.error_message,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
    }


class SimulateTransactionRequest(BaseModel):
    """Request to simulate a transaction"""
    bridge_name: str = Field(..., description="Bridge to simulate (e.g., 'Across Protocol')")
    source_chain: str = Field(..., description="Source chain")
    destination_chain: str = Field(..., description="Destination chain")
    amount: str = Field(..., description="Amount in smallest unit")
    should_fail: bool = Field(False, description="Whether transaction should fail")
    completion_time_seconds: Optional[int] = Field(180, description="Time to complete (seconds)")

    class Config:
        json_schema_extra = {
            "example": {
                "bridge_name": "Across Protocol",
                "source_chain": "ethereum",
                "destination_chain": "arbitrum",
                "amount": "1000000000",
                "should_fail": False,
                "completion_time_seconds": 180
            }
        }


class SimulateTransactionResponse(BaseModel):
    """Response from simulation"""
    transaction_id: int
    transaction_hash: str
    status: str
    message: str
    estimated_completion: str


class BulkSimulateRequest(BaseModel):
    """Request to simulate multiple transactions"""
    count: int = Field(..., ge=1, le=100, description="Number of transactions to simulate")
    bridge_name: Optional[str] = Field(None, description="Specific bridge or random if None")
    source_chain: Optional[str] = Field(None, description="Specific source chain or random")
    destination_chain: Optional[str] = Field(None, description="Specific dest chain or random")


@router.post("/simulate", response_model=SimulateTransactionResponse)
async def simulate_transaction(
    request: SimulateTransactionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Simulate a cross-chain bridge transaction.

    Creates a transaction in the database and simulates its progression
    through different states (pending → processing → completed/failed).

    This is useful for:
    - Testing WebSocket monitoring
    - Testing webhook notifications
    - Demonstrating dashboard features
    - Load testing the system
    """
    try:
        log.info(f"Simulating transaction: {request.bridge_name} {request.source_chain} -> {request.destination_chain}")

        # Generate realistic transaction hash
        hash_input = f"{request.source_chain}{request.destination_chain}{request.amount}{datetime.utcnow().timestamp()}"
        tx_hash = "0x" + hashlib.sha256(hash_input.encode()).hexdigest()

        # Create transaction in database
        transaction = Transaction(
            api_key_id=1,  # Default for simulation
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            source_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            destination_token="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC on Arbitrum
            amount=request.amount,
            bridge_name=request.bridge_name,
            status="pending",
            user_address_hash=hashlib.sha256(b"simulated_user").hexdigest(),
            estimated_time_seconds=request.completion_time_seconds,
            source_tx_hash=tx_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Send webhook notification for transaction creation
        await webhook_service.notify_transaction_event(
            "transaction.created",
            _transaction_to_webhook_data(transaction),
            db,
            transaction.id
        )

        # Schedule background task to progress the transaction
        background_tasks.add_task(
            progress_simulated_transaction,
            transaction.id,
            request.completion_time_seconds,
            request.should_fail
        )

        estimated_completion = transaction.created_at + timedelta(seconds=request.completion_time_seconds)

        return SimulateTransactionResponse(
            transaction_id=transaction.id,
            transaction_hash=tx_hash,
            status="pending",
            message=f"Simulated transaction created. Will {'fail' if request.should_fail else 'complete'} in {request.completion_time_seconds}s",
            estimated_completion=estimated_completion.isoformat()
        )

    except Exception as e:
        log.error(f"Error simulating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/bulk")
async def simulate_bulk_transactions(
    request: BulkSimulateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Simulate multiple transactions at once.

    Useful for load testing and populating the dashboard with activity.
    """
    try:
        log.info(f"Simulating {request.count} transactions")

        bridges = [
            "Across Protocol", "Hop Protocol", "Stargate Finance",
            "Synapse Protocol", "Celer cBridge", "Connext",
            "Orbiter Finance", "LayerZero", "deBridge", "Wormhole"
        ]

        chains = ["ethereum", "arbitrum", "optimism", "polygon", "base"]

        created_transactions = []

        for i in range(request.count):
            # Random or specified parameters
            bridge = request.bridge_name or random.choice(bridges)
            source = request.source_chain or random.choice(chains)
            dest = request.destination_chain or random.choice([c for c in chains if c != source])

            # Random amount between $100 and $10,000
            amount = str(random.randint(100, 10000) * 1_000_000)  # 6 decimals

            # Random completion time
            completion_time = random.randint(60, 600)

            # 5% chance of failure
            should_fail = random.random() < 0.05

            # Generate tx hash
            hash_input = f"{source}{dest}{amount}{datetime.utcnow().timestamp()}{i}"
            tx_hash = "0x" + hashlib.sha256(hash_input.encode()).hexdigest()

            # Create transaction
            transaction = Transaction(
                api_key_id=1,
                source_chain=source,
                destination_chain=dest,
                source_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                destination_token="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                amount=amount,
                bridge_name=bridge,
                status="pending",
                user_address_hash=hashlib.sha256(f"user_{i}".encode()).hexdigest(),
                estimated_time_seconds=completion_time,
                source_tx_hash=tx_hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(transaction)
            created_transactions.append({
                "id": i + 1,
                "hash": tx_hash,
                "bridge": bridge,
                "route": f"{source} -> {dest}"
            })

            # Schedule progression
            background_tasks.add_task(
                progress_simulated_transaction,
                transaction.id,
                completion_time,
                should_fail
            )

        db.commit()

        return {
            "message": f"Created {request.count} simulated transactions",
            "transactions": created_transactions[:10],  # Return first 10
            "total": request.count
        }

    except Exception as e:
        log.error(f"Error bulk simulating: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def progress_simulated_transaction(
    transaction_id: int,
    completion_time_seconds: int,
    should_fail: bool
):
    """
    Background task to progress a simulated transaction through states.

    Progression:
    pending (25%) -> processing (50%) -> confirming (75%) -> completed/failed (100%)
    """
    from app.db.base import SessionLocal

    db = SessionLocal()

    try:
        # Wait 25% of time, then set to processing
        await asyncio.sleep(completion_time_seconds * 0.25)

        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if tx:
            tx.status = "processing"
            tx.updated_at = datetime.utcnow()
            db.commit()
            log.info(f"Transaction {transaction_id} -> processing")

            # Send webhook notification
            await webhook_service.notify_transaction_event(
                "transaction.processing",
                _transaction_to_webhook_data(tx),
                db,
                tx.id
            )

        # Wait another 25%, then set to confirming
        await asyncio.sleep(completion_time_seconds * 0.25)

        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if tx:
            tx.status = "confirming"
            tx.updated_at = datetime.utcnow()

            # Generate destination tx hash
            dest_hash = "0x" + hashlib.sha256(f"dest_{transaction_id}".encode()).hexdigest()
            tx.destination_tx_hash = dest_hash

            db.commit()
            log.info(f"Transaction {transaction_id} -> confirming")

            # Send webhook notification
            await webhook_service.notify_transaction_event(
                "transaction.confirming",
                _transaction_to_webhook_data(tx),
                db,
                tx.id
            )

        # Wait final 50%, then set to final state
        await asyncio.sleep(completion_time_seconds * 0.5)

        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if tx:
            if should_fail:
                tx.status = "failed"
                tx.error_message = random.choice([
                    "Insufficient liquidity",
                    "Transaction reverted",
                    "Timeout waiting for confirmations",
                    "Bridge contract error"
                ])
                log.info(f"Transaction {transaction_id} -> failed")
            else:
                tx.status = "completed"
                log.info(f"Transaction {transaction_id} -> completed")

            tx.completed_at = datetime.utcnow()
            tx.updated_at = datetime.utcnow()
            db.commit()

            # Send webhook notification
            event_type = "transaction.failed" if should_fail else "transaction.completed"
            await webhook_service.notify_transaction_event(
                event_type,
                _transaction_to_webhook_data(tx),
                db,
                tx.id
            )

    except Exception as e:
        log.error(f"Error progressing transaction {transaction_id}: {e}")
    finally:
        db.close()


@router.get("/simulate/active")
async def get_active_simulations(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get currently active simulated transactions"""
    try:
        active_txs = db.query(Transaction).filter(
            Transaction.status.in_(["pending", "processing", "confirming"])
        ).all()

        return {
            "active_count": len(active_txs),
            "transactions": [
                {
                    "id": tx.id,
                    "hash": tx.source_tx_hash,
                    "status": tx.status,
                    "bridge": tx.bridge_name,
                    "route": f"{tx.source_chain} -> {tx.destination_chain}",
                    "created_at": tx.created_at.isoformat()
                }
                for tx in active_txs[:20]
            ]
        }

    except Exception as e:
        log.error(f"Error getting active simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
