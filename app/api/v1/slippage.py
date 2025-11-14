"""Slippage protection endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.slippage import (
    SlippageCalculationRequest,
    SlippageCalculationResponse,
    ProtectionParametersRequest,
    ProtectionParametersResponse,
    HistoricalSlippageResponse,
    SlippageBreakdown
)
from app.services.slippage_calculator import slippage_calculator
from app.core.security import get_api_key
from app.core.logging import log


router = APIRouter()


@router.post("/calculate", response_model=SlippageCalculationResponse)
async def calculate_slippage(
    request: SlippageCalculationRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Calculate slippage for a bridge transaction.

    Analyzes:
    - Base slippage
    - Liquidity impact
    - Bridge-specific factors
    - Risk assessment

    Returns detailed breakdown and recommendations.
    """
    try:
        result = slippage_calculator.calculate_slippage(
            bridge_name=request.bridge_name,
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            token=request.token,
            amount=request.amount,
            available_liquidity=request.available_liquidity
        )

        return SlippageCalculationResponse(
            estimated_slippage_percent=result["estimated_slippage_percent"],
            min_received_amount=result["min_received_amount"],
            max_slippage_percent=result["max_slippage_percent"],
            risk_level=result["risk_level"],
            warnings=result["warnings"],
            recommendation=result["recommendation"],
            liquidity_utilization=result["liquidity_utilization"],
            breakdown=SlippageBreakdown(**result["breakdown"])
        )

    except Exception as e:
        log.error(f"Error calculating slippage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate slippage: {str(e)}")


@router.post("/protection-parameters", response_model=ProtectionParametersResponse)
async def get_protection_parameters(
    request: ProtectionParametersRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Get slippage protection parameters for transaction execution.

    Returns parameters that can be used directly in smart contract calls:
    - Minimum amount out
    - Slippage tolerance in basis points
    - Transaction deadline

    These parameters protect users from excessive slippage and front-running.
    """
    try:
        result = slippage_calculator.calculate_protection_parameters(
            amount=request.amount,
            max_slippage_tolerance=request.max_slippage_tolerance
        )

        return ProtectionParametersResponse(**result)

    except Exception as e:
        log.error(f"Error getting protection parameters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get protection parameters: {str(e)}")


@router.get("/historical/{bridge_name}/{source_chain}/{destination_chain}", response_model=HistoricalSlippageResponse)
async def get_historical_slippage(
    bridge_name: str,
    source_chain: str,
    destination_chain: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get historical slippage data for a specific route.

    Analyzes the last 24 hours of slippage calculations to provide:
    - Average slippage
    - Maximum/minimum observed
    - Sample size

    Useful for understanding typical slippage ranges for a route.
    """
    try:
        result = slippage_calculator.analyze_historical_slippage(
            bridge_name=bridge_name,
            source_chain=source_chain,
            destination_chain=destination_chain,
            db_session=db
        )

        return HistoricalSlippageResponse(**result)

    except Exception as e:
        log.error(f"Error getting historical slippage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get historical slippage: {str(e)}")
