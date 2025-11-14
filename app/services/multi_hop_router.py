"""Multi-hop routing algorithm for cross-chain bridges"""
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.bridge_clients.base import BridgeClient
from app.services.bridge_clients.across import AcrossClient
from app.services.bridge_clients.hop import HopClient
from app.services.bridge_clients.stargate import StargateClient
from app.services.bridge_clients.synapse import SynapseClient
from app.services.bridge_clients.celer import CelerClient
from app.services.bridge_clients.connext import ConnextClient
from app.services.bridge_clients.multichain import MultichainClient
from app.services.bridge_clients.wormhole import WormholeClient
from app.services.bridge_clients.layerzero import LayerZeroClient
from app.services.bridge_clients.socket import SocketClient
from app.core.logging import log


@dataclass
class RouteHop:
    """Single hop in a multi-hop route"""
    source_chain: str
    destination_chain: str
    bridge_name: str
    token: str
    amount_in: str
    amount_out: str
    estimated_cost_usd: float
    estimated_time_minutes: int
    gas_cost_native: str
    gas_cost_usd: float


@dataclass
class MultiHopRoute:
    """Complete multi-hop route"""
    hops: List[RouteHop]
    total_cost_usd: float
    total_time_minutes: int
    final_amount: str
    slippage_percent: float
    is_better_than_direct: bool
    savings_usd: Optional[float] = None


