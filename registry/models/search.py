from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .agent import Protocol

class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None