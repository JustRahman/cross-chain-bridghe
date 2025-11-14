"""Blockchain explorer service for enhanced transaction tracking"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from app.core.logging import log


class BlockchainExplorerService:
    """
    Service for fetching transaction data from blockchain explorers.

    Supports Etherscan, Arbiscan, Polygonscan, etc. using FREE APIs.
    You can register for free API keys at each explorer's website.

    To use, set these environment variables:
    - ETHERSCAN_API_KEY
    - ARBISCAN_API_KEY
    - POLYGONSCAN_API_KEY
    - OPTIMISM_API_KEY
    - BASESCAN_API_KEY
    """

    def __init__(self):
        # Explorer API endpoints
        self.explorer_apis = {
            "ethereum": "https://api.etherscan.io/api",
            "arbitrum": "https://api.arbiscan.io/api",
            "optimism": "https://api-optimistic.etherscan.io/api",
            "polygon": "https://api.polygonscan.com/api",
            "base": "https://api.basescan.org/api",
            "bsc": "https://api.bscscan.com/api",
            "avalanche": "https://api.snowtrace.io/api",
        }

        # API keys (can be set via environment variables)
        # For now, we'll use without keys (rate limited but still works)
        self.api_keys = {
            "ethereum": None,  # Set via env: ETHERSCAN_API_KEY
            "arbitrum": None,  # Set via env: ARBISCAN_API_KEY
            "optimism": None,  # Set via env: OPTIMISM_API_KEY
            "polygon": None,   # Set via env: POLYGONSCAN_API_KEY
            "base": None,      # Set via env: BASESCAN_API_KEY
        }

    async def get_transaction(self, chain: str, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from block explorer.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Transaction details or None
        """
        api_url = self.explorer_apis.get(chain.lower())
        if not api_url:
            log.warning(f"Unsupported chain for explorer: {chain}")
            return None

        params = {
            "module": "transaction",
            "action": "gettxreceiptstatus",
            "txhash": tx_hash,
        }

        # Add API key if available
        api_key = self.api_keys.get(chain.lower())
        if api_key:
            params["apikey"] = api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            result = data.get("result", {})
                            return {
                                "status": result.get("status"),
                                "from": result.get("from"),
                                "to": result.get("to"),
                                "value": result.get("value"),
                                "gasUsed": result.get("gasUsed"),
                                "blockNumber": result.get("blockNumber"),
                            }
                        else:
                            log.warning(f"Explorer API returned error: {data.get('message')}")

        except Exception as e:
            log.error(f"Error fetching from explorer: {e}")

        return None

    async def get_transaction_info(self, chain: str, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed transaction information.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Detailed transaction info
        """
        api_url = self.explorer_apis.get(chain.lower())
        if not api_url:
            return None

        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
        }

        api_key = self.api_keys.get(chain.lower())
        if api_key:
            params["apikey"] = api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result"):
                            return data["result"]

        except Exception as e:
            log.error(f"Error fetching transaction info: {e}")

        return None

    def get_explorer_url(self, chain: str, tx_hash: str) -> str:
        """Get block explorer URL for transaction"""
        urls = {
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
            "arbitrum": f"https://arbiscan.io/tx/{tx_hash}",
            "optimism": f"https://optimistic.etherscan.io/tx/{tx_hash}",
            "polygon": f"https://polygonscan.com/tx/{tx_hash}",
            "base": f"https://basescan.org/tx/{tx_hash}",
            "bsc": f"https://bscscan.com/tx/{tx_hash}",
            "avalanche": f"https://snowtrace.io/tx/{tx_hash}",
        }
        return urls.get(chain.lower(), f"https://etherscan.io/tx/{tx_hash}")


# Global instance
blockchain_explorer = BlockchainExplorerService()
