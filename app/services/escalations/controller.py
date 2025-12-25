import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.services.escalations.models import EscalationResponse, EscalationPriority, EscalationReason, EscalationRequest

logger = logging.getLogger(__name__)

class EscalationService:
    """
    Service for managing escalations to human agents.
    
    This is a base implementation that can be extended to integrate with:
    - Zendesk
    - Freshdesk
    - Intercom
    - Internal ticketing systems
    - Email notifications
    - Slack/Teams notifications
    """
    
    def __init__(self):
        # In-memory storage for demo. Replace with database/external service.
        self._escalations: Dict[str, EscalationRequest] = {}
        self._webhooks: List[str] = []  # Webhook URLs to notify
    
    async def create_escalation(
        self,
        user_id: str,
        channel: str,
        thread_id: str,
        reason: str,
        summary: str,
        priority: str = "medium",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EscalationResponse:
        """
        Create a new escalation request.
        
        Args:
            user_id: The user requesting escalation
            channel: Channel of conversation (web, whatsapp, telegram)
            thread_id: Conversation thread ID
            reason: Reason for escalation
            summary: AI-generated summary of the issue
            priority: Priority level (low, medium, high, urgent)
            conversation_history: Optional conversation history
            metadata: Optional additional metadata
            
        Returns:
            EscalationResponse with escalation ID and status
        """
        try:
            # Map reason string to enum
            reason_enum = EscalationReason(reason) if reason in [e.value for e in EscalationReason] else EscalationReason.OTHER
            priority_enum = EscalationPriority(priority) if priority in [e.value for e in EscalationPriority] else EscalationPriority.MEDIUM
            
            escalation = EscalationRequest(
                user_id=user_id,
                channel=channel,
                thread_id=thread_id,
                reason=reason_enum,
                priority=priority_enum,
                summary=summary,
                conversation_history=conversation_history or [],
                metadata=metadata or {}
            )
            
            # Store escalation
            self._escalations[escalation.id] = escalation
            
            # Log escalation
            logger.info(
                "Escalation created",
                extra={
                    "escalation_id": escalation.id,
                    "user_id": user_id,
                    "channel": channel,
                    "reason": reason,
                    "priority": priority
                }
            )
            
            # Notify via webhooks (async, fire-and-forget)
            await self._notify_webhooks(escalation)
            
            # Estimate wait time based on priority
            wait_times = {
                EscalationPriority.URGENT: "5-10 minutes",
                EscalationPriority.HIGH: "15-30 minutes",
                EscalationPriority.MEDIUM: "1-2 hours",
                EscalationPriority.LOW: "4-8 hours"
            }
            
            return EscalationResponse(
                success=True,
                escalation_id=escalation.id,
                message=f"Your request has been escalated to our support team. Reference ID: {escalation.id}",
                estimated_wait_time=wait_times.get(priority_enum, "1-2 hours")
            )
            
        except Exception as e:
            logger.error(f"Failed to create escalation: {e}")
            return EscalationResponse(
                success=False,
                escalation_id="",
                message=f"Failed to create escalation: {str(e)}"
            )
    
    async def get_escalation(self, escalation_id: str) -> Optional[EscalationRequest]:
        """Get an escalation by ID."""
        return self._escalations.get(escalation_id)
    
    async def get_user_escalations(self, user_id: str) -> List[EscalationRequest]:
        """Get all escalations for a user."""
        return [e for e in self._escalations.values() if e.user_id == user_id]
    
    async def get_pending_escalations(self) -> List[EscalationRequest]:
        """Get all pending escalations (for admin dashboard)."""
        return [e for e in self._escalations.values() if e.status == "pending"]
    
    async def update_status(
        self, 
        escalation_id: str, 
        status: str,
        assigned_to: Optional[str] = None
    ) -> bool:
        """Update escalation status."""
        if escalation_id not in self._escalations:
            return False
        
        self._escalations[escalation_id].status = status
        if assigned_to:
            self._escalations[escalation_id].metadata["assigned_to"] = assigned_to
        
        logger.info(f"Escalation {escalation_id} status updated to {status}")
        return True
    
    async def _notify_webhooks(self, escalation: EscalationRequest):
        """
        Notify external systems about the escalation.
        
        Override this method to integrate with:
        - Slack: Post to a support channel
        - Email: Send notification to support team
        - Ticketing: Create ticket in Zendesk/Freshdesk
        """
        # Placeholder for webhook notification
        # In production, implement actual HTTP calls
        logger.info(f"Would notify webhooks about escalation {escalation.id}")
        
        # Example Slack payload structure (for future implementation):
        # payload = {
        #     "text": f"🚨 New Escalation: {escalation.summary}",
        #     "blocks": [
        #         {"type": "section", "text": {"type": "mrkdwn", "text": f"*Priority:* {escalation.priority.value}"}},
        #         {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reason:* {escalation.reason.value}"}},
        #         {"type": "section", "text": {"type": "mrkdwn", "text": f"*User:* {escalation.user_id}"}},
        #     ]
        # }


# Singleton instance
escalation_service = EscalationService()
