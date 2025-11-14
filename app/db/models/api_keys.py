"""API key management models"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class APIKey(Base):
    """API key management - matches legacy database schema"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    # Core fields (matching actual database)
    key = Column(String(64), name='key_hash', unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    tier = Column(String(50), nullable=True)

    # Rate limiting (actual column name)
    rate_limit_per_minute = Column(Integer, name='requests_per_minute', nullable=True)

    # Transfer limits (legacy columns)
    monthly_transfer_limit = Column(Integer, nullable=True)
    monthly_transfers_used = Column(Integer, nullable=True)

    # Usage stats (actual columns)
    total_requests = Column(Integer, nullable=True, default=0)
    total_transfers = Column(Integer, nullable=True, default=0)

    # Status
    is_active = Column(Boolean, nullable=True, default=True)

    # Timestamps (actual columns)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    # Owner (actual column name)
    user_email = Column(String(255), name='email', nullable=True)

    # Additional
    webhook_url = Column(String(512), nullable=True)

    # Virtual properties for compatibility with new API code
    @property
    def rate_limit_per_hour(self):
        return (self.rate_limit_per_minute or 60) * 60

    @property
    def rate_limit_per_day(self):
        return (self.rate_limit_per_minute or 60) * 60 * 24

    @property
    def successful_requests(self):
        return self.total_requests or 0

    @property
    def failed_requests(self):
        return 0

    @property
    def is_revoked(self):
        return not self.is_active

    @property
    def allowed_endpoints(self):
        return None

    @property
    def allowed_chains(self):
        return None

    @property
    def allowed_ip_addresses(self):
        return None

    @property
    def expires_at(self):
        return None

    @property
    def revoked_at(self):
        return None

    @property
    def revoke_reason(self):
        return None

    @property
    def description(self):
        return None


class APIUsage(Base):
    """Detailed API usage logs"""
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)

    api_key_id = Column(Integer, nullable=False, index=True)

    # Request details
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)

    # Request metadata
    ip_address = Column(String(50))
    user_agent = Column(String(500), nullable=True)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(String(1000), nullable=True)
    error_type = Column(String(100), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class RateLimitLog(Base):
    """Rate limit violation log"""
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True, index=True)

    api_key_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(50), index=True)

    endpoint = Column(String(200), nullable=False)
    limit_type = Column(String(20), nullable=False)  # minute, hour, day
    limit_value = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Compatibility property
    @property
    def occurred_at(self):
        return self.created_at
