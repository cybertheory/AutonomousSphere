from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import asyncio
import json
import uuid
import httpx
from datetime import datetime
import os
import yaml

# Import FastMCP
from fastmcp import FastMCP

# Import registry models and functions
from AutonomousSphere.registry.models.search import SearchQuery

# Import search models
from AutonomousSphere.search.models import SearchResult, MCPServiceRegistration, MCPEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize MCP
mcp = FastMCP(
    "AutonomousSphere Search MCP",
    "MCP server for unified search across agents and Matrix"
)

# Load configuration
def get_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# MCP search tool
@mcp.tool()
async def search(query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Search across agents and Matrix rooms/messages
    
    Args:
        query: The search query
        filters: Optional filters to apply to the search
    
    Returns:
        Search results
    """
    try:
        # Create SearchQuery object
        search_query = SearchQuery(query=query, filters=filters or {})
        
        # Import the unified_search function here to avoid circular imports
        from AutonomousSphere.search.search import unified_search
        
        # Call the unified search function
        results = await unified_search(search_query)
        
        return results.dict()
    except Exception as e:
        logger.error(f"MCP search error: {str(e)}")
        return SearchResult(
            query=query,
            filters=filters,
            results={
                "agents": [],
                "matrix": {
                    "rooms": [],
                    "messages": []
                }
            },
            metadata={
                "total_results": 0,
                "search_time_ms": 0,
                "source": "mcp",
                "error": str(e)
            }
        ).dict()

# SSE endpoint for MCP events
@router.get("/sse")
async def mcp_sse(request: Request):
    """
    Server-Sent Events (SSE) endpoint for MCP server events
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Send initial connection message
            connected_event = MCPEvent(
                event="connected",
                data={"message": "Connected to MCP SSE stream"}
            )
            yield f"data: {json.dumps(connected_event.dict())}\n\n"
            
            # Create a queue for events
            queue = asyncio.Queue()
            
            # Register this client with the MCP server for events
            client_id = f"sse-{uuid.uuid4().hex}"
            
            # In a real implementation, you would register this queue with your MCP server
            # to receive events. For now, we'll just simulate some events.
            
            # Send periodic status updates
            count = 0
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE client {client_id} disconnected")
                    break
                
                # In a real implementation, you would wait for events from the MCP server
                # For now, we'll just send a heartbeat every 10 seconds
                count += 1
                heartbeat_event = MCPEvent(
                    event="heartbeat",
                    data={"count": count}
                )
                
                yield f"data: {json.dumps(heartbeat_event.dict())}\n\n"
                
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled")
        except Exception as e:
            logger.error(f"SSE error: {str(e)}")
            error_event = MCPEvent(
                event="error",
                data={"error": str(e)}
            )
            yield f"data: {json.dumps(error_event.dict())}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in Nginx
        }
    )

# Function to register the MCP service with the registry
async def register_mcp_service():
    """Register the MCP search service with the registry"""
    # Import here to avoid circular imports
    import httpx
    
    # Get configuration
    config = get_config()
    
    # Determine the endpoint URL based on configuration
    host = os.environ.get("API_HOST", "localhost")
    port = int(os.environ.get("API_PORT", 8000))
    
    # Create service registration model
    service_data = MCPServiceRegistration(
        endpoint_url=f"ws://{host}:{port}/search/mcp",
        custom_metadata={
            "mcp_capabilities": ["search"],
            "mcp_server_url": f"ws://{host}:{port}/search/mcp"
        }
    )
    
    # Register with the registry
    try:
        async with httpx.AsyncClient() as client:
            registry_url = f"http://{host}:{port}/registry/agents"
            response = await client.post(registry_url, json=service_data.dict())
            
            if response.status_code == 201:
                logger.info(f"MCP search service registered successfully: {service_data.id}")
                return True
            else:
                logger.error(f"Failed to register MCP search service: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error registering MCP search service: {str(e)}")
        return False

# Get the Starlette app for mounting
starlette_app = mcp.create_starlette_app(debug=True)

# Function to mount the MCP server to the FastAPI app
def mount_mcp_server(app):
    """Mount the MCP server to the FastAPI app"""
    app.mount("/mcp", starlette_app)
    
    # Register the MCP service with the registry
    @app.on_event("startup")
    async def startup_event():
        await register_mcp_service()