class MultiHopRouter:
    """Find optimal routes including multi-hop paths"""

    def __init__(self):
        """Initialize bridge clients"""
        self.bridges = {
            "across": AcrossClient(),
            "hop": HopClient(),
            "stargate": StargateClient(),
            "synapse": SynapseClient(),
            "celer": CelerClient(),
            "connext": ConnextClient(),
            "multichain": MultichainClient(),
            "wormhole": WormholeClient(),
            "layerzero": LayerZeroClient(),
            "socket": SocketClient()
        }

        # Common intermediate chains
        self.intermediate_chains = [
            "ethereum",
            "arbitrum",
            "optimism",
            "polygon",
            "base"
        ]

    async def find_best_route(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        max_hops: int = 2,
        include_multi_hop: bool = True
    ) -> Dict:
        """
        Find the best route, including multi-hop options.

        Args:
            source_chain: Source chain name
            destination_chain: Destination chain name
            token: Token symbol
            amount: Amount to transfer
            max_hops: Maximum number of hops to consider (1-3)
            include_multi_hop: Whether to search for multi-hop routes

        Returns:
            Dictionary with best route (direct or multi-hop)
        """
        try:
            # Get direct route quotes
            direct_quotes = await self._get_direct_quotes(
                source_chain, destination_chain, token, amount
            )

            if not direct_quotes:
                log.warning(f"No direct routes found from {source_chain} to {destination_chain}")
                direct_best = None
                direct_cost = float('inf')
            else:
                # Find best direct route
                direct_best = min(direct_quotes, key=lambda x: x.get("estimated_cost_usd", float('inf')))
                direct_cost = direct_best.get("estimated_cost_usd", float('inf'))

            # If multi-hop is disabled, return direct route
            if not include_multi_hop or max_hops < 2:
                return {
                    "route_type": "direct",
                    "best_route": direct_best,
                    "alternatives": []
                }

            # Find multi-hop routes
            multi_hop_routes = await self._find_multi_hop_routes(
                source_chain, destination_chain, token, amount, max_hops
            )

            if not multi_hop_routes:
                # No multi-hop routes found
                return {
                    "route_type": "direct",
                    "best_route": direct_best,
                    "alternatives": [],
                    "multi_hop_checked": True
                }

            # Find best multi-hop route
            best_multi_hop = min(multi_hop_routes, key=lambda x: x.total_cost_usd)

            # Compare direct vs multi-hop
            if direct_best and direct_cost <= best_multi_hop.total_cost_usd:
                # Direct is better
                return {
                    "route_type": "direct",
                    "best_route": direct_best,
                    "alternatives": [self._format_multi_hop_route(best_multi_hop)],
                    "multi_hop_checked": True,
                    "direct_savings_usd": round(best_multi_hop.total_cost_usd - direct_cost, 2)
                }
            else:
                # Multi-hop is better
                savings = direct_cost - best_multi_hop.total_cost_usd if direct_best else None

                return {
                    "route_type": "multi-hop",
                    "best_route": self._format_multi_hop_route(best_multi_hop),
                    "alternatives": [direct_best] if direct_best else [],
                    "multi_hop_checked": True,
                    "savings_usd": round(savings, 2) if savings else None
                }

        except Exception as e:
            log.error(f"Error finding best route: {str(e)}")
            raise

    async def _get_direct_quotes(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> List[Dict]:
        """Get quotes from all bridges for direct route"""
        try:
            tasks = []

            for bridge_name, client in self.bridges.items():
                task = self._get_quote_safe(
                    client, bridge_name, source_chain, destination_chain, token, amount
                )
                tasks.append(task)

            # Execute all in parallel
            results = await asyncio.gather(*tasks)

            # Filter out None results
            valid_quotes = [q for q in results if q is not None]

            return valid_quotes

        except Exception as e:
            log.error(f"Error getting direct quotes: {str(e)}")
            return []

    async def _get_quote_safe(
        self,
        client: BridgeClient,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str
    ) -> Optional[Dict]:
        """Get quote with error handling"""
        try:
            quote = await client.get_quote(source_chain, destination_chain, token, amount)
            if quote:
                quote["bridge_name"] = bridge_name
            return quote
        except Exception as e:
            log.debug(f"Bridge {bridge_name} failed: {str(e)}")
            return None

    async def _find_multi_hop_routes(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        max_hops: int
    ) -> List[MultiHopRoute]:
        """Find all possible multi-hop routes"""
        routes = []

        # For now, implement 2-hop routes (source -> intermediate -> destination)
        if max_hops >= 2:
            for intermediate in self.intermediate_chains:
                # Skip if intermediate is source or destination
                if intermediate == source_chain or intermediate == destination_chain:
                    continue

                # Try to find route through this intermediate chain
                route = await self._try_two_hop_route(
                    source_chain, intermediate, destination_chain, token, amount
                )

                if route:
                    routes.append(route)

        # Could implement 3-hop routes here if max_hops >= 3

        return routes

    async def _try_two_hop_route(
        self,
        source: str,
        intermediate: str,
        destination: str,
        token: str,
        amount: str
    ) -> Optional[MultiHopRoute]:
        """Try to find a valid 2-hop route"""
        try:
            # Get quotes for first hop (source -> intermediate)
            hop1_quotes = await self._get_direct_quotes(source, intermediate, token, amount)

            if not hop1_quotes:
                return None

            # Use best quote for first hop
            hop1_best = min(hop1_quotes, key=lambda x: x.get("estimated_cost_usd", float('inf')))

            # Amount received after first hop
            hop1_output = hop1_best.get("amount_out", "0")

            if not hop1_output or hop1_output == "0":
                return None

            # Get quotes for second hop (intermediate -> destination)
            hop2_quotes = await self._get_direct_quotes(intermediate, destination, token, hop1_output)

            if not hop2_quotes:
                return None

            # Use best quote for second hop
            hop2_best = min(hop2_quotes, key=lambda x: x.get("estimated_cost_usd", float('inf')))

            # Build multi-hop route
            hop1 = RouteHop(
                source_chain=source,
                destination_chain=intermediate,
                bridge_name=hop1_best.get("bridge_name"),
                token=token,
                amount_in=amount,
                amount_out=hop1_output,
                estimated_cost_usd=hop1_best.get("estimated_cost_usd", 0),
                estimated_time_minutes=hop1_best.get("estimated_time_minutes", 0),
                gas_cost_native=hop1_best.get("gas_cost_native", "0"),
                gas_cost_usd=hop1_best.get("gas_cost_usd", 0)
            )

            hop2 = RouteHop(
                source_chain=intermediate,
                destination_chain=destination,
                bridge_name=hop2_best.get("bridge_name"),
                token=token,
                amount_in=hop1_output,
                amount_out=hop2_best.get("amount_out", "0"),
                estimated_cost_usd=hop2_best.get("estimated_cost_usd", 0),
                estimated_time_minutes=hop2_best.get("estimated_time_minutes", 0),
                gas_cost_native=hop2_best.get("gas_cost_native", "0"),
                gas_cost_usd=hop2_best.get("gas_cost_usd", 0)
            )

            # Calculate totals
            total_cost = hop1.estimated_cost_usd + hop2.estimated_cost_usd
            total_time = hop1.estimated_time_minutes + hop2.estimated_time_minutes
            final_amount = hop2.amount_out

            # Calculate total slippage
            amount_float = float(amount)
            final_float = float(final_amount)
            slippage = ((amount_float - final_float) / amount_float * 100) if amount_float > 0 else 0

            return MultiHopRoute(
                hops=[hop1, hop2],
                total_cost_usd=total_cost,
                total_time_minutes=total_time,
                final_amount=final_amount,
                slippage_percent=round(slippage, 2),
                is_better_than_direct=False  # Will be determined later
            )

        except Exception as e:
            log.error(f"Error trying 2-hop route: {str(e)}")
            return None

    def _format_multi_hop_route(self, route: MultiHopRoute) -> Dict:
        """Format multi-hop route for API response"""
        return {
            "route_type": "multi-hop",
            "hops": [
                {
                    "hop_number": i + 1,
                    "source_chain": hop.source_chain,
                    "destination_chain": hop.destination_chain,
                    "bridge_name": hop.bridge_name,
                    "token": hop.token,
                    "amount_in": hop.amount_in,
                    "amount_out": hop.amount_out,
                    "estimated_cost_usd": hop.estimated_cost_usd,
                    "estimated_time_minutes": hop.estimated_time_minutes,
                    "gas_cost_usd": hop.gas_cost_usd
                }
                for i, hop in enumerate(route.hops)
            ],
            "total_hops": len(route.hops),
            "total_cost_usd": route.total_cost_usd,
            "total_time_minutes": route.total_time_minutes,
            "final_amount": route.final_amount,
            "slippage_percent": route.slippage_percent,
            "is_better_than_direct": route.is_better_than_direct,
            "savings_usd": route.savings_usd
        }


# Singleton instance
multi_hop_router = MultiHopRouter()
