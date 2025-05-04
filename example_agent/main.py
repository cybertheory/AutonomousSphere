from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
import logging

# Add parent directory to path to import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent.base_agent import BaseA2AAgent, AgentCapabilities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Example A2A Agent", description="A simple example of an A2A-compatible agent")

class MessageRequest(BaseModel):
    message: str
    channel_id: Optional[int] = None
    user_id: Optional[int] = None

class MessageResponse(BaseModel):
    response: str
    agent: str
    metadata: Dict[str, Any] = {}

# Get environment variables
AGENT_NAME = os.getenv("AGENT_NAME", "ExampleAgent")
AGENT_URL = os.getenv("AGENT_URL", "http://example-agent:8080")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8081")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://api:8000")

# Create agent instance
agent = BaseA2AAgent(
    name=AGENT_NAME,
    description="A simple example agent that echoes messages with some additional information",
    url=AGENT_URL,
    registry_url=REGISTRY_URL,
    chat_service_url=CHAT_SERVICE_URL,
    capabilities=AgentCapabilities(
        text=True,
        streaming=False,
        functions=["echo", "info"]
    )
)

# Implement text message handler
def handle_text(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a text message"""
    text = message.get("message", "")
    channel_id = message.get("channel_id")
    user_id = message.get("user_id")
    
    # Simple echo response with some metadata
    response = f"Echo: {text}"
    
    # Add channel info if provided
    channel_info = f" (from channel {channel_id})" if channel_id else ""
    user_info = f" (from user {user_id})" if user_id else ""
    
    return {
        "response": response + channel_info + user_info,
        "agent": AGENT_NAME,
        "metadata": {
            "channel_id": channel_id,
            "user_id": user_id,
            "message_length": len(text)
        }
    }

# Register the handler
agent.register_message_handler("text", handle_text)

# Override the abstract method
agent.handle_text_message = handle_text

@app.get("/")
def read_root():
    return {"status": "ok", "agent": AGENT_NAME}

@app.get("/agent-card")
def get_agent_card():
    """Return the agent card for A2A discovery"""
    return {
        "name": AGENT_NAME,
        "url": AGENT_URL,
        "description": "A simple example agent that echoes messages with some additional information",
        "capabilities": {
            "text": True,
            "streaming": False,
            "functions": ["echo", "info"]
        }
    }

@app.post("/message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Process a message sent to the agent"""
    try:
        logger.info(f"Received message: {request.message}")
        
        # Convert to dict for the handler
        message_dict = {
            "type": "text",
            "message": request.message,
            "channel_id": request.channel_id,
            "user_id": request.user_id
        }
        
        # Process with the agent
        result = agent.handle_message(message_dict)
        
        return MessageResponse(
            response=result["response"],
            agent=result["agent"],
            metadata=result["metadata"]
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)