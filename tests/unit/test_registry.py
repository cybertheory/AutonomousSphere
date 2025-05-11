import pytest
import asyncio
from datetime import datetime
from AutonomousSphere.registry.models import Agent, Protocol, SearchQuery

# Mock the registry storage for unit tests
@pytest.fixture
def mock_registry():
    from AutonomousSphere.registry.registry import agents_registry
    
    # Save original registry
    original_registry = agents_registry.copy()
    
    # Clear registry for tests
    agents_registry.clear()
    
    # Add some test agents
    test_agents = [
        Agent(
            id="test-agent-1",
            display_name="Test Agent 1",
            description="A test agent for unit testing",
            protocol=Protocol.MATRIX,
            endpoint_url="https://example.com/agent1",
            public=True,
            languages=["en"],
            tools=["search", "calculator"],
            registered_at=datetime.now(),
            last_seen=datetime.now()
        ),
        Agent(
            id="test-agent-2",
            display_name="Test Agent 2",
            description="Another test agent with different capabilities",
            protocol=Protocol.HTTP,
            endpoint_url="https://example.com/agent2",
            public=False,
            languages=["en", "es"],
            tools=["weather", "news"],
            registered_at=datetime.now(),
            last_seen=datetime.now()
        )
    ]
    
    for agent in test_agents:
        agents_registry[agent.id] = agent
    
    yield agents_registry
    
    # Restore original registry
    agents_registry.clear()
    agents_registry.update(original_registry)

@pytest.mark.asyncio
async def test_register_agent(mock_registry):
    from AutonomousSphere.registry.registry import register_agent
    
    new_agent = Agent(
        id="new-test-agent",
        display_name="New Test Agent",
        description="A newly registered test agent",
        protocol=Protocol.MATRIX,
        endpoint_url="https://example.com/new-agent",
        public=True,
        languages=["en"],
        tools=["search"],
    )
    
    result = await register_agent(new_agent)
    
    assert result.id == "new-test-agent"
    assert result.display_name == "New Test Agent"
    assert result.registered_at is not None
    assert result.last_seen is not None
    assert "new-test-agent" in mock_registry

@pytest.mark.asyncio
async def test_list_agents(mock_registry):
    from AutonomousSphere.registry.registry import list_agents
    
    # Test listing all agents
    all_agents = await list_agents(protocol=None, public=None)
    assert len(all_agents) == 2
    
    # Test filtering by protocol
    matrix_agents = await list_agents(protocol=Protocol.MATRIX, public=None)
    assert len(matrix_agents) == 1
    assert matrix_agents[0].id == "test-agent-1"
    
    # Test filtering by public visibility
    public_agents = await list_agents(protocol=None, public=True)
    assert len(public_agents) == 1
    assert public_agents[0].id == "test-agent-1"

@pytest.mark.asyncio
async def test_search_agents(mock_registry):
    from AutonomousSphere.registry.registry import search_agents
    
    # Basic search
    results = await search_agents(SearchQuery(query="test agent", filters={}))
    assert len(results) == 2
    
    # Search with protocol filter
    results = await search_agents(SearchQuery(
        query="test agent", 
        filters={"protocol": [Protocol.HTTP]}
    ))
    assert len(results) == 1
    assert results[0].id == "test-agent-2"
    
    # Search with tools filter
    results = await search_agents(SearchQuery(
        query="test agent", 
        filters={"tools": ["search"]}
    ))
    assert len(results) == 1
    assert results[0].id == "test-agent-1"