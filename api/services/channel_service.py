from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from ..db.models import Channel, User, channel_members, dm_participants
from ..schemas.channel import ChannelCreate, ChannelUpdate

def get_channels(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None):
    """Get all channels or channels for a specific user"""
    query = db.query(Channel)
    
    if user_id:
        # Get channels where the user is a member
        query = query.join(channel_members).filter(channel_members.c.user_id == user_id)
    
    return query.offset(skip).limit(limit).all()

def get_channel(db: Session, channel_id: int):
    """Get a specific channel by ID"""
    return db.query(Channel).filter(Channel.id == channel_id).first()

def create_channel(db: Session, channel: ChannelCreate, user_id: int):
    """Create a new channel"""
    db_channel = Channel(
        name=channel.name,
        description=channel.description,
        is_private=channel.is_private,
        is_dm=channel.is_dm,
        created_by=user_id
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    
    # Add creator as a member
    add_channel_member(db, db_channel.id, user_id)
    
    # Add additional members if provided
    if channel.member_ids:
        for member_id in channel.member_ids:
            if member_id != user_id:  # Skip creator as they're already added
                add_channel_member(db, db_channel.id, member_id)
    
    return db_channel

def update_channel(db: Session, channel_id: int, channel_update: ChannelUpdate):
    """Update a channel's details"""
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    update_data = channel_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_channel, key, value)
    
    db.commit()
    db.refresh(db_channel)
    return db_channel

def delete_channel(db: Session, channel_id: int):
    """Delete a channel"""
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    db.delete(db_channel)
    db.commit()
    return {"message": "Channel deleted successfully"}

def add_channel_member(db: Session, channel_id: int, user_id: int):
    """Add a user to a channel"""
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already a member
    is_member = db.query(channel_members).filter(
        channel_members.c.channel_id == channel_id,
        channel_members.c.user_id == user_id
    ).first() is not None
    
    if is_member:
        return {"message": "User is already a member of this channel"}
    
    # Add user to channel
    statement = channel_members.insert().values(channel_id=channel_id, user_id=user_id)
    db.execute(statement)
    db.commit()
    
    return {"message": "User added to channel successfully"}

def remove_channel_member(db: Session, channel_id: int, user_id: int):
    """Remove a user from a channel"""
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is a member
    is_member = db.query(channel_members).filter(
        channel_members.c.channel_id == channel_id,
        channel_members.c.user_id == user_id
    ).first() is not None
    
    if not is_member:
        raise HTTPException(status_code=400, detail="User is not a member of this channel")
    
    # Remove user from channel
    statement = channel_members.delete().where(
        channel_members.c.channel_id == channel_id,
        channel_members.c.user_id == user_id
    )
    db.execute(statement)
    db.commit()
    
    return {"message": "User removed from channel successfully"}

def get_channel_members(db: Session, channel_id: int):
    """Get all members of a channel"""
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return db_channel.members

def create_dm_channel(db: Session, user_id1: int, user_id2: int):
    """Create a direct message channel between two users"""
    # Check if DM channel already exists
    existing_dm = (
        db.query(Channel)
        .filter(Channel.is_dm == True)
        .join(dm_participants, Channel.id == dm_participants.c.dm_channel_id)
        .group_by(Channel.id)
        .having(
            db.func.count(
                db.case(
                    [
                        (dm_participants.c.user_id.in_([user_id1, user_id2]), 1)
                    ],
                    else_=0
                )
            ) == 2
        )
        .first()
    )
    
    if existing_dm:
        return existing_dm
    
    # Create new DM channel
    user1 = db.query(User).filter(User.id == user_id1).first()
    user2 = db.query(User).filter(User.id == user_id2).first()
    
    if not user1 or not user2:
        raise HTTPException(status_code=404, detail="One or both users not found")
    
    dm_name = f"DM: {user1.username} & {user2.username}"
    
    db_channel = Channel(
        name=dm_name,
        is_private=True,
        is_dm=True,
        created_by=user_id1
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    
    # Add both users to the DM channel
    statement1 = dm_participants.insert().values(dm_channel_id=db_channel.id, user_id=user_id1)
    statement2 = dm_participants.insert().values(dm_channel_id=db_channel.id, user_id=user_id2)
    
    db.execute(statement1)
    db.execute(statement2)
    db.commit()
    
    return db_channel