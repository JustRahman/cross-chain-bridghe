"""Webhook notification models"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Webhook(Base):
    """Webhook configuration for transaction notifications"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)

    # Webhook details
    url = Column(String(500), nullable=False)
    secret = Column(String(100))  # For HMAC verification
    is_active = Column(Boolean, default=True)

    # Event filters
    events = Column(JSON)  # ['transaction.completed', 'transaction.failed', etc.]
    chain_filter = Column(JSON, nullable=True)  # Only trigger for specific chains
    bridge_filter = Column(JSON, nullable=True)  # Only trigger for specific bridges

    # Owner
    api_key_id = Column(Integer, index=True)
    user_email = Column(String(255), nullable=True)

    # Stats
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WebhookDelivery(Base):
    """Webhook delivery attempts log"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)

    webhook_id = Column(Integer, nullable=False, index=True)
    transaction_id = Column(Integer, nullable=True, index=True)

    # Request details
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON)
    url = Column(String(500))

    # Response details
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Retry logic
    attempt_number = Column(Integer, default=1)
    success = Column(Boolean, default=False)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
