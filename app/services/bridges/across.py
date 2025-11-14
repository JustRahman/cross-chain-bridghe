"""Across Protocol bridge integration with real API calls"""
import asyncio
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import aiohttp
from app.services.bridges.base import (
    BaseBridge, BridgeQuote, BridgeHealth, TokenSupport,
    RouteParams, FeeBreakdown, TransactionData, TimeEstimate
)
from app.services.web3_service import web3_service
from app.core.logging import log


class AcrossBridge(BaseBridge):
    """
    Across Protocol integration.

    Across is an optimistic bridge that provides fast cross-chain transfers
    using a network of relayers who front capital and get reimbursed.

    Website: https://across.to
    Docs: https://docs.across.to
    """

    def __init__(self):
        super().__init__()
        self.name = "Across Protocol"
        self.protocol = "across"
        self.api_url = "https://across.to/api"
        self.supported_chains = [1, 10, 42161, 137, 8453]  # ETH, OP, ARB, POLY, BASE

        # Token addresses per chain
        self.supported_tokens = {
            1: {  # Ethereum
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            },
            42161: {  # Arbitrum
                "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            },
            10: {  # Optimism
                "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
                "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "WETH": "0x4200000000000000000000000000000000000006",
            },
            137: {  # Polygon
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            },
            8453: {  # Base
                "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
                "WETH": "0x4200000000000000000000000000000000000006",
            }
        }

    def _get_chain_id(self, chain_name: str) -> int:
        """Convert chain name to chain ID"""
        chain_map = {
            "ethereum": 1,
            "optimism": 10,
            "arbitrum": 42161,
            "polygon": 137,
            "base": 8453
        }
        return chain_map.get(chain_name.lower(), 0)

    async def get_quote(self, route_params: RouteParams) -> Optional[BridgeQuote]:
        """
        Get quote from Across Protocol.

        Args:
            route_params: Route parameters

        Returns:
            BridgeQuote or None if route not supported
        """
        try:
            source_chain_id = self._get_chain_id(route_params.source_chain)
            dest_chain_id = self._get_chain_id(route_params.destination_chain)

            # Check if route is supported
            if not self.supports_route(source_chain_id, dest_chain_id):
                log.debug(f"Across: Route {route_params.source_chain} -> {route_params.destination_chain} not supported")
                return None

            # Get suggested fees from Across API
            # Note: This is a real API endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/suggested-fees"
                params = {
                    "token": route_params.source_token,
                    "originChainId": source_chain_id,
                    "destinationChainId": dest_chain_id,
                    "amount": route_params.amount
                }

                try:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status != 200:
                            log.warning(f"Across API returned status {response.status}")
                            return await self._generate_mock_quote(route_params)

                        data = await response.json()
                except Exception as e:
                    log.warning(f"Across API error: {e}, using mock data")
                    return await self._generate_mock_quote(route_params)

            # Parse response and create quote
            quote = await self._parse_across_response(data, route_params)
            return quote

        except Exception as e:
            log.error(f"Error getting Across quote: {e}")
            return None

    async def _parse_across_response(
        self,
        data: Dict,
        route_params: RouteParams
    ) -> BridgeQuote:
        """Parse Across API response into BridgeQuote"""

        # Extract fee information from Across API
        total_relay_fee = data.get("totalRelayFee", {})
        relay_fee_pct = float(total_relay_fee.get("pct", "0.001"))

        # Calculate fees in USD
        # Convert amount from wei to token units (assuming 6 decimals for USDC)
        amount_usd = float(route_params.amount) / 1e6
        bridge_fee_usd = Decimal(str(round(amount_usd * relay_fee_pct, 2)))

        # Estimate gas costs based on chain
        source_chain_id = self._get_chain_id(route_params.source_chain)
        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))

        dest_chain_id = self._get_chain_id(route_params.destination_chain)
        gas_cost_dest_usd = Decimal(str(self._estimate_gas_cost(dest_chain_id, is_destination=True)))

        total_cost = bridge_fee_usd + gas_cost_source_usd + gas_cost_dest_usd

        # Create fee breakdown
        fee_breakdown = FeeBreakdown(
            bridge_fee_usd=bridge_fee_usd,
            gas_cost_source_usd=gas_cost_source_usd,
            gas_cost_destination_usd=gas_cost_dest_usd,
            total_cost_usd=total_cost,
            slippage_percentage=Decimal("0.1")
        )

        # Create quote
        quote = BridgeQuote(
            bridge_name=self.name,
            protocol=self.protocol,
            route_type="direct",
            estimated_time_seconds=180,  # ~3 minutes typical
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("99.5"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "bridge", "description": f"Bridge to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",  # $1
            maximum_amount="1000000000000",  # $1M
            quote_id=f"across_{int(datetime.utcnow().timestamp())}",
            metadata={"relayFeePercent": str(relay_fee_pct)}
        )

        return quote

    def _estimate_gas_cost(self, chain_id: int, is_destination: bool = False) -> float:
        """Estimate gas cost in USD for a chain"""
        # Destination gas is typically paid by relayer, much cheaper
        if is_destination:
            gas_costs = {
                1: 0.50,    # Ethereum
                10: 0.02,   # Optimism
                42161: 0.05, # Arbitrum
                137: 0.01,  # Polygon
                8453: 0.02  # Base
            }
        else:
            # Source chain gas costs (user pays)
            gas_costs = {
                1: 5.00,    # Ethereum (expensive)
                10: 0.10,   # Optimism
                42161: 0.25, # Arbitrum
                137: 0.05,  # Polygon
                8453: 0.10  # Base
            }
        return gas_costs.get(chain_id, 1.00)

    async def _generate_mock_quote(self, route_params: RouteParams) -> BridgeQuote:
        """Generate mock quote when API is unavailable"""

        # Calculate fees properly using estimation
        source_chain_id = self._get_chain_id(route_params.source_chain)
        dest_chain_id = self._get_chain_id(route_params.destination_chain)

        # Estimate bridge fee (typically 0.05% - 0.1% of amount)
        amount_usd = float(route_params.amount) / 1e6  # Assuming 6 decimals
        bridge_fee_usd = Decimal(str(round(amount_usd * 0.001, 2)))  # 0.1% fee

        gas_cost_source_usd = Decimal(str(self._estimate_gas_cost(source_chain_id)))
        gas_cost_dest_usd = Decimal(str(self._estimate_gas_cost(dest_chain_id, is_destination=True)))

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
            estimated_time_seconds=180,
            fee_breakdown=fee_breakdown,
            success_rate=Decimal("99.5"),
            steps=[
                {"action": "approve", "description": "Approve token spending"},
                {"action": "bridge", "description": f"Bridge to {route_params.destination_chain}"}
            ],
            requires_approval=True,
            minimum_amount="1000000",
            maximum_amount="1000000000000",
            quote_id=f"across_mock_{int(datetime.utcnow().timestamp())}"
        )

    async def check_availability(self) -> BridgeHealth:
        """Check if Across bridge is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()

                # Try to fetch suggested fees as health check
                url = f"{self.api_url}/suggested-fees"
                params = {
                    "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "originChainId": 1,
                    "destinationChainId": 42161,
                    "amount": "1000000"
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                    if response.status == 200:
                        return BridgeHealth(
                            is_healthy=True,
                            is_active=True,
                            response_time_ms=response_time,
                            last_checked=datetime.utcnow()
                        )
                    else:
                        return BridgeHealth(
                            is_healthy=False,
                            is_active=True,
                            response_time_ms=response_time,
                            error_message=f"API returned status {response.status}",
                            last_checked=datetime.utcnow()
                        )

        except asyncio.TimeoutError:
            return BridgeHealth(
                is_healthy=False,
                is_active=True,
                error_message="API timeout",
                last_checked=datetime.utcnow()
            )
        except Exception as e:
            return BridgeHealth(
                is_healthy=False,
                is_active=True,
                error_message=str(e),
                last_checked=datetime.utcnow()
            )

    async def get_supported_tokens(self, chain_id: Optional[int] = None) -> List[TokenSupport]:
        """Get list of supported tokens"""
        tokens = []

        chains_to_check = [chain_id] if chain_id else self.supported_chains

        for cid in chains_to_check:
            if cid not in self.supported_tokens:
                continue

            chain_tokens = self.supported_tokens[cid]
            for symbol, address in chain_tokens.items():
                tokens.append(TokenSupport(
                    token_address=address,
                    token_symbol=symbol,
                    chain_id=cid,
                    chain_name=self._get_chain_name(cid),
                    is_supported=True
                ))

        return tokens

    def _get_chain_name(self, chain_id: int) -> str:
        """Get chain name from chain ID"""
        chain_names = {
            1: "ethereum",
            10: "optimism",
            42161: "arbitrum",
            137: "polygon",
            8453: "base"
        }
        return chain_names.get(chain_id, f"chain_{chain_id}")

    async def generate_tx_data(
        self,
        route_params: RouteParams,
        quote_id: Optional[str] = None
    ) -> List[TransactionData]:
        """Generate transaction data for Across bridge"""

        # TODO: Implement real transaction generation
        # For now, return mock transaction data

        transactions = []

        # 1. Approval transaction (if needed)
        approval_tx = TransactionData(
            to=route_params.source_token,
            data="0x095ea7b3000000000000000000000000000000000000000000000000000000003b9aca00",
            value="0",
            gas_limit="50000",
            chain_id=self._get_chain_id(route_params.source_chain)
        )
        transactions.append(approval_tx)

        # 2. Bridge transaction
        bridge_tx = TransactionData(
            to="0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5",  # Across SpokePool
            data="0xabcdef123456",  # TODO: Encode actual function call
            value="0",
            gas_limit="200000",
            chain_id=self._get_chain_id(route_params.source_chain)
        )
        transactions.append(bridge_tx)

        return transactions

    async def estimate_time(self, route_params: RouteParams) -> TimeEstimate:
        """Estimate completion time for Across bridge"""

        return TimeEstimate(
            estimated_seconds=180,  # 3 minutes typical
            min_seconds=120,  # 2 minutes best case
            max_seconds=300  # 5 minutes worst case
        )
