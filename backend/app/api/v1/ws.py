from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.websocket.manager import ws_manager
from app.core.security import decode_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
):
    """
    درگاه وب‌سوکت برای دریافت آنی نوتیفیکیشن‌های داوری، تغییر وضعیت مشارکت و اعتبارات MCC.
    """
    # Verify token if provided
    if token:
        payload = decode_access_token(token)
        if not payload or payload.get("sub") != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect(user_id, websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "اتصال بی‌درنگ به شبکه نوتیفیکیشن MAHOUNN برقرار شد.",
        })
        while True:
            # Keep socket open and listen for pings / client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
        ws_manager.disconnect(user_id, websocket)
