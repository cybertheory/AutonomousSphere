from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from .user import User

class ChannelBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False
    is_dm: bool = False

class ChannelCreate(ChannelBase):
    member_ids: Optional[List[int]] = None

class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None

class ChannelInDB(ChannelBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Channel(ChannelInDB):
    members: List[User] = []
    creator: User