import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

logger = logging.getLogger(__name__)


class EscalationPriority(str, Enum):
    """Priority levels for escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EscalationReason(str, Enum):
    """Common reasons for escalation."""
    COMPLEX_ISSUE = "complex_issue"
    CUSTOMER_REQUEST = "customer_request"
    SENTIMENT_NEGATIVE = "sentiment_negative"
    TECHNICAL_LIMITATION = "technical_limitation"
    BILLING_ISSUE = "billing_issue"
    COMPLAINT = "complaint"
    OTHER = "other"


class EscalationRequest(BaseModel):
    """Model for an escalation request."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    channel: str
    thread_id: str
    reason: EscalationReason
    priority: EscalationPriority = EscalationPriority.MEDIUM
    summary: str  # AI-generated summary of the issue
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, assigned, in_progress, resolved


class EscalationResponse(BaseModel):
    """Response after creating an escalation."""
    success: bool
    escalation_id: str
    message: str
    estimated_wait_time: Optional[str] = None