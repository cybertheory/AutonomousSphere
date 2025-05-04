from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.database import get_db
from ..services.auth_service import get_current_active_user
from ..schemas.user import User
from ..pubsub.a2a_client import a2a_integration
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents"])

class AgentInfo(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    capabilities: Optional[dict] = None

@router.get("/", response_model=List[AgentInfo])
async def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all available agents"""
    agents = []
    for name, agent in a2a_integration.agents.items():
        url = agent.base_url if hasattr(agent, 'base_url') else agent
        agents.append(AgentInfo(
            name=name,
            url=url,
            description="",  # We could store this in the database
            capabilities={}  # We could store this in the database
        ))
    return agents

@router.post("/discover")
async def discover_agents(
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger agent discovery"""
    agents = await a2a_integration.discover_agents()
    return {"message": f"Discovered {len(agents)} agents"}

@router.post("/message/{agent_name}")
async def send_message_to_agent(
    agent_name: str,
    message: str,
    channel_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Send a message to an agent"""
    response = await a2a_integration.send_message_to_agent(
        agent_name=agent_name,
        message_content=message,
        channel_id=channel_id,
        user_id=current_user.id
    )
    return response