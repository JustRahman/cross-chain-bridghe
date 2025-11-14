"""Gas optimization schemas"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class GasForecast(BaseModel):
    """Gas price forecast for future hour"""
    hour_offset: int = Field(..., description="Hours from now")
    timestamp: str = Field(..., description="Forecast timestamp")
    forecasted_price_gwei: float = Field(..., description="Forecasted gas price in gwei")
    confidence: str = Field(..., description="Forecast confidence level")


class OptimalTimingResponse(BaseModel):
    """Optimal timing analysis response"""
    current_gas_price_gwei: float = Field(..., description="Current gas price")
    average_24h_gwei: float = Field(..., description="24-hour average")
    min_24h_gwei: float = Field(..., description="24-hour minimum")
    max_24h_gwei: float = Field(..., description="24-hour maximum")
    optimal_hour_utc: int = Field(..., description="Best hour to transact (UTC)")
    optimal_price_gwei: float = Field(..., description="Price at optimal hour")
    potential_savings_percent: float = Field(..., description="Potential savings %")
    potential_savings_usd: float = Field(..., description="Potential savings in USD")
    recommendation: str = Field(..., description="execute_now, consider_waiting, or wait")
    message: str = Field(..., description="Human-readable recommendation")
    price_trend: str = Field(..., description="Current price trend")
    hourly_averages: Dict[str, float] = Field(..., description="Average price by hour")
    forecast_next_hours: List[GasForecast] = Field(..., description="Price forecasts")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class TimingOption(BaseModel):
    """Timing option details"""
    gas_cost_usd: float = Field(..., description="Gas cost in USD")
    total_cost_usd: float = Field(..., description="Total transaction cost")
    wait_time_hours: int = Field(..., description="Hours to wait")
    recommendation: str = Field(..., description="Option description")


class SavingsInfo(BaseModel):
    """Savings information"""
    amount_usd: float = Field(..., description="Savings amount in USD")
    percent: float = Field(..., description="Savings percentage")


class TimingComparisonResponse(BaseModel):
    """Comparison of timing options"""
    execute_now: TimingOption = Field(..., description="Execute immediately")
    wait_for_optimal: TimingOption = Field(..., description="Wait for optimal timing")
    savings: SavingsInfo = Field(..., description="Savings by waiting")
    best_choice: str = Field(..., description="Recommended choice")
