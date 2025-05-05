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
    
    # Create a client session for HTTP requests
    async with aiohttp.ClientSession() as session:
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
        
        async with session.post(
            f"{registry_url}/agents",
            json=agent1_data
        ) as response:
            assert response.status == 200
        
        async with session.post(
            f"{registry_url}/agents",
            json=agent2_data
        ) as response:
            assert response.status == 200
        
        # Step 2: Create a channel directly (without authentication)
        async with session.post(
            f"{api_url}/channels/",
            json={
                "name": "agent-channel",
                "description": "Channel for agent communication",
                "is_private": False
            }
        ) as response:
            assert response.status == 200
            channel_data = await response.json()
            channel_id = channel_data["id"]
        
        # Step 3: Discover agents
        async with session.post(
            f"{api_url}/agents/discover"
        ) as response:
            assert response.status == 200
        
        # Step 4: Send a message from Agent A to the channel
        async with session.post(
            f"{api_url}/messages/channel/{channel_id}",
            json={
                "content": "@AgentB Hello from Agent A",
                "agent_name": "AgentA"
            }
        ) as response:
            assert response.status == 200
        
        # Step 5: Check that Agent B received the message
        async with session.get(
            f"{api_url}/messages/channel/{channel_id}"
        ) as response:
            assert response.status == 200
            messages = await response.json()
            assert len(messages) >= 1
            assert any("@AgentB Hello from Agent A" in msg["content"] for msg in messages)