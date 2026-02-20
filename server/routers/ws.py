# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""WebSocket broadcast endpoint for live event streaming."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events.

    Attributes:
        active: List of currently connected WebSocket clients.
    """

    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            ws: Incoming WebSocket to accept.
        """
        await ws.accept()
        self.active.append(ws)
        logger.info("WebSocket connected (%d total)", len(self.active))

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket from the active list.

        Args:
            ws: WebSocket to remove.
        """
        if ws in self.active:
            self.active.remove(ws)
        logger.info("WebSocket disconnected (%d remaining)", len(self.active))

    async def broadcast(self, event_type: str, data: dict) -> None:
        """Send a JSON event to all connected clients.

        Dead connections are silently pruned.

        Args:
            event_type: Event classification string (e.g. ``"packet"``).
            data: Payload dict to serialize as JSON.
        """
        msg = json.dumps({"type": event_type, "data": data})
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.active:
                self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Accept a WebSocket connection and keep it alive until the client disconnects.

    Args:
        websocket: The incoming WebSocket connection.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
