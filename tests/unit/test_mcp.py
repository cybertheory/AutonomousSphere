import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_mcp_search_tool():
    from AutonomousSphere.search.mcp.search_mcp import search
    
    # Mock the unified_search function
    with patch('AutonomousSphere.search.search.unified_search') as mock_unified_search:
        # Set up the mock to return a test result
        mock_result = MagicMock()
        mock_result.dict.return_value = {
            "query": "test query",
            "filters": {},
            "results": {
                "agents": [{"id": "test-agent"}],
                "matrix": {
                    "rooms": [],
                    "messages": []
                }
            },
            "metadata": {
                "total_results": 1,
                "search_time_ms": 100,
                "source": "mcp"
            }
        }
        mock_unified_search.return_value = mock_result
        
        # Call the MCP search tool
        result = await search("test query", {"filter_key": "filter_value"})
        
        # Verify the result
        assert result["query"] == "test query"
        assert result["results"]["agents"] == [{"id": "test-agent"}]
        assert result["metadata"]["total_results"] == 1
        
        # Verify that unified_search was called with the correct parameters
        mock_unified_search.assert_called_once()
        call_args = mock_unified_search.call_args[0][0]
        assert call_args.query == "test query"
        assert call_args.filters == {"filter_key": "filter_value"}

@pytest.mark.asyncio
async def test_register_mcp_service():
    from AutonomousSphere.search.mcp.search_mcp import register_mcp_service
    
    # Mock httpx.AsyncClient
    with patch('httpx.AsyncClient') as mock_client_class:
        # Set up the mock client
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client_class.return_value = mock_client
        
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response
        
        # Mock get_config
        with patch('AutonomousSphere.search.mcp.search_mcp.get_config') as mock_get_config:
            mock_get_config.return_value = {}
            
            # Mock environment variables
            with patch.dict('os.environ', {'API_HOST': 'testhost', 'API_PORT': '8000'}):
                # Call the register_mcp_service function
                result = await register_mcp_service()
                
                # Verify the result
                assert result is True
                
                # Verify that the client.post was called with the correct URL and data
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                assert call_args[0][0] == "http://testhost:8000/registry/agents"
                assert "endpoint_url" in call_args[1]["json"]
                assert call_args[1]["json"]["endpoint_url"] == "ws://testhost:8000/search/mcp"