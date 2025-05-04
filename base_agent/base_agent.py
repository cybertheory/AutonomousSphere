import requests
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentCapabilities(BaseModel):
    text: bool = True
    streaming: bool = False
    functions: List[str] = []

class BaseA2AAgent:
    """Base class for A2A-compatible agents that self-registers with the registry"""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        url: str, 
        registry_url: str = "http://registry:8081",
        chat_service_url: Optional[str] = None,
        capabilities: Optional[AgentCapabilities] = None
    ):
        self.name = name
        self.description = description
        self.url = url
        self.registry_url = registry_url
        self.chat_service_url = chat_service_url
        self.capabilities = capabilities or AgentCapabilities()
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        # Start registration and heartbeat
        self._start_registration_thread()
    
    def _start_registration_thread(self):
        """Start a background thread for registration and heartbeat"""
        thread = threading.Thread(target=self._registration_loop, daemon=True)
        thread.start()
    
    def _registration_loop(self):
        """Background loop for registration and heartbeat"""
        while True:
            try:
                # Register with registry
                self._register_with_registry()
                
                # Send heartbeat every 30 seconds
                time.sleep(30)
            except Exception as e:
                logger.error(f"Error in registration loop: {e}")
                time.sleep(10)  # Retry after a short delay
    
    def _register_with_registry(self):
        """Register this agent with the A2A registry"""
        try:
            agent_card = {
                "name": self.name,
                "url": self.url,
                "description": self.description,
                "capabilities": self.capabilities.dict()
            }
            
            response = requests.post(f"{self.registry_url}/agents", json=agent_card)
            
            if response.status_code == 200:
                logger.info(f"Successfully registered with registry at {self.registry_url}")
            else:
                logger.error(f"Failed to register with registry: {response.text}")
        except Exception as e:
            logger.error(f"Error registering with registry: {e}")
    
    def _send_heartbeat(self):
        """Send a heartbeat to the registry"""
        try:
            response = requests.put(f"{self.registry_url}/agents/{self.name}/heartbeat")
            
            if response.status_code != 200:
                logger.error(f"Failed to send heartbeat: {response.text}")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
    
    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming message"""
        message_type = message.get("type", "text")
        
        if message_type in self.message_handlers:
            return self.message_handlers[message_type](message)
        
        # Default handler for text messages
        return self.handle_text_message(message)
    
    def handle_text_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a text message (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement handle_text_message")
    
    def notify_chat_service(self, message: Dict[str, Any]):
        """Send a notification to the chat service"""
        if not self.chat_service_url:
            logger.warning("Chat service URL not set, can't send notification")
            return
        
        try:
            requests.post(f"{self.chat_service_url}/agent/notification", json={
                "agent_name": self.name,
                "message": message
            })
        except Exception as e:
            logger.error(f"Error notifying chat service: {e}")