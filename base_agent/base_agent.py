import requests
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel
import socket

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
        
        # Log configuration
        logger.info(f"Initializing agent: {name}")
        logger.info(f"Agent URL: {url}")
        logger.info(f"Registry URL: {registry_url}")
        logger.info(f"Chat Service URL: {chat_service_url}")
        
        # Start registration and heartbeat
        self._start_registration_thread()
    
    def _start_registration_thread(self):
        """Start a background thread for registration and heartbeat"""
        thread = threading.Thread(target=self._registration_loop, daemon=True)
        thread.start()
    
    def _registration_loop(self):
        """Background loop for registration and heartbeat"""
        # Initial delay to allow network to stabilize
        time.sleep(5)
        
        retry_count = 0
        max_retries = 10
        backoff_factor = 1.5
        
        while True:
            try:
                # Try to resolve registry hostname
                registry_host = self.registry_url.split("://")[1].split(":")[0]
                try:
                    registry_ip = socket.gethostbyname(registry_host)
                    logger.info(f"Resolved registry host {registry_host} to {registry_ip}")
                except Exception as e:
                    logger.warning(f"Could not resolve registry host {registry_host}: {e}")
                
                # Register with registry
                success = self._register_with_registry()
                
                if success:
                    # Reset retry count on success
                    retry_count = 0
                    # Send heartbeat every 30 seconds
                    time.sleep(30)
                    self._send_heartbeat()
                else:
                    # Exponential backoff on failure
                    retry_count += 1
                    wait_time = min(60, backoff_factor ** retry_count)
                    logger.warning(f"Registration failed, retrying in {wait_time:.1f} seconds (attempt {retry_count})")
                    time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error in registration loop: {e}")
                retry_count += 1
                wait_time = min(60, backoff_factor ** retry_count)
                time.sleep(wait_time)  # Retry after a delay with exponential backoff
    
    def _register_with_registry(self):
        """Register this agent with the A2A registry"""
        try:
            # Format the agent card according to the registry's expected format
            agent_card = {
                "name": self.name,
                "url": self.url,
                "description": self.description,
                "capabilities": self.capabilities.dict()
            }
            
            logger.info(f"Attempting to register with registry at {self.registry_url}")
            logger.info(f"Sending agent card: {agent_card}")
            
            # Use a timeout to avoid hanging indefinitely
            response = requests.post(f"{self.registry_url}/agents", json=agent_card, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully registered with registry at {self.registry_url}")
                return True
            else:
                logger.error(f"Failed to register with registry: {response.status_code} - {response.text}")
                # Log the response details for debugging
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Could not parse error response as JSON")
                return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error registering with registry: {e}")
            return False
        except Exception as e:
            logger.error(f"Error registering with registry: {e}")
            return False
    
    def _send_heartbeat(self):
        """Send a heartbeat to the registry"""
        try:
            response = requests.put(f"{self.registry_url}/agents/{self.name}/heartbeat", timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Failed to send heartbeat: {response.text}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
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
            }, timeout=5)
        except Exception as e:
            logger.error(f"Error notifying chat service: {e}")