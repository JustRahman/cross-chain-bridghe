"""Transaction tracking and statistics endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.db.base import get_db
from app.schemas.transaction import (
    TransactionTrackingResponse,
    TransactionStatus,
    BridgeStatisticsResponse,
    BridgeStatistics,
    ChainStatisticsResponse,
    ChainStatistics
)
from app.core.security import get_api_key
from app.core.logging import log
from app.services.route_discovery import route_discovery_engine
from app.services.blockchain_rpc import blockchain_rpc
from app.models.transaction import Transaction
from sqlalchemy import func, desc


router = APIRouter()


def _get_steps_completed(status: str) -> int:
    """Helper to determine steps completed based on status"""
    status_steps = {
        "pending": 1,
        "processing": 2,
        "confirming": 3,
        "completed": 4,
        "failed": 1,
    }
    return status_steps.get(status, 1)


def _get_current_step(status: str, steps_completed: int, total_steps: int) -> str:
    """Helper to determine current step description"""
    if status == "completed":
        return "Transaction completed successfully"
    elif status == "failed":
        return "Transaction failed"
    elif status == "pending":
        return f"Processing step {steps_completed}/{total_steps}"
    elif status == "processing":
        return "Bridge transfer in progress"
    elif status == "confirming":
        return "Waiting for confirmations on destination chain"
    else:
        return f"Step {steps_completed}/{total_steps}"


@router.get("/track/{transaction_hash}", response_model=TransactionTrackingResponse)
async def track_transaction(
    transaction_hash: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Track the status of a cross-chain transaction.

    Provides real-time status updates including:
    - Current step in the bridging process
    - Progress percentage
    - Estimated completion time
    - Error details if failed
    """
    try:
        log.info(f"Tracking transaction: {transaction_hash}")

        # Step 1: Check if transaction exists in our database
        db_transaction = db.query(Transaction).filter(
            Transaction.source_tx_hash == transaction_hash
        ).first()

        if db_transaction:
            # We have this transaction in our DB - return tracked status
            log.info(f"Found transaction in database: {db_transaction.id}")

            transaction = TransactionStatus(
                transaction_hash=transaction_hash,
                bridge_protocol=db_transaction.bridge_name,
                source_chain=db_transaction.source_chain,
                destination_chain=db_transaction.destination_chain,
                status=db_transaction.status,
                amount=db_transaction.amount,
                token=db_transaction.source_token,
                created_at=db_transaction.created_at,
                completed_at=db_transaction.completed_at,
                estimated_completion=db_transaction.created_at + timedelta(seconds=db_transaction.estimated_time_seconds) if db_transaction.status == "pending" else None,
                steps_completed=_get_steps_completed(db_transaction.status),
                total_steps=4,
                error_message=db_transaction.error_message
            )
        else:
            # Step 2: Transaction not in DB - try to fetch from blockchain
            log.info(f"Transaction not in DB, fetching from blockchain...")

            # Try common chains
            tx_data = None
            detected_chain = None

            for chain in ["ethereum", "arbitrum", "optimism", "polygon", "base"]:
                log.debug(f"Trying chain: {chain}")
                tx_data = await blockchain_rpc.get_transaction(chain, transaction_hash)
                if tx_data:
                    detected_chain = chain
                    log.info(f"Found transaction on {chain}")
                    break

            if not tx_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Transaction {transaction_hash} not found on any supported chain"
                )

            # Parse blockchain data
            status = "completed" if tx_data.get("status") == "0x1" else "failed" if tx_data.get("status") == "0x0" else "pending"

            transaction = TransactionStatus(
                transaction_hash=transaction_hash,
                bridge_protocol="unknown",  # Can't determine from on-chain data
                source_chain=detected_chain,
                destination_chain="unknown",
                status=status,
                amount=tx_data.get("value", "0"),
                token=tx_data.get("to", "native"),
                created_at=datetime.utcnow(),  # Would need block timestamp
                completed_at=datetime.utcnow() if status == "completed" else None,
                estimated_completion=None,
                steps_completed=4 if status == "completed" else 1,
                total_steps=4,
                error_message="Transaction failed" if status == "failed" else None
            )

        # Calculate progress
        progress = (transaction.steps_completed / transaction.total_steps) * 100

        # Determine current step
        current_step = _get_current_step(transaction.status, transaction.steps_completed, transaction.total_steps)

        response = TransactionTrackingResponse(
            transaction=transaction,
            progress_percentage=progress,
            current_step=current_step
        )

        return response

    except Exception as e:
        log.error(f"Error tracking transaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track transaction: {str(e)}"
        )


