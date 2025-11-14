"""Hop Protocol bridge integration"""
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


class HopBridge(BaseBridge):
    """
    Hop Protocol integration.

    Hop is a scalable rollup-to-rollup general token bridge.
    It allows users to send tokens from one rollup to another almost immediately
    without waiting for the rollup's challenge period.

    Website: https://hop.exchange
    Docs: https://docs.hop.exchange
    API: https://api.hop.exchange/v1
    """

    def __init__(self):
        super().__init__()
        self.name = "Hop Protocol"
        self.protocol = "hop"
        self.api_url = "https://api.hop.exchange/v1"
        self.supported_chains = [1, 10, 42161, 137, 8453, 100]  # ETH, OP, ARB, POLY, BASE, xDAI

        self.supported_tokens_map = {
            "ETH": ["ethereum", "optimism", "arbitrum", "polygon", "base"],
            "USDC": ["ethereum", "optimism", "arbitrum", "polygon"],
            "USDT": ["ethereum", "optimism", "arbitrum", "polygon"],
            "DAI": ["ethereum", "optimism", "arbitrum", "polygon"],
            "MATIC": ["ethereum", "polygon"]
        }

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1,
            "optimism": 10,
            "arbitrum": 42161,
            "polygon": 137,
            "base": 8453,
            "gnosis": 100
        }
        return chain_map.get(chain_name.lower(), 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        """Get quote from Hop Protocol API"""
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            if not self.supports_route(source_chain_id, dest_chain_id):
                return None

            # Try to get real quote from Hop API
            try:
                quote_data = await self._fetch_hop_quote(route_params)
                if quote_data:
                    return await self._parse_hop_response(quote_data, route_params)
            except:
                pass

            # Fallback to estimation
            return await self._generate_estimated_quote(route_params)

        except Exception as e:
            log.error(f"Error getting Hop quote: {e}")
            return None

    async def _fetch_hop_quote(self, route_params: RouteParams) -> Optional[Dict]:
        """Fetch quote from Hop API"""
        async with aiohttp.ClientSession() as session:
            # Hop API endpoint for quotes
            url = f"{self.api_url}/quote"

            params = {
                "amount": route_params.amount,
                "token": "USDC",  # Simplified for now
                "fromChainId": self._get_chain_id(route_params.source_chain),
                "toChainId": self._get_chain_id(route_params.destination_chain),
                "slippage": "0.5"
            }

            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def _parse_hop_response(self, data: Dict, route_params: RouteParams) -> BridgeQuote:
        """Parse Hop API response"""

        # Extract fees from response
        amount_usd = float(route_params.amount) / 1e6
        bonder_fee = float(data.get("bonderFee", 0)) / 1e6
        destination_tx_fee = float(data.get("destinationTxFee", 0)) / 1e6

        bridge_fee_usd = Decimal(str(round(bonder_fee, 2)))

        source_chain_id = self._get_chain_id(route_params.source_chain)
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal(str(round(destination_tx_fee, 2)))

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.5")
        )

        return BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=300,
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("97.5"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "bridge", "description": f"Bridge to {route_params.destination_chain} via AMM"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="10000000000000",  # $10M
            quote_id=f"hop_{int(datetime.utcnow().timestamp())}",
            metadata={"amm_based": "true"}
        )

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        """Generate estimated quote when API is unavailable"""

        source_chain_id = self._get_chain_id(route_params.source_chain)
        dest_chain_id = self._get_chain_id(route_params.destination_chain)

        amount_usd = float(route_params.amount) / 1e6

        # Hop fees vary: bonder fee + LP fee
        bonder_fee_pct = 0.0004  # 0.04%
        lp_fee_pct = 0.0004      # 0.04%
        total_fee_pct = bonder_fee_pct + lp_fee_pct

        bridge_fee_usd = Decimal(str(round(amount_usd * total_fee_pct, 2)))
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal(str(0.50))  # Bonder pays gas

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
            estimated_time_seconds=420,  # 7 minutes
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("96.0"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "bridge", "description": f"Bridge to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="10000000000000",
            quote_id=f"hop_est_{int(datetime.utcnow().timestamp())}"
        )

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {
            1: 6.00,
            10: 0.12,
            42161: 0.28,
            137: 0.06,
            8453: 0.12,
            100: 0.02
        }
        return gas_costs.get(chain_id, 1.00)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()

                async with session.get(
                    f"{self.api_url}/available-routes",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                    return BridgeHealth(
                        is_healthy=response.status == 200,
                        is_active=True,
                        response_time_ms=response_time,
                        last_checked=datetime.utcnow()
                    )
        except:
            return BridgeHealth(is_healthy=False, is_active=True, last_checked=datetime.utcnow())

    async def get_supported_tokens(self, chain_id: Optional[int] = None) -> List[TokenSupport]:
        return []

    async def generate_tx_data(self, route_params: RouteParams, quote_id: Optional[str] = None) -> List[TransactionData]:
        return []

    async def estimate_time(self, route_params: RouteParams) -> TimeEstimate:
        return TimeEstimate(estimated_seconds=420, min_seconds=300, max_seconds=600)
