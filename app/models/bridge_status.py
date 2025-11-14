"""Bridge status model for health monitoring"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from app.db.base import Base


class BridgeStatus(Base):
    """Bridge health status history"""

    __tablename__ = "bridge_status"

    id = Column(Integer, primary_key=True, index=True)
    bridge_id = Column(Integer, ForeignKey("bridges.id"), nullable=False, index=True)

    # Status check results
    is_healthy = Column(Boolean, nullable=False)
    response_time_ms = Column(Float, nullable=True)

    # Error tracking
    error_message = Column(String(1000), nullable=True)
    error_type = Column(String(100), nullable=True)

    # Chain-specific status
    chain_id = Column(Integer, nullable=True)
    chain_name = Column(String(50), nullable=True)

    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<BridgeStatus(bridge_id={self.bridge_id}, healthy={self.is_healthy}, checked_at={self.checked_at})>"
