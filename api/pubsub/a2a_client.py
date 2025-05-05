from python_a2a import A2AClient, Message, TextContent, MessageRole, AgentCard
from python_a2a.discovery import DiscoveryClient, enable_discovery
from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
import aiohttp
from .broker import broker
import time

logger = logging.getLogger(__name__)

class A2AIntegration:
    def __init__(self, registry_url):
        self.registry_url = registry_url
        # Fix: Initialize DiscoveryClient correctly
        self.discovery_client = DiscoveryClient(agent_card=None)
        self.discovery_client.add_registry(registry_url)
        self.agents = {}
        self._discovery_task = None
        # Add these missing properties that are used in discover_agents
        self.discovery_interval = 60  # Default to 60 seconds
        self.last_discovery_time = 0
        
    async def start(self):
        """Start the periodic discovery task"""
        if self._discovery_task is None:
            self._discovery_task = asyncio.create_task(self._periodic_discovery())
        return self
    
    def setup_discovery(self, registry_url: str):
        """Set up the A2A discovery client"""
        try:
            self.discovery_client = DiscoveryClient(agent_card=None)
            self.discovery_client.add_registry(registry_url)
            logger.info(f"A2A discovery client set up with registry: {registry_url}")
        except Exception as e:
            logger.error(f"Failed to set up A2A discovery client: {e}")
    
    async def _periodic_discovery(self):
        """Periodically discover new agents"""
        while True:
            try:
                # Discover agents
                await self.discover_agents()
                
                # Wait for the next discovery interval
                await asyncio.sleep(self.discovery_interval)
            except Exception as e:
                logger.error(f"Error in periodic discovery: {e}")
                await asyncio.sleep(10)  # Shorter interval on error
    
    async def discover_agents(self) -> List[AgentCard]:
        """Discover available A2A agents from the registry"""
        # Skip if we've checked recently
        current_time = time.time()
        if current_time - self.last_discovery_time < self.discovery_interval:
            return []
            
        self.last_discovery_time = current_time
        
        if self.discovery_client:
            try:
                agents = self.discovery_client.discover()
                
                # Register discovered agents
                for agent in agents:
                    self.register_agent(agent.name, agent.url)
                
                return agents
            except Exception as e:
                logger.error(f"Error discovering agents with python-a2a: {e}")
                # Fall back to HTTP discovery if python-a2a fails
        
        # Fallback HTTP discovery method
        try:
            if not self.registry_url:
                return []
                
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.registry_url}/agents") as response:
                    if response.status == 200:
                        agents_data = await response.json()
                        agent_cards = [AgentCard(**agent) for agent in agents_data]
                        
                        # Register discovered agents
                        for agent in agent_cards:
                            self.register_agent(agent.name, agent.url)
                            
                        return agent_cards
                    return []
        except Exception as e:
            logger.error(f"Error discovering agents with HTTP: {e}")
            return []
    
    def register_agent(self, name: str, url: str) -> bool:
        """Register an A2A agent with the integration"""
        # Skip if already registered with same URL
        if name in self.agents:
            if isinstance(self.agents[name], str) and self.agents[name] == url:
                return True
            elif hasattr(self.agents[name], 'base_url') and self.agents[name].base_url == url:
                return True
        
        try:
            self.agents[name] = A2AClient(url)
            logger.info(f"Registered A2A agent: {name} at {url}")
            
            # Subscribe to agent responses
            self._setup_agent_subscription(name)
            
            # Publish agent discovery event
            asyncio.create_task(broker.publish("agent.discovered", {
                "name": name,
                "url": url
            }))
            
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {name}: {e}")
            # Store the URL directly as fallback
            self.agents[name] = url
            return False
    
    def _setup_agent_subscription(self, agent_name: str):
        """Set up subscription to handle agent responses"""
        if not isinstance(self.agents[agent_name], A2AClient):
            return
            
        def agent_response_handler(response):
            # Publish the agent's response to the appropriate topic
            asyncio.create_task(broker.publish(f"agent.response.{agent_name}", response))
        
        # Store the handler for potential cleanup later
        self.agents[agent_name].response_handler = agent_response_handler
    
    async def send_message_to_agent(self, agent_name: str, message_content: str, channel_id: Optional[int] = None, user_id: Optional[int] = None) -> Any:
        """Send a message to an A2A agent"""
        if agent_name not in self.agents:
            logger.error(f"Agent {agent_name} not registered")
            return {"error": f"Agent {agent_name} not registered"}
        
        try:
            # If we have an A2AClient instance
            if isinstance(self.agents[agent_name], A2AClient):
                # Create A2A message
                message = Message(
                    content=TextContent(text=message_content),
                    role=MessageRole.USER
                )
                
                # Send message to agent
                response = await asyncio.to_thread(self.agents[agent_name].ask, message)
                
                # If channel_id is provided, publish to that channel
                if channel_id:
                    await broker.publish_to_channel(channel_id, {
                        "agent": agent_name,
                        "response": response
                    })
                
                return response
            else:
                # Fallback to HTTP method if we only have the URL
                agent_url = self.agents[agent_name]
                
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "message": message_content,
                        "channel_id": channel_id,
                        "user_id": user_id
                    }
                    
                    async with session.post(f"{agent_url}/message", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # If channel_id is provided, publish to that channel
                            if channel_id:
                                await broker.publish_to_channel(channel_id, {
                                    "agent": agent_name,
                                    "response": result
                                })
                                
                            return result
                        else:
                            error_text = await response.text()
                            return {"error": f"Agent returned error: {error_text}"}
                            
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_name}: {e}")
            return {"error": f"Failed to communicate with agent: {str(e)}"}
    
    async def stream_message_to_agent(self, agent_name: str, message_content: str, callback: callable):
        """Stream a message to an A2A agent with real-time updates"""
        if agent_name not in self.agents:
            logger.error(f"Agent {agent_name} not registered")
            return
        
        try:
            # Only support streaming with A2AClient instances
            if not isinstance(self.agents[agent_name], A2AClient):
                logger.error(f"Streaming not supported for HTTP-only agent {agent_name}")
                await callback({"error": "Streaming not supported for this agent"})
                return
                
            from python_a2a import StreamingClient, Message, TextContent, MessageRole
            
            # Create streaming client
            streaming_client = StreamingClient(self.agents[agent_name].base_url)
            
            # Create A2A message
            message = Message(
                content=TextContent(text=message_content),
                role=MessageRole.USER
            )
            
            # Stream the response
            async for chunk in streaming_client.stream_response(message):
                await callback(chunk)
                
        except Exception as e:
            logger.error(f"Error streaming message to agent {agent_name}: {e}")
            await callback({"error": f"Streaming error: {str(e)}"})

# Create a singleton instance
import os
from dotenv import load_dotenv

load_dotenv()
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8081")
_a2a_integration = None

def get_a2a_integration():
    global _a2a_integration
    if _a2a_integration is None:
        _a2a_integration = A2AIntegration(registry_url=REGISTRY_URL)
    return _a2a_integration