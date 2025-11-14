"""Analytics dashboard schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class EndpointStats(BaseModel):
    """Statistics for a specific endpoint"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time_ms: int
    min_response_time_ms: int
    max_response_time_ms: int


class ChainStats(BaseModel):
    """Statistics for a specific chain"""
    chain_name: str
    chain_id: int
    total_transactions: int
    total_volume_usd: float
    average_gas_price_gwei: float
    most_popular_bridge: str


class BridgePopularity(BaseModel):
    """Bridge usage popularity"""
    bridge_name: str
    total_uses: int
    success_rate: float
    average_cost_usd: float
    average_time_minutes: int


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    timestamp: str
    value: float


class SystemHealthMetrics(BaseModel):
    """Overall system health metrics"""
    total_requests_24h: int
    total_transactions_24h: int
    average_response_time_ms: int
    error_rate_percent: float
    active_api_keys: int
    rate_limit_violations_24h: int
    webhook_deliveries_24h: int
    webhook_success_rate: float


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics dashboard"""
    system_health: SystemHealthMetrics
    top_endpoints: List[EndpointStats] = Field(..., description="Top 10 endpoints by usage")
    chain_statistics: List[ChainStats] = Field(..., description="Stats per chain")
    bridge_popularity: List[BridgePopularity] = Field(..., description="Bridge usage ranking")
    requests_over_time: List[TimeSeriesDataPoint] = Field(..., description="Request volume over time")
    error_rate_over_time: List[TimeSeriesDataPoint] = Field(..., description="Error rate over time")
    generated_at: datetime


class UserAnalyticsResponse(BaseModel):
    """Analytics for a specific user/API key"""
    api_key_name: str
    user_email: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    total_cost_usd: float = Field(..., description="Estimated total gas costs")
    favorite_chains: List[str]
    favorite_bridges: List[str]
    most_used_endpoints: List[str]
    requests_per_day_average: float
    first_request: Optional[datetime]
    last_request: Optional[datetime]


class BridgeReliabilityScore(BaseModel):
    """Reliability score for a bridge"""
    bridge_name: str
    reliability_score: float = Field(..., ge=0, le=100, description="Score 0-100")
    success_rate: float
    average_completion_time_minutes: int
    total_transactions_analyzed: int
    uptime_percentage: float
    cost_rating: str = Field(..., description="cheap, moderate, expensive")
    speed_rating: str = Field(..., description="fast, moderate, slow")
    recommendation: str


class ReliabilityScoresResponse(BaseModel):
    """Reliability scores for all bridges"""
    scores: List[BridgeReliabilityScore]
    analysis_period_hours: int
    last_updated: datetime
