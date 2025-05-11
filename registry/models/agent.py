from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class Protocol(str, Enum):
    MCP = "MCP"
    A2A = "A2A"
    ACP = "ACP"

class Agent(BaseModel):
    id: str = Field(..., description="Unique agent identifier")
    matrix_id: Optional[str] = Field(None, description="Matrix user ID")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Brief summary of the agent's functionality")
    protocol: Protocol = Field(..., description="Communication protocol used by the agent")
    tools: List[str] = Field(default=[], description="List of callable tools")
    skills: List[str] = Field(default=[], description="Freeform tags representing agent skills")
    languages: List[str] = Field(default=[], description="Languages the agent can communicate in")
    endpoint_url: Optional[HttpUrl] = Field(None, description="Public URL for agent communication")
    room_ids: List[str] = Field(default=[], description="Matrix room IDs the agent is active in")
    owner: Optional[str] = Field(None, description="Identifier for the entity or user that owns the agent")
    registered_at: datetime = Field(default_factory=datetime.now, description="Timestamp of agent registration")
    last_seen: datetime = Field(default_factory=datetime.now, description="Timestamp of the last heartbeat or activity")
    public: bool = Field(default=True, description="Indicates if the agent is publicly discoverable")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Protocol-specific metadata")