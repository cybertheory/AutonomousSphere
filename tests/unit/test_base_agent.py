import pytest
import os
import sys
import time
import threading
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the base agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_agent.base_agent import BaseA2AAgent, AgentCapabilities

def test_base_agent_init():
    """Test the initialization of the base agent."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        agent = BaseA2AAgent(
            name="TestAgent",
            description="A test agent",
            url="http://test-agent:8080",
            registry_url="http://registry:8081",
            chat_service_url="http://api:8000"
        )
        
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert agent.url == "http://test-agent:8080"
        assert agent.registry_url == "http://registry:8081"
        assert agent.chat_service_url == "http://api:8000"
        assert isinstance(agent.capabilities, AgentCapabilities)

def test_agent_registration():
    """Test that the agent registers with the registry."""
    with patch('requests.post') as mock_post, \
         patch('threading.Thread') as mock_thread:
        
        mock_post.return_value.status_code = 200
        mock_thread.return_value = MagicMock()
        
        agent = BaseA2AAgent(
            name="TestAgent",
            description="A test agent",
            url="http://test-agent:8080",
            registry_url="http://registry:8081"
        )
        
        # Check that the registration thread was started
        mock_thread.assert_called_once()
        
        # Manually call the registration method
        agent._register_with_registry()
        
        # Check that the post request was made
        mock_post.assert_called_with(
            "http://registry:8081/agents",
            json={
                "name": "TestAgent",
                "url": "http://test-agent:8080",
                "description": "A test agent",
                "capabilities": {"text": True, "streaming": False, "functions": []}
            }
        )

def test_agent_heartbeat():
    """Test that the agent sends heartbeats."""
    with patch('requests.put') as mock_put:
        mock_put.return_value.status_code = 200
        
        agent = BaseA2AAgent(
            name="TestAgent",
            description="A test agent",
            url="http://test-agent:8080",
            registry_url="http://registry:8081"
        )
        
        # Manually call the heartbeat method
        agent._send_heartbeat()
        
        # Check that the put request was made
        mock_put.assert_called_with(
            "http://registry:8081/agents/TestAgent/heartbeat"
        )

def test_message_handler_registration():
    """Test that message handlers can be registered."""
    with patch('requests.post') as mock_post, \
         patch('threading.Thread') as mock_thread:
        
        mock_post.return_value.status_code = 200
        mock_thread.return_value = MagicMock()
        
        agent = BaseA2AAgent(
            name="TestAgent",
            description="A test agent",
            url="http://test-agent:8080",
            registry_url="http://registry:8081"
        )
        
        # Define a handler
        def test_handler(message):
            return {"response": f"Handled: {message.get('message', '')}"}
        
        # Register the handler
        agent.register_message_handler("test", test_handler)
        
        # Check that the handler was registered
        assert "test" in agent.message_handlers
        assert agent.message_handlers["test"] == test_handler
        
        # Test the handler
        result = agent.message_handlers["test"]({"message": "Hello"})
        assert result["response"] == "Handled: Hello"