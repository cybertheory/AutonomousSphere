from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="A2A Registry Service", description="Registry for A2A-compatible agents")

class AgentCard(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    last_seen: Optional[str] = None

# In-memory storage for registered agents
registered_agents: Dict[str, AgentCard] = {}

@app.get("/")
def read_root():
    return {"status": "ok", "service": "A2A Registry"}

@app.get("/agents", response_model=List[AgentCard])
def get_agents():
    """Get all registered agents"""
    # Convert dict to list
    return list(registered_agents.values())

@app.get("/agents/{agent_name}", response_model=AgentCard)
def get_agent(agent_name: str):
    """Get a specific agent by name"""
    if agent_name not in registered_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return registered_agents[agent_name]

@app.post("/agents", response_model=AgentCard)
def register_agent(agent: AgentCard):
    """Register an agent with the registry"""
    # Add timestamp
    agent.last_seen = datetime.utcnow().isoformat()
    registered_agents[agent.name] = agent
    logger.info(f"Agent registered: {agent.name} at {agent.url}")
    return agent

@app.put("/agents/{agent_name}/heartbeat")
def agent_heartbeat(agent_name: str):
    """Update agent's last seen timestamp"""
    if agent_name not in registered_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    registered_agents[agent_name].last_seen = datetime.utcnow().isoformat()
    return {"status": "ok", "agent": agent_name}

# Background task to clean up stale agents
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_stale_agents())

async def cleanup_stale_agents():
    """Remove agents that haven't sent a heartbeat in 2 minutes"""
    while True:
        try:
            current_time = datetime.utcnow()
            stale_threshold = current_time - timedelta(minutes=2)
            
            # Find stale agents
            stale_agents = []
            for name, agent in registered_agents.items():
                if agent.last_seen:
                    last_seen = datetime.fromisoformat(agent.last_seen)
                    if last_seen < stale_threshold:
                        stale_agents.append(name)
            
            # Remove stale agents
            for name in stale_agents:
                logger.info(f"Removing stale agent: {name}")
                del registered_agents[name]
                
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(30)  # Continue despite errors

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)