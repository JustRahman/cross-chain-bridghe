"""Orbiter Finance integration"""
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


class OrbiterBridge(BaseBridge):
    """
    Orbiter Finance integration.

    Orbiter is a decentralized cross-rollup bridge focused on Layer 2 solutions.
    Ultra-fast transfers between Ethereum L2s with minimal fees.

    Website: https://orbiter.finance
    Docs: https://docs.orbiter.finance
    """

    def __init__(self):
        super().__init__()
        self.name = "Orbiter Finance"
        self.protocol = "orbiter"
        self.api_url = "https://api.orbiter.finance"
        # Focused on L2s
        self.supported_chains = [1, 10, 42161, 8453, 324, 59144]  # + zkSync Era, Linea

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1,
            "optimism": 10,
            "arbitrum": 42161,
            "base": 8453,
            "zksync": 324,
            "linea": 59144
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
            log.error(f"Error getting Orbiter quote: {e}")
            return None

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        source_chain_id = self._get_chain_id(route_params.source_chain)
        dest_chain_id = self._get_chain_id(route_params.destination_chain)
        amount_usd = float(route_params.amount) / 1e6

        # Orbiter has very low fees for L2-L2 transfers
        is_l2_to_l2 = source_chain_id != 1 and dest_chain_id != 1

        if is_l2_to_l2:
            # Ultra cheap for L2-L2
            bridge_fee_usd = Decimal("0.10")  # Fixed low fee
            gas_cost_source_usd = Decimal("0.05")
            gas_cost_dest_usd = Decimal("0.05")
            estimated_time = 120  # 2 minutes
        else:
            # Still competitive for L1 involved
            bridge_fee_usd = Decimal(str(round(amount_usd * 0.0003, 2)))
            gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
            gas_cost_dest_usd = Decimal("0.10")
            estimated_time = 300  # 5 minutes

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
            estimated_time_seconds=estimated_time,
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("99.2"),
            steps=[
                {"action": "send", "description": f"Transfer to {route_params.destination_chain} via Orbiter"}
            ],
            requires_approval=False,  # Direct transfer
            minimum_amount="5000000",  # $5 minimum
            maximum_amount="10000000000",
            quote_id=f"orbiter_{int(datetime.utcnow().timestamp())}",
            metadata={"l2_optimized": "true", "direct_transfer": "true"}
        )

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {1: 5.00, 10: 0.08, 42161: 0.15, 8453: 0.08, 324: 0.20, 59144: 0.12}
        return gas_costs.get(chain_id, 0.50)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get("https://orbiter.finance",
                                      timeout=aiohttp.ClientTimeout(total=5)) as response:
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
        source_id = self._get_chain_id(route_params.source_chain)
        dest_id = self._get_chain_id(route_params.destination_chain)
        is_l2_to_l2 = source_id != 1 and dest_id != 1

        if is_l2_to_l2:
            return TimeEstimate(estimated_seconds=120, min_seconds=60, max_seconds=180)
        else:
            return TimeEstimate(estimated_seconds=300, min_seconds=180, max_seconds=420)
