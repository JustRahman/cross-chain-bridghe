"""Transaction model for tracking cross-chain transfers"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Transaction(Base):
    """Transaction tracking model"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # API Key reference
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)

    # Route information
    source_chain = Column(String(50), nullable=False)
    destination_chain = Column(String(50), nullable=False)
    source_token = Column(String(255), nullable=False)
    destination_token = Column(String(255), nullable=False)
    amount = Column(String(100), nullable=False)  # Store as string to preserve precision

    # Bridge used
    bridge_name = Column(String(100), nullable=False)
    bridge_id = Column(Integer, ForeignKey("bridges.id"), nullable=True)

    # Transaction hashes
    source_tx_hash = Column(String(66), index=True, nullable=True)
    destination_tx_hash = Column(String(66), index=True, nullable=True)

    # Status tracking
    status = Column(String(50), default="pending")  # pending, processing, completed, failed

    # Cost breakdown
    estimated_cost_usd = Column(Float, nullable=True)
    actual_cost_usd = Column(Float, nullable=True)
    bridge_fee_usd = Column(Float, nullable=True)
    gas_cost_usd = Column(Float, nullable=True)

    # Timing
    estimated_time_seconds = Column(Integer, nullable=True)
    actual_time_seconds = Column(Integer, nullable=True)

    # User info (hashed for privacy)
    user_address_hash = Column(String(64), index=True, nullable=True)

    # Route details
    route_data = Column(JSON, nullable=True)  # Full route details

    # Error tracking
    error_message = Column(String(1000), nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Transaction(id={self.id}, {self.source_chain}->{self.destination_chain}, status={self.status})>"
