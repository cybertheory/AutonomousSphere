from fastapi import APIRouter, HTTPException, Body, Depends, Header
from typing import List, Dict, Any, Optional
import logging
import httpx
import yaml
import os
import time
import json
import asyncio

# Import the SearchQuery model from registry models
from AutonomousSphere.registry.models.search import SearchQuery

# Import search models
from .models import MatrixSearchRequest, SearchResult

# Import registry functions for agent search
from AutonomousSphere.registry.registry import search_agents

# Import MCP search module
from .mcp import router as mcp_router, mount_mcp_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Load configuration
def get_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Function to perform Matrix search
async def search_matrix(query: str, access_token: str, config: Dict[str, Any], next_batch: Optional[str] = None):
    """
    Perform a search on the Matrix homeserver
    """
    homeserver_url = config["homeserver"]["address"]
    
    # Construct search request
    search_request = MatrixSearchRequest(
        search_categories={
            "room_events": {
                "search_term": query,
                "order_by": "rank",
                "keys": ["content.body", "content.name", "content.topic"],
                "filter": {
                    "limit": 20
                }
            }
        }
    )
    
    # Add next_batch if provided
    params = {}
    if next_batch:
        params["next_batch"] = next_batch
    
    # Make request to Matrix API
    async with httpx.AsyncClient() as client:
        try:
            url = f"{homeserver_url}/_matrix/client/v3/search"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            logger.info(f"Searching Matrix at {url}")
            response = await client.post(
                url, 
                json=search_request.dict(), 
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Matrix search error: {response.status_code} - {response.text}")
                return {
                    "error": f"Matrix search failed with status {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            logger.error(f"Matrix search request error: {str(e)}")
            return {"error": f"Matrix search request failed: {str(e)}"}

@router.post("/", response_model=SearchResult)
async def unified_search(
    search_query: SearchQuery,
    authorization: Optional[str] = Header(None)
):
    """
    Unified search endpoint that searches across both the agent registry
    and Matrix rooms/messages.
    
    This endpoint combines results from:
    1. Agent registry - searching for agents matching the query
    2. Matrix API - searching for messages and rooms matching the query
    
    The search can be filtered using the filters parameter.
    """
    try:
        start_time = time.time()
        logger.info(f"Processing unified search query: {search_query.query}")
        
        # Get configuration
        config = get_config()
        
        # Initialize results structure
        results = SearchResult(
            query=search_query.query,
            filters=search_query.filters,
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
                "source": "api"
            }
        )
        
        # 1. Search agents in registry
        agent_results = await search_agents(search_query)
        results.results["agents"] = agent_results
        
        # 2. Search Matrix if authorization token is provided
        matrix_results = None
        if authorization:
            # Extract token from Authorization header
            access_token = None
            if authorization.startswith("Bearer "):
                access_token = authorization.split(" ")[1]
            
            if access_token:
                matrix_results = await search_matrix(
                    search_query.query, 
                    access_token, 
                    config
                )
                
                # Process Matrix results if successful
                if matrix_results and "search_categories" in matrix_results:
                    room_events = matrix_results["search_categories"].get("room_events", {})
                    
                    # Extract messages
                    if "results" in room_events:
                        for result in room_events["results"]:
                            # Add to messages list
                            results.results["matrix"]["messages"].append({
                                "event_id": result["result"]["event_id"],
                                "room_id": result["result"]["room_id"],
                                "sender": result["result"]["sender"],
                                "content": result["result"]["content"],
                                "origin_server_ts": result["result"]["origin_server_ts"],
                                "rank": result.get("rank", 0)
                            })
                    
                    # Extract room information from state if available
                    if "state" in room_events:
                        for room_id, state_events in room_events["state"].items():
                            room_info = {
                                "room_id": room_id,
                                "name": None,
                                "topic": None,
                                "members_count": 0
                            }
                            
                            # Extract room name and topic from state events
                            for event in state_events:
                                if event["type"] == "m.room.name":
                                    room_info["name"] = event["content"].get("name")
                                elif event["type"] == "m.room.topic":
                                    room_info["topic"] = event["content"].get("topic")
                            
                            results.results["matrix"]["rooms"].append(room_info)
                
                # Add pagination token if available
                if matrix_results and "search_categories" in matrix_results and "room_events" in matrix_results["search_categories"]:
                    next_batch = matrix_results["search_categories"]["room_events"].get("next_batch")
                    if next_batch:
                        results.results["matrix"]["next_batch"] = next_batch
        
        # Calculate total results
        total_agents = len(results.results["agents"])
        total_matrix_messages = len(results.results["matrix"]["messages"])
        total_matrix_rooms = len(results.results["matrix"]["rooms"])
        total_results = total_agents + total_matrix_messages + total_matrix_rooms
        
        # Update metadata
        results.metadata.total_results = total_results
        results.metadata.search_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Search completed with {total_results} results in {results.metadata.search_time_ms}ms")
        return results
        
    except Exception as e:
        logger.error(f"Unified search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# Include MCP router
router.include_router(mcp_router, prefix="/mcp", tags=["mcp"])

# Mount the MCP server
mount_mcp_server(router)
