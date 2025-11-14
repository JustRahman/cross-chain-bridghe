"""Bridge status and information endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import asyncio

from app.db.base import get_db
from app.schemas.bridge import (
    BridgeStatusResponse,
    BridgeHealthStatus,
    SupportedTokensResponse,
    SupportedToken
)
from app.models.bridge import Bridge
from app.core.security import get_api_key
from app.core.logging import log
from app.services.route_discovery import route_discovery_engine


router = APIRouter()


# Chain ID to name mapping
CHAIN_ID_TO_NAME = {
    1: "ethereum",
    10: "optimism",
    42161: "arbitrum",
    137: "polygon",
    8453: "base"
}

# Comprehensive token metadata (address -> info) for all chains
# All addresses are lowercase for consistent matching
TOKEN_METADATA = {
    # Ethereum (chain_id: 1)
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
    "0xdac17f958d2ee523a2206206994597c13d831ec7": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
    "0x6b175474e89094c44da98b954eedeac495271d0f": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "decimals": 8},
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"symbol": "UNI", "name": "Uniswap", "decimals": 18},
    "0x514910771af9ca656af840dff83e8264ecf986ca": {"symbol": "LINK", "name": "Chainlink", "decimals": 18},
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": {"symbol": "AAVE", "name": "Aave Token", "decimals": 18},

    # Arbitrum (chain_id: 42161)
    "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
    "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
    "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
    "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
    "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "decimals": 8},
    "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0": {"symbol": "UNI", "name": "Uniswap", "decimals": 18},
    "0xf97f4df75117a78c1a5a0dbb814af92458539fb4": {"symbol": "LINK", "name": "Chainlink", "decimals": 18},
    "0xba5ddd1f9d7f570dc94a51479a000e3bce967196": {"symbol": "AAVE", "name": "Aave Token", "decimals": 18},

    # Optimism (chain_id: 10)
    "0x7f5c764cbc14f9669b88837ca1490cca17c31607": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
    "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
    "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
    "0x4200000000000000000000000000000000000006": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
    "0x68f180fcce6836688e9084f035309e29bf0a2095": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "decimals": 8},
    "0x6fd9d7ad17242c41f7131d257212c54a0e816691": {"symbol": "UNI", "name": "Uniswap", "decimals": 18},
    "0x350a791bfc2c21f9ed5d10980dad2e2638ffa7f6": {"symbol": "LINK", "name": "Chainlink", "decimals": 18},
    "0x76fb31fb4af56892a25e32cfc43de717950c9278": {"symbol": "AAVE", "name": "Aave Token", "decimals": 18},

    # Polygon (chain_id: 137)
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
    "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
    "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
    "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": {"symbol": "WMATIC", "name": "Wrapped Matic", "decimals": 18},
    "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "decimals": 8},
    "0xb33eaad8d922b1083446dc23f610c2567fb5180f": {"symbol": "UNI", "name": "Uniswap", "decimals": 18},
    "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39": {"symbol": "LINK", "name": "Chainlink", "decimals": 18},
    "0xd6df932a45c0f255f85145f286ea0b292b21c90b": {"symbol": "AAVE", "name": "Aave Token", "decimals": 18},

    # Base (chain_id: 8453)
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
    "0x4200000000000000000000000000000000000006": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
}


def convert_chain_ids_to_names(chain_ids):
    """Convert chain IDs (integers) to chain names (strings)"""
    if not chain_ids:
        return []
    return [CHAIN_ID_TO_NAME.get(chain_id, str(chain_id)) for chain_id in chain_ids]


@router.get("/status", response_model=BridgeStatusResponse)
async def get_bridge_status(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get health status of all integrated bridges.

    Returns real-time health information, success rates, and uptime
    for all bridge protocols integrated in the system.
    """
    try:
        log.info("Performing real-time health checks on all bridges")

        # Get all bridge instances from route discovery engine
        bridges = route_discovery_engine.bridges

        # Perform health checks in parallel
        health_check_tasks = [bridge.check_availability() for bridge in bridges]
        health_results = await asyncio.gather(*health_check_tasks, return_exceptions=True)

        # Build bridge status list
        bridge_statuses = []

        for i, bridge in enumerate(bridges):
            health_result = health_results[i]

            # Handle exceptions in health checks
            if isinstance(health_result, Exception):
                log.error(f"Health check failed for {bridge.name}: {health_result}")
                is_healthy = False
            else:
                is_healthy = health_result.is_healthy

            # Get chain names from supported chain IDs
            supported_chain_names = convert_chain_ids_to_names(bridge.supported_chains)

            # Fetch historical data from database if available
            db_bridge = db.query(Bridge).filter(Bridge.protocol == bridge.protocol).first()

            if db_bridge:
                success_rate = db_bridge.success_rate
                avg_completion_time = db_bridge.average_completion_time
                uptime_pct = db_bridge.uptime_percentage
            else:
                # Use estimated values for new bridges
                success_rate = 95.0 if is_healthy else 85.0
                avg_completion_time = 300  # 5 minutes default
                uptime_pct = 98.0 if is_healthy else 90.0

            bridge_status = BridgeHealthStatus(
                name=bridge.name,
                protocol=bridge.protocol,
                is_healthy=is_healthy,
                is_active=True,
                success_rate=success_rate,
                average_completion_time=avg_completion_time,
                uptime_percentage=uptime_pct,
                last_health_check=datetime.utcnow(),
                supported_chains=supported_chain_names
            )

            bridge_statuses.append(bridge_status)

        healthy_count = sum(1 for b in bridge_statuses if b.is_healthy)

        log.info(f"Health check complete: {healthy_count}/{len(bridge_statuses)} bridges healthy")

        response = BridgeStatusResponse(
            bridges=bridge_statuses,
            total_bridges=len(bridge_statuses),
            healthy_bridges=healthy_count,
            checked_at=datetime.utcnow()
        )

        return response

    except Exception as e:
        log.error(f"Error getting bridge status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get bridge status: {str(e)}"
        )


