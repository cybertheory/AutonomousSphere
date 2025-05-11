import pytest
import requests
import json
import time
import asyncio
import websockets
import os

@pytest.mark.asyncio
async def test_mcp_websocket_connection():
    """Test that the MCP WebSocket server is running and accepting connections"""
    try:
        uri = "ws://localhost:8000/search/mcp"
        async with websockets.connect(uri) as websocket:
            # Send a ping message
            await websocket.send(json.dumps({
                "type": "ping",
                "id": "test-ping"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            assert response_data["type"] == "pong"
            assert response_data["id"] == "test-ping"
    except (websockets.exceptions.ConnectionError, asyncio.TimeoutError) as e:
        pytest.fail(f"Could not connect to MCP WebSocket server: {str(e)}")

@pytest.mark.asyncio
async def test_mcp_search_tool():
    """Test the MCP search tool functionality"""
    try:
        uri = "ws://localhost:8000/search/mcp"
        async with websockets.connect(uri) as websocket:
            # Send a search request
            await websocket.send(json.dumps({
                "type": "tool",
                "id": "test-search",
                "name": "search",
                "params": {
                    "query": "test",
                    "filters": {}
                }
            }))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            
            assert response_data["type"] == "tool_result"
            assert response_data["id"] == "test-search"
            assert "result" in response_data
            assert "query" in response_data["result"]
            assert response_data["result"]["query"] == "test"
    except (websockets.exceptions.ConnectionError, asyncio.TimeoutError) as e:
        pytest.fail(f"Error testing MCP search tool: {str(e)}")

def test_mcp_registration():
    """Test that the MCP service is registered with the registry"""
    # Get the list of agents from the registry
    response = requests.get("http://localhost:8000/registry/agents")
    
    assert response.status_code == 200
    agents = response.json()
    
    # Check if the MCP service is registered
    mcp_agents = [agent for agent in agents if "mcp" in agent.get("id", "").lower()]
    assert len(mcp_agents) > 0
    
    # Check the MCP service details
    mcp_agent = mcp_agents[0]
    assert "mcp_capabilities" in mcp_agent.get("custom_metadata", {})
    assert "search" in mcp_agent["custom_metadata"]["mcp_capabilities"]