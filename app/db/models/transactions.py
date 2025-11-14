"""Transaction history database models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.db.base import Base


class TransactionHistory(Base):
    """Store all bridge transaction requests and results"""
    __tablename__ = "transaction_history"

    id = Column(Integer, primary_key=True, index=True)

    # Request details
    source_chain = Column(String(50), nullable=False, index=True)
    destination_chain = Column(String(50), nullable=False, index=True)
    token = Column(String(100), nullable=False)
    amount = Column(String(100), nullable=False)  # Store as string to avoid precision loss
    user_address = Column(String(100), index=True)

    # Selected route
    selected_bridge = Column(String(50), index=True)
    estimated_cost_usd = Column(Float)
    estimated_time_minutes = Column(Integer)
    estimated_gas_cost = Column(Float)

    # Transaction details
    transaction_hash = Column(String(100), unique=True, index=True)
    status = Column(String(20), default="pending")  # pending, completed, failed, cancelled

    # Actual results
    actual_cost_usd = Column(Float, nullable=True)
    actual_time_minutes = Column(Integer, nullable=True)

    # Additional data
    quote_data = Column(JSON)  # Store full quote response
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # API tracking
    api_key_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(50))


class TransactionSimulation(Base):
    """Store transaction simulation results"""
    __tablename__ = "transaction_simulations"

    id = Column(Integer, primary_key=True, index=True)

    source_chain = Column(String(50), nullable=False)
    destination_chain = Column(String(50), nullable=False)
    token = Column(String(100), nullable=False)
    amount = Column(String(100), nullable=False)

    bridge = Column(String(50), nullable=False)
    simulation_result = Column(JSON)  # Full simulation data
    success_probability = Column(Float)  # 0-1
    estimated_slippage = Column(Float)

    warnings = Column(JSON)  # Array of warning messages

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    api_key_id = Column(Integer, nullable=True)
