import pytest
import asyncio
import aiohttp
import json
import websockets
from datetime import datetime

@pytest.mark.asyncio
async def test_full_chat_flow(wait_for_services, http_session):
    """Test the full chat flow from registration to messaging."""
    # Base URLs
    api_url = "http://api:8000"
    
    # Step 1: Register a user
    async with http_session.post(
        f"{api_url}/auth/register",
        json={
            "username": "e2euser",
            "email": "e2e@example.com",
            "password": "password123"
        }
    ) as response:
        assert response.status == 200
        user_data = await response.json()
        assert user_data["username"] == "e2euser"
    
    # Step 2: Login
    async with http_session.post(
        f"{api_url}/auth/token",
        data={
            "username": "e2euser",
            "password": "password123"
        }
    ) as response:
        assert response.status == 200
        token_data = await response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 3: Create a channel
    async with http_session.post(
        f"{api_url}/channels/",
        headers=headers,
        json={
            "name": "e2e-channel",
            "description": "End-to-end test channel",
            "is_private": False
        }
    ) as response:
        assert response.status == 200
        channel_data = await response.json()
        channel_id = channel_data["id"]
    
    # Step 4: Discover agents
    async with http_session.post(
        f"{api_url}/agents/discover",
        headers=headers
    ) as response:
        assert response.status == 200
    
    # Step 5: List agents
    async with http_session.get(
        f"{api_url}/agents/",
        headers=headers
    ) as response:
        assert response.status == 200
        agents = await response.json()
        # If there are agents, use the first one
        if agents:
            agent_name = agents[0]["name"]
            
            # Step 6: Send a message to the agent
            async with http_session.post(
                f"{api_url}/agents/message/{agent_name}",
                headers=headers,
                params={"message": "Hello agent", "channel_id": channel_id}
            ) as response:
                assert response.status == 200
                agent_response = await response.json()
                assert "response" in agent_response
    
    # Step 7: Connect to WebSocket and send/receive messages
    uri = f"ws://api:8000/ws/channel/{channel_id}"
    async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {access_token}"}) as websocket:
        # Send a message
        message = {
            "content": "Hello from WebSocket",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send(json.dumps(message))
        
        # Receive the message back (echo)
        response = await websocket.recv()
        response_data = json.loads(response)
        assert "content" in response_data
        assert response_data["content"] == "Hello from WebSocket"

@pytest.mark.asyncio
async def test_agent_registration(wait_for_services, http_session):
    """Test that agents can register with the registry and be discovered."""
    # Base URLs
    registry_url = "http://registry:8081"
    
    # Step 1: Register a new agent
    agent_data = {
        "name": "TestAgent",
        "url": "http://test-agent:8080",
        "description": "A test agent for e2e testing",
        "capabilities": {"text": True}
    }
    
    async with http_session.post(
        f"{registry_url}/agents",
        json=agent_data
    ) as response:
        assert response.status == 200
        registered_agent = await response.json()
        assert registered_agent["name"] == "TestAgent"
    
    # Step 2: Get the agent from the registry
    async with http_session.get(
        f"{registry_url}/agents/TestAgent"
    ) as response:
        assert response.status == 200
        agent = await response.json()
        assert agent["name"] == "TestAgent"
        assert agent["url"] == "http://test-agent:8080"
    
    # Step 3: List all agents
    async with http_session.get(
        f"{registry_url}/agents"
    ) as response:
        assert response.status == 200
        agents = await response.json()
        assert any(a["name"] == "TestAgent" for a in agents)