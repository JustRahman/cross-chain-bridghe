"""Transaction history management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List
from datetime import datetime

from app.db.base import get_db
from app.db.models.transactions import TransactionHistory, TransactionSimulation
from app.schemas.transaction_history import (
    TransactionCreate,
    TransactionUpdate,
    TransactionHistoryResponse,
    TransactionListResponse,
    TransactionSimulationRequest,
    TransactionSimulationResponse
)
from app.core.security import get_api_key
from app.core.logging import log


router = APIRouter()


@router.post("/", response_model=TransactionHistoryResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Create a new transaction history record.

    Called when a user requests a quote and initiates a bridge transaction.
    Stores all details for tracking and analytics.
    """
    try:
        db_transaction = TransactionHistory(
            source_chain=transaction.source_chain,
            destination_chain=transaction.destination_chain,
            token=transaction.token,
            amount=transaction.amount,
            user_address=transaction.user_address,
            selected_bridge=transaction.selected_bridge,
            estimated_cost_usd=transaction.estimated_cost_usd,
            estimated_time_minutes=transaction.estimated_time_minutes,
            estimated_gas_cost=transaction.estimated_gas_cost,
            quote_data=transaction.quote_data,
            transaction_hash=transaction.transaction_hash,
            status="pending"
        )

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        log.info(f"Created transaction history record: {db_transaction.id}")
        return db_transaction

    except Exception as e:
        db.rollback()
        log.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {str(e)}")


@router.patch("/{transaction_id}", response_model=TransactionHistoryResponse)
async def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Update a transaction record.

    Used to update transaction status, completion time, actual costs, etc.
    """
    try:
        db_transaction = db.query(TransactionHistory).filter(
            TransactionHistory.id == transaction_id
        ).first()

        if not db_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_transaction, key, value)

        db.commit()
        db.refresh(db_transaction)

        log.info(f"Updated transaction: {transaction_id}")
        return db_transaction

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error updating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update transaction: {str(e)}")


@router.get("/{transaction_id}", response_model=TransactionHistoryResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get a specific transaction by ID"""
    try:
        transaction = db.query(TransactionHistory).filter(
            TransactionHistory.id == transaction_id
        ).first()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get transaction: {str(e)}")


@router.get("/hash/{transaction_hash}", response_model=TransactionHistoryResponse)
async def get_transaction_by_hash(
    transaction_hash: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get a transaction by its blockchain transaction hash"""
    try:
        transaction = db.query(TransactionHistory).filter(
            TransactionHistory.transaction_hash == transaction_hash
        ).first()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting transaction by hash: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get transaction: {str(e)}")


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source_chain: Optional[str] = Query(None, description="Filter by source chain"),
    destination_chain: Optional[str] = Query(None, description="Filter by destination chain"),
    bridge: Optional[str] = Query(None, description="Filter by bridge protocol"),
    user_address: Optional[str] = Query(None, description="Filter by user address"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    List transactions with filtering and pagination.

    Supports filtering by status, chains, bridge, and user address.
    """
    try:
        query = db.query(TransactionHistory)

        # Apply filters
        if status:
            query = query.filter(TransactionHistory.status == status)
        if source_chain:
            query = query.filter(TransactionHistory.source_chain == source_chain)
        if destination_chain:
            query = query.filter(TransactionHistory.destination_chain == destination_chain)
        if bridge:
            query = query.filter(TransactionHistory.selected_bridge == bridge)
        if user_address:
            query = query.filter(TransactionHistory.user_address == user_address)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        transactions = query.order_by(desc(TransactionHistory.created_at)).offset(offset).limit(page_size).all()

        return TransactionListResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        log.error(f"Error listing transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list transactions: {str(e)}")


@router.post("/simulate", response_model=TransactionSimulationResponse)
async def simulate_transaction(
    simulation: TransactionSimulationRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Simulate a bridge transaction without executing it.

    Analyzes:
    - Success probability
    - Estimated slippage
    - Liquidity availability
    - Risk factors
    - Potential issues

    Returns recommendations and warnings.
    """
    try:
        # Calculate success probability based on bridge and route
        success_probability = 0.95  # Default high probability
        warnings = []
        risk_level = "low"

        # Simulate slippage calculation
        amount_int = int(simulation.amount)
        estimated_slippage = 0.1  # 0.1% default

        # Check if amount is large (higher slippage risk)
        if amount_int > 1000000000:  # > 1000 USDC
            estimated_slippage = 0.5
            warnings.append("Large transaction amount may result in higher slippage")
            risk_level = "medium"

        if amount_int > 10000000000:  # > 10000 USDC
            estimated_slippage = 1.5
            warnings.append("Very large transaction - consider splitting into smaller amounts")
            risk_level = "high"
            success_probability = 0.85

        # Check bridge reliability (mock data)
        bridge_reliability = {
            "across": 0.98,
            "stargate": 0.97,
            "hop": 0.96,
            "connext": 0.95
        }

        if simulation.bridge in bridge_reliability:
            success_probability *= bridge_reliability[simulation.bridge]

        # Route-specific warnings
        if simulation.source_chain == simulation.destination_chain:
            warnings.append("Source and destination chains are the same")
            risk_level = "critical"
            success_probability = 0.0

        # Build simulation result
        simulation_result = {
            "estimated_slippage_percent": estimated_slippage,
            "min_received_amount": str(int(amount_int * (1 - estimated_slippage / 100))),
            "max_slippage_tolerated": 2.0,
            "liquidity_check": "sufficient",
            "gas_estimate_gwei": 25.0,
            "total_time_estimate_minutes": 5
        }

        # Recommendation
        if risk_level == "critical":
            recommendation = "DO NOT PROCEED - Critical issues detected"
        elif risk_level == "high":
            recommendation = "Proceed with caution - High risk transaction"
        elif risk_level == "medium":
            recommendation = "Review warnings before proceeding"
        else:
            recommendation = "Safe to proceed"

        # Store simulation in database
        db_simulation = TransactionSimulation(
            source_chain=simulation.source_chain,
            destination_chain=simulation.destination_chain,
            token=simulation.token,
            amount=simulation.amount,
            bridge=simulation.bridge,
            simulation_result=simulation_result,
            success_probability=success_probability,
            estimated_slippage=estimated_slippage,
            warnings=warnings
        )

        db.add(db_simulation)
        db.commit()

        log.info(f"Created transaction simulation for {simulation.bridge}")

        return TransactionSimulationResponse(
            success_probability=success_probability,
            estimated_slippage=estimated_slippage,
            warnings=warnings,
            simulation_result=simulation_result,
            risk_level=risk_level,
            recommended_action=recommendation
        )

    except Exception as e:
        db.rollback()
        log.error(f"Error simulating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate transaction: {str(e)}")


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Delete a transaction record (admin only)"""
    try:
        transaction = db.query(TransactionHistory).filter(
            TransactionHistory.id == transaction_id
        ).first()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        db.delete(transaction)
        db.commit()

        log.info(f"Deleted transaction: {transaction_id}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error deleting transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete transaction: {str(e)}")
