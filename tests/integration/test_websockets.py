import pytest
import asyncio
import websockets
import json
from datetime import datetime

@pytest.mark.asyncio
async def test_websocket_connection(wait_for_services, auth_client):
    """Test WebSocket connection and message exchange."""
    # Create a channel
    response = auth_client.post(
        "/channels/",
        json={
            "name": "websocket-channel",
            "description": "A channel for WebSocket testing",
            "is_private": False
        }
    )
    assert response.status_code == 200
    channel_id = response.json()["id"]
    
    # Get the auth token
    token = auth_client.headers["Authorization"].split(" ")[1]
    
    # Connect to the WebSocket
    uri = f"ws://api:8000/ws/channel/{channel_id}"
    async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {token}"}) as websocket:
        # Send a message
        message = {
            "content": "Hello from WebSocket test",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send(json.dumps(message))
        
        # Receive the message back
        response = await websocket.recv()
        response_data = json.loads(response)
        assert "content" in response_data
        assert response_data["content"] == "Hello from WebSocket test"
        
        # Send another message
        message2 = {
            "content": "Second message",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send(json.dumps(message2))
        
        # Receive the second message
        response2 = await websocket.recv()
        response_data2 = json.loads(response2)
        assert "content" in response_data2
        assert response_data2["content"] == "Second message"

@pytest.mark.asyncio
async def test_multiple_websocket_clients(wait_for_services, auth_client):
    """Test multiple WebSocket clients connected to the same channel."""
    # Create a channel
    response = auth_client.post(
        "/channels/",
        json={
            "name": "multi-client-channel",
            "description": "A channel for multiple WebSocket clients",
            "is_private": False
        }
    )
    assert response.status_code == 200
    channel_id = response.json()["id"]
    
    # Get the auth token
    token = auth_client.headers["Authorization"].split(" ")[1]
    
    # Connect two WebSocket clients
    uri = f"ws://api:8000/ws/channel/{channel_id}"
    
    async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {token}"}) as websocket1, \
               websockets.connect(uri, extra_headers={"Authorization": f"Bearer {token}"}) as websocket2:
        
        # Client 1 sends a message
        message = {
            "content": "Hello from client 1",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket1.send(json.dumps(message))
        
        # Both clients should receive the message
        response1 = await websocket1.recv()
        response_data1 = json.loads(response1)
        assert response_data1["content"] == "Hello from client 1"
        
        response2 = await websocket2.recv()
        response_data2 = json.loads(response2)
        assert response_data2["content"] == "Hello from client 1"
        
        # Client 2 sends a message
        message2 = {
            "content": "Hello from client 2",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket2.send(json.dumps(message2))
        
        # Both clients should receive the message
        response3 = await websocket1.recv()
        response_data3 = json.loads(response3)
        assert response_data3["content"] == "Hello from client 2"
        
        response4 = await websocket2.recv()
        response_data4 = json.loads(response4)
        assert response_data4["content"] == "Hello from client 2"