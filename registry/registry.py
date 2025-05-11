from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path, status
from typing import List, Dict, Any, Optional, Union
import os
import json
import logging
from datetime import datetime
import uuid

# Import models from the models directory
from .models import Agent, Protocol, SearchQuery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# In-memory storage (replace with database in production)
agents_registry = {}

# Agent registry routes
@router.post("/agents", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(agent: Agent):
    """Register a new agent"""
    if agent.id in agents_registry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                           detail=f"Agent with ID {agent.id} already exists")
    
    # Set timestamps
    agent.registered_at = datetime.now()
    agent.last_seen = datetime.now()
    
    agents_registry[agent.id] = agent
    logger.info(f"Agent registered: {agent.id}")
    return agent

@router.get("/agents", response_model=List[Agent])
async def list_agents(
    protocol: Optional[Protocol] = Query(None, description="Filter agents by protocol"),
    public: Optional[bool] = Query(None, description="Filter agents by public visibility")
):
    """Retrieve a list of agents with optional filtering"""
    filtered_agents = list(agents_registry.values())
    
    # Apply protocol filter if provided
    if protocol:
        filtered_agents = [agent for agent in filtered_agents if agent.protocol == protocol]
    
    # Apply public visibility filter if provided
    if public is not None:
        filtered_agents = [agent for agent in filtered_agents if agent.public == public]
    
    return filtered_agents

@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str = Path(..., description="Unique agent identifier")):
    """Retrieve a specific agent by ID"""
    if agent_id not in agents_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                           detail=f"Agent with ID {agent_id} not found")
    return agents_registry[agent_id]

@router.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str = Path(..., description="Unique agent identifier"),
    agent: Agent = Body(...)
):
    """Update an existing agent"""
    if agent_id not in agents_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                           detail=f"Agent with ID {agent_id} not found")
    
    # Ensure ID consistency
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                           detail="Agent ID in path must match ID in body")
    
    # Preserve registration timestamp
    agent.registered_at = agents_registry[agent_id].registered_at
    agent.last_seen = datetime.now()
    
    agents_registry[agent_id] = agent
    logger.info(f"Agent updated: {agent_id}")
    return agent

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str = Path(..., description="Unique agent identifier")):
    """Delete an agent"""
    if agent_id not in agents_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                           detail=f"Agent with ID {agent_id} not found")
    
    del agents_registry[agent_id]
    logger.info(f"Agent deleted: {agent_id}")
    return None

@router.post("/agents/search", response_model=List[Agent])
async def search_agents(search_query: SearchQuery):
    """Semantic search for agents"""
    # In a real implementation, this would use vector embeddings or a search engine
    # For now, we'll do a simple text-based search
    results = []
    query_lower = search_query.query.lower()
    
    for agent in agents_registry.values():
        # Simple text matching in name and description
        if (query_lower in agent.display_name.lower() or 
            (agent.description and query_lower in agent.description.lower())):
            
            # Apply filters if provided
            if search_query.filters:
                # Protocol filter
                if "protocol" in search_query.filters and search_query.filters["protocol"]:
                    if agent.protocol not in search_query.filters["protocol"]:
                        continue
                
                # Language filter
                if "language" in search_query.filters and search_query.filters["language"]:
                    if not any(lang in agent.languages for lang in search_query.filters["language"]):
                        continue
                
                # Tools filter
                if "tools" in search_query.filters and search_query.filters["tools"]:
                    if not any(tool in agent.tools for tool in search_query.filters["tools"]):
                        continue
            
            results.append(agent)
    
    return results

# Health check for registry
@router.get("/health")
async def registry_health():
    """Check the health of the registry service"""
    return {
        "status": "healthy",
        "agents_count": len(agents_registry)
    }