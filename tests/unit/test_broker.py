import pytest
import asyncio
from api.pubsub.broker import PubSubBroker

@pytest.mark.asyncio
async def test_broker_publish():
    """Test that the broker can publish messages."""
    # Create a new broker instance for testing
    broker = PubSubBroker()
    
    # Create a mock subscriber
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    # Subscribe to a topic
    broker.subscribe("test_topic", callback)
    
    # Publish a message
    test_message = {"content": "test message"}
    await broker.publish("test_topic", test_message)
    
    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0] == test_message

@pytest.mark.asyncio
async def test_broker_publish_to_channel():
    """Test that the broker can publish messages to a channel."""
    # Create a new broker instance for testing
    broker = PubSubBroker()
    
    # Create a mock subscriber
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    # Subscribe to a channel
    broker.subscribe_to_channel(1, callback)
    
    # Publish a message
    test_message = {"content": "test message"}
    await broker.publish_to_channel(1, test_message)
    
    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0] == test_message

@pytest.mark.asyncio
async def test_broker_publish_to_dm():
    """Test that the broker can publish messages to a DM."""
    # Create a new broker instance for testing
    broker = PubSubBroker()
    
    # Create a mock subscriber
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    # Subscribe to a DM
    broker.subscribe_to_dm("user1-user2", callback)
    
    # Publish a message
    test_message = {"content": "test message"}
    await broker.publish_to_dm("user1-user2", test_message)
    
    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0] == test_message

@pytest.mark.asyncio
async def test_broker_unsubscribe():
    """Test that subscribers can unsubscribe."""
    # Create a new broker instance for testing
    broker = PubSubBroker()
    
    # Create a mock subscriber
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    # Subscribe to a topic
    unsubscribe = broker.subscribe("test_topic", callback)
    
    # Publish a message
    test_message = {"content": "test message"}
    await broker.publish("test_topic", test_message)
    
    # Check that the message was received
    assert len(received_messages) == 1
    
    # Unsubscribe
    unsubscribe()
    
    # Publish another message
    await broker.publish("test_topic", {"content": "another message"})
    
    # Check that no new message was received
    assert len(received_messages) == 1