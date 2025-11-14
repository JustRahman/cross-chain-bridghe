"""LayerZero direct bridge integration"""
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


class LayerZeroBridge(BaseBridge):
    """
    LayerZero direct integration.

    LayerZero is an omnichain interoperability protocol that enables
    cross-chain messaging and asset transfers across 30+ chains.

    Website: https://layerzero.network
    Docs: https://layerzero.gitbook.io
    """

    def __init__(self):
        super().__init__()
        self.name = "LayerZero"
        self.protocol = "layerzero"
        self.api_url = "https://api-mainnet.layerzero-scan.com"
        # LayerZero supports 30+ chains
        self.supported_chains = [1, 10, 42161, 137, 8453, 56, 43114, 250, 42220, 100, 324]

    def _get_chain_id(self, chain_name: str) -> int:
        chain_map = {
            "ethereum": 1, "optimism": 10, "arbitrum": 42161, "polygon": 137,
            "base": 8453, "bnb": 56, "avalanche": 43114, "fantom": 250,
            "celo": 42220, "gnosis": 100, "zksync": 324
        }
        return chain_map.get(chain_name.lower(), 0)

    def _get_layerzero_chain_id(self, chain_id: int) -> int:
        """Convert standard chain ID to LayerZero chain ID"""
        lz_map = {
            1: 101,      # Ethereum
            10: 111,     # Optimism
            42161: 110,  # Arbitrum
            137: 109,    # Polygon
            8453: 184,   # Base
            56: 102,     # BSC
            43114: 106,  # Avalanche
            250: 112,    # Fantom
        }
        return lz_map.get(chain_id, 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            if not self.supports_route(source_chain_id, dest_chain_id):
                return None

            return await self._generate_estimated_quote(route_params)
        except Exception as e:
            log.error(f"Error getting LayerZero quote: {e}")
            return None

    async def _generate_estimated_quote(self, route_params: RouteParams) -> BridgeQuote:
        source_chain_id = self._get_chain_id(route_params.source_chain)
        dest_chain_id = self._get_chain_id(route_params.destination_chain)
        amount_usd = float(route_params.amount) / 1e6

        # LayerZero messaging fees
        source_lz_id = self._get_layerzero_chain_id(source_chain_id)
        dest_lz_id = self._get_layerzero_chain_id(dest_chain_id)

        # Estimate LayerZero messaging cost
        messaging_fee = self._estimate_lz_messaging_fee(source_lz_id, dest_lz_id)

        bridge_fee_usd = Decimal(str(messaging_fee))
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal("0.30")

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
            estimated_time_seconds=300,  # 5 minutes
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("98.0"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "send_message", "description": "Send LayerZero message"},
                {"action": "relay", "description": f"Relay to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="50000000000000",
            quote_id=f"layerzero_{int(datetime.utcnow().timestamp())}",
            metadata={
                "omnichain": "true",
                "source_lz_id": str(source_lz_id),
                "dest_lz_id": str(dest_lz_id)
            }
        )

    def _estimate_lz_messaging_fee(self, source_lz_id: int, dest_lz_id: int) -> float:
        """Estimate LayerZero messaging fee based on chains"""
        # Base messaging fees vary by destination
        base_fees = {
            101: 1.20,  # Ethereum (expensive to receive on)
            111: 0.30,  # Optimism
            110: 0.35,  # Arbitrum
            109: 0.20,  # Polygon
            184: 0.30,  # Base
            102: 0.40,  # BSC
            106: 0.50,  # Avalanche
        }
        return base_fees.get(dest_lz_id, 0.50)

    def _estimate_gas_cost(self, chain_id: int) -> float:
        gas_costs = {1: 9.00, 10: 0.18, 42161: 0.32, 137: 0.10, 8453: 0.18, 56: 0.30, 43114: 0.65}
        return gas_costs.get(chain_id, 2.00)

    async def check_availability(self) -> BridgeHealth:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(f"{self.api_url}/v1/messages",
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
        return TimeEstimate(estimated_seconds=300, min_seconds=180, max_seconds=480)
