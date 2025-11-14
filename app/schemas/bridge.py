"""Schemas for bridge status and health"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BridgeHealthStatus(BaseModel):
    """Health status for a single bridge"""

    name: str
    protocol: str
    is_healthy: bool
    is_active: bool
    success_rate: float = Field(..., description="Success rate percentage (0-100)")
    average_completion_time: int = Field(..., description="Average completion time in seconds")
    uptime_percentage: float = Field(..., description="Uptime percentage (0-100)")
    last_health_check: Optional[datetime] = None
    supported_chains: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Across Protocol",
                "protocol": "across",
                "is_healthy": True,
                "is_active": True,
                "success_rate": 99.5,
                "average_completion_time": 180,
                "uptime_percentage": 99.8,
                "last_health_check": "2024-01-15T10:30:00Z",
                "supported_chains": ["ethereum", "arbitrum", "optimism", "polygon"]
            }
        }


class BridgeStatusResponse(BaseModel):
    """Response for bridge status endpoint"""

    bridges: List[BridgeHealthStatus]
    total_bridges: int
    healthy_bridges: int
    checked_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "bridges": [
                    {
                        "name": "Across Protocol",
                        "protocol": "across",
                        "is_healthy": True,
                        "is_active": True,
                        "success_rate": 99.5,
                        "average_completion_time": 180,
                        "uptime_percentage": 99.8,
                        "supported_chains": ["ethereum", "arbitrum", "optimism"]
                    }
                ],
                "total_bridges": 4,
                "healthy_bridges": 3,
                "checked_at": "2024-01-15T10:30:00Z"
            }
        }


class SupportedToken(BaseModel):
    """Supported token information"""

    symbol: str
    name: str
    address: str
    decimals: int
    chain: str


class SupportedTokensResponse(BaseModel):
    """Response for supported tokens endpoint"""

    tokens: List[SupportedToken]
    total_tokens: int

    class Config:
        json_schema_extra = {
            "example": {
                "tokens": [
                    {
                        "symbol": "USDC",
                        "name": "USD Coin",
                        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        "decimals": 6,
                        "chain": "ethereum"
                    }
                ],
                "total_tokens": 45
            }
        }
