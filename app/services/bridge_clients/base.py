"""Base class for bridge client implementations"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
from app.core.logging import log


class BridgeClient(ABC):
    """
    Abstract base class for bridge protocol clients.

    All bridge implementations must inherit from this class and implement
    the get_quote method to fetch quotes from their respective protocols.
    """

    def __init__(self):
        self.name = self.__class__.__name__.replace("Client", "")
        log.debug(f"Initialized {self.name} bridge client")

    @abstractmethod
    async def get_quote(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> Optional[Dict]:
        """
        Get a quote for a bridge transfer.

        Args:
            source_chain: Source blockchain name
            destination_chain: Destination blockchain name
            token: Token symbol
            amount: Amount to transfer (in smallest unit)

        Returns:
            Dictionary with quote details or None if quote unavailable

            Expected format:
            {
                "bridge_name": str,
                "estimated_cost_usd": float,
                "estimated_time_minutes": int,
                "amount_out": str,
                "gas_cost_usd": float,
                "gas_cost_native": str,
                ...
            }
        """
        pass

    def supports_route(self, source_chain: str, destination_chain: str) -> bool:
        """
        Check if this bridge supports the given route.

        Override this method if your bridge has specific route limitations.
        """
        return True

    async def check_health(self) -> bool:
        """
        Check if the bridge API is healthy.

        Override this method to implement actual health checks.
        """
        return True
