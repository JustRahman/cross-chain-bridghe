"""Schemas for route quote and execution"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class RouteQuoteRequest(BaseModel):
    """Request schema for getting route quotes"""

    source_chain: str = Field(..., description="Source chain name (e.g., 'ethereum', 'arbitrum')")
    destination_chain: str = Field(..., description="Destination chain name")
    source_token: str = Field(..., description="Source token address")
    destination_token: str = Field(..., description="Destination token address")
    amount: str = Field(..., description="Amount to transfer (in wei or smallest unit)")
    user_address: Optional[str] = Field(None, description="User wallet address for personalized quotes")

    @validator("source_chain", "destination_chain")
    def validate_chain(cls, v):
        """Validate chain names"""
        allowed_chains = ["ethereum", "arbitrum", "optimism", "polygon", "base"]
        if v.lower() not in allowed_chains:
            raise ValueError(f"Chain must be one of: {', '.join(allowed_chains)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "source_chain": "ethereum",
                "destination_chain": "arbitrum",
                "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                "amount": "1000000000",
                "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            }
        }


class CostBreakdown(BaseModel):
    """Cost breakdown for a route"""

    bridge_fee_usd: float = Field(..., description="Bridge protocol fee in USD")
    gas_cost_source_usd: float = Field(..., description="Gas cost on source chain in USD")
    gas_cost_destination_usd: float = Field(..., description="Gas cost on destination chain in USD")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    slippage_percentage: Optional[float] = Field(None, description="Expected slippage percentage")


class RouteOption(BaseModel):
    """A single route option"""

    bridge_name: str = Field(..., description="Bridge protocol name")
    route_type: str = Field(..., description="Type of route (direct, multi-hop)")
    estimated_time_seconds: int = Field(..., description="Estimated completion time in seconds")
    cost_breakdown: CostBreakdown
    success_rate: float = Field(..., description="Historical success rate (0-100)")
    steps: List[Dict[str, Any]] = Field(..., description="Detailed steps for this route")

    # Additional metadata
    requires_approval: bool = Field(False, description="Whether token approval is needed")
    minimum_amount: Optional[str] = Field(None, description="Minimum transfer amount")
    maximum_amount: Optional[str] = Field(None, description="Maximum transfer amount")


class RouteQuoteResponse(BaseModel):
    """Response schema for route quotes"""

    routes: List[RouteOption] = Field(..., description="Available route options, sorted by cost")
    quote_id: str = Field(..., description="Unique quote ID for tracking")
    expires_at: int = Field(..., description="Unix timestamp when quote expires")

    class Config:
        json_schema_extra = {
            "example": {
                "routes": [
                    {
                        "bridge_name": "Across Protocol",
                        "route_type": "direct",
                        "estimated_time_seconds": 180,
                        "cost_breakdown": {
                            "bridge_fee_usd": 0.50,
                            "gas_cost_source_usd": 5.20,
                            "gas_cost_destination_usd": 0.10,
                            "total_cost_usd": 5.80
                        },
                        "success_rate": 99.5,
                        "steps": [
                            {"action": "approve", "description": "Approve USDC spending"},
                            {"action": "bridge", "description": "Bridge USDC to Arbitrum"}
                        ],
                        "requires_approval": True
                    }
                ],
                "quote_id": "quote_abc123xyz",
                "expires_at": 1699564800
            }
        }


class RouteExecuteRequest(BaseModel):
    """Request schema for executing a route"""

    quote_id: str = Field(..., description="Quote ID from previous quote request")
    route_index: int = Field(0, description="Index of selected route from quote response")
    user_address: str = Field(..., description="User wallet address")
    slippage_tolerance: Optional[float] = Field(0.5, description="Maximum acceptable slippage percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "quote_abc123xyz",
                "route_index": 0,
                "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "slippage_tolerance": 0.5
            }
        }


class TransactionData(BaseModel):
    """Transaction data for user to sign and submit"""

    to: str = Field(..., description="Contract address to send transaction to")
    data: str = Field(..., description="Encoded transaction data")
    value: str = Field("0", description="ETH value to send (in wei)")
    gas_limit: str = Field(..., description="Estimated gas limit")
    chain_id: int = Field(..., description="Chain ID for the transaction")


class RouteExecuteResponse(BaseModel):
    """Response schema for route execution"""

    transaction_id: str = Field(..., description="Internal transaction tracking ID")
    transactions: List[TransactionData] = Field(..., description="Transactions for user to sign")
    estimated_completion_time: int = Field(..., description="Estimated completion time in seconds")
    status_url: str = Field(..., description="URL to check transaction status")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "tx_def456uvw",
                "transactions": [
                    {
                        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        "data": "0x095ea7b3...",
                        "value": "0",
                        "gas_limit": "50000",
                        "chain_id": 1
                    }
                ],
                "estimated_completion_time": 180,
                "status_url": "/api/v1/routes/status/tx_def456uvw"
            }
        }


class TransactionStatus(BaseModel):
    """Transaction status response"""

    transaction_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    source_tx_hash: Optional[str] = Field(None, description="Source chain transaction hash")
    destination_tx_hash: Optional[str] = Field(None, description="Destination chain transaction hash")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Human-readable status message")
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "tx_def456uvw",
                "status": "completed",
                "source_tx_hash": "0xabc123...",
                "destination_tx_hash": "0xdef456...",
                "progress": 100,
                "message": "Transfer completed successfully",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:33:00Z",
                "completed_at": "2024-01-15T10:33:00Z"
            }
        }


class BatchQuoteRequest(BaseModel):
    """Request multiple route quotes in a single API call"""

    quotes: List[RouteQuoteRequest] = Field(..., description="List of quote requests", min_length=1, max_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "quotes": [
                    {
                        "source_chain": "ethereum",
                        "destination_chain": "arbitrum",
                        "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                        "amount": "1000000000"
                    },
                    {
                        "source_chain": "ethereum",
                        "destination_chain": "optimism",
                        "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        "destination_token": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                        "amount": "1000000000"
                    }
                ]
            }
        }


class BatchQuoteResult(BaseModel):
    """Result for a single quote in batch"""

    request_index: int = Field(..., description="Index of the request in the batch")
    success: bool = Field(..., description="Whether the quote was successful")
    quote: Optional[RouteQuoteResponse] = Field(None, description="Quote response if successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchQuoteResponse(BaseModel):
    """Response for batch quote request"""

    results: List[BatchQuoteResult] = Field(..., description="Results for each quote request")
    total_requests: int = Field(..., description="Total number of requests")
    successful: int = Field(..., description="Number of successful quotes")
    failed: int = Field(..., description="Number of failed quotes")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
