from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for channel members
channel_members = Table(
    'channel_members',
    Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# Association table for direct message participants
dm_participants = Table(
    'dm_participants',
    Base.metadata,
    Column('dm_channel_id', Integer, ForeignKey('channels.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="user")
    channels = relationship("Channel", secondary=channel_members, back_populates="members")
    dm_channels = relationship("Channel", secondary=dm_participants, back_populates="dm_participants")

class Channel(Base):
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False)
    is_dm = Column(Boolean, default=False)  # Flag for direct message channels
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="channel")
    members = relationship("User", secondary=channel_members, back_populates="channels")
    dm_participants = relationship("User", secondary=dm_participants, back_populates="dm_channels")
    creator = relationship("User", foreign_keys=[created_by])

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    is_agent_message = Column(Boolean, default=False)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    user = relationship("User", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    url = Column(String(255))
    capabilities = Column(Text, nullable=True)  # JSON string of capabilities
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="agent")