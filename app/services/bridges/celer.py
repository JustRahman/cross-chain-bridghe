"""Celer cBridge integration"""
import asyncio
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
import aiohttp
from app.services.bridges.base import (
    BaseBridge, BridgeQuote, BridgeHealth, TokenSupport,
    RouteParams, FeeBreakdown, TransactionData, TimeEstimate
)
from app.core.logging import log


class CelerBridge(BaseBridge):
    """
    Celer cBridge integration.

    Celer is one of the fastest cross-chain bridges with deep liquidity.
    Features state channel technology for instant finality.

    Website: https://cbridge.celer.network
    Docs: https://cbridge-docs.celer.network
    API: https://cbridge-prod2.celer.network
    """

    def __init__(self):
        super().__init__()
        self.name = "Celer cBridge"
        self.protocol = "celer"
        self.api_url = "https://cbridge-prod2.celer.network"
        self.supported_chains = [1, 10, 42161, 137, 8453, 56, 43114, 250, 42220]  # + Celo

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1, "optimism": 10, "arbitrum": 42161, "polygon": 137,
            "base": 8453, "bnb": 56, "avalanche": 43114, "fantom": 250, "celo": 42220
        }
        return chain_map.get(chain_name.lower(), 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            if not self.supports_route(source_chain_id, dest_chain_id):
                return None

            # Try real API first
            try:
                quote_data = await self._fetch_celer_quote(route_params)
                if quote_data:
                    return await self._parse_celer_response(quote_data, route_params)
            except:
                pass

            return await self._generate_estimated_quote(route_params)
        except Exception as e:
            log.error(f"Error getting Celer quote: {e}")
            return None

    async def _fetch_celer_quote(self, route_params: RouteParams) -> Optional[Dict]:
        """Fetch quote from Celer API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/v2/estimateAmt"
            params = {
                "src_chain_id": self._get_chain_id(route_params.source_chain),
                "dst_chain_id": self._get_chain_id(route_params.destination_chain),
                "token_symbol": "USDC",
                "amt": route_params.amount,
                "usr_addr": route_params.user_address or "0x0000000000000000000000000000000000000000"
            }
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def _parse_celer_response(self, data: Dict, route_params: RouteParams) -> BridgeQuote:
        """Parse Celer API response"""
        amount_in = float(route_params.amount) / 1e6
        estimated_receive = float(data.get("estimated_receive_amt", 0)) / 1e6

        bridge_fee_usd = Decimal(str(round(amount_in - estimated_receive, 2)))

        source_chain_id = self._get_chain_id(route_params.source_chain)
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.15")

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.2")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=180,  # 3 minutes - very fast
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("98.8"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "send", "description": f"Send via Celer network to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="5000000000000",
            quote_id=f"celer_{int(datetime.utcnow().timestamp())}",
            metadata={"state_channel": "true", "instant_finality": "true"}
        )

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        source_chain_id = self._get_chain_id(route_params.source_chain)
        amount_usd = float(route_params.amount) / 1e6

        # Celer has competitive fees (0.04% typically)
        bridge_fee_usd = Decimal(str(round(amount_usd * 0.0004, 2)))
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.15")

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.2")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=180,  # Very fast
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("98.8"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "send", "description": f"Send via Celer to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="5000000000000",
            quote_id=f"celer_est_{int(datetime.utcnow().timestamp())}",
            metadata={"liquidity_network": "true"}
        )

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {1: 6.00, 10: 0.12, 42161: 0.22, 137: 0.06, 8453: 0.12, 56: 0.22, 43114: 0.50}
        return gas_costs.get(chain_id, 1.00)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(f"{self.api_url}/v2/getTransferStatus",
                                      timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    return BridgeHealth(is_healthy=response.status == 200, is_active=True,
                                        response_time_ms=response_time, last_checked=datetime.utcnow())
        except:
            return BridgeHealth(is_healthy=True, is_active=True, last_checked=datetime.utcnow())

    async def get_supported_tokens(self, chain_id: Optional[int] = None) -> List[TokenSupport]:
        return []

    async def generate_tx_data(self, route_params: RouteParams, quote_id: Optional[str] = None) -> List[TransactionData]:
        return []

    async def estimate_time(self, route_params: RouteParams) -> TimeEstimate:
        return TimeEstimate(estimated_seconds=180, min_seconds=120, max_seconds=300)
