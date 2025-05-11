from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class MCPServiceRegistration(BaseModel):
    """
    Model for MCP service registration with the registry
    """
    id: str = Field(default_factory=lambda: f"search-mcp-{uuid.uuid4().hex[:8]}")
    name: str = "AutonomousSphere Search MCP"
    description: str = "MCP server for unified search across agents and Matrix"
    protocol: str = "MCP"
    endpoint_url: str
    tools: List[str] = ["search"]
    skills: List[str] = ["search", "matrix_search", "agent_search"]
    public: bool = True
    custom_metadata: Dict[str, Any] = {
        "mcp_capabilities": ["search"]
    }
    
    class Config:
        schema_extra = {
            "example": {
                "id": "search-mcp-a1b2c3d4",
                "name": "AutonomousSphere Search MCP",
                "description": "MCP server for unified search across agents and Matrix",
                "protocol": "MCP",
                "endpoint_url": "ws://localhost:8000/search/mcp",
                "tools": ["search"],
                "skills": ["search", "matrix_search", "agent_search"],
                "public": True,
                "custom_metadata": {
                    "mcp_capabilities": ["search"],
                    "mcp_server_url": "ws://localhost:8000/search/mcp"
                }
            }
        }

class MCPEvent(BaseModel):
    """
    Model for MCP server events
    """
    event: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "event": "search_completed",
                "timestamp": "2023-07-01T12:34:56.789Z",
                "data": {
                    "query": "example query",
                    "results_count": 10
                }
            }
        }