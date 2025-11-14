"""Transaction tracking and statistics schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TransactionStatus(BaseModel):
    """Transaction status information"""
    transaction_hash: str = Field(..., description="Transaction hash on source chain")
    bridge_protocol: str = Field(..., description="Bridge protocol used")
    source_chain: str = Field(..., description="Source chain")
    destination_chain: str = Field(..., description="Destination chain")
    status: str = Field(..., description="Transaction status: pending, completed, failed")
    amount: str = Field(..., description="Amount transferred")
    token: str = Field(..., description="Token address")
    created_at: datetime = Field(..., description="Transaction creation time")
    completed_at: Optional[datetime] = Field(None, description="Transaction completion time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    steps_completed: int = Field(..., description="Number of steps completed")
    total_steps: int = Field(..., description="Total number of steps")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class TransactionTrackingResponse(BaseModel):
    """Response for transaction tracking"""
    transaction: TransactionStatus
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Description of current step")


class BridgeStatistics(BaseModel):
    """Statistics for a single bridge"""
    bridge_name: str
    protocol: str
    total_transactions: int = Field(..., description="Total transactions processed")
    successful_transactions: int = Field(..., description="Successful transactions")
    failed_transactions: int = Field(..., description="Failed transactions")
    success_rate: Decimal = Field(..., description="Success rate percentage")
    average_completion_time: int = Field(..., description="Average completion time in seconds")
    total_volume_usd: Decimal = Field(..., description="Total volume in USD")
    uptime_percentage: Decimal = Field(..., description="Uptime percentage")
    cheapest_route_count: int = Field(..., description="Number of times this bridge was cheapest")
    fastest_route_count: int = Field(..., description="Number of times this bridge was fastest")


class BridgeStatisticsResponse(BaseModel):
    """Response for bridge statistics"""
    statistics: List[BridgeStatistics]
    total_transactions: int = Field(..., description="Total transactions across all bridges")
    total_volume_usd: Decimal = Field(..., description="Total volume across all bridges")
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")


class ChainStatistics(BaseModel):
    """Statistics by chain"""
    chain_name: str
    chain_id: int
    outbound_transactions: int = Field(..., description="Transactions from this chain")
    inbound_transactions: int = Field(..., description="Transactions to this chain")
    total_volume_usd: Decimal = Field(..., description="Total volume")
    most_popular_destination: Optional[str] = Field(None, description="Most popular destination chain")
    average_transaction_size_usd: Decimal = Field(..., description="Average transaction size")


class ChainStatisticsResponse(BaseModel):
    """Response for chain statistics"""
    chains: List[ChainStatistics]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
