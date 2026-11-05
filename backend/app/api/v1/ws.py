from typing import Optional
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.websocket.manager import ws_manager
from app.core.security import decode_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

REVALIDATION_INTERVAL = 300  # 5 minutes


@router.websocket("/ws/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
):
    """
    درگاه وب‌سوکت برای دریافت آنی نوتیفیکیشن‌های داوری، تغییر وضعیت مشارکت و اعتبارات MCC.
    شامل اعتبارسنجی دوره‌ای توکن برای جلوگیری از دسترسی با توکن منقضی.
    توکن اختیاری است برای سازگاری با گذشته، اما در صورت ارائه اعتبارسنجی می‌شود.
    """
    # Validate token if provided
    authenticated = False
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub") == user_id:
            authenticated = True
        else:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    
    await ws_manager.connect(user_id, websocket)
    
    # Start periodic revalidation task only if authenticated
    revalidation_task = None
    if authenticated:
        revalidation_task = asyncio.create_task(_periodic_token_revalidation(websocket, user_id, token))
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "اتصال بی‌درنگ به شبکه نوتیفیکیشن MAHOUNN برقرار شد.",
            "authenticated": authenticated
        })
        
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("revalidate:"):
                # Manual revalidation request from client
                new_token = data.split(":", 1)[1]
                payload = decode_access_token(new_token)
                if payload and payload.get("sub") == user_id:
                    await websocket.send_json({"type": "revalidation_success"})
                else:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token revalidation failed")
                    return
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
    finally:
        if revalidation_task:
            revalidation_task.cancel()
            try:
                await revalidation_task
            except asyncio.CancelledError:
                pass
        ws_manager.disconnect(user_id, websocket)


async def _periodic_token_revalidation(websocket: WebSocket, user_id: str, current_token: str):
    """Periodically validate the WebSocket token to detect expiry/revocation."""
    while True:
        try:
            await asyncio.sleep(REVALIDATION_INTERVAL)
            
            # Check if token is still valid
            payload = decode_access_token(current_token)
            if not payload or payload.get("sub") != user_id:
                logger.warning(f"WebSocket token expired for user {user_id}, closing connection")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token expired")
                return
                
            # Optionally send a heartbeat to client
            await websocket.send_json({"type": "heartbeat"})
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during token revalidation for {user_id}: {e}")
            try:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Revalidation error")
            except Exception:
                pass
            return