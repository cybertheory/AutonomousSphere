import pytest
import asyncio
import httpx
import json
from AutonomousSphere.registry.models import Protocol

@pytest.mark.asyncio
async def test_registry_health(async_client):
    response = await async_client.get("/registry/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_register_and_get_agent(async_client):
    # Test agent data
    test_agent = {
        "id": "integration-test-agent",
        "display_name": "Integration Test Agent",
        "description": "An agent for integration testing",
        "protocol": Protocol.MATRIX.value,
        "endpoint_url": "https://example.com/integration-agent",
        "public": True,
        "languages": ["en"],
        "tools": ["test"]
    }
    
    # Register the agent
    response = await async_client.post("/registry/agents", json=test_agent)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "integration-test-agent"
    assert data["registered_at"] is not None
    
    # Get the agent
    response = await async_client.get(f"/registry/agents/{test_agent['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_agent["id"]
    assert data["display_name"] == test_agent["display_name"]
    
    # Clean up - delete the agent
    response = await async_client.delete(f"/registry/agents/{test_agent['id']}")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_list_agents(async_client):
    # Register a couple of test agents
    test_agents = [
        {
            "id": "integration-test-agent-1",
            "display_name": "Integration Test Agent 1",
            "description": "An agent for integration testing",
            "protocol": Protocol.MATRIX.value,
            "endpoint_url": "https://example.com/integration-agent-1",
            "public": True,
            "languages": ["en"],
            "tools": ["test"]
        },
        {
            "id": "integration-test-agent-2",
            "display_name": "Integration Test Agent 2",
            "description": "Another agent for integration testing",
            "protocol": Protocol.HTTP.value,
            "endpoint_url": "https://example.com/integration-agent-2",
            "public": False,
            "languages": ["en", "fr"],
            "tools": ["search", "calculator"]
        }
    ]
    
    # Register the agents
    for agent in test_agents:
        response = await async_client.post("/registry/agents", json=agent)
        assert response.status_code == 201
    
    # List all agents
    response = await async_client.get("/registry/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # There might be other agents registered
    
    # Filter by protocol
    response = await async_client.get("/registry/agents?protocol=matrix")
    assert response.status_code == 200
    data = response.json()
    assert any(agent["id"] == "integration-test-agent-1" for agent in data)
    assert not any(agent["id"] == "integration-test-agent-2" for agent in data)
    
    # Filter by public visibility
    response = await async_client.get("/registry/agents?public=true")
    assert response.status_code == 200
    data = response.json()
    assert any(agent["id"] == "integration-test-agent-1" for agent in data)
    assert not any(agent["id"] == "integration-test-agent-2" for agent in data)
    
    # Clean up
    for agent in test_agents:
        response = await async_client.delete(f"/registry/agents/{agent['id']}")
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_search_agents(async_client):
    # Register test agents
    test_agents = [
        {
            "id": "search-test-agent-1",
            "display_name": "Search Test Agent",
            "description": "An agent for testing search functionality",
            "protocol": Protocol.MATRIX.value,
            "endpoint_url": "https://example.com/search-agent-1",
            "public": True,
            "languages": ["en"],
            "tools": ["search"]
        },
        {
            "id": "search-test-agent-2",
            "display_name": "Another Search Agent",
            "description": "A different agent with search capabilities",
            "protocol": Protocol.HTTP.value,
            "endpoint_url": "https://example.com/search-agent-2",
            "public": True,
            "languages": ["en", "es"],
            "tools": ["search", "calculator"]
        }
    ]
    
    # Register the agents
    for agent in test_agents:
        response = await async_client.post("/registry/agents", json=agent)
        assert response.status_code == 201
    
    # Search for agents
    search_query = {
        "query": "search",
        "filters": {}
    }
    response = await async_client.post("/registry/agents/search", json=search_query)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(agent["id"] == "search-test-agent-1" for agent in data)
    assert any(agent["id"] == "search-test-agent-2" for agent in data)
    
    # Search with filters
    search_query = {
        "query": "search",
        "filters": {
            "protocol": ["matrix"]
        }
    }
    response = await async_client.post("/registry/agents/search", json=search_query)
    assert response.status_code == 200
    data = response.json()
    assert any(agent["id"] == "search-test-agent-1" for agent in data)
    assert not any(agent["id"] == "search-test-agent-2" for agent in data)
    
    # Clean up
    for agent in test_agents:
        response = await async_client.delete(f"/registry/agents/{agent['id']}")
        assert response.status_code == 204