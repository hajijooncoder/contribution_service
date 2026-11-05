import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.websocket.manager import ws_manager
from app.core.security import create_access_token
import asyncio

client = TestClient(app)

def test_websocket_connect_and_ping():
    """Test connecting to websocket endpoint and exchanging ping/pong"""
    user_id = "test-ws-user-1"
    with client.websocket_connect(f"/api/v1/ws/{user_id}") as websocket:
        # Check initial acknowledgment
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["user_id"] == user_id

        # Send ping
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"

def test_websocket_direct_notification():
    """Test dispatching real-time notification to connected client"""
    user_id = "test-ws-user-2"
    with client.websocket_connect(f"/api/v1/ws/{user_id}") as websocket:
        # Initial ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_established"

        # Push notification via manager
        asyncio.run(
            ws_manager.send_personal_notification(
                user_id,
                {
                    "type": "review_decision_update",
                    "title": "ماده ۱۰ قانون مدنی",
                    "new_status": "accepted",
                    "message": "مشارکت شما تایید شد!"
                }
            )
        )

        msg = websocket.receive_json()
        assert msg["type"] == "review_decision_update"
        assert msg["new_status"] == "accepted"
        assert "مشارکت شما تایید شد!" in msg["message"]

def test_websocket_token_validation():
    """Test connecting with valid and invalid JWT tokens"""
    user_id = "test-ws-user-3"
    valid_token = create_access_token(user_id, role="contributor")
    
    # Valid token
    with client.websocket_connect(f"/api/v1/ws/{user_id}?token={valid_token}") as websocket:
        ack = websocket.receive_json()
        assert ack["type"] == "connection_established"

    # Token for a different user should be rejected
    mismatch_token = create_access_token("other-user-999", role="contributor")
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/{user_id}?token={mismatch_token}") as websocket:
            websocket.receive_json()
