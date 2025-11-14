"""API key management schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Create new API key"""
    name: str = Field(..., min_length=3, max_length=100, description="API key name/label")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    user_email: EmailStr = Field(..., description="Owner email address")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Requests per minute")
    rate_limit_per_hour: int = Field(1000, ge=1, le=100000, description="Requests per hour")
    rate_limit_per_day: int = Field(10000, ge=1, le=1000000, description="Requests per day")
    allowed_endpoints: Optional[List[str]] = Field(None, description="Allowed endpoints (null = all)")
    allowed_chains: Optional[List[str]] = Field(None, description="Allowed chains (null = all)")
    allowed_ip_addresses: Optional[List[str]] = Field(None, description="IP whitelist (null = all)")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration")


class APIKeyUpdate(BaseModel):
    """Update API key configuration"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    allowed_endpoints: Optional[List[str]] = None
    allowed_chains: Optional[List[str]] = None
    allowed_ip_addresses: Optional[List[str]] = None


class APIKeyResponse(BaseModel):
    """API key response (without sensitive key value)"""
    id: int
    name: str
    description: Optional[str]
    user_email: str
    is_active: bool
    is_revoked: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_per_day: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    last_used_at: Optional[datetime]
    allowed_endpoints: Optional[List[str]]
    allowed_chains: Optional[List[str]]
    allowed_ip_addresses: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoke_reason: Optional[str]

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """API key created response (includes actual key - shown once)"""
    key: str = Field(..., description="API key value - save this, it won't be shown again!")


class APIKeyListResponse(BaseModel):
    """List of API keys"""
    keys: List[APIKeyResponse]
    total: int


class APIKeyRevokeRequest(BaseModel):
    """Revoke API key"""
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for revocation")


class APIKeyUsageStats(BaseModel):
    """API key usage statistics"""
    api_key_id: int
    api_key_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    requests_last_24h: int
    requests_last_hour: int
    most_used_endpoint: Optional[str]
    most_used_chain: Optional[str]
    average_response_time_ms: Optional[int]
    last_used_at: Optional[datetime]


class APIKeyUsageResponse(BaseModel):
    """Detailed API key usage"""
    stats: APIKeyUsageStats
    rate_limits: Dict[str, Dict[str, int]] = Field(..., description="Current rate limit status")
    recent_errors: List[Dict[str, Any]] = Field(..., description="Recent error logs")
