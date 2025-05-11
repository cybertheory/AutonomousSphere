from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class MatrixSearchRequest(BaseModel):
    """
    Model for Matrix search API requests
    """
    search_categories: Dict[str, Any] = Field(
        ...,
        description="Describes which categories to search in and their criteria"
    )

class MatrixMessage(BaseModel):
    """
    Model for a Matrix message search result
    """
    event_id: str
    room_id: str
    sender: str
    content: Dict[str, Any]
    origin_server_ts: int
    rank: float = 0

class MatrixRoom(BaseModel):
    """
    Model for a Matrix room search result
    """
    room_id: str
    name: Optional[str] = None
    topic: Optional[str] = None
    members_count: int = 0

class MatrixResults(BaseModel):
    """
    Model for Matrix search results
    """
    messages: List[MatrixMessage] = []
    rooms: List[MatrixRoom] = []
    next_batch: Optional[str] = None

class SearchMetadata(BaseModel):
    """
    Model for search metadata
    """
    total_results: int = 0
    search_time_ms: int = 0
    source: str = "api"
    timestamp: datetime = Field(default_factory=datetime.now)

class SearchResult(BaseModel):
    """
    Model for unified search results
    """
    query: str
    filters: Optional[Dict[str, Any]] = None
    results: Dict[str, Any] = {
        "agents": [],
        "matrix": {
            "rooms": [],
            "messages": []
        }
    }
    metadata: SearchMetadata = Field(default_factory=SearchMetadata)