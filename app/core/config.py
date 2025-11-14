"""Application configuration using Pydantic settings"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Cross-Chain Bridge Aggregator"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(..., min_length=32)
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @validator("ALLOWED_ORIGINS")
    def parse_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into a list"""
        return [origin.strip() for origin in v.split(",")]

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Blockchain RPC Endpoints
    ETHEREUM_RPC_URL: str
    ETHEREUM_RPC_FALLBACK_URL: Optional[str] = None

    ARBITRUM_RPC_URL: str
    ARBITRUM_RPC_FALLBACK_URL: Optional[str] = None

    OPTIMISM_RPC_URL: str
    OPTIMISM_RPC_FALLBACK_URL: Optional[str] = None

    POLYGON_RPC_URL: str
    POLYGON_RPC_FALLBACK_URL: Optional[str] = None

    BASE_RPC_URL: str
    BASE_RPC_FALLBACK_URL: Optional[str] = None

    # Bridge API Configuration
    ACROSS_API_URL: str = "https://across.to/api"
    STARGATE_API_URL: str = "https://api.stargate.finance"
    CONNEXT_API_URL: str = "https://api.connext.network"
    HOP_API_URL: str = "https://api.hop.exchange"

    # DEX Aggregator APIs
    VELORA_API_URL: str = "https://api.velora.xyz/v6.2"
    OPENOCEAN_API_URL: str = "https://open-api.openocean.finance/v4"
    ZEROX_API_URL: str = "https://api.0x.org"

    # Legacy (keep for backwards compatibility)
    ONEINCH_API_KEY: Optional[str] = None
    ONEINCH_API_URL: str = "https://api.1inch.dev/swap/v5.2"

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Transaction Monitoring
    TX_MONITOR_INTERVAL: int = 10
    TX_TIMEOUT: int = 1800
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    WEBHOOK_RETRY_DELAY: int = 60

    # Feature Flags
    ENABLE_BRIDGE_HEALTH_MONITORING: bool = True
    ENABLE_CIRCUIT_BREAKER: bool = True
    ENABLE_TRANSACTION_SIMULATION: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Chain configuration
CHAIN_CONFIG = {
    "ethereum": {
        "chain_id": 1,
        "name": "Ethereum",
        "rpc_url": settings.ETHEREUM_RPC_URL,
        "rpc_fallback": settings.ETHEREUM_RPC_FALLBACK_URL,
        "explorer": "https://etherscan.io",
        "native_token": "ETH",
    },
    "arbitrum": {
        "chain_id": 42161,
        "name": "Arbitrum One",
        "rpc_url": settings.ARBITRUM_RPC_URL,
        "rpc_fallback": settings.ARBITRUM_RPC_FALLBACK_URL,
        "explorer": "https://arbiscan.io",
        "native_token": "ETH",
    },
    "optimism": {
        "chain_id": 10,
        "name": "Optimism",
        "rpc_url": settings.OPTIMISM_RPC_URL,
        "rpc_fallback": settings.OPTIMISM_RPC_FALLBACK_URL,
        "explorer": "https://optimistic.etherscan.io",
        "native_token": "ETH",
    },
    "polygon": {
        "chain_id": 137,
        "name": "Polygon PoS",
        "rpc_url": settings.POLYGON_RPC_URL,
        "rpc_fallback": settings.POLYGON_RPC_FALLBACK_URL,
        "explorer": "https://polygonscan.com",
        "native_token": "MATIC",
    },
    "base": {
        "chain_id": 8453,
        "name": "Base",
        "rpc_url": settings.BASE_RPC_URL,
        "rpc_fallback": settings.BASE_RPC_FALLBACK_URL,
        "explorer": "https://basescan.org",
        "native_token": "ETH",
    },
}
