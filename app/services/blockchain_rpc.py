"""Blockchain RPC service for interacting with multiple chains using FREE public RPC endpoints"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
from app.core.logging import log


class BlockchainRPCService:
    """
    Service for interacting with blockchain networks using FREE public RPC endpoints.

    Uses Grove's free public endpoints (no API key required) as primary,
    with fallback to other public endpoints.

    Supported chains: Ethereum, Arbitrum, Optimism, Polygon, Base
    """

    def __init__(self):
        # Free public RPC endpoints (no API key required)
        self.rpc_endpoints = {
            "ethereum": [
                "https://eth.public-rpc.com",
                "https://rpc.ankr.com/eth",
                "https://ethereum.publicnode.com",
                "https://1rpc.io/eth",
            ],
            "arbitrum": [
                "https://arbitrum.public-rpc.com",
                "https://rpc.ankr.com/arbitrum",
                "https://arbitrum-one.publicnode.com",
                "https://1rpc.io/arb",
            ],
            "optimism": [
                "https://optimism.public-rpc.com",
                "https://rpc.ankr.com/optimism",
                "https://optimism.publicnode.com",
                "https://1rpc.io/op",
            ],
            "polygon": [
                "https://polygon.public-rpc.com",
                "https://rpc.ankr.com/polygon",
                "https://polygon.publicnode.com",
                "https://1rpc.io/matic",
            ],
            "base": [
                "https://base.public-rpc.com",
                "https://rpc.ankr.com/base",
                "https://base.publicnode.com",
                "https://1rpc.io/base",
            ],
            "bsc": [
                "https://bsc.public-rpc.com",
                "https://rpc.ankr.com/bsc",
                "https://bsc.publicnode.com",
                "https://1rpc.io/bsc",
            ],
            "avalanche": [
                "https://avalanche.public-rpc.com",
                "https://rpc.ankr.com/avalanche",
                "https://avalanche.publicnode.com",
                "https://1rpc.io/avax/c",
            ],
        }

        # Chain IDs
        self.chain_ids = {
            "ethereum": 1,
            "arbitrum": 42161,
            "optimism": 10,
            "polygon": 137,
            "base": 8453,
            "bsc": 56,
            "avalanche": 43114,
        }

    async def get_transaction(self, chain: str, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from blockchain.

        Args:
            chain: Chain name (ethereum, arbitrum, etc.)
            tx_hash: Transaction hash

        Returns:
            Transaction details or None if not found
        """
        endpoints = self.rpc_endpoints.get(chain.lower())
        if not endpoints:
            log.error(f"Unsupported chain: {chain}")
            return None

        # Try each endpoint until one works
        for endpoint in endpoints:
            try:
                tx_data = await self._rpc_call(
                    endpoint,
                    "eth_getTransactionByHash",
                    [tx_hash]
                )

                if tx_data:
                    # Get transaction receipt for status
                    receipt = await self._rpc_call(
                        endpoint,
                        "eth_getTransactionReceipt",
                        [tx_hash]
                    )

                    return {
                        "hash": tx_data.get("hash"),
                        "from": tx_data.get("from"),
                        "to": tx_data.get("to"),
                        "value": tx_data.get("value"),
                        "gas": tx_data.get("gas"),
                        "gasPrice": tx_data.get("gasPrice"),
                        "nonce": tx_data.get("nonce"),
                        "blockNumber": tx_data.get("blockNumber"),
                        "blockHash": tx_data.get("blockHash"),
                        "input": tx_data.get("input"),
                        "status": receipt.get("status") if receipt else None,
                        "gasUsed": receipt.get("gasUsed") if receipt else None,
                    }

            except Exception as e:
                log.warning(f"RPC endpoint {endpoint} failed: {e}")
                continue

        log.error(f"All RPC endpoints failed for {chain}")
        return None

    async def get_transaction_receipt(self, chain: str, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt from blockchain.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Transaction receipt or None
        """
        endpoints = self.rpc_endpoints.get(chain.lower())
        if not endpoints:
            return None

        for endpoint in endpoints:
            try:
                receipt = await self._rpc_call(
                    endpoint,
                    "eth_getTransactionReceipt",
                    [tx_hash]
                )

                if receipt:
                    return receipt

            except Exception as e:
                log.warning(f"RPC endpoint {endpoint} failed: {e}")
                continue

        return None

    async def get_block_number(self, chain: str) -> Optional[int]:
        """
        Get latest block number.

        Args:
            chain: Chain name

        Returns:
            Block number or None
        """
        endpoints = self.rpc_endpoints.get(chain.lower())
        if not endpoints:
            return None

        for endpoint in endpoints:
            try:
                result = await self._rpc_call(endpoint, "eth_blockNumber", [])
                if result:
                    return int(result, 16)
            except Exception as e:
                log.warning(f"Failed to get block number from {endpoint}: {e}")
                continue

        return None

    async def get_gas_price(self, chain: str) -> Optional[str]:
        """
        Get current gas price.

        Args:
            chain: Chain name

        Returns:
            Gas price in wei (hex string)
        """
        endpoints = self.rpc_endpoints.get(chain.lower())
        if not endpoints:
            return None

        for endpoint in endpoints:
            try:
                result = await self._rpc_call(endpoint, "eth_gasPrice", [])
                if result:
                    return result
            except Exception as e:
                log.warning(f"Failed to get gas price from {endpoint}: {e}")
                continue

        return None

    async def estimate_gas(self, chain: str, transaction: Dict[str, Any]) -> Optional[str]:
        """
        Estimate gas for a transaction.

        Args:
            chain: Chain name
            transaction: Transaction object

        Returns:
            Estimated gas (hex string)
        """
        endpoints = self.rpc_endpoints.get(chain.lower())
        if not endpoints:
            return None

        for endpoint in endpoints:
            try:
                result = await self._rpc_call(endpoint, "eth_estimateGas", [transaction])
                if result:
                    return result
            except Exception as e:
                log.warning(f"Failed to estimate gas from {endpoint}: {e}")
                continue

        return None

    async def _rpc_call(
        self,
        endpoint: str,
        method: str,
        params: List[Any],
        timeout: int = 5
    ) -> Optional[Any]:
        """
        Make a JSON-RPC call to an endpoint.

        Args:
            endpoint: RPC endpoint URL
            method: RPC method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Result from RPC call or None
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                        elif "error" in data:
                            log.error(f"RPC error: {data['error']}")
                            return None
                    else:
                        log.warning(f"RPC returned status {response.status}")
                        return None

        except asyncio.TimeoutError:
            log.warning(f"RPC timeout for {endpoint}")
            return None
        except Exception as e:
            log.error(f"RPC call failed: {e}")
            return None

    def get_chain_id(self, chain: str) -> Optional[int]:
        """Get chain ID for a chain name"""
        return self.chain_ids.get(chain.lower())

    def get_explorer_url(self, chain: str, tx_hash: str) -> str:
        """Get blockchain explorer URL for a transaction"""
        explorers = {
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
            "arbitrum": f"https://arbiscan.io/tx/{tx_hash}",
            "optimism": f"https://optimistic.etherscan.io/tx/{tx_hash}",
            "polygon": f"https://polygonscan.com/tx/{tx_hash}",
            "base": f"https://basescan.org/tx/{tx_hash}",
            "bsc": f"https://bscscan.com/tx/{tx_hash}",
            "avalanche": f"https://snowtrace.io/tx/{tx_hash}",
        }
        return explorers.get(chain.lower(), f"https://etherscan.io/tx/{tx_hash}")


# Global instance
blockchain_rpc = BlockchainRPCService()
