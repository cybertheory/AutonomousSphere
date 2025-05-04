import pytest
import aiohttp
from datetime import datetime

@pytest.mark.asyncio
async def test_registry_service(wait_for_services, http_session):
    """Test the registry service functionality."""
    # Base URL
    registry_url = "http://registry:8081"
    
    # Step 1: Register a new agent
    agent_data = {
        "name": "IntegrationTestAgent",
        "url": "http://integration-test-agent:8080",
        "description": "An agent for integration testing",
        "capabilities": {"text": True, "streaming": False}
    }
    
    async with http_session.post(
        f"{registry_url}/agents",
        json=agent_data
    ) as response:
        assert response.status == 200
        registered_agent = await response.json()
        assert registered_agent["name"] == "IntegrationTestAgent"
        assert "last_seen" in registered_agent
    
    # Step 2: Get the agent from the registry
    async with http_session.get(
        f"{registry_url}/agents/IntegrationTestAgent"
    ) as response:
        assert response.status == 200
        agent = await response.json()
        assert agent["name"] == "IntegrationTestAgent"
        assert agent["url"] == "http://integration-test-agent:8080"
    
    # Step 3: Send a heartbeat
    async with http_session.put(
        f"{registry_url}/agents/IntegrationTestAgent/heartbeat"
    ) as response:
        assert response.status == 200
        result = await response.json()
        assert result["status"] == "ok"
        assert result["agent"] == "IntegrationTestAgent"
    
    # Step 4: Get the agent again to check updated last_seen
    async with http_session.get(
        f"{registry_url}/agents/IntegrationTestAgent"
    ) as response:
        assert response.status == 200
        agent = await response.json()
        assert agent["last_seen"] is not None
        
    # Step 5: Try to get a non-existent agent
    async with http_session.get(
        f"{registry_url}/agents/NonExistentAgent"
    ) as response:
        assert response.status == 404