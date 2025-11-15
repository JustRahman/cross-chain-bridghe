"""Route discovery engine with intelligent optimization"""
import asyncio
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta
import hashlib
import json
from app.services.bridges.base import BaseBridge, BridgeQuote, RouteParams
from app.services.bridges.across import AcrossBridge
from app.services.bridges.stargate import StargateBridge
from app.services.bridges.hop import HopBridge
from app.services.bridges.connext import ConnextBridge
from app.services.bridges.wormhole import WormholeBridge
from app.services.bridges.synapse import SynapseBridge
from app.services.bridges.celer import CelerBridge
from app.services.bridges.orbiter import OrbiterBridge
from app.services.bridges.debridge import DeBridgeBridge
from app.services.bridges.layerzero import LayerZeroBridge
from app.core.logging import log
from app.core.config import settings


class RouteDiscoveryEngine:
    """
    Core routing intelligence that:
    - Queries multiple bridges in parallel
    - Ranks routes by cost, speed, and reliability
    - Handles failures gracefully
    - Caches results for performance
    """

    def __init__(self):
        # Initialize all bridge integrations
        self.bridges: List[BaseBridge] = [
            AcrossBridge(),
            StargateBridge(),
            HopBridge(),
            ConnextBridge(),
            WormholeBridge(),
            SynapseBridge(),
            CelerBridge(),
            OrbiterBridge(),
            DeBridgeBridge(),
            LayerZeroBridge(),
        ]
        log.info(f"Route discovery engine initialized with {len(self.bridges)} bridges")

        # Cache for quotes (in-memory, could be moved to Redis)
        self.quote_cache: Dict[str, Dict] = {}
        self.cache_ttl_seconds = 30

    async def discover_routes(
        self,
        route_params: RouteParams,
        preferences: Optional[Dict] = None
    ) -> List[BridgeQuote]:
        """
        Discover optimal routes across all bridges.

        Args:
            route_params: Route parameters
            preferences: User preferences for ranking (cost_weight, speed_weight, etc)

        Returns:
            List of BridgeQuote sorted by score (best first)
        """
        # Check cache first
        cache_key = self._get_cache_key(route_params)
        cached = self._get_cached_quote(cache_key)
        if cached:
            log.debug(f"Returning cached routes for {cache_key}")
            return cached

        # Query all bridges in parallel
        log.info(f"Discovering routes for {route_params.source_chain} -> {route_params.destination_chain}")
        quotes = await self._query_all_bridges(route_params)

        if not quotes:
            log.warning("No routes found from any bridge")
            return []

        # Rank routes by score
        ranked_quotes = self._rank_routes(quotes, preferences or {})

        # Cache results
        self._cache_quotes(cache_key, ranked_quotes)

        log.info(f"Found {len(ranked_quotes)} routes")
        return ranked_quotes

    async def _query_all_bridges(self, route_params: RouteParams) -> List[BridgeQuote]:
        """
        Query all bridges in parallel with timeout.

        Args:
            route_params: Route parameters

        Returns:
            List of successful quotes
        """
        tasks = []

        for bridge in self.bridges:
            task = asyncio.create_task(
                self._query_bridge_with_timeout(bridge, route_params)
            )
            tasks.append(task)

        # Wait for all tasks to complete (or timeout)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        quotes = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log.error(f"Bridge {self.bridges[i].name} error: {result}")
            elif result is not None:
                quotes.append(result)

        return quotes

    async def _query_bridge_with_timeout(
        self,
        bridge: BaseBridge,
        route_params: RouteParams,
        timeout_seconds: int = 6
    ) -> Optional[BridgeQuote]:
        """
        Query a single bridge with timeout.

        Args:
            bridge: Bridge instance
            route_params: Route parameters
            timeout_seconds: Timeout in seconds

        Returns:
            BridgeQuote or None
        """
        try:
            # Use asyncio.wait_for to enforce timeout
            quote = await asyncio.wait_for(
                bridge.get_quote(route_params),
                timeout=timeout_seconds
            )

            if quote:
                log.debug(f"Got quote from {bridge.name}: ${quote.fee_breakdown.total_cost_usd}")

            return quote

        except asyncio.TimeoutError:
            log.warning(f"{bridge.name} timeout after {timeout_seconds}s")
            return None
        except Exception as e:
            log.error(f"Error querying {bridge.name}: {e}")
            return None

    def _rank_routes(
        self,
        quotes: List[BridgeQuote],
        preferences: Dict
    ) -> List[BridgeQuote]:
        """
        Rank routes by weighted score.

        Algorithm:
        - Cost (40%): Lower is better
        - Speed (30%): Faster is better
        - Reliability (20%): Higher success rate is better
        - Liquidity (10%): Confidence score

        Args:
            quotes: List of quotes to rank
            preferences: User preferences (can override default weights)

        Returns:
            Sorted list of quotes (best first)
        """
        if not quotes:
            return []

        # Default weights
        weights = {
            "cost": preferences.get("cost_weight", 0.40),
            "speed": preferences.get("speed_weight", 0.30),
            "reliability": preferences.get("reliability_weight", 0.20),
            "liquidity": preferences.get("liquidity_weight", 0.10)
        }

        # Find min/max for normalization
        costs = [float(q.fee_breakdown.total_cost_usd) for q in quotes]
        times = [q.estimated_time_seconds for q in quotes]

        max_cost = max(costs) if costs else 1
        max_time = max(times) if times else 1

        # Calculate scores
        scored_quotes = []
        for quote in quotes:
            # Cost score (lower is better, so invert)
            cost_score = 100 * (1 - (float(quote.fee_breakdown.total_cost_usd) / max_cost))

            # Speed score (faster is better, so invert time)
            speed_score = 100 * (1 - (quote.estimated_time_seconds / max_time))

            # Reliability score (success rate as percentage)
            reliability_score = float(quote.success_rate)

            # Liquidity score (assume 100 for now, can be enhanced)
            liquidity_score = 100.0

            # Calculate weighted score
            total_score = (
                cost_score * weights["cost"] +
                speed_score * weights["speed"] +
                reliability_score * weights["reliability"] +
                liquidity_score * weights["liquidity"]
            )

            scored_quotes.append((total_score, quote))

        # Sort by score (highest first)
        scored_quotes.sort(key=lambda x: x[0], reverse=True)

        # Return just the quotes
        ranked_quotes = [quote for score, quote in scored_quotes]

        # Log rankings
        for i, (score, quote) in enumerate(scored_quotes):
            log.debug(
                f"Rank {i+1}: {quote.bridge_name} - "
                f"Score: {score:.2f}, "
                f"Cost: ${quote.fee_breakdown.total_cost_usd}, "
                f"Time: {quote.estimated_time_seconds}s"
            )

        return ranked_quotes

    def _get_cache_key(self, route_params: RouteParams) -> str:
        """
        Generate cache key for route parameters.

        Args:
            route_params: Route parameters

        Returns:
            Cache key string
        """
        key_data = {
            "source_chain": route_params.source_chain,
            "destination_chain": route_params.destination_chain,
            "source_token": route_params.source_token,
            "destination_token": route_params.destination_token,
            "amount": route_params.amount
        }

        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()

        return f"route_quote:{key_hash}"

    def _get_cached_quote(self, cache_key: str) -> Optional[List[BridgeQuote]]:
        """Get cached quote if not expired"""
        if cache_key not in self.quote_cache:
            return None

        cached_data = self.quote_cache[cache_key]
        cached_time = cached_data["timestamp"]

        # Check if expired
        if datetime.utcnow() - cached_time > timedelta(seconds=self.cache_ttl_seconds):
            del self.quote_cache[cache_key]
            return None

        return cached_data["quotes"]

    def _cache_quotes(self, cache_key: str, quotes: List[BridgeQuote]):
        """Cache quote results"""
        self.quote_cache[cache_key] = {
            "timestamp": datetime.utcnow(),
            "quotes": quotes
        }

        # Simple cache cleanup (remove old entries if cache is too large)
        if len(self.quote_cache) > 1000:
            # Remove oldest 100 entries
            sorted_keys = sorted(
                self.quote_cache.keys(),
                key=lambda k: self.quote_cache[k]["timestamp"]
            )
            for key in sorted_keys[:100]:
                del self.quote_cache[key]

    async def get_bridge_by_name(self, bridge_name: str) -> Optional[BaseBridge]:
        """
        Get bridge instance by name.

        Args:
            bridge_name: Bridge name

        Returns:
            Bridge instance or None
        """
        for bridge in self.bridges:
            if bridge.name.lower() == bridge_name.lower():
                return bridge

        return None


# Global route discovery engine instance
route_discovery_engine = RouteDiscoveryEngine()
