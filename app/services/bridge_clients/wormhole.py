"""Wormhole bridge client"""
from typing import Optional, Dict
from app.services.bridge_clients.base import BridgeClient
from app.core.logging import log


class WormholeClient(BridgeClient):
    """Client for Wormhole bridge"""

    def __init__(self):
        super().__init__()
        self.supported_chains = ["ethereum", "arbitrum", "optimism", "polygon", "base", "avalanche", "bsc", "fantom", "solana"]

    async def get_quote(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> Optional[Dict]:
        """Get quote from Wormhole (mock implementation)"""

        if source_chain not in self.supported_chains or destination_chain not in self.supported_chains:
            return None

        try:
            amount_float = float(amount)

            bridge_fee = amount_float * 0.00025  # 0.025% fee - very low
            gas_cost_source = 10.0  # Higher gas due to guardian signatures
            gas_cost_dest = 0.5
            slippage = 0.001  # 0.1% slippage

            amount_out = str(int(amount_float * (1 - slippage)))

            return {
                "bridge_name": "Wormhole",
                "estimated_cost_usd": bridge_fee + gas_cost_source + gas_cost_dest,
                "estimated_time_minutes": 10,  # Longer due to guardian finality
                "amount_out": amount_out,
                "gas_cost_usd": gas_cost_source + gas_cost_dest,
                "gas_cost_native": "0.004",
                "slippage": slippage * 100,
                "route_type": "direct"
            }
        except Exception as e:
            log.error(f"Error getting Wormhole quote: {e}")
            return None

    def supports_route(self, source_chain: str, destination_chain: str) -> bool:
        return (source_chain in self.supported_chains and
                destination_chain in self.supported_chains and
                source_chain != destination_chain)
