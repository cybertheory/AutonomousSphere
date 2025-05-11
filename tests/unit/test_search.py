import pytest
import asyncio
from unittest.mock import patch, MagicMock
from AutonomousSphere.registry.models.search import SearchQuery
from AutonomousSphere.search.models import SearchResult

@pytest.mark.asyncio
async def test_unified_search():
    from AutonomousSphere.search.search import unified_search
    
    # Create a mock search query
    search_query = SearchQuery(
        query="test query",
        filters={}
    )
    
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
            
            # Mock the get_config function
            with patch('AutonomousSphere.search.search.get_config') as mock_get_config:
                mock_get_config.return_value = {
                    "homeserver": {
                        "address": "http://localhost:8008"
                    }
                }
                
                # Call the unified_search function
                result = await unified_search(search_query, authorization="Bearer test_token")
                
                # Verify the result
                assert isinstance(result, SearchResult)
                assert result.query == "test query"
                assert len(result.results["agents"]) == 1
                assert len(result.results["matrix"]["messages"]) == 1
                assert result.results["matrix"]["messages"][0]["event_id"] == "event1"
                assert result.metadata.total_results > 0