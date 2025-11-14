"""
Across Protocol API integration for real bridge quotes.

Official API: https://across.to/api/suggested-fees
"""
import aiohttp
import asyncio
from typing import Optional, Dict
from decimal import Decimal
from app.core.logging import log


class AcrossAPI:
    """Client for Across Protocol API"""

    def __init__(self):
        self.base_url = "https://across.to/api"
        self.supported_chains = {
            1: "ethereum",
            10: "optimism",
            137: "polygon",
            42161: "arbitrum",
            8453: "base",
        }

    async def get_quote(
        self,
        source_chain_id: int,
        destination_chain_id: int,
        token_address: str,
        amount: str
    ) -> Optional[Dict]:
        """
        Get real quote from Across Protocol API.

        Args:
            source_chain_id: Source chain ID
            destination_chain_id: Destination chain ID
            token_address: Token contract address
            amount: Amount in smallest unit

        Returns:
            Quote data or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/suggested-fees"
                params = {
                    "token": token_address,
                    "destinationChainId": destination_chain_id,
                    "originChainId": source_chain_id,
                    "amount": amount,
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse Across response
                        return {
                            "bridge_name": "Across Protocol",
                            "estimated_time_seconds": data.get("estimatedFillTimeSec", 180),
                            "relay_fee_pct": float(data.get("relayFeePct", "0")) * 100,
                            "capital_fee_pct": float(data.get("capitalFeePct", "0")) * 100,
                            "total_relay_fee": {
                                "pct": data.get("totalRelayFee", {}).get("pct"),
                                "total": data.get("totalRelayFee", {}).get("total"),
                            },
                            "is_amm": data.get("isAmm", False),
                            "timestamp": data.get("timestamp"),
                        }
                    else:
                        log.warning(f"Across API returned status {response.status}")
                        return None

        except asyncio.TimeoutError:
            log.warning("Across API timeout")
            return None
        except Exception as e:
            log.error(f"Error calling Across API: {e}")
            return None

    async def get_limits(
        self,
        token_address: str,
        source_chain_id: int,
        destination_chain_id: int
    ) -> Optional[Dict]:
        """Get route limits from Across"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/limits"
                params = {
                    "token": token_address,
                    "originChainId": source_chain_id,
                    "destinationChainId": destination_chain_id,
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "min_deposit": data.get("minDeposit"),
                            "max_deposit": data.get("maxDeposit"),
                            "max_deposit_instant": data.get("maxDepositInstant"),
                            "max_deposit_short_delay": data.get("maxDepositShortDelay"),
                        }

        except Exception as e:
            log.error(f"Error getting Across limits: {e}")
            return None


# Global instance
across_api = AcrossAPI()
