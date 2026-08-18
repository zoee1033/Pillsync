from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import ws_manager

router = APIRouter(
    prefix="/ws",
    tags=["Real-time WebSockets"]
)


@router.websocket("/notifications/{user_id}")
async def websocket_notification_endpoint(
    websocket: WebSocket,
    user_id: int
):
    """
    WebSocket endpoint for real-time notification sync, unread badge count,
    and instant UI updates on PillSync frontend.
    """
    await ws_manager.connect(user_id=user_id, websocket=websocket)
    try:
        while True:
            # Keep connection alive & listen for client ping/ack
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id=user_id, websocket=websocket)
    except Exception:
        ws_manager.disconnect(user_id=user_id, websocket=websocket)
