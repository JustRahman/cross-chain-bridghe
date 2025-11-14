"""Web3 service for blockchain interactions with multi-provider failover"""
import asyncio
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from web3 import Web3
from web3.exceptions import Web3Exception
import aiohttp
from app.core.config import settings, CHAIN_CONFIG
from app.core.logging import log


@dataclass
class GasPrice:
    """Gas price information"""
    base_fee: int
    priority_fee: int
    max_fee: int
    gas_price_gwei: Decimal


@dataclass
class TokenInfo:
    """Token information"""
    address: str
    symbol: str
    name: str
    decimals: int
    total_supply: Optional[int] = None


class Web3Service:
    """
    Web3 service with multi-provider failover and caching.

    Features:
    - Multiple RPC providers per chain
    - Automatic failover on errors
    - Connection pooling
    - Response caching
    """

    def __init__(self):
        self.providers: Dict[int, List[Web3]] = {}
        self.current_provider_index: Dict[int, int] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize Web3 providers for all chains"""
        for chain_name, chain_info in CHAIN_CONFIG.items():
            chain_id = chain_info["chain_id"]
            providers = []

            # Add primary RPC
            try:
                web3 = Web3(Web3.HTTPProvider(chain_info["rpc_url"]))
                if web3.is_connected():
                    providers.append(web3)
                    log.info(f"Connected to {chain_name} primary RPC")
            except Exception as e:
                log.error(f"Failed to connect to {chain_name} primary RPC: {e}")

            # Add fallback RPC if available
            if chain_info.get("rpc_fallback"):
                try:
                    web3_fallback = Web3(Web3.HTTPProvider(chain_info["rpc_fallback"]))
                    if web3_fallback.is_connected():
                        providers.append(web3_fallback)
                        log.info(f"Connected to {chain_name} fallback RPC")
                except Exception as e:
                    log.error(f"Failed to connect to {chain_name} fallback RPC: {e}")

            if providers:
                self.providers[chain_id] = providers
                self.current_provider_index[chain_id] = 0
            else:
                log.warning(f"No RPC providers available for {chain_name}")

    def get_provider(self, chain_id: int) -> Optional[Web3]:
        """
        Get current provider for a chain.

        Args:
            chain_id: Chain ID

        Returns:
            Web3 instance or None
        """
        if chain_id not in self.providers:
            return None

        providers = self.providers[chain_id]
        if not providers:
            return None

        index = self.current_provider_index.get(chain_id, 0)
        return providers[index]

    async def _failover_provider(self, chain_id: int):
        """Switch to next provider for a chain"""
        if chain_id not in self.providers:
            return

        providers = self.providers[chain_id]
        if len(providers) <= 1:
            return

        current = self.current_provider_index.get(chain_id, 0)
        self.current_provider_index[chain_id] = (current + 1) % len(providers)
        log.warning(f"Switched to fallback RPC for chain {chain_id}")

    async def get_block_number(self, chain_id: int) -> Optional[int]:
        """
        Get current block number.

        Args:
            chain_id: Chain ID

        Returns:
            Block number or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            return provider.eth.block_number
        except Exception as e:
            log.error(f"Error getting block number for chain {chain_id}: {e}")
            await self._failover_provider(chain_id)
            return None

    async def get_gas_price(self, chain_id: int) -> Optional[GasPrice]:
        """
        Get current gas price information.

        Args:
            chain_id: Chain ID

        Returns:
            GasPrice or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            # Get latest block for base fee
            latest_block = provider.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)

            # Get max priority fee
            max_priority_fee = provider.eth.max_priority_fee

            # Calculate max fee (base fee + priority fee + buffer)
            max_fee = base_fee * 2 + max_priority_fee

            # Legacy gas price
            gas_price = provider.eth.gas_price

            return GasPrice(
                base_fee=base_fee,
                priority_fee=max_priority_fee,
                max_fee=max_fee,
                gas_price_gwei=Decimal(str(gas_price)) / Decimal('1e9')
            )
        except Exception as e:
            log.error(f"Error getting gas price for chain {chain_id}: {e}")
            await self._failover_provider(chain_id)
            return None

    async def estimate_gas(
        self,
        chain_id: int,
        transaction: Dict
    ) -> Optional[int]:
        """
        Estimate gas for a transaction.

        Args:
            chain_id: Chain ID
            transaction: Transaction dict with to, from, data, value

        Returns:
            Estimated gas limit or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            estimate = provider.eth.estimate_gas(transaction)
            # Add 20% buffer for safety
            return int(estimate * 1.2)
        except Exception as e:
            log.error(f"Error estimating gas for chain {chain_id}: {e}")
            await self._failover_provider(chain_id)
            return None

    async def get_token_info(
        self,
        token_address: str,
        chain_id: int
    ) -> Optional[TokenInfo]:
        """
        Get token information (symbol, decimals, etc).

        Args:
            token_address: Token contract address
            chain_id: Chain ID

        Returns:
            TokenInfo or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            # Standard ERC20 ABI
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]

            contract = provider.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )

            symbol = contract.functions.symbol().call()
            name = contract.functions.name().call()
            decimals = contract.functions.decimals().call()

            return TokenInfo(
                address=token_address,
                symbol=symbol,
                name=name,
                decimals=decimals
            )
        except Exception as e:
            log.error(f"Error getting token info for {token_address} on chain {chain_id}: {e}")
            return None

    async def get_token_balance(
        self,
        wallet_address: str,
        token_address: str,
        chain_id: int
    ) -> Optional[int]:
        """
        Get token balance for a wallet.

        Args:
            wallet_address: Wallet address
            token_address: Token contract address
            chain_id: Chain ID

        Returns:
            Token balance (in smallest unit) or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            erc20_abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]

            contract = provider.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )

            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()

            return balance
        except Exception as e:
            log.error(f"Error getting token balance: {e}")
            return None

    async def get_transaction_receipt(
        self,
        tx_hash: str,
        chain_id: int
    ) -> Optional[Dict]:
        """
        Get transaction receipt.

        Args:
            tx_hash: Transaction hash
            chain_id: Chain ID

        Returns:
            Receipt dict or None
        """
        provider = self.get_provider(chain_id)
        if not provider:
            return None

        try:
            receipt = provider.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            log.debug(f"Transaction {tx_hash} not found yet: {e}")
            return None

    async def get_token_price_usd(
        self,
        token_address: str,
        chain_id: int
    ) -> Optional[Decimal]:
        """
        Get token price in USD using external price API.

        Args:
            token_address: Token address
            chain_id: Chain ID

        Returns:
            Price in USD or None
        """
        # TODO: Implement with 1inch API or Coingecko
        # For now, return mock data
        mock_prices = {
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": Decimal("1.00"),  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": Decimal("1.00"),  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": Decimal("1.00"),  # DAI
        }

        return mock_prices.get(token_address, Decimal("0"))

    def is_valid_address(self, address: str) -> bool:
        """
        Check if an address is valid.

        Args:
            address: Ethereum address

        Returns:
            True if valid
        """
        return Web3.is_address(address)

    def to_checksum_address(self, address: str) -> str:
        """
        Convert address to checksum format.

        Args:
            address: Ethereum address

        Returns:
            Checksummed address
        """
        return Web3.to_checksum_address(address)


# Global Web3 service instance
web3_service = Web3Service()
