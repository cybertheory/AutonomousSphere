from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta
import asyncio
import json

# Import the database and models from the API module
import sys
import os
# Add the parent directory to sys.path to import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.db.database import engine, SessionLocal, get_db
from api.db.models import Agent, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="A2A Registry Service", description="Registry for A2A-compatible agents")

class AgentCard(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    last_seen: Optional[str] = None
    
    class Config:
        orm_mode = True

@app.get("/")
def read_root():
    return {"status": "ok", "service": "A2A Registry"}

# Helper function to convert Agent models to AgentCard models
def convert_to_agent_cards(agents):
    agent_cards = []
    for agent in agents:
        capabilities = {}
        if agent.capabilities:
            try:
                capabilities = json.loads(agent.capabilities)
            except:
                capabilities = {}
                
        agent_cards.append(AgentCard(
            name=agent.name,
            url=agent.url,
            description=agent.description,
            capabilities=capabilities,
            last_seen=agent.updated_at.isoformat() if agent.updated_at else None
        ))
    
    return agent_cards

@app.get("/agents", response_model=List[AgentCard])
def get_agents(db = Depends(get_db)):
    """Get all registered agents"""
    agents = db.query(Agent).all()
    return convert_to_agent_cards(agents)

# Add support for the incorrectly requested endpoint
@app.get("/registry/agents", response_model=List[AgentCard])
def get_registry_agents(db = Depends(get_db)):
    """Get all registered agents (alternative endpoint)"""
    logger.info("Received request to /registry/agents - this endpoint is deprecated, use /agents instead")
    agents = db.query(Agent).all()
    return convert_to_agent_cards(agents)

@app.get("/agents/{agent_name}", response_model=AgentCard)
def get_agent(agent_name: str, db = Depends(get_db)):
    """Get a specific agent by name"""
    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    capabilities = {}
    if agent.capabilities:
        try:
            capabilities = json.loads(agent.capabilities)
        except:
            capabilities = {}
            
    return AgentCard(
        name=agent.name,
        url=agent.url,
        description=agent.description,
        capabilities=capabilities,
        last_seen=agent.updated_at.isoformat() if agent.updated_at else None
    )

# Add support for the incorrectly requested endpoint
@app.get("/registry/agents/{agent_name}", response_model=AgentCard)
def get_registry_agent(agent_name: str, db = Depends(get_db)):
    """Get a specific agent by name (alternative endpoint)"""
    logger.info(f"Received request to /registry/agents/{agent_name} - this endpoint is deprecated, use /agents/{agent_name} instead")
    return get_agent(agent_name, db)

@app.post("/agents", response_model=AgentCard)
def register_agent(agent_card: AgentCard, db = Depends(get_db)):
    """Register an agent with the registry"""
    # Log the received data for debugging
    logger.info(f"Received agent registration: {agent_card}")
    
    # Check if agent already exists
    db_agent = db.query(Agent).filter(Agent.name == agent_card.name).first()
    
    # Convert capabilities to JSON string
    capabilities_json = None
    if agent_card.capabilities:
        capabilities_json = json.dumps(agent_card.capabilities)
    
    if db_agent:
        # Update existing agent
        db_agent.url = agent_card.url
        db_agent.description = agent_card.description
        db_agent.capabilities = capabilities_json
        # updated_at will be automatically updated by SQLAlchemy
    else:
        # Create new agent
        db_agent = Agent(
            name=agent_card.name,
            url=agent_card.url,
            description=agent_card.description,
            capabilities=capabilities_json,
            is_active=True
        )
        db.add(db_agent)
    
    db.commit()
    db.refresh(db_agent)
    logger.info(f"Agent registered: {agent_card.name} at {agent_card.url}")
    
    return AgentCard(
        name=db_agent.name,
        url=db_agent.url,
        description=db_agent.description,
        capabilities=json.loads(db_agent.capabilities) if db_agent.capabilities else None,
        last_seen=db_agent.updated_at.isoformat() if db_agent.updated_at else None
    )

# Add support for the incorrectly requested endpoint
@app.post("/registry/agents", response_model=AgentCard)
def register_registry_agent(agent_card: AgentCard, db = Depends(get_db)):
    """Register an agent with the registry (alternative endpoint)"""
    logger.info("Received request to /registry/agents - this endpoint is deprecated, use /agents instead")
    return register_agent(agent_card, db)

@app.put("/agents/{agent_name}/heartbeat")
def agent_heartbeat(agent_name: str, db = Depends(get_db)):
    """Update agent's last seen timestamp"""
    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Just touch the record to update the updated_at timestamp
    agent.is_active = True  # This will trigger an update
    db.commit()
    return {"status": "ok", "agent": agent_name}

# Add support for the incorrectly requested endpoint
@app.put("/registry/agents/{agent_name}/heartbeat")
def registry_agent_heartbeat(agent_name: str, db = Depends(get_db)):
    """Update agent's last seen timestamp (alternative endpoint)"""
    logger.info(f"Received request to /registry/agents/{agent_name}/heartbeat - this endpoint is deprecated, use /agents/{agent_name}/heartbeat instead")
    return agent_heartbeat(agent_name, db)

# Background task to clean up stale agents
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_stale_agents())

async def cleanup_stale_agents():
    """Mark agents as inactive if they haven't sent a heartbeat in 2 minutes"""
    while True:
        try:
            db = SessionLocal()
            current_time = datetime.utcnow()
            stale_threshold = current_time - timedelta(minutes=2)
            
            # Find and mark stale agents as inactive
            stale_agents = db.query(Agent).filter(
                Agent.is_active == True,
                Agent.updated_at < stale_threshold
            ).all()
            
            for agent in stale_agents:
                logger.info(f"Marking agent as inactive: {agent.name}")
                agent.is_active = False
            
            db.commit()
            db.close()
                
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            if 'db' in locals():
                db.close()
            await asyncio.sleep(30)  # Continue despite errors

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)