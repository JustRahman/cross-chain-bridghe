"""Base bridge interface that all bridge implementations must follow"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass
class RouteParams:
    """Parameters for route quote request"""
    source_chain: str
    destination_chain: str
    source_token: str
    destination_token: str
    amount: str
    user_address: Optional[str] = None


@dataclass
class FeeBreakdown:
    """Detailed fee breakdown"""
    bridge_fee_usd: Decimal
    gas_cost_source_usd: Decimal
    gas_cost_destination_usd: Decimal
    total_cost_usd: Decimal
    slippage_percentage: Optional[Decimal] = None


@dataclass
class BridgeQuote:
    """Quote from a bridge protocol"""
    bridge_name: str
    protocol: str
    route_type: str  # 'direct', 'multi-hop'
    estimated_time_seconds: int
    fee_breakdown: FeeBreakdown
    success_rate: Decimal
    steps: List[Dict[str, Any]]
    requires_approval: bool = False
    minimum_amount: Optional[str] = None
    maximum_amount: Optional[str] = None
    quote_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BridgeHealth:
    """Health status of a bridge"""
    is_healthy: bool
    is_active: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_checked: Optional[datetime] = None


@dataclass
class TokenSupport:
    """Token support information"""
    token_address: str
    token_symbol: str
    chain_id: int
    chain_name: str
    is_supported: bool


@dataclass
class TransactionData:
    """Transaction data for user to sign"""
    to: str
    data: str
    value: str
    gas_limit: str
    chain_id: int


@dataclass
class TimeEstimate:
    """Time estimate for a route"""
    estimated_seconds: int
    min_seconds: int
    max_seconds: int


class BaseBridge(ABC):
    """
    Abstract base class for all bridge integrations.

    All bridge implementations must inherit from this class and implement
    all abstract methods to ensure consistency across the platform.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name: str = ""
        self.protocol: str = ""
        self.supported_chains: List[int] = []

    @abstractmethod
    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        """
        Get a quote for a specific route.

        Args:
            route_params: Route parameters including chains, tokens, and amount

        Returns:
            BridgeQuote if route is supported, None otherwise

        Raises:
            Exception: If there's an error fetching the quote
        """
        pass

    @abstractmethod
    async def check_availability(self) -> BridgeHealth:
        """
        Check if the bridge is currently available and healthy.

        Returns:
            BridgeHealth with current status
        """
        pass

    @abstractmethod
    async def get_supported_tokens(self, chain_id: Optional[int] = None) -> List[TokenSupport]:
        """
        Get list of supported tokens.

        Args:
            chain_id: Optional filter by chain ID

        Returns:
            List of supported tokens
        """
        pass

    @abstractmethod
    async def generate_tx_data(
        self,
        route_params: RouteParams,
        quote_id: Optional[str] = None
    ) -> List[TransactionData]:
        """
        Generate transaction data for user to sign and submit.

        Args:
            route_params: Route parameters
            quote_id: Optional quote ID from previous get_quote call

        Returns:
            List of transactions (may include approval + bridge transaction)
        """
        pass

    @abstractmethod
    async def estimate_time(self, route_params: RouteParams) -> TimeEstimate:
        """
        Estimate completion time for a route.

        Args:
            route_params: Route parameters

        Returns:
            TimeEstimate with min, max, and expected times
        """
        pass

    def supports_route(self, source_chain_id: int, dest_chain_id: int) -> bool:
        """
        Check if bridge supports a specific chain pair.

        Args:
            source_chain_id: Source chain ID
            dest_chain_id: Destination chain ID

        Returns:
            True if route is supported
        """
        return (source_chain_id in self.supported_chains and
                dest_chain_id in self.supported_chains and
                source_chain_id != dest_chain_id)

    async def health_check(self) -> bool:
        """
        Quick health check (simpler than check_availability).

        Returns:
            True if healthy, False otherwise
        """
        try:
            health = await self.check_availability()
            return health.is_healthy
        except Exception:
            return False
