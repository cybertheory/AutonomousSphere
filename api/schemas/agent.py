from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    capabilities: Optional[Dict[str, Any]] = None

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AgentInDB(AgentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Agent(AgentInDB):
    pass