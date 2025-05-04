import pytest
import asyncio
from unittest.mock import patch, MagicMock
from api.pubsub.a2a_client import A2AIntegration

@pytest.mark.asyncio
async def test_a2a_register_agent():
    """Test that an agent can be registered."""
    # Create a new A2A integration instance for testing
    a2a = A2AIntegration()
    
    # Register an agent
    result = a2a.register_agent("test_agent", "http://test-agent:8080")
    
    # Check that the agent was registered
    assert result is True
    assert "test_agent" in a2a.agents
    assert a2a.agents["test_agent"] == "http://test-agent:8080"

@pytest.mark.asyncio
async def test_a2a_discover_agents():
    """Test that agents can be discovered."""
    # Create a new A2A integration instance for testing
    a2a = A2AIntegration(registry_url="http://registry:8081")
    
    # Mock the HTTP response
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {
                "name": "test_agent",
                "url": "http://test-agent:8080",
                "description": "Test agent",
                "capabilities": {"text": True}
            }
        ]
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Discover agents
        agents = await a2a.discover_agents()
        
        # Check that the agent was discovered
        assert len(agents) == 1
        assert agents[0].name == "test_agent"
        assert agents[0].url == "http://test-agent:8080"
        assert "test_agent" in a2a.agents

@pytest.mark.asyncio
async def test_a2a_send_message():
    """Test that a message can be sent to an agent."""
    # Create a new A2A integration instance for testing
    a2a = A2AIntegration()
    
    # Register an agent
    a2a.register_agent("test_agent", "http://test-agent:8080")
    
    # Mock the HTTP response
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": "Echo: test message",
            "agent": "test_agent",
            "metadata": {}
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Send a message
        response = await a2a.send_message_to_agent(
            "test_agent", 
            "test message", 
            channel_id=1
        )
        
        # Check the response
        assert response["response"] == "Echo: test message"
        assert response["agent"] == "test_agent"