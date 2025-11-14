"""Bridge model for storing bridge metadata"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float
from app.db.base import Base


class Bridge(Base):
    """Bridge metadata model"""

    __tablename__ = "bridges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    protocol = Column(String(50), nullable=False)  # across, stargate, connext, hop

    # Configuration
    api_url = Column(String(255), nullable=False)
    supported_chains = Column(JSON, nullable=False)  # List of chain IDs
    supported_tokens = Column(JSON, nullable=False)  # Token addresses per chain

    # Fee structure
    base_fee_percentage = Column(Float, default=0.0)
    min_fee_usd = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)

    # Performance metrics
    success_rate = Column(Float, default=100.0)
    average_completion_time = Column(Integer, default=0)  # seconds
    total_volume_usd = Column(Float, default=0.0)

    # Reliability tracking
    uptime_percentage = Column(Float, default=100.0)
    last_health_check = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Contract addresses
    contracts = Column(JSON, nullable=True)  # Bridge contract addresses per chain

    def __repr__(self):
        return f"<Bridge(name={self.name}, protocol={self.protocol}, active={self.is_active})>"
