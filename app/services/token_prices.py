"""Token price fetching service using multiple FREE APIs"""
import asyncio
import aiohttp
import requests
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.logging import log


class TokenPriceService:
    """
    Token price service using multiple FREE APIs with fallback chain.

    Primary: CoinLore API (100% free, no API key)
    Fallback 1: Binance API (100% free, no API key)
    Fallback 2: DIA API (100% free, no registration)

    All APIs are completely free with no authentication required.
    """

    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 60  # 60 seconds cache
        self.last_update: Dict[str, datetime] = {}

        # API endpoints
        self.coinlore_api = "https://api.coinlore.net/api"
        self.binance_api = "https://data-api.binance.vision/api/v3"
        self.dia_api = "https://api.diadata.org/v1"

        # CoinLore token ID mapping (ID -> Symbol mapping for correct matching)
        # Note: CoinLore IDs can be unreliable for some tokens, use Binance fallback
        self.coinlore_ids = {
            "USDC": "33285",
            "USDT": "518",
            "DAI": "33285",  # Use USDC as proxy (stablecoin)
            "WETH": "80",    # Use ETH for WETH
            "ETH": "80",
            "MATIC": "2496",
            "AVAX": "44073",
            "FTM": "33830",
            "OP": "95797",
            "ARB": "128123",
            "WBTC": "5032",
            "UNI": "7083",   # Correct Uniswap ID
            "AAVE": "7278",  # Correct Aave ID
            # LINK and BNB use Binance fallback (CoinLore IDs are wrong)
        }

        # Reverse mapping for CoinLore ID -> Our Symbol (one ID can map to multiple symbols)
        self.coinlore_id_to_symbol = {
            "33285": "USDC",  # Also used for DAI (stablecoin proxy)
            "518": "USDT",
            "80": "ETH",      # Also used for WETH
            "2496": "MATIC",
            "44073": "AVAX",
            "33830": "FTM",
            "95797": "OP",
            "128123": "ARB",
            "5032": "WBTC",
            "7083": "UNI",
            "7278": "AAVE",
        }

        # Handle tokens that share the same CoinLore ID
        self.token_aliases = {
            "WETH": "ETH",  # WETH uses ETH price
            "DAI": "USDC",  # DAI uses USDC price (both stablecoins)
        }

        # Binance trading pair mapping (symbol + USDT)
        self.binance_pairs = {
            "USDC": "USDCUSDT",
            "USDT": "USDCUSDT",  # Use USDC as proxy, USDT = ~1.0
            "DAI": "DAIUSDT",
            "WETH": "ETHUSDT",
            "ETH": "ETHUSDT",
            "MATIC": "MATICUSDT",
            "BNB": "BNBUSDT",
            "AVAX": "AVAXUSDT",
            "FTM": "FTMUSDT",
            "OP": "OPUSDT",
            "ARB": "ARBUSDT",
            "WBTC": "BTCUSDT",
            "UNI": "UNIUSDT",
            "LINK": "LINKUSDT",
            "AAVE": "AAVEUSDT",
        }

    async def get_token_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current price for a token using multiple free APIs.

        Tries APIs in order:
        1. CoinLore (primary)
        2. Binance (fallback 1)
        3. DIA (fallback 2)

        Args:
            symbol: Token symbol (e.g., "USDC", "ETH")

        Returns:
            Price in USD as Decimal
        """
        symbol_upper = symbol.upper()

        # Check cache
        if self._is_cached(symbol_upper):
            log.debug(f"Using cached price for {symbol_upper}")
            return Decimal(str(self.cache[symbol_upper]["price"]))

        # Try CoinLore first
        price = await self._fetch_from_coinlore(symbol_upper)
        if price:
            log.info(f"CoinLore price for {symbol_upper}: ${price}")
            self._cache_price(symbol_upper, price)
            return Decimal(str(price))

        # Fallback to Binance
        log.warning(f"CoinLore failed for {symbol_upper}, trying Binance...")
        price = await self._fetch_from_binance(symbol_upper)
        if price:
            log.info(f"Binance price for {symbol_upper}: ${price}")
            self._cache_price(symbol_upper, price)
            return Decimal(str(price))

        # Fallback to DIA
        log.warning(f"Binance failed for {symbol_upper}, trying DIA...")
        price = await self._fetch_from_dia(symbol_upper)
        if price:
            log.info(f"DIA price for {symbol_upper}: ${price}")
            self._cache_price(symbol_upper, price)
            return Decimal(str(price))

        log.error(f"All APIs failed for {symbol_upper}")
        return None

    def _cache_price(self, symbol: str, price: float):
        """Cache price data"""
        self.cache[symbol] = {
            "price": price,
            "timestamp": datetime.utcnow()
        }
        self.last_update[symbol] = datetime.utcnow()

    def _is_cached(self, symbol: str) -> bool:
        """Check if price is cached and not expired"""
        if symbol not in self.cache or symbol not in self.last_update:
            return False

        elapsed = (datetime.utcnow() - self.last_update[symbol]).total_seconds()
        return elapsed < self.cache_ttl

    async def _fetch_from_coinlore(self, symbol: str) -> Optional[float]:
        """
        Fetch token price from CoinLore API (100% free, no API key).

        API Docs: https://www.coinlore.com/cryptocurrency-data-api
        """
        coin_id = self.coinlore_ids.get(symbol)
        if not coin_id:
            log.debug(f"CoinLore: Token {symbol} not in mapping")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.coinlore_api}/ticker/"
                params = {"id": coin_id}

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            price = data[0].get("price_usd")
                            if price:
                                return float(price)
                    else:
                        log.warning(f"CoinLore API returned status {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"CoinLore API timeout for {symbol}")
        except Exception as e:
            log.warning(f"CoinLore API error for {symbol}: {e}")

        return None

    async def _fetch_from_binance(self, symbol: str) -> Optional[float]:
        """
        Fetch token price from Binance API (100% free, no API key).

        API Docs: https://developers.binance.com/docs/binance-spot-api-docs/rest-api
        """
        trading_pair = self.binance_pairs.get(symbol)
        if not trading_pair:
            log.debug(f"Binance: Token {symbol} not in mapping")
            return None

        # Special case for USDT (assume ~$1.0)
        if symbol == "USDT":
            return 1.0

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.binance_api}/ticker/price"
                params = {"symbol": trading_pair}

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get("price")
                        if price:
                            return float(price)
                    else:
                        log.warning(f"Binance API returned status {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"Binance API timeout for {symbol}")
        except Exception as e:
            log.warning(f"Binance API error for {symbol}: {e}")

        return None

    async def _fetch_from_dia(self, symbol: str) -> Optional[float]:
        """
        Fetch token price from DIA API (100% free, no registration).

        API Docs: https://docs.diadata.org/
        """
        # DIA uses different symbol formats
        dia_symbols = {
            "ETH": "Ethereum",
            "WETH": "Ethereum",
            "BTC": "Bitcoin",
            "WBTC": "Bitcoin",
            "USDC": "USD Coin",
            "USDT": "Tether",
            "DAI": "Dai",
            "MATIC": "Polygon",
            "BNB": "Binance Coin",
            "AVAX": "Avalanche",
        }

        dia_symbol = dia_symbols.get(symbol)
        if not dia_symbol:
            log.debug(f"DIA: Token {symbol} not in mapping")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.dia_api}/quotation/{dia_symbol}"

                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get("Price")
                        if price:
                            return float(price)
                    else:
                        log.warning(f"DIA API returned status {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"DIA API timeout for {symbol}")
        except Exception as e:
            log.warning(f"DIA API error for {symbol}: {e}")

        return None

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        Get prices for multiple tokens.

        Args:
            symbols: List of token symbols

        Returns:
            Dict mapping symbol to price
        """
        tasks = [self.get_token_price(symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks)

        return {symbol: price for symbol, price in zip(symbols, prices)}

    async def get_all_supported_prices(self) -> Dict[str, Decimal]:
        """Get prices for all supported tokens"""
        # Get all unique symbols from all API mappings
        all_symbols = set()
        all_symbols.update(self.coinlore_ids.keys())
        all_symbols.update(self.binance_pairs.keys())

        symbols = list(all_symbols)
        prices = await self.get_multiple_prices(symbols)

        # Filter out None values
        return {symbol: price for symbol, price in prices.items() if price is not None}

    async def get_token_details(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed token information using CoinLore API.

        Returns price, market cap, 24h change, etc.
        """
        symbol_upper = symbol.upper()
        coin_id = self.coinlore_ids.get(symbol_upper)
        if not coin_id:
            log.warning(f"Token {symbol_upper} not supported for detailed info")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.coinlore_api}/ticker/"
                params = {"id": coin_id}

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            coin = data[0]
                            return {
                                "symbol": coin.get("symbol", symbol_upper),
                                "name": coin.get("name"),
                                "price_usd": float(coin.get("price_usd", 0)),
                                "market_cap": float(coin.get("market_cap_usd", 0)) if coin.get("market_cap_usd") else None,
                                "volume_24h": float(coin.get("volume24", 0)) if coin.get("volume24") else None,
                                "price_change_24h": float(coin.get("percent_change_24h", 0)) if coin.get("percent_change_24h") else None,
                                "price_change_7d": float(coin.get("percent_change_7d", 0)) if coin.get("percent_change_7d") else None,
                                "last_updated": datetime.utcnow().isoformat()
                            }
        except Exception as e:
            log.error(f"Error fetching details for {symbol}: {e}")

        return None

    def calculate_token_amount(
        self,
        amount_usd: Decimal,
        token_price: Decimal,
        decimals: int = 6
    ) -> str:
        """
        Calculate token amount from USD value.

        Args:
            amount_usd: Amount in USD
            token_price: Token price in USD
            decimals: Token decimals

        Returns:
            Token amount in smallest unit (e.g., wei)
        """
        if token_price == 0:
            return "0"

        token_amount = amount_usd / token_price
        smallest_unit = int(token_amount * (10 ** decimals))
        return str(smallest_unit)

    def calculate_usd_value(
        self,
        token_amount: str,
        token_price: Decimal,
        decimals: int = 6
    ) -> Decimal:
        """
        Calculate USD value from token amount.

        Args:
            token_amount: Amount in smallest unit
            token_price: Token price in USD
            decimals: Token decimals

        Returns:
            USD value
        """
        amount_decimal = Decimal(token_amount) / Decimal(10 ** decimals)
        usd_value = amount_decimal * token_price
        return usd_value.quantize(Decimal("0.01"))

    def get_all_prices_sync(self) -> Dict[str, Dict]:
        """
        Synchronous version of get_all_supported_prices for use in Celery tasks.
        Uses CoinLore API as primary source.

        Returns:
            Dict mapping symbol to price data
        """
        result = {}

        try:
            # Get all coin IDs for CoinLore
            coin_ids = ",".join(self.coinlore_ids.values())

            url = f"{self.coinlore_api}/ticker/"
            params = {"id": coin_ids}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Map back to symbols using ID-based matching (more reliable)
                for coin in data:
                    coin_id = coin.get("id")
                    # Match by ID, not by symbol (CoinLore symbols can be ambiguous)
                    if coin_id in self.coinlore_id_to_symbol:
                        our_symbol = self.coinlore_id_to_symbol[coin_id]
                        result[our_symbol] = {
                            "price": float(coin.get("price_usd", 0)),
                            "market_cap": float(coin.get("market_cap_usd", 0)) if coin.get("market_cap_usd") else None,
                            "volume_24h": float(coin.get("volume24", 0)) if coin.get("volume24") else None,
                            "price_change_24h": float(coin.get("percent_change_24h", 0)) if coin.get("percent_change_24h") else None
                        }

                        # Update cache
                        if coin.get("price_usd"):
                            self.cache[our_symbol] = {
                                "price": float(coin.get("price_usd")),
                                "timestamp": datetime.utcnow()
                            }
                            self.last_update[our_symbol] = datetime.utcnow()

                # Handle token aliases (WETH -> ETH, DAI -> USDC)
                for alias, base_symbol in self.token_aliases.items():
                    if base_symbol in result:
                        result[alias] = result[base_symbol].copy()

                # Get LINK and BNB from Binance (CoinLore IDs are unreliable)
                for symbol in ["LINK", "BNB"]:
                    if symbol not in result:
                        pair = self.binance_pairs.get(symbol)
                        if pair:
                            try:
                                url = f"{self.binance_api}/ticker/price"
                                response = requests.get(url, params={"symbol": pair}, timeout=5)
                                if response.status_code == 200:
                                    data = response.json()
                                    price = float(data.get("price", 0))
                                    result[symbol] = {
                                        "price": price,
                                        "market_cap": None,
                                        "volume_24h": None,
                                        "price_change_24h": None
                                    }
                            except Exception as e:
                                log.warning(f"Binance fallback failed for {symbol}: {e}")

        except Exception as e:
            log.error(f"Error fetching token prices sync: {e}")

            # Fallback to Binance for major tokens
            try:
                for symbol in ["ETH", "BTC", "USDC", "USDT", "LINK", "BNB"]:
                    if symbol == "USDT":
                        result[symbol] = {"price": 1.0, "market_cap": None, "volume_24h": None, "price_change_24h": None}
                        continue

                    pair = self.binance_pairs.get(symbol)
                    if pair:
                        url = f"{self.binance_api}/ticker/price"
                        response = requests.get(url, params={"symbol": pair}, timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            price = float(data.get("price", 0))
                            result[symbol] = {
                                "price": price,
                                "market_cap": None,
                                "volume_24h": None,
                                "price_change_24h": None
                            }
            except Exception as e2:
                log.error(f"Binance fallback also failed: {e2}")

        return result


# Global token price service instance
token_price_service = TokenPriceService()
