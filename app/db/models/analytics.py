"""Analytics and historical data models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.db.base import Base


class HistoricalGasPrice(Base):
    """Historical gas price tracking"""
    __tablename__ = "historical_gas_prices"

    id = Column(Integer, primary_key=True, index=True)

    chain_id = Column(Integer, nullable=False, index=True)
    chain_name = Column(String(50), nullable=False)

    # Gas prices in gwei
    slow = Column(Float, nullable=False)
    standard = Column(Float, nullable=False)
    fast = Column(Float, nullable=False)
    rapid = Column(Float, nullable=False)

    # Gas limit estimate for standard bridge transaction
    estimated_gas_limit = Column(Integer, default=100000)

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_chain_time', 'chain_id', 'recorded_at'),
    )


class HistoricalTokenPrice(Base):
    """Historical token price tracking"""
    __tablename__ = "historical_token_prices"

    id = Column(Integer, primary_key=True, index=True)

    token_symbol = Column(String(20), nullable=False, index=True)
    token_address = Column(String(100), nullable=True)

    # Prices in USD
    price_usd = Column(Float, nullable=False)

    # Market data
    market_cap = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_token_time', 'token_symbol', 'recorded_at'),
    )


class BridgePerformanceMetric(Base):
    """Bridge performance metrics tracking"""
    __tablename__ = "bridge_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)

    bridge_name = Column(String(50), nullable=False, index=True)
    source_chain = Column(String(50), nullable=False)
    destination_chain = Column(String(50), nullable=False)

    # Performance metrics
    total_transactions = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # 0-100

    # Timing metrics
    avg_completion_time_minutes = Column(Integer, nullable=True)
    min_completion_time_minutes = Column(Integer, nullable=True)
    max_completion_time_minutes = Column(Integer, nullable=True)

    # Cost metrics
    avg_cost_usd = Column(Float, nullable=True)
    min_cost_usd = Column(Float, nullable=True)
    max_cost_usd = Column(Float, nullable=True)

    # Reliability score (0-100)
    reliability_score = Column(Float, default=0.0)

    # Calculated for period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Timestamp
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_bridge_route_period', 'bridge_name', 'source_chain', 'destination_chain', 'period_start'),
    )


class LiquiditySnapshot(Base):
    """Liquidity monitoring snapshots"""
    __tablename__ = "liquidity_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    bridge_name = Column(String(50), nullable=False, index=True)
    chain_id = Column(Integer, nullable=False, index=True)
    chain_name = Column(String(50), nullable=False)

    # Liquidity data
    token = Column(String(100), nullable=False)
    available_liquidity = Column(String(100), nullable=False)  # Store as string
    available_liquidity_usd = Column(Float, nullable=True)

    # Pool info
    total_liquidity_usd = Column(Float, nullable=True)
    utilization_rate = Column(Float, nullable=True)  # 0-100

    # Status
    is_sufficient = Column(String(20), default="unknown")  # sufficient, low, critical, unknown

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_bridge_chain_time', 'bridge_name', 'chain_id', 'recorded_at'),
    )


class SlippageCalculation(Base):
    """Slippage protection calculations"""
    __tablename__ = "slippage_calculations"

    id = Column(Integer, primary_key=True, index=True)

    bridge_name = Column(String(50), nullable=False)
    source_chain = Column(String(50), nullable=False)
    destination_chain = Column(String(50), nullable=False)
    token = Column(String(100), nullable=False)
    amount = Column(String(100), nullable=False)

    # Slippage analysis
    estimated_slippage_percent = Column(Float, nullable=False)
    min_received = Column(String(100), nullable=False)
    max_slippage_percent = Column(Float, default=1.0)

    # Risk assessment
    risk_level = Column(String(20))  # low, medium, high, critical
    warnings = Column(JSON)  # Array of warning messages

    # Liquidity context
    available_liquidity = Column(String(100), nullable=True)
    liquidity_utilization = Column(Float, nullable=True)

    # Timestamp
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    transaction_id = Column(Integer, nullable=True, index=True)
