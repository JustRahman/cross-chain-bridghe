"""Celery tasks module"""
from app.services.tasks.historical_data import (
    collect_historical_gas_prices,
    collect_historical_token_prices,
    cleanup_old_historical_data
)
from app.services.tasks.bridge_metrics import (
    calculate_bridge_performance_metrics,
    update_liquidity_snapshots
)

__all__ = [
    "collect_historical_gas_prices",
    "collect_historical_token_prices",
    "cleanup_old_historical_data",
    "calculate_bridge_performance_metrics",
    "update_liquidity_snapshots",
]
