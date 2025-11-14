"""Gas optimization endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.gas_optimization import (
    OptimalTimingResponse,
    TimingComparisonResponse,
    GasForecast
)
from app.services.gas_optimizer import gas_optimizer
from app.core.security import get_api_key
from app.core.logging import log


router = APIRouter()


@router.get("/optimal-timing/{chain_id}", response_model=OptimalTimingResponse)
async def get_optimal_timing(
    chain_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Analyze optimal timing for transaction based on historical gas prices.

    Provides:
    - Best hour to execute transaction
    - Potential savings by waiting
    - Price trend analysis
    - Next 4 hours forecast

    Useful for users who can delay transactions to save on gas costs.
    """
    try:
        result = gas_optimizer.analyze_optimal_timing(
            chain_id=chain_id,
            db_session=db
        )

        # Convert forecast to models
        forecasts = [GasForecast(**f) for f in result.get("forecast_next_hours", [])]
        result["forecast_next_hours"] = forecasts

        return OptimalTimingResponse(**result)

    except Exception as e:
        log.error(f"Error getting optimal timing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimal timing: {str(e)}")


@router.get("/compare-timing/{chain_id}", response_model=TimingComparisonResponse)
async def compare_timing(
    chain_id: int,
    amount_usd: float = Query(..., description="Transaction amount in USD", gt=0),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Compare executing now vs waiting for optimal timing.

    Shows side-by-side comparison of:
    - Gas costs for each option
    - Total transaction costs
    - Wait time required
    - Potential savings

    Helps users make informed decisions about transaction timing.
    """
    try:
        result = gas_optimizer.compare_timing_options(
            chain_id=chain_id,
            amount_usd=amount_usd,
            db_session=db
        )

        return TimingComparisonResponse(**result)

    except Exception as e:
        log.error(f"Error comparing timing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare timing: {str(e)}")
