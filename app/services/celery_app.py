"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "nexbridge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule - Periodic tasks
celery_app.conf.beat_schedule = {
    # Collect gas prices every 5 minutes
    "collect-gas-prices": {
        "task": "collect_gas_prices",
        "schedule": 300.0,  # 5 minutes in seconds
    },
    # Collect token prices every 5 minutes
    "collect-token-prices": {
        "task": "collect_token_prices",
        "schedule": 300.0,  # 5 minutes in seconds
    },
    # Calculate bridge performance metrics every hour
    "calculate-bridge-metrics": {
        "task": "calculate_bridge_performance_metrics",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Update liquidity snapshots every 10 minutes
    "update-liquidity": {
        "task": "update_liquidity_snapshots",
        "schedule": 600.0,  # 10 minutes
    },
    # Cleanup old data daily at 2 AM
    "cleanup-old-data": {
        "task": "cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

# Auto-discover tasks from all app modules
celery_app.autodiscover_tasks(["app.services.tasks"])
