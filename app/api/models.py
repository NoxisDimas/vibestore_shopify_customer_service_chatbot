from typing import Optional
from pydantic import BaseModel

class IngestRequest(BaseModel):
    text: str
    description: str | None = None

class SearchRequest(BaseModel):
    query: str
    mode : str = "hybrid"

class updateEscalationRequest(BaseModel):
    status: str
    assigned_to: Optional[str] = None
