"""API Key model for authentication and rate limiting"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from app.db.base import Base


class APIKey(Base):
    """API Key model for customer authentication (Legacy - deprecated)"""

    __tablename__ = "legacy_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    tier = Column(String(50), default="free")  # free, starter, growth, enterprise

    # Rate limiting
    requests_per_minute = Column(Integer, default=60)
    monthly_transfer_limit = Column(Integer, default=100)
    monthly_transfers_used = Column(Integer, default=0)

    # Usage tracking
    total_requests = Column(BigInteger, default=0)
    total_transfers = Column(BigInteger, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Customer info
    email = Column(String(255), nullable=True)
    webhook_url = Column(String(512), nullable=True)

    def __repr__(self):
        return f"<APIKey(name={self.name}, tier={self.tier}, active={self.is_active})>"