@router.get("/statistics/bridges", response_model=BridgeStatisticsResponse)
async def get_bridge_statistics(
    days: int = Query(7, description="Number of days to include in statistics", ge=1, le=90),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get comprehensive statistics for all bridge protocols.

    Includes:
    - Transaction success rates
    - Average completion times
    - Total volume processed
    - Uptime percentages
    - Performance rankings (cheapest/fastest routes)
    """
    try:
        log.info(f"Getting bridge statistics for last {days} days")

        # Calculate date range
        period_start = datetime.utcnow() - timedelta(days=days)
        period_end = datetime.utcnow()

        # Get all transactions in the time period
        transactions_query = db.query(Transaction).filter(
            Transaction.created_at >= period_start,
            Transaction.created_at <= period_end
        )

        # Get list of all bridge names from route discovery engine
        bridges = route_discovery_engine.bridges
        statistics = []

        total_tx_count = 0
        total_volume_sum = Decimal("0")

        for bridge in bridges:
            bridge_name = bridge.name

            # Query database for this bridge
            bridge_txs = transactions_query.filter(
                Transaction.bridge_name == bridge_name
            ).all()

            if len(bridge_txs) == 0:
                # If no transactions in DB, use minimal mock data
                stat = BridgeStatistics(
                    bridge_name=bridge_name,
                    protocol=bridge.protocol,
                    total_transactions=0,
                    successful_transactions=0,
                    failed_transactions=0,
                    success_rate=Decimal("0"),
                    average_completion_time=300,
                    total_volume_usd=Decimal("0"),
                    uptime_percentage=Decimal("100.0"),
                    cheapest_route_count=0,
                    fastest_route_count=0
                )
            else:
                # Calculate real statistics from database
                total_txs = len(bridge_txs)
                successful_txs = len([tx for tx in bridge_txs if tx.status == "completed"])
                failed_txs = len([tx for tx in bridge_txs if tx.status == "failed"])

                success_rate = Decimal(str((successful_txs / total_txs * 100))) if total_txs > 0 else Decimal("0")

                # Calculate average completion time (for completed transactions)
                completed_txs = [tx for tx in bridge_txs if tx.status == "completed" and tx.completed_at and tx.created_at]
                if completed_txs:
                    avg_time = sum((tx.completed_at - tx.created_at).total_seconds() for tx in completed_txs) / len(completed_txs)
                else:
                    # Use estimated time from first transaction or default to 300
                    avg_time = bridge_txs[0].estimated_time_seconds if bridge_txs and bridge_txs[0].estimated_time_seconds else 300

                # Estimate total volume (this is rough since amounts are in wei)
                total_volume = sum(Decimal(tx.amount) / Decimal("1000000") for tx in bridge_txs)  # Assuming 6 decimals

                stat = BridgeStatistics(
                    bridge_name=bridge_name,
                    protocol=bridge.protocol,
                    total_transactions=total_txs,
                    successful_transactions=successful_txs,
                    failed_transactions=failed_txs,
                    success_rate=success_rate,
                    average_completion_time=int(avg_time),
                    total_volume_usd=total_volume,
                    uptime_percentage=Decimal("99.5") if success_rate > 95 else Decimal("95.0"),
                    cheapest_route_count=0,  # Would need additional tracking
                    fastest_route_count=0   # Would need additional tracking
                )

                total_tx_count += total_txs
                total_volume_sum += total_volume

            statistics.append(stat)

        # Sort by success rate (highest first), then by total transactions
        statistics.sort(key=lambda x: (x.success_rate, x.total_transactions), reverse=True)

        total_transactions = total_tx_count if total_tx_count > 0 else sum(s.total_transactions for s in statistics)
        total_volume = total_volume_sum if total_volume_sum > 0 else sum(s.total_volume_usd for s in statistics)

        response = BridgeStatisticsResponse(
            statistics=statistics,
            total_transactions=total_transactions,
            total_volume_usd=total_volume,
            period_start=datetime.utcnow() - timedelta(days=days),
            period_end=datetime.utcnow()
        )

        return response

    except Exception as e:
        log.error(f"Error getting bridge statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get bridge statistics: {str(e)}"
        )


@router.get("/statistics/chains", response_model=ChainStatisticsResponse)
async def get_chain_statistics(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get statistics for all supported chains.

    Includes:
    - Inbound/outbound transaction counts
    - Total volume per chain
    - Most popular routes
    - Average transaction sizes
    """
    try:
        log.info("Getting chain statistics")

        # TODO: Implement actual database queries
        # For now, return mock data

        chains_data = [
            {
                "chain_name": "ethereum",
                "chain_id": 1,
                "outbound": 850,
                "inbound": 920,
                "volume": Decimal("12500000"),
                "popular_dest": "arbitrum",
                "avg_size": Decimal("15000")
            },
            {
                "chain_name": "arbitrum",
                "chain_id": 42161,
                "outbound": 720,
                "inbound": 850,
                "volume": Decimal("8900000"),
                "popular_dest": "ethereum",
                "avg_size": Decimal("12000")
            },
            {
                "chain_name": "optimism",
                "chain_id": 10,
                "outbound": 580,
                "inbound": 640,
                "volume": Decimal("6200000"),
                "popular_dest": "ethereum",
                "avg_size": Decimal("10500")
            },
            {
                "chain_name": "polygon",
                "chain_id": 137,
                "outbound": 950,
                "inbound": 780,
                "volume": Decimal("5800000"),
                "popular_dest": "ethereum",
                "avg_size": Decimal("6100")
            },
            {
                "chain_name": "base",
                "chain_id": 8453,
                "outbound": 420,
                "inbound": 510,
                "volume": Decimal("4100000"),
                "popular_dest": "ethereum",
                "avg_size": Decimal("9800")
            }
        ]

        chains = []
        for data in chains_data:
            chain = ChainStatistics(
                chain_name=data["chain_name"],
                chain_id=data["chain_id"],
                outbound_transactions=data["outbound"],
                inbound_transactions=data["inbound"],
                total_volume_usd=data["volume"],
                most_popular_destination=data["popular_dest"],
                average_transaction_size_usd=data["avg_size"]
            )
            chains.append(chain)

        response = ChainStatisticsResponse(
            chains=chains,
            generated_at=datetime.utcnow()
        )

        return response

    except Exception as e:
        log.error(f"Error getting chain statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chain statistics: {str(e)}"
        )
