"""Slippage protection schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class SlippageCalculationRequest(BaseModel):
    """Request slippage calculation"""
    bridge_name: str = Field(..., description="Bridge protocol name")
    source_chain: str = Field(..., description="Source blockchain")
    destination_chain: str = Field(..., description="Destination blockchain")
    token: str = Field(..., description="Token address")
    amount: str = Field(..., description="Amount in smallest unit")
    available_liquidity: Optional[str] = Field(None, description="Available liquidity if known")


class SlippageBreakdown(BaseModel):
    """Breakdown of slippage components"""
    base_slippage: float = Field(..., description="Base slippage percentage")
    liquidity_impact: float = Field(..., description="Impact from liquidity utilization")
    bridge_factor: float = Field(..., description="Bridge-specific factor")


class SlippageCalculationResponse(BaseModel):
    """Slippage calculation result"""
    estimated_slippage_percent: float = Field(..., description="Estimated total slippage %")
    min_received_amount: str = Field(..., description="Minimum amount user will receive")
    max_slippage_percent: float = Field(..., description="Maximum tolerated slippage %")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    warnings: List[str] = Field(..., description="Warning messages")
    recommendation: str = Field(..., description="Recommendation for user")
    liquidity_utilization: float = Field(..., description="Percentage of liquidity used")
    breakdown: SlippageBreakdown = Field(..., description="Slippage breakdown")


class ProtectionParametersRequest(BaseModel):
    """Request protection parameters"""
    amount: str = Field(..., description="Transaction amount")
    max_slippage_tolerance: float = Field(2.0, ge=0.1, le=10.0, description="Max slippage tolerance %")


class ProtectionParametersResponse(BaseModel):
    """Protection parameters for transaction"""
    min_amount_out: str = Field(..., description="Minimum amount out (with slippage protection)")
    max_slippage_bps: int = Field(..., description="Max slippage in basis points")
    deadline: int = Field(..., description="Transaction deadline (Unix timestamp)")
    amount_in: str = Field(..., description="Input amount")
    protection_enabled: bool = Field(..., description="Whether protection is enabled")


class HistoricalSlippageResponse(BaseModel):
    """Historical slippage analysis"""
    average_slippage: float = Field(..., description="Average slippage over period")
    max_slippage: float = Field(..., description="Maximum observed slippage")
    min_slippage: float = Field(..., description="Minimum observed slippage")
    sample_size: int = Field(..., description="Number of samples analyzed")
    period_hours: int = Field(..., description="Time period analyzed in hours")
