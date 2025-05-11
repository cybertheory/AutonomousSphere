import pytest
import asyncio
import httpx
from unittest.mock import patch
from AutonomousSphere.registry.models.search import SearchQuery

@pytest.mark.asyncio
async def test_unified_search_endpoint(async_client):
    # Mock the search_agents function
    with patch('AutonomousSphere.search.search.search_agents') as mock_search_agents:
        # Set up the mock to return some test agents
        mock_search_agents.return_value = [
            {
                "id": "test-agent-1",
                "display_name": "Test Agent 1",
                "description": "A test agent",
                "protocol": "matrix",
                "endpoint_url": "https://example.com/agent1",
                "public": True,
                "languages": ["en"],
                "tools": ["search"],
                "registered_at": "2023-01-01T00:00:00",
                "last_seen": "2023-01-01T00:00:00"
            }
        ]
        
        # Mock the search_matrix function
        with patch('AutonomousSphere.search.search.search_matrix') as mock_search_matrix:
            # Set up the mock to return some test matrix results
            mock_search_matrix.return_value = {
                "search_categories": {
                    "room_events": {
                        "results": [
                            {
                                "result": {
                                    "event_id": "event1",
                                    "room_id": "room1",
                                    "sender": "user1",
                                    "content": {"body": "test message"},
                                    "origin_server_ts": 1609459200000
                                },
                                "rank": 1.0
                            }
                        ],
                        "state": {
                            "room1": [
                                {
                                    "type": "m.room.name",
                                    "content": {"name": "Test Room"}
                                },
                                {
                                    "type": "m.room.topic",
                                    "content": {"topic": "Test Topic"}
                                }
                            ]
                        }
                    }
                }
            }
            
            # Call the unified search endpoint
            search_query = {
                "query": "test query",
                "filters": {}
            }
            response = await async_client.post("/search/", json=search_query, headers={"Authorization": "Bearer test_token"})
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            assert len(data["results"]["agents"]) == 1
            assert len(data["results"]["matrix"]["messages"]) == 1
            assert data["results"]["matrix"]["messages"][0]["event_id"] == "event1"
            assert data["metadata"]["total_results"] > 0

@pytest.mark.asyncio
async def test_mcp_sse_endpoint(async_client):
    # Test the SSE endpoint
    async with httpx.AsyncClient(app=async_client.app, base_url="http://testserver") as client:
        with client.stream("GET", "/search/mcp/sse") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            # Read the first event (connected event)
            for line in response.iter_lines():
                if line.startswith(b"data: "):
                    data = json.loads(line[6:])
                    assert data["event"] == "connected"
                    assert "message" in data["data"]
                    break