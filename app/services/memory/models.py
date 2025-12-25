from datetime import datetime
from typing import List, Union, Dict, Any, Optional
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    id: str = Field(alias="id")
    user_id: str
    content: str = Field(alias="memory")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
