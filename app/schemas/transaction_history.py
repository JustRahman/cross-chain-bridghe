"""Transaction history schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TransactionCreate(BaseModel):
    """Create transaction history record"""
    source_chain: str
    destination_chain: str
    token: str
    amount: str
    user_address: Optional[str] = None
    selected_bridge: str
    estimated_cost_usd: float
    estimated_time_minutes: int
    estimated_gas_cost: float
    quote_data: Optional[Dict[str, Any]] = None
    transaction_hash: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Update transaction record"""
    status: Optional[str] = None
    transaction_hash: Optional[str] = None
    actual_cost_usd: Optional[float] = None
    actual_time_minutes: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class TransactionHistoryResponse(BaseModel):
    """Transaction history response"""
    id: int
    source_chain: str
    destination_chain: str
    token: str
    amount: str
    user_address: Optional[str]
    selected_bridge: str
    estimated_cost_usd: float
    estimated_time_minutes: int
    estimated_gas_cost: float
    transaction_hash: Optional[str]
    status: str
    actual_cost_usd: Optional[float]
    actual_time_minutes: Optional[int]
    quote_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """List of transactions"""
    transactions: List[TransactionHistoryResponse]
    total: int
    page: int
    page_size: int


class TransactionSimulationRequest(BaseModel):
    """Transaction simulation request"""
    source_chain: str = Field(..., description="Source chain (e.g., ethereum, arbitrum)")
    destination_chain: str = Field(..., description="Destination chain")
    token: str = Field(..., description="Token address")
    amount: str = Field(..., description="Amount to bridge")
    bridge: str = Field(..., description="Bridge protocol to simulate")
    user_address: Optional[str] = Field(None, description="User wallet address for simulation")


class TransactionSimulationResponse(BaseModel):
    """Transaction simulation response"""
    success_probability: float = Field(..., description="Success probability (0-1)")
    estimated_slippage: float = Field(..., description="Estimated slippage percentage")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    simulation_result: Dict[str, Any] = Field(..., description="Detailed simulation data")
    risk_level: str = Field(..., description="Overall risk level: low, medium, high, critical")
    recommended_action: str = Field(..., description="Recommendation for the user")
