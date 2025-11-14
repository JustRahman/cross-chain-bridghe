"""Synapse Protocol bridge client"""
from typing import Optional, Dict
from app.services.bridge_clients.base import BridgeClient
from app.core.logging import log


class SynapseClient(BridgeClient):
    """Client for Synapse Protocol bridge"""

    def __init__(self):
        super().__init__()
        self.supported_chains = ["ethereum", "arbitrum", "optimism", "polygon", "base", "avalanche", "bsc", "fantom"]

    async def get_quote(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> Optional[Dict]:
        """Get quote from Synapse Protocol (mock implementation)"""

        if source_chain not in self.supported_chains or destination_chain not in self.supported_chains:
            return None

        try:
            amount_float = float(amount)

            bridge_fee = amount_float * 0.0008  # 0.08% fee
            gas_cost_source = 7.5
            gas_cost_dest = 0.25
            slippage = 0.003  # 0.3% slippage

            amount_out = str(int(amount_float * (1 - slippage)))

            return {
                "bridge_name": "Synapse Protocol",
                "estimated_cost_usd": bridge_fee + gas_cost_source + gas_cost_dest,
                "estimated_time_minutes": 6,
                "amount_out": amount_out,
                "gas_cost_usd": gas_cost_source + gas_cost_dest,
                "gas_cost_native": "0.003",
                "slippage": slippage * 100,
                "route_type": "direct"
            }
        except Exception as e:
            log.error(f"Error getting Synapse quote: {e}")
            return None

    def supports_route(self, source_chain: str, destination_chain: str) -> bool:
        return (source_chain in self.supported_chains and
                destination_chain in self.supported_chains and
                source_chain != destination_chain)
