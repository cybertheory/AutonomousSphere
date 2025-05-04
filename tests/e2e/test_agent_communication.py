import pytest
import asyncio
import aiohttp
import json
from datetime import datetime

@pytest.mark.asyncio
async def test_agent_to_agent_communication(wait_for_services, http_session):
    """Test communication between agents through the chat platform."""
    # Base URLs
    api_url = "http://api:8000"
    registry_url = "http://registry:8081"
    
    # Step 1: Register two test agents
    agent1_data = {
        "name": "AgentA",
        "url": "http://agent1:8080",
        "description": "Agent A for testing",
        "capabilities": {"text": True}
    }
    
    agent2_data = {
        "name": "AgentB",
        "url": "http://agent2:8080",
        "description": "Agent B for testing",
        "capabilities": {"text": True}
    }
    
    async with http_session.post(
        f"{registry_url}/agents",
        json=agent1_data
    ) as response:
        assert response.status == 200
    
    async with http_session.post(
        f"{registry_url}/agents",
        json=agent2_data
    ) as response:
        assert response.status == 200
    
    # Step 2: Register a user
    async with http_session.post(
        f"{api_url}/auth/register",
        json={
            "username": "a2auser",
            "email": "a2a@example.com",
            "password": "password123"
        }
    ) as response:
        assert response.status == 200
    
    # Step 3: Login
    async with http_session.post(
        f"{api_url}/auth/token",
        data={
            "username": "a2auser",
            "password": "password123"
        }
    ) as response:
        assert response.status == 200
        token_data = await response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 4: Create a channel
    async with http_session.post(
        f"{api_url}/channels/",
        headers=headers,
        json={
            "name": "agent-channel",
            "description": "Channel for agent communication",
            "is_private": False
        }
    ) as response:
        assert response.status == 200
        channel_data = await response.json()
        channel_id = channel_data["id"]
    
    # Step 5: Discover agents
    async with http_session.post(
        f"{api_url}/agents/discover",
        headers=headers
    ) as response:
        assert response.status == 200
    
    # Step 6: Send a message from Agent A to the channel
    # (Simulating this since we don't have actual agent implementations)
    agent_message = {
        "content": "@AgentB Hello from Agent A",
        "agent": "AgentA",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # This would normally be done by the agent itself
    # For testing, we'll use the API to post a message as if it came from Agent A
    async with http_session.post(
        f"{api_url}/messages/channel/{channel_id}",
        headers=headers,
        json={
            "content": "@AgentB Hello from Agent A",
            "agent_name": "AgentA"  # This would be handled by the API in a real scenario
        }
    ) as response:
        assert response.status == 200
    
    # Step 7: Check that Agent B received the message
    # In a real scenario, Agent B would be notified via the A2A protocol
    # For testing, we'll check the channel messages
    async with http_session.get(
        f"{api_url}/messages/channel/{channel_id}",
        headers=headers
    ) as response:
        assert response.status == 200
        messages = await response.json()
        assert len(messages) >= 1
        assert any("@AgentB Hello from Agent A" in msg["content"] for msg in messages)