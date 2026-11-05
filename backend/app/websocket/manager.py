from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Thread-safe / Async WebSocket Connection Manager.
    Manages active user connections, direct targeted notifications, and broadcasts.
    """
    def __init__(self):
        # Maps user_id to a set of active WebSockets (allows multiple tabs/devices)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Active sockets: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_notification(self, user_id: str, message: Dict[str, Any]):
        """Sends JSON notification to all active sockets of a specific user."""
        if user_id in self.active_connections:
            dead_sockets = set()
            for ws in list(self.active_connections[user_id]):
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")
                    dead_sockets.add(ws)
            for dead in dead_sockets:
                self.active_connections[user_id].discard(dead)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts notification to all connected users."""
        for user_id, sockets in list(self.active_connections.items()):
            dead_sockets = set()
            for ws in list(sockets):
                try:
                    await ws.send_json(message)
                except Exception as e:
                    dead_sockets.add(ws)
            for dead in dead_sockets:
                sockets.discard(dead)


# Global singleton instance
ws_manager = ConnectionManager()
