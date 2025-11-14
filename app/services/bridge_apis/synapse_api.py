"""
Synapse Protocol API integration.

Official API: https://api.synapseprotocol.com
Documentation: https://docs.synapseprotocol.com
"""
import aiohttp
import asyncio
from typing import Optional, Dict, List
from app.core.logging import log


class SynapseAPI:
    """Client for Synapse Protocol API"""

    def __init__(self):
        self.base_url = "https://api.synapseprotocol.com"
        self.supported_chains = {
            1: "ethereum",
            10: "optimism",
            137: "polygon",
            42161: "arbitrum",
            56: "bsc",
            43114: "avalanche",
            250: "fantom",
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
        Get real quote from Synapse Protocol API.

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
                url = f"{self.base_url}/v1/bridge"
                params = {
                    "fromChain": source_chain_id,
                    "toChain": destination_chain_id,
                    "fromToken": token_address,
                    "amount": amount,
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        return {
                            "bridge_name": "Synapse Protocol",
                            "amount_out": data.get("amountToReceive"),
                            "bridge_fee": data.get("bridgeFee"),
                            "exchange_rate": data.get("exchangeRate"),
                            "estimated_time_seconds": data.get("estimatedTime", 360),
                            "route_type": data.get("routeType"),  # swap, bridge, or swap+bridge
                            "gas_estimate": data.get("gasEstimate"),
                        }
                    else:
                        log.warning(f"Synapse API returned status {response.status}")
                        return None

        except asyncio.TimeoutError:
            log.warning("Synapse API timeout")
            return None
        except Exception as e:
            log.error(f"Error calling Synapse API: {e}")
            return None

    async def get_supported_chains(self) -> Optional[List[Dict]]:
        """Get list of supported chains from Synapse"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/chains"

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None

        except Exception as e:
            log.error(f"Error getting Synapse chains: {e}")
            return None

    async def get_bridge_status(self, tx_hash: str, chain_id: int) -> Optional[Dict]:
        """Get status of a Synapse bridge transaction"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/bridge-status"
                params = {
                    "hash": tx_hash,
                    "chainId": chain_id,
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": data.get("status"),
                            "source_tx_hash": data.get("sourceTxHash"),
                            "dest_tx_hash": data.get("destTxHash"),
                            "amount_sent": data.get("amountSent"),
                            "amount_received": data.get("amountReceived"),
                            "timestamp": data.get("timestamp"),
                        }
                    return None

        except Exception as e:
            log.error(f"Error getting Synapse bridge status: {e}")
            return None


# Global instance
synapse_api = SynapseAPI()
