"""Structured logging configuration"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    """Configure structured JSON logging"""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Format logs as JSON in production, human-readable in development
    if settings.APP_ENV == "production":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)

    return logger


# Initialize logging
log = setup_logging()
