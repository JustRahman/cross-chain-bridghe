"""Bridge client implementations for fetching quotes from different bridge protocols"""

from app.services.bridge_clients.base import BridgeClient
from app.services.bridge_clients.across import AcrossClient
from app.services.bridge_clients.hop import HopClient
from app.services.bridge_clients.stargate import StargateClient
from app.services.bridge_clients.synapse import SynapseClient
from app.services.bridge_clients.celer import CelerClient
from app.services.bridge_clients.connext import ConnextClient
from app.services.bridge_clients.multichain import MultichainClient
from app.services.bridge_clients.wormhole import WormholeClient
from app.services.bridge_clients.layerzero import LayerZeroClient
from app.services.bridge_clients.socket import SocketClient

__all__ = [
    "BridgeClient",
    "AcrossClient",
    "HopClient",
    "StargateClient",
    "SynapseClient",
    "CelerClient",
    "ConnextClient",
    "MultichainClient",
    "WormholeClient",
    "LayerZeroClient",
    "SocketClient",
]
