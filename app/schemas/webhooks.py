"""Webhook schemas"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class WebhookCreate(BaseModel):
    """Create a new webhook"""
    url: HttpUrl = Field(..., description="Webhook URL to send notifications to")
    secret: Optional[str] = Field(None, description="Secret key for HMAC verification")
    events: List[str] = Field(..., description="Events to subscribe to")
    chain_filter: Optional[List[str]] = Field(None, description="Filter by specific chains")
    bridge_filter: Optional[List[str]] = Field(None, description="Filter by specific bridges")
    user_email: Optional[str] = Field(None, description="User email for webhook owner")


class WebhookUpdate(BaseModel):
    """Update webhook configuration"""
    url: Optional[HttpUrl] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    chain_filter: Optional[List[str]] = None
    bridge_filter: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Webhook response"""
    id: int
    url: str
    is_active: bool
    events: List[str]
    chain_filter: Optional[List[str]]
    bridge_filter: Optional[List[str]]
    user_email: Optional[str]
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """List of webhooks"""
    webhooks: List[WebhookResponse]
    total: int


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log response"""
    id: int
    webhook_id: int
    transaction_id: Optional[int]
    event_type: str
    status_code: Optional[int]
    success: bool
    attempt_number: int
    error_message: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]
    response_time_ms: Optional[int]

    class Config:
        from_attributes = True


class WebhookTestRequest(BaseModel):
    """Test webhook request"""
    webhook_id: int = Field(..., description="Webhook ID to test")
    event_type: str = Field("test.ping", description="Event type for test")


class WebhookTestResponse(BaseModel):
    """Test webhook response"""
    success: bool
    status_code: Optional[int]
    response_body: Optional[str]
    error_message: Optional[str]
    response_time_ms: int


class WebhookEvent(BaseModel):
    """Webhook event payload"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None  # HMAC signature
