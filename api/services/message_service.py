from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
import asyncio

from ..db.models import Message, Channel, User, Agent, channel_members
from ..schemas.message import MessageCreate, MessageUpdate
from ..pubsub.broker import broker

def get_messages(db: Session, channel_id: int, skip: int = 0, limit: int = 100):
    """Get messages for a specific channel"""
    return db.query(Message).filter(Message.channel_id == channel_id).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

def get_message(db: Session, message_id: int):
    """Get a specific message by ID"""
    return db.query(Message).filter(Message.id == message_id).first()

async def create_message(db: Session, message: MessageCreate, user_id: int):
    """Create a new message in a channel"""
    # Check if channel exists
    channel = db.query(Channel).filter(Channel.id == message.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if user is a member of the channel
    is_member = db.query(channel_members).filter(
        channel_members.c.channel_id == message.channel_id,
        channel_members.c.user_id == user_id
    ).first() is not None
    
    if not is_member and not channel.is_dm:
        raise HTTPException(status_code=403, detail="User is not a member of this channel")
    
    # Create message
    db_message = Message(
        content=message.content,
        channel_id=message.channel_id,
        user_id=user_id,
        is_agent_message=message.is_agent_message,
        agent_id=message.agent_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Publish message to channel subscribers
    await broker.publish_to_channel(message.channel_id, db_message)
    
    return db_message

def update_message(db: Session, message_id: int, message_update: MessageUpdate, user_id: int):
    """Update a message"""
    db_message = get_message(db, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the author of the message
    if db_message.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this message")
    
    update_data = message_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_message, key, value)
    
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_message(db: Session, message_id: int, user_id: int):
    """Delete a message"""
    db_message = get_message(db, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the author of the message
    if db_message.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    db.delete(db_message)
    db.commit()
    return {"message": "Message deleted successfully"}

async def create_agent_message(db: Session, channel_id: int, content: str, agent_id: int):
    """Create a message from an agent"""
    # Check if channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create message
    db_message = Message(
        content=content,
        channel_id=channel_id,
        user_id=None,  # No user for agent messages
        is_agent_message=True,
        agent_id=agent_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Publish message to channel subscribers
    await broker.publish_to_channel(channel_id, db_message)
    
    return db_message