import pytest
from fastapi.testclient import TestClient
import json
from api.main import app

@pytest.fixture
def auth_client(client):
    """Create an authenticated test client."""
    # Register a test user
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    
    # Login
    response = client.post(
        "/auth/token",
        data={
            "username": "testuser",
            "password": "password123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Create a client with the auth token
    client.headers = {
        "Authorization": f"Bearer {token}"
    }
    
    return client

def test_create_channel(auth_client):
    """Test creating a channel."""
    response = auth_client.post(
        "/channels/",
        json={
            "name": "test-channel",
            "description": "A test channel",
            "is_private": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-channel"
    assert data["description"] == "A test channel"
    assert data["is_private"] is False
    
    # Check that the channel exists
    response = auth_client.get("/channels/")
    assert response.status_code == 200
    channels = response.json()
    assert len(channels) == 1
    assert channels[0]["name"] == "test-channel"

def test_send_message(auth_client):
    """Test sending a message to a channel."""
    # Create a channel
    response = auth_client.post(
        "/channels/",
        json={
            "name": "message-channel",
            "description": "A channel for messages",
            "is_private": False
        }
    )
    assert response.status_code == 200
    channel_id = response.json()["id"]
    
    # Send a message
    response = auth_client.post(
        f"/messages/channel/{channel_id}",
        json={
            "content": "Hello, world!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, world!"
    
    # Get channel messages
    response = auth_client.get(f"/messages/channel/{channel_id}")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello, world!"

def test_agent_endpoints(auth_client):
    """Test agent-related endpoints."""
    # Trigger agent discovery
    response = auth_client.post("/agents/discover")
    assert response.status_code == 200
    
    # List agents
    response = auth_client.get("/agents/")
    assert response.status_code == 200
    # Note: The actual agents will depend on what's registered in the registry