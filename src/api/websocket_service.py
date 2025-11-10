"""
WebSocket Service for Real-Time Dashboard Updates

Manages WebSocket connections and broadcasts updates to connected clients.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        """
        async with self._lock:
            self.active_connections.discard(websocket)

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message_type: Type of message (metrics_update, alert, intervention, analytics_update)
            data: Message payload
        """
        if not self.active_connections:
            return

        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        message_json = json.dumps(message)

        # Get a snapshot of connections to avoid iteration issues
        async with self._lock:
            connections = list(self.active_connections)

        # Broadcast to all connections
        disconnected = []

        for connection in connections:
            try:
                await connection.send_text(message_json)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections.discard(conn)

        logger.debug(f"Broadcasted {message_type} to {len(connections) - len(disconnected)} clients")

    async def send_personal(self, websocket: WebSocket, message_type: str, data: Dict[str, Any]) -> None:
        """
        Send a message to a specific client.

        Args:
            websocket: Target WebSocket connection
            message_type: Type of message
            data: Message payload
        """
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        """
        return len(self.active_connections)


# Singleton instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Get the singleton connection manager instance.
    """
    return connection_manager
