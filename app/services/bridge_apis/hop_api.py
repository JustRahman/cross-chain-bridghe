"""
Hop Protocol API integration for real bridge quotes.

Official API: https://hop.exchange/v1-api
Documentation: https://docs.hop.exchange/api
"""
import aiohttp
import asyncio
from typing import Optional, Dict, List
from decimal import Decimal
from app.core.logging import log


class HopAPI:
    """Client for Hop Protocol API"""

    def __init__(self):
        self.base_url = "https://api.hop.exchange/v1"
        self.supported_chains = {
            1: "ethereum",
            10: "optimism",
            137: "polygon",
            42161: "arbitrum",
            100: "gnosis",
        }

        # Hop supported tokens
        self.supported_tokens = {
            "USDC": "USDC",
            "USDT": "USDT",
            "DAI": "DAI",
            "ETH": "ETH",
            "MATIC": "MATIC",
        }

    async def get_quote(
        self,
        source_chain_id: int,
        destination_chain_id: int,
        token_symbol: str,
        amount: str
    ) -> Optional[Dict]:
        """
        Get real quote from Hop Protocol API.

        Args:
            source_chain_id: Source chain ID
            destination_chain_id: Destination chain ID
            token_symbol: Token symbol (USDC, ETH, etc.)
            amount: Amount in smallest unit

        Returns:
            Quote data or None
        """
        try:
            source_chain = self.supported_chains.get(source_chain_id)
            dest_chain = self.supported_chains.get(destination_chain_id)

            if not source_chain or not dest_chain:
                log.warning(f"Hop doesn't support chain pair: {source_chain_id} -> {destination_chain_id}")
                return None

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/quote"
                params = {
                    "amount": amount,
                    "token": token_symbol.upper(),
                    "fromChain": source_chain_id,
                    "toChain": destination_chain_id,
                    "slippage": "0.5",  # 0.5% slippage tolerance
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        return {
                            "bridge_name": "Hop Protocol",
                            "amount_out": data.get("amountOut"),
                            "estimated_received": data.get("estimatedReceived"),
                            "deadline": data.get("deadline"),
                            "price_impact": data.get("priceImpact"),
                            "total_fee": data.get("totalFee"),
                            "bonder_fee": data.get("bonderFee"),
                            "estimated_time_seconds": 300,  # ~5 minutes typical
                        }
                    else:
                        log.warning(f"Hop API returned status {response.status}")
                        return None

        except asyncio.TimeoutError:
            log.warning("Hop API timeout")
            return None
        except Exception as e:
            log.error(f"Error calling Hop API: {e}")
            return None

    async def get_available_routes(self) -> Optional[List[Dict]]:
        """Get all available routes from Hop"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/available-routes"

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    return None

        except Exception as e:
            log.error(f"Error getting Hop available routes: {e}")
            return None

    async def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Get status of a Hop transfer"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/transfer-status"
                params = {"transferId": transfer_id}

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None

        except Exception as e:
            log.error(f"Error getting Hop transfer status: {e}")
            return None


# Global instance
hop_api = HopAPI()
