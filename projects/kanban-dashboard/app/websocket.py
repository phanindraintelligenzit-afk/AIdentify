"""
WebSocket connection manager for real-time updates.
"""
import json
from typing import Dict, List, Set

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections organized by board rooms."""

    def __init__(self):
        # board_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Global connections (all boards)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, board_id: int = None):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if board_id:
            if board_id not in self.active_connections:
                self.active_connections[board_id] = set()
            self.active_connections[board_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, board_id: int = None):
        """Remove a WebSocket connection."""
        if board_id and board_id in self.active_connections:
            self.active_connections[board_id].discard(websocket)
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]
        else:
            self.global_connections.discard(websocket)

    async def broadcast_to_board(self, board_id: int, message: dict):
        """Send a message to all connections watching a specific board."""
        connections = self.active_connections.get(board_id, set()).copy()
        # Also include global connections
        connections.update(self.global_connections)

        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, board_id)

    async def broadcast_global(self, message: dict):
        """Send a message to all connections."""
        all_conns = set(self.global_connections)
        for conns in self.active_connections.values():
            all_conns.update(conns)

        disconnected = []
        for connection in all_conns:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Global instance
manager = ConnectionManager()
