from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
# Comment out the auth dependency
# from ..services.auth_service import get_current_active_user
from ..services.message_service import (
    get_messages, get_message, create_message, update_message, delete_message
)
from ..schemas.message import Message, MessageCreate, MessageUpdate
from ..schemas.user import User

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/{channel_id}", response_model=List[Message])
async def read_messages(
    channel_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # Remove the current_user dependency
    # current_user: User = Depends(get_current_active_user)
):
    """Get messages for a specific channel"""
    return get_messages(db=db, channel_id=channel_id, skip=skip, limit=limit)

@router.post("/", response_model=Message)
async def create_new_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    # Remove the current_user dependency
    # current_user: User = Depends(get_current_active_user)
):
    """Create a new message in a channel"""
    # Use a default user ID for now
    user_id = 1
    return await create_message(db=db, message=message, user_id=user_id)

@router.put("/{message_id}", response_model=Message)
async def update_message_endpoint(
    message_id: int,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    # Remove the current_user dependency
    # current_user: User = Depends(get_current_active_user)
):
    """Update a message"""
    # Use a default user ID for now
    user_id = 1
    return update_message(db=db, message_id=message_id, message_update=message_update, user_id=user_id)

@router.delete("/{message_id}")
async def delete_message_endpoint(
    message_id: int,
    db: Session = Depends(get_db),
    # Remove the current_user dependency
    # current_user: User = Depends(get_current_active_user)
):
    """Delete a message"""
    # Use a default user ID for now
    user_id = 1
    return delete_message(db=db, message_id=message_id, user_id=user_id)