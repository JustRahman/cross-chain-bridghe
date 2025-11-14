#!/usr/bin/env python3
"""Update bridges with comprehensive token support"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.models.bridge import Bridge
from app.core.logging import log


def update_bridge_tokens():
    """Update all bridges with comprehensive token addresses"""

    print("Updating bridge token configurations...")

    db = SessionLocal()
    try:
        # Comprehensive token addresses per chain
        # Format: {chain_id: [token_addresses]}

        # Get all bridges
        bridges = db.query(Bridge).all()

        if not bridges:
            print("❌ No bridges found in database!")
            print("   Run: python scripts/init_db.py first")
            return

        # Token configurations for different bridge protocols
        token_configs = {
            "Across Protocol": {
                "1": [  # Ethereum
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                ],
                "42161": [  # Arbitrum
                    "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
                    "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # USDT
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
                ],
                "10": [  # Optimism
                    "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC
                    "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x4200000000000000000000000000000000000006",  # WETH
                ],
                "137": [  # Polygon
                    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
                    "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
                    "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",  # DAI
                    "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
                ],
                "8453": [  # Base
                    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
                    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",  # DAI
                    "0x4200000000000000000000000000000000000006",  # WETH
                ]
            },
            "Stargate Finance": {
                "1": [  # Ethereum
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                ],
                "42161": [  # Arbitrum
                    "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
                    "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # USDT
                ],
                "10": [  # Optimism
                    "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC
                    "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT
                ],
                "137": [  # Polygon
                    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
                    "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
                ]
            },
            "Hop Protocol": {
                "1": [  # Ethereum
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                ],
                "42161": [  # Arbitrum
                    "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
                    "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # USDT
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
                ],
                "10": [  # Optimism
                    "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC
                    "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x4200000000000000000000000000000000000006",  # WETH
                ],
                "137": [  # Polygon
                    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
                    "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
                    "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",  # DAI
                ]
            },
            "Connext": {
                "1": [  # Ethereum
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                ],
                "42161": [  # Arbitrum
                    "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
                ],
                "10": [  # Optimism
                    "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC
                    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                    "0x4200000000000000000000000000000000000006",  # WETH
                ]
            }
        }

        # Update each bridge
        updated_count = 0
        for bridge in bridges:
            if bridge.name in token_configs:
                old_tokens = bridge.supported_tokens
                bridge.supported_tokens = token_configs[bridge.name]

                print(f"\n✓ Updated {bridge.name}")
                print(f"  Old: {len(old_tokens)} chains configured")
                print(f"  New: {len(bridge.supported_tokens)} chains configured")

                # Count total tokens
                total_tokens = sum(len(tokens) for tokens in bridge.supported_tokens.values())
                print(f"  Total tokens: {total_tokens}")

                updated_count += 1
            else:
                print(f"\n⚠️  Skipped {bridge.name} (no token config)")

        # Commit changes
        db.commit()

        print(f"\n{'=' * 60}")
        print(f"✅ Successfully updated {updated_count} bridges!")
        print(f"{'=' * 60}")

        # Show summary
        print("\n📊 Summary of token support:")
        for bridge in db.query(Bridge).all():
            if bridge.supported_tokens:
                total = sum(len(tokens) for tokens in bridge.supported_tokens.values())
                chains = len(bridge.supported_tokens)
                print(f"  • {bridge.name}: {total} tokens across {chains} chains")

        print("\n✨ Run this to test:")
        print("   curl -X GET 'http://localhost:8000/api/v1/bridges/tokens/supported' \\")
        print("     -H 'X-API-Key: nxb_dev_key_12345' | python3 -m json.tool")

    except Exception as e:
        print(f"\n❌ Error updating bridges: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_bridge_tokens()
