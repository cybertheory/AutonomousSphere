import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_mcp_registration(async_client):
    # Mock the register_mcp_service function
    with patch('AutonomousSphere.search.mcp.search_mcp.register_mcp_service') as mock_register:
        mock_register.return_value = True
        
        # Trigger the startup event by calling a health endpoint
        response = await async_client.get("/registry/health")
        assert response.status_code == 200
        
        # Verify that register_mcp_service was called
        mock_register.assert_called_once()

@pytest.mark.asyncio
async def test_mcp_registration_process():
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