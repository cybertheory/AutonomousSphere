import pytest
from sqlalchemy.orm import Session
from api.db.models import User, Channel, Message, ChannelMemberModel
from api.db.database import Base, engine

def test_user_model(db_session: Session):
    """Test the User model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    
    # Query the user
    db_user = db_session.query(User).filter(User.username == "testuser").first()
    assert db_user is not None
    assert db_user.username == "testuser"
    assert db_user.email == "test@example.com"
    assert db_user.hashed_password == "hashedpassword"

def test_channel_model(db_session: Session):
    """Test the Channel model."""
    # Create a user
    user = User(
        username="channeluser",
        email="channel@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a channel
    channel = Channel(
        name="test-channel",
        description="A test channel",
        is_private=False,
        created_by=user.id
    )
    db_session.add(channel)
    db_session.commit()
    
    # Query the channel
    db_channel = db_session.query(Channel).filter(Channel.name == "test-channel").first()
    assert db_channel is not None
    assert db_channel.name == "test-channel"
    assert db_channel.description == "A test channel"
    assert db_channel.is_private is False
    assert db_channel.created_by == user.id

def test_message_model(db_session: Session):
    """Test the Message model."""
    # Create a user
    user = User(
        username="messageuser",
        email="message@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user)
    
    # Create a channel
    channel = Channel(
        name="message-channel",
        description="A channel for messages",
        is_private=False,
        created_by=user.id
    )
    db_session.add(channel)
    db_session.commit()
    
    # Create a message
    message = Message(
        content="Hello, world!",
        user_id=user.id,
        channel_id=channel.id
    )
    db_session.add(message)
    db_session.commit()
    
    # Query the message
    db_message = db_session.query(Message).filter(Message.content == "Hello, world!").first()
    assert db_message is not None
    assert db_message.content == "Hello, world!"
    assert db_message.user_id == user.id
    assert db_message.channel_id == channel.id

def test_channel_member_model(db_session: Session):
    """Test the ChannelMember model."""
    # Create two users
    user1 = User(
        username="member1",
        email="member1@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user1)
    
    user2 = User(
        username="member2",
        email="member2@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user2)
    
    # Create a channel
    channel = Channel(
        name="member-channel",
        description="A channel for testing members",
        is_private=False,
        created_by=user1.id
    )
    db_session.add(channel)
    db_session.commit()
    
    # Add users as members
    member1 = ChannelMember(
        channel_id=channel.id,
        user_id=user1.id
    )
    db_session.add(member1)
    
    member2 = ChannelMember(
        channel_id=channel.id,
        user_id=user2.id
    )
    db_session.add(member2)
    db_session.commit()
    
    # Query the members
    db_members = db_session.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).all()
    assert len(db_members) == 2
    assert any(m.user_id == user1.id for m in db_members)
    assert any(m.user_id == user2.id for m in db_members)