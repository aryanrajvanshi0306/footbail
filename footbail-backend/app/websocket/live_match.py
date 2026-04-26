"""
Live Match WebSocket Manager

WS  /ws/match/{match_id}   → real-time event stream for a match room
POST /ws/match/{match_id}/broadcast → (internal) push event to all subscribers
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState

from app.core.redis import get_redis

log = logging.getLogger(__name__)
router = APIRouter()

# ─── Connection Manager ───────────────────────────────────────────────────────

class MatchConnectionManager:
    """Manages per-match WebSocket rooms with Redis pub/sub bridging."""

    def __init__(self) -> None:
        # match_id → set of active WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, match_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[match_id].add(ws)
        log.info("WS connected: match=%s  total=%d", match_id, len(self._rooms[match_id]))

    def disconnect(self, match_id: str, ws: WebSocket) -> None:
        self._rooms[match_id].discard(ws)
        if not self._rooms[match_id]:
            del self._rooms[match_id]
        log.info("WS disconnected: match=%s", match_id)

    async def broadcast(self, match_id: str, data: Any) -> None:
        """Fan-out a message to all connections in a room."""
        payload = json.dumps(data) if not isinstance(data, str) else data
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(match_id, [])):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(match_id, ws)


manager = MatchConnectionManager()


# ─── Redis → WebSocket bridge (background task) ──────────────────────────────

async def redis_to_ws_bridge(match_id: str) -> None:
    """Subscribe to Redis channel and forward messages to all WS clients."""
    r = await get_redis()
    pubsub = r.pubsub()
    channel = f"match:{match_id}:events"
    await pubsub.subscribe(channel)
    log.info("Redis bridge started for match %s", match_id)
    try:
        while True:
            if not manager._rooms.get(match_id):
                break  # nobody left — stop the bridge task
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg["type"] == "message":
                await manager.broadcast(match_id, msg["data"])
            await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        log.info("Redis bridge stopped for match %s", match_id)


# Track running bridge tasks so we don't spawn duplicates
_bridge_tasks: dict[str, asyncio.Task] = {}


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/match/{match_id}")
async def match_websocket(websocket: WebSocket, match_id: str):
    await manager.connect(match_id, websocket)

    # Start Redis bridge if not already running for this match
    if match_id not in _bridge_tasks or _bridge_tasks[match_id].done():
        task = asyncio.create_task(redis_to_ws_bridge(match_id))
        _bridge_tasks[match_id] = task

    try:
        # Send current match state on connect
        await websocket.send_json({
            "type": "connected",
            "match_id": match_id,
            "message": "Connected to live match feed",
        })

        # Keep the connection alive; process incoming pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send keep-alive
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(match_id, websocket)
