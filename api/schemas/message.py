from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime
from .user import User
from .agent import Agent

class MessageBase(BaseModel):
    content: str
    channel_id: int
    is_agent_message: bool = False
    agent_id: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageInDB(MessageBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Message(MessageInDB):
    user: User
    agent: Optional[Agent] = None