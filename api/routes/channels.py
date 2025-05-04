from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.channel_service import (
    get_channels, get_channel, create_channel, update_channel, delete_channel,
    add_channel_member, remove_channel_member, get_channel_members, create_dm_channel
)
from ..schemas.channel import Channel, ChannelCreate, ChannelUpdate
from ..schemas.user import User
from ..pubsub.broker import broker

router = APIRouter(prefix="/channels", tags=["channels"])

@router.get("/", response_model=List[Channel])
def read_channels(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all channels the current user is a member of"""
    return get_channels(db=db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=Channel)
def create_new_channel(
    channel: ChannelCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new channel"""
    return create_channel(db=db, channel=channel, user_id=current_user.id)

@router.get("/{channel_id}", response_model=Channel)
def read_channel(
    channel_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific channel"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return db_channel

@router.put("/{channel_id}", response_model=Channel)
def update_channel_details(
    channel_id: int, 
    channel_update: ChannelUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a channel's details"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is the creator of the channel
    if db_channel.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this channel")
    
    return update_channel(db=db, channel_id=channel_id, channel_update=channel_update)

@router.delete("/{channel_id}")
def delete_channel_endpoint(
    channel_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a channel"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is the creator of the channel
    if db_channel.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this channel")
    
    return delete_channel(db=db, channel_id=channel_id)

@router.post("/{channel_id}/members/{user_id}")
def add_member_to_channel(
    channel_id: int, 
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a user to a channel"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is the creator of the channel
    if db_channel.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add members to this channel")
    
    return add_channel_member(db=db, channel_id=channel_id, user_id=user_id)

@router.delete("/{channel_id}/members/{user_id}")
def remove_member_from_channel(
    channel_id: int, 
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a user from a channel"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is the creator of the channel or removing themselves
    if db_channel.created_by != current_user.id and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to remove members from this channel")
    
    return remove_channel_member(db=db, channel_id=channel_id, user_id=user_id)

@router.get("/{channel_id}/members", response_model=List[User])
def read_channel_members(
    channel_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all members of a channel"""
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is a member of the channel
    is_member = any(member.id == current_user.id for member in db_channel.members)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to view channel members")
    
    return get_channel_members(db=db, channel_id=channel_id)

@router.post("/dm/{user_id}", response_model=Channel)
def create_direct_message(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create or get a direct message channel with another user"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot create DM with yourself")
    
    return create_dm_channel(db=db, user_id1=current_user.id, user_id2=user_id)

@router.websocket("/{channel_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time messaging in a channel"""
    # Authenticate user from token
    try:
        user = await get_current_active_user(token=token, db=db)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Check if channel exists
    db_channel = get_channel(db=db, channel_id=channel_id)
    if db_channel is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Check if user is a member of the channel
    is_member = any(member.id == user.id for member in db_channel.members)
    if not is_member and not db_channel.is_dm:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Accept connection
    await websocket.accept()
    
    # Subscribe to channel
    await broker.subscribe(channel_id, websocket, user.id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Unsubscribe on disconnect
        broker.unsubscribe(channel_id, websocket)