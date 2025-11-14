"""
WebSocket endpoint for real-time transaction monitoring.

Allows clients to subscribe to transaction updates and receive push notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import asyncio
import json
from datetime import datetime

from app.core.logging import log
from app.core.security import get_api_key_from_query
from app.db.base import get_db
from app.models.transaction import Transaction
from sqlalchemy.orm import Session


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # Map of transaction_hash -> Set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of websocket -> Set of subscribed transaction hashes
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, transaction_hash: str):
        """Accept WebSocket connection and subscribe to transaction"""
        await websocket.accept()

        # Add to subscriptions
        if websocket not in self.subscriptions:
            self.subscriptions[websocket] = set()
        self.subscriptions[websocket].add(transaction_hash)

        # Add to active connections
        if transaction_hash not in self.active_connections:
            self.active_connections[transaction_hash] = set()
        self.active_connections[transaction_hash].add(websocket)

        log.info(f"WebSocket connected and subscribed to {transaction_hash}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket and cleanup subscriptions"""
        # Get all transaction hashes this websocket was subscribed to
        if websocket in self.subscriptions:
            tx_hashes = self.subscriptions[websocket]

            # Remove from active connections
            for tx_hash in tx_hashes:
                if tx_hash in self.active_connections:
                    self.active_connections[tx_hash].discard(websocket)
                    if not self.active_connections[tx_hash]:
                        del self.active_connections[tx_hash]

            # Remove from subscriptions
            del self.subscriptions[websocket]

        log.info("WebSocket disconnected")

    async def send_update(self, transaction_hash: str, message: dict):
        """Send update to all connections subscribed to a transaction"""
        if transaction_hash not in self.active_connections:
            return

        # Get all websockets subscribed to this transaction
        websockets = self.active_connections[transaction_hash].copy()

        # Send to all connections
        for websocket in websockets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                log.error(f"Error sending WebSocket message: {e}")
                self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for websockets in self.active_connections.values():
            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    log.error(f"Error broadcasting: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/track/{transaction_hash}")
async def websocket_track_transaction(
    websocket: WebSocket,
    transaction_hash: str,
    api_key: str = Depends(get_api_key_from_query)
):
    """
    WebSocket endpoint for real-time transaction tracking.

    Usage:
        ws://localhost:8000/api/v1/ws/track/{transaction_hash}?api_key=your_key

    Messages sent to client:
        {
            "type": "status_update",
            "transaction_hash": "0x...",
            "status": "completed",
            "progress": 100,
            "timestamp": "2025-11-12T10:30:00Z",
            "data": {...}
        }
    """
    await manager.connect(websocket, transaction_hash)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "transaction_hash": transaction_hash,
            "message": "Connected to transaction monitoring",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Start monitoring the transaction
        asyncio.create_task(
            monitor_transaction(transaction_hash, websocket)
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages from client (e.g., ping/pong)
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        log.info(f"Client disconnected from tracking {transaction_hash}")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def monitor_transaction(transaction_hash: str, websocket: WebSocket):
    """
    Monitor a transaction and send updates via WebSocket.

    This is a background task that continuously checks transaction status.
    """
    from app.services.blockchain_rpc import blockchain_rpc

    db = next(get_db())
    last_status = None

    try:
        while True:
            # Check if websocket is still connected
            if websocket not in manager.subscriptions:
                break

            # Query database for transaction
            db_tx = db.query(Transaction).filter(
                Transaction.source_tx_hash == transaction_hash
            ).first()

            if db_tx:
                current_status = db_tx.status

                # Send update if status changed
                if current_status != last_status:
                    await manager.send_update(transaction_hash, {
                        "type": "status_update",
                        "transaction_hash": transaction_hash,
                        "status": current_status,
                        "progress": _calculate_progress(current_status),
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "bridge_name": db_tx.bridge_name,
                            "source_chain": db_tx.source_chain,
                            "destination_chain": db_tx.destination_chain,
                            "amount": db_tx.amount,
                            "destination_tx_hash": db_tx.destination_tx_hash,
                        }
                    })
                    last_status = current_status

                # Stop monitoring if transaction is final
                if current_status in ["completed", "failed"]:
                    await manager.send_update(transaction_hash, {
                        "type": "final_status",
                        "transaction_hash": transaction_hash,
                        "status": current_status,
                        "message": "Transaction monitoring complete",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break

            else:
                # Transaction not in DB, try to fetch from blockchain
                for chain in ["ethereum", "arbitrum", "optimism", "polygon"]:
                    tx_data = await blockchain_rpc.get_transaction(chain, transaction_hash)
                    if tx_data:
                        # Send blockchain update
                        await manager.send_update(transaction_hash, {
                            "type": "blockchain_update",
                            "transaction_hash": transaction_hash,
                            "chain": chain,
                            "status": "0x1" if tx_data.get("status") == "0x1" else "pending",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        break

            # Wait before next check (5 seconds)
            await asyncio.sleep(5)

    except Exception as e:
        log.error(f"Error monitoring transaction {transaction_hash}: {e}")
    finally:
        db.close()


def _calculate_progress(status: str) -> int:
    """Calculate progress percentage based on status"""
    progress_map = {
        "pending": 25,
        "processing": 50,
        "confirming": 75,
        "completed": 100,
        "failed": 0,
    }
    return progress_map.get(status, 0)


@router.websocket("/ws/stats")
async def websocket_stats(
    websocket: WebSocket,
    api_key: str = Depends(get_api_key_from_query)
):
    """
    WebSocket endpoint for real-time bridge statistics.

    Sends periodic updates with bridge performance metrics.
    """
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to bridge statistics stream",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            # Send stats every 10 seconds
            await asyncio.sleep(10)

            # Get database session
            db = next(get_db())

            try:
                # Query recent transaction counts
                from sqlalchemy import func
                from datetime import timedelta

                one_hour_ago = datetime.utcnow() - timedelta(hours=1)

                stats = db.query(
                    Transaction.bridge_name,
                    func.count(Transaction.id).label('count'),
                    func.sum(func.cast(func.length(Transaction.amount), func.Integer)).label('volume')
                ).filter(
                    Transaction.created_at >= one_hour_ago
                ).group_by(
                    Transaction.bridge_name
                ).all()

                stats_data = [
                    {
                        "bridge_name": stat.bridge_name,
                        "transactions_1h": stat.count,
                        "volume_1h": stat.volume or 0
                    }
                    for stat in stats
                ]

                await websocket.send_json({
                    "type": "stats_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": stats_data
                })

            finally:
                db.close()

    except WebSocketDisconnect:
        log.info("Stats WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket stats error: {e}")
