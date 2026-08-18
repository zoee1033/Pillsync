import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("WEBSOCKET_MANAGER")


class WebSocketNotificationManager:
    """
    Centralized real-time WebSocket connection manager for PillSync frontend clients.
    Broadcasts real-time notification, badge, unread count, and dashboard sync events.
    Also handles SSE fallback streams.
    """

    def __init__(self):
        # Maps user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Maps user_id -> Set[asyncio.Queue] for SSE fallback streaming
        self.sse_subscribers: Dict[int, Set[asyncio.Queue]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Accepts and registers a new WebSocket client connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"[WebSocket] Connected for User #{user_id}. Active sockets: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: int, websocket: WebSocket):
        """Removes a disconnected WebSocket client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"[WebSocket] Disconnected for User #{user_id}")

    def add_sse_subscriber(self, user_id: int) -> asyncio.Queue:
        """Registers a queue for SSE streaming."""
        queue: asyncio.Queue = asyncio.Queue()
        if user_id not in self.sse_subscribers:
            self.sse_subscribers[user_id] = set()
        self.sse_subscribers[user_id].add(queue)
        logger.info(f"[SSE] Subscriber added for User #{user_id}")
        return queue

    def remove_sse_subscriber(self, user_id: int, queue: asyncio.Queue):
        """Removes an SSE subscriber queue."""
        if user_id in self.sse_subscribers:
            self.sse_subscribers[user_id].discard(queue)
            if not self.sse_subscribers[user_id]:
                del self.sse_subscribers[user_id]
        logger.info(f"[SSE] Subscriber removed for User #{user_id}")

    async def send_personal_event(self, user_id: int, event_type: str, payload: dict):
        """Sends an event payload asynchronously to all open WS connections and SSE streams of a user."""
        message_data = json.dumps({"event": event_type, "data": payload})

        # 1. WebSocket Broadcast
        if user_id in self.active_connections:
            dead_sockets = set()
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_text(message_data)
                    logger.info(f"[WebSocket] Broadcast sent ({event_type}) to User #{user_id}")
                except Exception as err:
                    logger.warning(f"[WebSocket] Broadcast error for User #{user_id}: {err}")
                    dead_sockets.add(connection)
            for dead_ws in dead_sockets:
                self.disconnect(user_id, dead_ws)

        # 2. SSE Broadcast Fallback
        if user_id in self.sse_subscribers:
            for sse_q in list(self.sse_subscribers[user_id]):
                try:
                    sse_q.put_nowait(message_data)
                    logger.info(f"[SSE] Broadcast queued ({event_type}) for User #{user_id}")
                except Exception as err:
                    logger.warning(f"[SSE] Queue error for User #{user_id}: {err}")


ws_manager = WebSocketNotificationManager()


def broadcast_notification_event(user_id: int, event_type: str, payload: dict):
    """
    Thread-safe synchronous bridge function to trigger WebSocket/SSE broadcasts
    from synchronous scheduler jobs or DB transaction threads.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ws_manager.send_personal_event(user_id, event_type, payload),
                loop
            )
        else:
            new_loop = asyncio.new_event_loop()
            new_loop.run_until_complete(ws_manager.send_personal_event(user_id, event_type, payload))
            new_loop.close()
    except Exception as ex:
        logger.warning(f"[RealTime] Event broadcast error: {ex}")

