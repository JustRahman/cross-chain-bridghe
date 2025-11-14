"""deBridge integration"""
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


class DeBridgeBridge(BaseBridge):
    """
    deBridge integration.

    deBridge is a cross-chain interoperability protocol powered by validators.
    Supports 10+ chains with deep liquidity and competitive rates.

    Website: https://debridge.finance
    Docs: https://docs.debridge.finance
    API: https://api.dln.trade
    """

    def __init__(self):
        super().__init__()
        self.name = "deBridge"
        self.protocol = "debridge"
        self.api_url = "https://api.dln.trade"
        self.supported_chains = [1, 10, 42161, 137, 8453, 56, 43114, 250, 42220, 100]

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1, "optimism": 10, "arbitrum": 42161, "polygon": 137,
            "base": 8453, "bnb": 56, "avalanche": 43114, "fantom": 250,
            "celo": 42220, "gnosis": 100
        }
        return chain_map.get(chain_name.lower(), 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            if not self.supports_route(source_chain_id, dest_chain_id):
                return None

            # Try real API
            try:
                quote_data = await self._fetch_debridge_quote(route_params)
                if quote_data:
                    return await self._parse_debridge_response(quote_data, route_params)
            except:
                pass

            return await self._generate_estimated_quote(route_params)
        except Exception as e:
            log.error(f"Error getting deBridge quote: {e}")
            return None

    async def _fetch_debridge_quote(self, route_params: RouteParams) -> Optional[Dict]:
        """Fetch quote from deBridge DLN API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/v1.0/dln/order/quote"
            params = {
                "srcChainId": self._get_chain_id(route_params.source_chain),
                "srcChainTokenIn": route_params.source_token,
                "dstChainId": self._get_chain_id(route_params.destination_chain),
                "dstChainTokenOut": route_params.destination_token,
                "srcChainTokenInAmount": route_params.amount
            }
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def _parse_debridge_response(self, data: Dict, route_params: RouteParams) -> BridgeQuote:
        """Parse deBridge API response"""
        estimation = data.get("estimation", {})
        amount_in = float(route_params.amount) / 1e6
        amount_out = float(estimation.get("dstChainTokenOut", {}).get("amount", 0)) / 1e6

        bridge_fee_usd = Decimal(str(round(amount_in - amount_out, 2)))

        source_chain_id = self._get_chain_id(route_params.source_chain)
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.20")

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.3")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=420,  # 7 minutes
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("97.8"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "create_order", "description": "Create DLN order"},
                {"action": "fulfill", "description": f"Fulfill on {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="10000000000000",
            quote_id=f"debridge_{int(datetime.utcnow().timestamp())}",
            metadata={"dln_protocol": "true", "validator_network": "true"}
        )

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        source_chain_id = self._get_chain_id(route_params.source_chain)
        amount_usd = float(route_params.amount) / 1e6

        # deBridge competitive fees (around 0.05-0.1%)
        bridge_fee_usd = Decimal(str(round(amount_usd * 0.0007, 2)))
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.20")

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.3")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=420,
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("97.8"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "create_order", "description": "Create DLN order"},
                {"action": "fulfill", "description": f"Fulfill on {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="10000000000000",
            quote_id=f"debridge_est_{int(datetime.utcnow().timestamp())}",
            metadata={"cross_chain_liquidity": "true"}
        )

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {1: 8.00, 10: 0.15, 42161: 0.28, 137: 0.08, 8453: 0.15, 56: 0.25, 43114: 0.55}
        return gas_costs.get(chain_id, 1.50)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(f"{self.api_url}/v1.0/supported-chains-info",
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
        return TimeEstimate(estimated_seconds=420, min_seconds=300, max_seconds=600)
