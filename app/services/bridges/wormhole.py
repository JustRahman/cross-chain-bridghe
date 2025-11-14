"""Wormhole bridge integration"""
import asyncio
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import aiohttp
from app.services.bridges.base import (
    BaseBridge, BridgeQuote, BridgeHealth, TokenSupport,
    RouteParams, FeeBreakdown, TransactionData, TimeEstimate
)
from app.core.logging import log


class WormholeBridge(BaseBridge):
    """
    Wormhole integration.

    Wormhole is a generic message passing protocol that enables communication
    between blockchains. Supports 20+ chains.

    Website: https://wormhole.com
    Docs: https://docs.wormhole.com
    """

    def __init__(self):
        super().__init__()
        self.name = "Wormhole"
        self.protocol = "wormhole"
        self.api_url = "https://api.wormholescan.io"
        self.supported_chains = [1, 10, 42161, 137, 8453, 56, 43114, 250, 1284]  # Many more!

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1, "optimism": 10, "arbitrum": 42161, "polygon": 137,
            "base": 8453, "bnb": 56, "avalanche": 43114, "fantom": 250, "moonbeam": 1284
        }
        return chain_map.get(chain_name.lower(), 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            if not self.supports_route(source_chain_id, dest_chain_id):
                return None

            return await self._generate_estimated_quote(route_params)
        except Exception as e:
            log.error(f"Error getting Wormhole quote: {e}")
            return None

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        source_chain_id = self._get_chain_id(route_params.source_chain)
        amount_usd = float(route_params.amount) / 1e6

        # Wormhole has minimal fees (just gas for relaying)
        bridge_fee_usd = Decimal("0.25")  # Fixed relayer fee
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.50")  # Destination relayer fee

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.1")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=600,  # 10 minutes (slower due to finality)
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("95.0"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "lock", "description": "Lock tokens in Wormhole contract"},
                {"action": "wait", "description": "Wait for guardian signatures"},
                {"action": "redeem", "description": f"Redeem on {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="10000000000000",
            quote_id=f"wormhole_{int(datetime.utcnow().timestamp())}",
            metadata={"guardian_network": "true", "chains_supported": "20+"}
        )

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {1: 10.00, 10: 0.15, 42161: 0.30, 137: 0.08, 8453: 0.15, 56: 0.30, 43114: 0.60}
        return gas_costs.get(chain_id, 2.00)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(f"{self.api_url}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    return BridgeHealth(is_healthy=response.status == 200, is_active=True,
                                        response_time_ms=response_time, last_checked=datetime.utcnow())
        except:
            return BridgeHealth(is_healthy=False, is_active=True, last_checked=datetime.utcnow())

    async def get_supported_tokens(self, chain_id: Optional[int] = None) -> List[TokenSupport]:
        return []

    async def generate_tx_data(self, route_params: RouteParams, quote_id: Optional[str] = None) -> List[TransactionData]:
        return []

    async def estimate_time(self, route_params: RouteParams) -> TimeEstimate:
        return TimeEstimate(estimated_seconds=600, min_seconds=420, max_seconds=900)
