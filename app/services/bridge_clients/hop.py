"""Hop Protocol bridge client"""
from typing import Optional, Dict
from app.services.bridge_clients.base import BridgeClient
from app.core.logging import log


class HopClient(BridgeClient):
    """Client for Hop Protocol bridge"""

    def __init__(self):
        super().__init__()
        self.supported_chains = ["ethereum", "arbitrum", "optimism", "polygon", "base"]

    async def get_quote(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> Optional[Dict]:
        """Get quote from Hop Protocol (mock implementation)"""

        if source_chain not in self.supported_chains or destination_chain not in self.supported_chains:
            log.debug(f"Hop doesn't support {source_chain} -> {destination_chain}")
            return None

        try:
            amount_float = float(amount)

            # Mock quote data - Hop has higher fees but good liquidity
            bridge_fee = amount_float * 0.002  # 0.2% fee
            gas_cost_source = 6.0
            gas_cost_dest = 0.05
            slippage = 0.003  # 0.3% slippage

            amount_out = str(int(amount_float * (1 - slippage)))

            return {
                "bridge_name": "Hop Protocol",
                "estimated_cost_usd": bridge_fee + gas_cost_source + gas_cost_dest,
                "estimated_time_minutes": 5,  # 5 minutes
                "amount_out": amount_out,
                "gas_cost_usd": gas_cost_source + gas_cost_dest,
                "gas_cost_native": "0.0025",
                "slippage": slippage * 100,
                "route_type": "direct"
            }
        except Exception as e:
            log.error(f"Error getting Hop quote: {e}")
            return None

    def supports_route(self, source_chain: str, destination_chain: str) -> bool:
        return (source_chain in self.supported_chains and
                destination_chain in self.supported_chains and
                source_chain != destination_chain)
