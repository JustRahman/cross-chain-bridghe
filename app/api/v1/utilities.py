"""Utility endpoints for gas prices, token prices, and calculations"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.security import get_api_key
from app.core.logging import log
from app.services.gas_estimator import gas_estimator
from app.services.token_prices import token_price_service


router = APIRouter()


class GasPriceResponse(BaseModel):
    """Gas price response model"""
    chain_id: int
    chain_name: str
    slow: float = Field(..., description="Slow gas price in gwei")
    standard: float = Field(..., description="Standard gas price in gwei")
    fast: float = Field(..., description="Fast gas price in gwei")
    rapid: float = Field(..., description="Rapid gas price in gwei")
    estimated_cost_usd: dict = Field(..., description="Estimated transaction costs")


class TokenPriceResponse(BaseModel):
    """Token price response model"""
    symbol: str
    price_usd: Decimal
    last_updated: str


class TokenDetailsResponse(BaseModel):
    """Detailed token information"""
    symbol: str
    name: str
    price_usd: float
    market_cap: Optional[float]
    volume_24h: Optional[float]
    price_change_24h: Optional[float]
    price_change_7d: Optional[float]
    last_updated: str


class SavingsCalculatorRequest(BaseModel):
    """Request for savings calculator"""
    amount_usd: Decimal = Field(..., description="Amount in USD")
    cheapest_route_cost: Decimal = Field(..., description="Cheapest route cost")
    expensive_route_cost: Decimal = Field(..., description="Most expensive route cost")


class SavingsCalculatorResponse(BaseModel):
    """Savings calculator response"""
    amount_usd: Decimal
    cheapest_route_cost: Decimal
    expensive_route_cost: Decimal
    savings_usd: Decimal
    savings_percentage: Decimal
    recommendation: str


CHAIN_NAMES = {
    1: "ethereum",
    10: "optimism",
    42161: "arbitrum",
    137: "polygon",
    8453: "base",
    56: "bnb",
    43114: "avalanche"
}


@router.get("/gas-prices/{chain_id}", response_model=GasPriceResponse)
async def get_gas_prices(
    chain_id: int,
    api_key: str = Depends(get_api_key)
):
    """
    Get current gas prices for a specific chain.

    Returns real-time gas prices in gwei for different priority levels:
    - Slow: Cheapest, slower confirmation
    - Standard: Balanced price and speed
    - Fast: Higher price, faster confirmation
    - Rapid: Highest price, fastest confirmation

    Also includes estimated transaction costs in USD for common operations.
    """
    try:
        log.info(f"Fetching gas prices for chain {chain_id}")

        gas_prices = await gas_estimator.get_gas_prices(chain_id)

        if not gas_prices:
            raise HTTPException(status_code=404, detail=f"Chain {chain_id} not supported")

        # Calculate estimated costs for different transaction types
        estimated_costs = {}
        for priority in ["slow", "standard", "fast", "rapid"]:
            # Simple transfer (21000 gas)
            simple_cost = await gas_estimator.estimate_transaction_cost(chain_id, 21000, priority)
            # Bridge transaction (200000 gas)
            bridge_cost = await gas_estimator.estimate_transaction_cost(chain_id, 200000, priority)

            estimated_costs[priority] = {
                "simple_transfer": float(simple_cost),
                "bridge_transaction": float(bridge_cost)
            }

        return GasPriceResponse(
            chain_id=chain_id,
            chain_name=CHAIN_NAMES.get(chain_id, f"chain_{chain_id}"),
            slow=gas_prices["slow"],
            standard=gas_prices["standard"],
            fast=gas_prices["fast"],
            rapid=gas_prices["rapid"],
            estimated_cost_usd=estimated_costs
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting gas prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get gas prices: {str(e)}")


@router.get("/gas-prices", response_model=dict)
async def get_all_gas_prices(
    api_key: str = Depends(get_api_key)
):
    """
    Get current gas prices for all supported chains.

    Returns a comprehensive overview of gas prices across all chains,
    making it easy to compare transaction costs.
    """
    try:
        log.info("Fetching gas prices for all chains")

        all_prices = await gas_estimator.get_all_chain_gas_prices()

        response = {}
        for chain_id, prices in all_prices.items():
            chain_name = CHAIN_NAMES.get(chain_id, f"chain_{chain_id}")
            response[chain_name] = {
                "chain_id": chain_id,
                "slow": prices["slow"],
                "standard": prices["standard"],
                "fast": prices["fast"],
                "rapid": prices["rapid"]
            }

        return {
            "chains": response,
            "total_chains": len(response)
        }

    except Exception as e:
        log.error(f"Error getting all gas prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get gas prices: {str(e)}")


@router.get("/token-price/{symbol}", response_model=TokenPriceResponse)
async def get_token_price(
    symbol: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get current price for a token.

    Supported tokens: USDC, USDT, DAI, WETH, ETH, MATIC, BNB, AVAX, FTM, OP, ARB
    """
    try:
        log.info(f"Fetching price for {symbol}")

        price = await token_price_service.get_token_price(symbol)

        if price is None:
            raise HTTPException(status_code=404, detail=f"Token {symbol} not found or not supported")

        from datetime import datetime
        return TokenPriceResponse(
            symbol=symbol.upper(),
            price_usd=price,
            last_updated=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting token price: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get token price: {str(e)}")


@router.get("/token-prices", response_model=dict)
async def get_all_token_prices(
    api_key: str = Depends(get_api_key)
):
    """
    Get current prices for all supported tokens.

    Returns a comprehensive list of token prices in USD.
    """
    try:
        log.info("Fetching all token prices")

        prices = await token_price_service.get_all_supported_prices()

        from datetime import datetime
        return {
            "tokens": {symbol: float(price) for symbol, price in prices.items()},
            "total_tokens": len(prices),
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        log.error(f"Error getting token prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get token prices: {str(e)}")


@router.get("/token-details/{symbol}", response_model=TokenDetailsResponse)
async def get_token_details(
    symbol: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get detailed information about a token.

    Includes price, market cap, trading volume, and price changes.
    """
    try:
        log.info(f"Fetching details for {symbol}")

        details = await token_price_service.get_token_details(symbol)

        if not details:
            raise HTTPException(status_code=404, detail=f"Token {symbol} not found")

        return TokenDetailsResponse(**details)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting token details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get token details: {str(e)}")


@router.post("/calculate-savings", response_model=SavingsCalculatorResponse)
async def calculate_savings(
    request: SavingsCalculatorRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Calculate savings by using the cheapest bridge route.

    Compares the cost of the cheapest route vs the most expensive route
    to show potential savings.
    """
    try:
        savings_usd = request.expensive_route_cost - request.cheapest_route_cost
        savings_pct = (savings_usd / request.expensive_route_cost) * 100

        # Generate recommendation
        if savings_pct >= 50:
            recommendation = "Excellent savings! Using the cheapest route saves you over 50% in fees."
        elif savings_pct >= 30:
            recommendation = "Great savings! The cheapest route offers significant cost reduction."
        elif savings_pct >= 10:
            recommendation = "Good savings. Consider using the cheapest route to reduce costs."
        else:
            recommendation = "Minimal difference. Consider other factors like speed and reliability."

        return SavingsCalculatorResponse(
            amount_usd=request.amount_usd,
            cheapest_route_cost=request.cheapest_route_cost,
            expensive_route_cost=request.expensive_route_cost,
            savings_usd=savings_usd,
            savings_percentage=savings_pct.quantize(Decimal("0.01")),
            recommendation=recommendation
        )

    except Exception as e:
        log.error(f"Error calculating savings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate savings: {str(e)}")