@router.get("/tokens/supported", response_model=SupportedTokensResponse)
async def get_supported_tokens(
    chain: Optional[str] = Query(None, description="Filter by chain name"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get list of supported tokens across all chains.

    Queries all active bridges from the database and aggregates their supported tokens.
    Returns token contract addresses, symbols, names, and decimals for each chain.

    Optionally filter by chain to see which tokens are supported on a specific blockchain.
    """
    try:
        log.info(f"Getting supported tokens{' for chain: ' + chain if chain else ''}")

        # Query all active bridges from database
        bridges = db.query(Bridge).filter(Bridge.is_active == True).all()

        if not bridges:
            log.warning("No active bridges found in database")
            # Fallback to route_discovery_engine bridges
            bridges = route_discovery_engine.bridges

        # Aggregate all unique token addresses across all bridges
        token_set = set()  # (chain_id, address) tuples to avoid duplicates

        for bridge in bridges:
            # Get supported_tokens from bridge (JSON field: {chain_id: [addresses]})
            if hasattr(bridge, 'supported_tokens') and bridge.supported_tokens:
                supported_tokens = bridge.supported_tokens
            else:
                # Fallback: get from route_discovery_engine if database doesn't have it
                bridge_obj = next((b for b in route_discovery_engine.bridges if b.name == (bridge.name if hasattr(bridge, 'name') else str(bridge))), None)
                if bridge_obj and hasattr(bridge_obj, 'supported_tokens'):
                    supported_tokens = bridge_obj.supported_tokens
                else:
                    continue

            # Extract tokens from supported_tokens JSON
            for chain_id, addresses in supported_tokens.items():
                chain_id_int = int(chain_id) if isinstance(chain_id, str) else chain_id

                if isinstance(addresses, list):
                    for address in addresses:
                        token_set.add((chain_id_int, address.lower()))
                elif isinstance(addresses, dict):
                    # Format: {symbol: address}
                    for symbol, address in addresses.items():
                        token_set.add((chain_id_int, address.lower()))

        # Convert to SupportedToken objects with metadata
        tokens = []
        for chain_id, address in token_set:
            # Get chain name
            chain_name = CHAIN_ID_TO_NAME.get(chain_id, f"chain_{chain_id}")

            # Filter by chain if specified
            if chain and chain_name.lower() != chain.lower():
                continue

            # Get token metadata from our comprehensive mapping
            metadata = TOKEN_METADATA.get(address)

            if metadata:
                tokens.append(SupportedToken(
                    symbol=metadata["symbol"],
                    name=metadata["name"],
                    address=address,
                    decimals=metadata["decimals"],
                    chain=chain_name
                ))
            else:
                # Unknown token - include it but with minimal info
                log.warning(f"Unknown token address {address} on chain {chain_name}")
                tokens.append(SupportedToken(
                    symbol="UNKNOWN",
                    name="Unknown Token",
                    address=address,
                    decimals=18,  # Default
                    chain=chain_name
                ))

        # Sort by chain and symbol for consistent output
        tokens.sort(key=lambda t: (t.chain, t.symbol, t.address))

        log.info(f"Found {len(tokens)} supported tokens across {len(set(t.chain for t in tokens))} chains")

        response = SupportedTokensResponse(
            tokens=tokens,
            total_tokens=len(tokens)
        )

        return response

    except Exception as e:
        log.error(f"Error getting supported tokens: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported tokens: {str(e)}"
        )
