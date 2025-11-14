"""Gas price estimation service"""
import asyncio
import aiohttp
import requests
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.logging import log
from app.core.config import settings


class GasEstimator:
    """
    Gas price estimation service.

    Fetches real-time gas prices from multiple chains and provides
    cost estimates for bridge transactions.
    """

    def __init__(self):
        self.cache: Dict[int, Dict] = {}
        self.cache_ttl = 30  # 30 seconds cache
        self.last_update: Dict[int, datetime] = {}

    async def get_gas_prices(self, chain_id: int) -> Optional[Dict]:
        """
        Get current gas prices for a chain.

        Returns:
            Dict with slow, standard, fast, rapid gas prices in gwei
        """
        # Check cache
        if self._is_cached(chain_id):
            return self.cache[chain_id]

        # Fetch from providers
        gas_data = await self._fetch_gas_price(chain_id)

        if gas_data:
            self.cache[chain_id] = gas_data
            self.last_update[chain_id] = datetime.utcnow()
            return gas_data

        # Return defaults if fetch fails
        return self._get_default_gas_prices(chain_id)

    def _is_cached(self, chain_id: int) -> bool:
        """Check if gas price is cached and not expired"""
        if chain_id not in self.cache or chain_id not in self.last_update:
            return False

        elapsed = (datetime.utcnow() - self.last_update[chain_id]).total_seconds()
        return elapsed < self.cache_ttl

    async def _fetch_gas_price(self, chain_id: int) -> Optional[Dict]:
        """Fetch gas price from RPC or gas tracker API"""
        try:
            if chain_id == 1:
                # Ethereum - use Etherscan or Alchemy
                return await self._fetch_ethereum_gas()
            elif chain_id == 137:
                # Polygon - use PolygonScan
                return await self._fetch_polygon_gas()
            elif chain_id in [10, 42161, 8453]:
                # L2s - generally cheaper and more stable
                return self._get_l2_gas_estimate(chain_id)
            else:
                return self._get_default_gas_prices(chain_id)
        except Exception as e:
            log.error(f"Error fetching gas price for chain {chain_id}: {e}")
            return None

    async def _fetch_ethereum_gas(self) -> Dict:
        """Fetch Ethereum gas prices from Etherscan"""
        try:
            # Try Etherscan Gas Tracker API (free, no key needed for basic)
            async with aiohttp.ClientSession() as session:
                url = "https://api.etherscan.io/api"
                params = {
                    "module": "gastracker",
                    "action": "gasoracle"
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            result = data.get("result", {})
                            return {
                                "slow": float(result.get("SafeGasPrice", 20)),
                                "standard": float(result.get("ProposeGasPrice", 30)),
                                "fast": float(result.get("FastGasPrice", 40)),
                                "rapid": float(result.get("FastGasPrice", 40)) * 1.2,
                                "timestamp": datetime.utcnow(),
                                "chain_id": 1
                            }
        except:
            pass

        # Fallback to defaults
        return self._get_default_gas_prices(1)

    async def _fetch_polygon_gas(self) -> Dict:
        """Fetch Polygon gas prices"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://gasstation.polygon.technology/v2"

                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "slow": float(data.get("safeLow", {}).get("maxFee", 30)),
                            "standard": float(data.get("standard", {}).get("maxFee", 50)),
                            "fast": float(data.get("fast", {}).get("maxFee", 80)),
                            "rapid": float(data.get("fast", {}).get("maxFee", 80)) * 1.3,
                            "timestamp": datetime.utcnow(),
                            "chain_id": 137
                        }
        except:
            pass

        return self._get_default_gas_prices(137)

    def _get_l2_gas_estimate(self, chain_id: int) -> Dict:
        """Get estimated gas prices for L2s"""
        l2_defaults = {
            10: {"slow": 0.001, "standard": 0.002, "fast": 0.003, "rapid": 0.005},  # Optimism
            42161: {"slow": 0.1, "standard": 0.15, "fast": 0.2, "rapid": 0.3},      # Arbitrum
            8453: {"slow": 0.001, "standard": 0.002, "fast": 0.003, "rapid": 0.005} # Base
        }

        prices = l2_defaults.get(chain_id, {"slow": 1, "standard": 2, "fast": 3, "rapid": 5})
        prices["timestamp"] = datetime.utcnow()
        prices["chain_id"] = chain_id
        return prices

    def _get_default_gas_prices(self, chain_id: int) -> Dict:
        """Get default gas price estimates when fetching fails"""
        defaults = {
            1: {"slow": 20, "standard": 30, "fast": 40, "rapid": 50},       # Ethereum
            10: {"slow": 0.001, "standard": 0.002, "fast": 0.003, "rapid": 0.005},  # Optimism
            42161: {"slow": 0.1, "standard": 0.15, "fast": 0.2, "rapid": 0.3},  # Arbitrum
            137: {"slow": 30, "standard": 50, "fast": 80, "rapid": 120},    # Polygon
            8453: {"slow": 0.001, "standard": 0.002, "fast": 0.003, "rapid": 0.005},  # Base
            56: {"slow": 3, "standard": 5, "fast": 7, "rapid": 10},         # BSC
            43114: {"slow": 25, "standard": 30, "fast": 40, "rapid": 50},   # Avalanche
        }

        prices = defaults.get(chain_id, {"slow": 10, "standard": 20, "fast": 30, "rapid": 40})
        prices["timestamp"] = datetime.utcnow()
        prices["chain_id"] = chain_id
        return prices

    async def estimate_transaction_cost(
        self,
        chain_id: int,
        gas_limit: int = 200000,
        priority: str = "standard"
    ) -> Decimal:
        """
        Estimate transaction cost in USD.

        Args:
            chain_id: Chain ID
            gas_limit: Estimated gas limit
            priority: Gas priority (slow, standard, fast, rapid)

        Returns:
            Estimated cost in USD
        """
        gas_prices = await self.get_gas_prices(chain_id)
        gas_price_gwei = gas_prices.get(priority, gas_prices.get("standard"))

        # Get native token price in USD
        token_price_usd = await self._get_native_token_price(chain_id)

        # Calculate cost
        gas_cost_eth = (gas_limit * gas_price_gwei) / 1e9  # Convert gwei to ETH
        cost_usd = gas_cost_eth * token_price_usd

        return Decimal(str(round(cost_usd, 2)))

    async def _get_native_token_price(self, chain_id: int) -> float:
        """Get native token price in USD"""
        # Simplified - in production, fetch from price oracle
        prices = {
            1: 2000.0,    # ETH
            10: 2000.0,   # ETH (Optimism uses ETH)
            42161: 2000.0,  # ETH (Arbitrum uses ETH)
            137: 0.80,    # MATIC
            8453: 2000.0, # ETH (Base uses ETH)
            56: 300.0,    # BNB
            43114: 25.0,  # AVAX
        }
        return prices.get(chain_id, 1.0)

    async def get_all_chain_gas_prices(self) -> Dict[int, Dict]:
        """Get gas prices for all supported chains"""
        chain_ids = [1, 10, 42161, 137, 8453, 56, 43114]

        tasks = [self.get_gas_prices(chain_id) for chain_id in chain_ids]
        results = await asyncio.gather(*tasks)

        return {chain_id: result for chain_id, result in zip(chain_ids, results) if result}

    def get_gas_prices_sync(self, chain_id: int) -> Optional[Dict]:
        """
        Synchronous version of get_gas_prices for use in Celery tasks.

        Returns:
            Dict with slow, standard, fast, rapid gas prices in gwei
        """
        # Check cache
        if self._is_cached(chain_id):
            return self.cache[chain_id]

        try:
            # Fetch gas prices synchronously
            if chain_id == 1:  # Ethereum
                if not settings.ETHERSCAN_API_KEY:
                    return self._get_default_gas_prices(chain_id)

                url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={settings.ETHERSCAN_API_KEY}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1":
                        result = data.get("result", {})
                        gas_data = {
                            "slow": float(result.get("SafeGasPrice", 20)),
                            "standard": float(result.get("ProposeGasPrice", 30)),
                            "fast": float(result.get("FastGasPrice", 40)),
                            "rapid": float(result.get("FastGasPrice", 40)) * 1.2,
                            "timestamp": datetime.utcnow(),
                            "chain_id": chain_id
                        }

                        self.cache[chain_id] = gas_data
                        self.last_update[chain_id] = datetime.utcnow()
                        return gas_data

            elif chain_id == 137:  # Polygon
                url = "https://gasstation.polygon.technology/v2"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    gas_data = {
                        "slow": float(data.get("safeLow", {}).get("maxFee", 30)),
                        "standard": float(data.get("standard", {}).get("maxFee", 50)),
                        "fast": float(data.get("fast", {}).get("maxFee", 80)),
                        "rapid": float(data.get("fastest", {}).get("maxFee", 120)),
                        "timestamp": datetime.utcnow(),
                        "chain_id": chain_id
                    }

                    self.cache[chain_id] = gas_data
                    self.last_update[chain_id] = datetime.utcnow()
                    return gas_data

        except Exception as e:
            log.error(f"Error fetching gas prices for chain {chain_id}: {str(e)}")

        # Return defaults if fetch fails
        return self._get_default_gas_prices(chain_id)


# Global gas estimator instance
gas_estimator = GasEstimator()
