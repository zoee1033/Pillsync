import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("SSE_ROUTES")

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications SSE Fallback"]
)


@router.get("/sse/{user_id}")
async def sse_notification_endpoint(user_id: int, request: Request):
    """
    Server-Sent Events (SSE) streaming endpoint acting as real-time fallback
    when WebSockets are disconnected or unavailable.
    """
    async def sse_event_generator():
        queue = ws_manager.add_sse_subscriber(user_id)
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"[SSE] Client disconnected for User #{user_id}")
                    break
                try:
                    message_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: notification\ndata: {message_data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat pulse to keep SSE connection alive
                    yield "event: ping\ndata: keepalive\n\n"
        except Exception as err:
            logger.warning(f"[SSE] Stream error for User #{user_id}: {err}")
        finally:
            ws_manager.remove_sse_subscriber(user_id, queue)

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
