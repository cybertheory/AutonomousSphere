import pytest
import aiohttp

@pytest.mark.asyncio
async def test_example_agent(wait_for_services, http_session):
    """Test the example agent's functionality."""
    # Base URL
    agent_url = "http://example-agent:8080"
    
    # Step 1: Get the agent card
    async with http_session.get(f"{agent_url}/agent-card") as response:
        assert response.status == 200
        agent_card = await response.json()
        assert "name" in agent_card
        assert "url" in agent_card
        assert "capabilities" in agent_card
    
    # Step 2: Send a message to the agent
    async with http_session.post(
        f"{agent_url}/message",
        json={
            "message": "Hello agent",
            "channel_id": 1,
            "user_id": 1
        }
    ) as response:
        assert response.status == 200
        result = await response.json()
        assert "response" in result
        assert "Echo: Hello agent" in result["response"]
        assert "agent" in result
        assert "metadata" in result