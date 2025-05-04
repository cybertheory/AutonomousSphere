import asyncio
import json
import logging
from typing import Dict, List, Callable, Any, Optional, Set
from fastapi import WebSocket
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class PubSubBroker:
    def __init__(self, redis_url: Optional[str] = None):
        # Callback-based subscribers
        self.subscribers: Dict[str, List[Callable]] = {}
        self.channel_subscribers: Dict[int, List[Callable]] = {}
        self.dm_subscribers: Dict[str, List[Callable]] = {}
        
        # WebSocket-based subscribers
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Dict[int, WebSocket]] = {}  # channel_id -> {user_id -> websocket}
        self.lock = asyncio.Lock()
        
        # Redis client for pub/sub
        self.redis_url = redis_url
        self.redis = None
        self.pubsub = None
        self._initialize_redis()
        
    def _initialize_redis(self):
        """Initialize Redis connection if URL is provided"""
        if self.redis_url:
            try:
                # Create async Redis client
                self.redis = aioredis.from_url(self.redis_url)
                logger.info(f"Redis connection established at {self.redis_url}")
                
                # Start background task to listen for Redis messages
                asyncio.create_task(self._start_redis_listener())
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self.redis = None
    
    async def _start_redis_listener(self):
        """Start listening for Redis pub/sub messages"""
        if not self.redis:
            return
            
        try:
            self.pubsub = self.redis.pubsub()
            
            # Subscribe to channel messages
            await self.pubsub.psubscribe("channel:*")
            # Subscribe to direct messages
            await self.pubsub.psubscribe("dm:*")
            # Subscribe to general topics
            await self.pubsub.psubscribe("topic:*")
            
            logger.info("Redis pub/sub listener started")
            
            # Process incoming messages
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    await self._process_redis_message(message)
        except Exception as e:
            logger.error(f"Error in Redis listener: {e}")
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self._start_redis_listener())
    
    async def _process_redis_message(self, message):
        """Process a message received from Redis pub/sub"""
        try:
            channel = message["channel"].decode("utf-8")
            data = json.loads(message["data"].decode("utf-8"))
            
            if channel.startswith("channel:"):
                # Extract channel_id from the Redis channel name
                channel_id = int(channel.split(":")[1])
                await self._forward_to_websockets(channel_id, data)
            elif channel.startswith("dm:"):
                # Handle direct messages
                dm_id = channel.split(":")[1]
                await self._forward_to_dm_subscribers(dm_id, data)
            elif channel.startswith("topic:"):
                # Handle topic messages
                topic = channel.split(":")[1]
                await self._forward_to_topic_subscribers(topic, data)
        except Exception as e:
            logger.error(f"Error processing Redis message: {e}")
    
    async def _forward_to_websockets(self, channel_id: int, message: Any):
        """Forward a message to WebSocket subscribers"""
        await self.publish_to_channel(channel_id, message)
    
    async def _forward_to_dm_subscribers(self, dm_id: str, message: Any):
        """Forward a message to DM subscribers"""
        await self.publish_to_dm(dm_id, message)
    
    async def _forward_to_topic_subscribers(self, topic: str, message: Any):
        """Forward a message to topic subscribers"""
        await self.publish(topic, message)
        
    async def publish(self, topic: str, message: Any):
        """Publish a message to a topic"""
        # Publish to Redis if available
        if self.redis:
            try:
                message_json = self._serialize_message(message)
                await self.redis.publish(f"topic:{topic}", message_json)
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")
        
        # Publish to local subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
    
    async def publish_to_channel(self, channel_id: int, message: Any):
        """Publish a message to a specific channel"""
        # Publish to Redis if available
        if self.redis:
            try:
                message_json = self._serialize_message(message)
                await self.redis.publish(f"channel:{channel_id}", message_json)
            except Exception as e:
                logger.error(f"Error publishing to Redis channel: {e}")
        
        # Publish to callback subscribers
        if channel_id in self.channel_subscribers:
            for callback in self.channel_subscribers[channel_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in channel subscriber callback: {e}")
        
        # Publish to WebSocket subscribers
        if channel_id in self.active_connections:
            message_text = self._serialize_message(message)
            
            disconnected = set()
            for connection in self.active_connections[channel_id]:
                try:
                    await connection.send_text(message_text)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.unsubscribe(channel_id, connection)
    
    async def publish_to_dm(self, dm_id: str, message: Any):
        """Publish a message to a direct message conversation"""
        # Publish to Redis if available
        if self.redis:
            try:
                message_json = self._serialize_message(message)
                await self.redis.publish(f"dm:{dm_id}", message_json)
            except Exception as e:
                logger.error(f"Error publishing to Redis DM: {e}")
        
        # Publish to local subscribers
        if dm_id in self.dm_subscribers:
            for callback in self.dm_subscribers[dm_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in DM subscriber callback: {e}")
    
    async def publish_to_user(self, channel_id: int, user_id: int, message: Any):
        """Publish a message to a specific user in a channel"""
        if channel_id not in self.user_connections or user_id not in self.user_connections[channel_id]:
            return
        
        message_text = self._serialize_message(message)
        
        try:
            await self.user_connections[channel_id][user_id].send_text(message_text)
        except Exception as e:
            logger.error(f"Error sending message to user WebSocket: {e}")
            # Remove disconnected connection
            if channel_id in self.user_connections and user_id in self.user_connections[channel_id]:
                del self.user_connections[channel_id][user_id]
    
    def _serialize_message(self, message: Any) -> str:
        """Serialize a message to JSON string"""
        try:
            if isinstance(message, str):
                return message
            elif hasattr(message, 'dict'):
                return json.dumps(message.dict())
            else:
                return json.dumps(message)
        except Exception as e:
            logger.error(f"Error serializing message: {e}")
            return json.dumps({"error": "Failed to serialize message"})
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with a callback function"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            if topic in self.subscribers and callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)
        return unsubscribe
    
    def subscribe_to_channel(self, channel_id: int, callback: Callable):
        """Subscribe to messages in a specific channel with a callback function"""
        if channel_id not in self.channel_subscribers:
            self.channel_subscribers[channel_id] = []
        self.channel_subscribers[channel_id].append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            if channel_id in self.channel_subscribers and callback in self.channel_subscribers[channel_id]:
                self.channel_subscribers[channel_id].remove(callback)
        return unsubscribe
    
    def subscribe_to_dm(self, dm_id: str, callback: Callable):
        """Subscribe to direct messages between users with a callback function"""
        if dm_id not in self.dm_subscribers:
            self.dm_subscribers[dm_id] = []
        self.dm_subscribers[dm_id].append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            if dm_id in self.dm_subscribers and callback in self.dm_subscribers[dm_id]:
                self.dm_subscribers[dm_id].remove(callback)
        return unsubscribe
    
    async def subscribe(self, channel_id: int, websocket: WebSocket, user_id: int):
        """Subscribe a WebSocket connection to a channel"""
        async with self.lock:
            if channel_id not in self.active_connections:
                self.active_connections[channel_id] = set()
            
            self.active_connections[channel_id].add(websocket)
            
            if channel_id not in self.user_connections:
                self.user_connections[channel_id] = {}
            
            self.user_connections[channel_id][user_id] = websocket
            logger.info(f"User {user_id} subscribed to channel {channel_id} via WebSocket")

    def unsubscribe(self, channel_id: int, websocket: WebSocket):
        """Unsubscribe a WebSocket connection from a channel"""
        if channel_id in self.active_connections:
            self.active_connections[channel_id].discard(websocket)
            
            # Remove user connection
            if channel_id in self.user_connections:
                for user_id, ws in list(self.user_connections[channel_id].items()):
                    if ws == websocket:
                        del self.user_connections[channel_id][user_id]
                        logger.info(f"User {user_id} unsubscribed from channel {channel_id}")
                        break
    
    async def close(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()

# Create a singleton instance with Redis URL from environment
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
broker = PubSubBroker(redis_url=REDIS_URL)