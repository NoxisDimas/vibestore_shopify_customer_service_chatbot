import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from app.services.escalations.controller import  EscalationService

logger = logging.getLogger(__name__)

def create_escalation_tools(service: EscalationService) -> List[BaseTool]:
    """Create tools for human escalation/handoff."""
    
    @tool()
    async def escalate_to_human(
        reason: str,
        summary: str,
        priority: str,
        config: RunnableConfig
    ) -> str:
        """
            Escalate to Human Agent

            Transfers the conversation to a human support agent when the AI
            cannot adequately resolve the customer's issue. Use this when:
            - The issue is too complex for automated handling
            - The customer explicitly requests human assistance
            - The customer appears frustrated or upset
            - The issue involves billing, complaints, or sensitive matters

            Args:
                reason (str): Reason for escalation. Must be one of:
                    - "complex_issue": Issue too complex for AI
                    - "customer_request": Customer asked for human
                    - "sentiment_negative": Customer appears upset
                    - "technical_limitation": AI cannot perform action
                    - "billing_issue": Payment/billing related
                    - "complaint": Customer complaint
                    - "other": Other reasons
                summary (str): Brief summary of the issue and conversation context.
                    This helps the human agent understand the situation quickly.
                priority (str): Priority level. Must be one of:
                    - "low": General inquiries, can wait
                    - "medium": Standard issues (default)
                    - "high": Urgent issues needing quick attention
                    - "urgent": Critical issues requiring immediate attention
                config (RunnableConfig): Contains user_id and channel metadata.

            Returns:
                str: Confirmation message with escalation ID and estimated wait time.

            Example:
                Customer: "Saya sudah komplain 3 kali tapi tidak ada solusi!"
                Agent calls: escalate_to_human(
                    reason="complaint",
                    summary="Customer has complained 3 times about unresolved issue",
                    priority="high"
                )
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            channel = config.get("configurable", {}).get("channel", "web")
            thread_id = config.get("configurable", {}).get("thread_id", user_id)
            
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            
            result = await service.create_escalation(
                user_id=user_id,
                channel=channel,
                thread_id=thread_id,
                reason=reason,
                summary=summary,
                priority=priority
            )
            
            if result.success:
                return (
                    f"Percakapan Anda telah diteruskan ke tim support kami. "
                    f"Nomor referensi: {result.escalation_id}. "
                    f"Estimasi waktu tunggu: {result.estimated_wait_time}. "
                    f"Tim kami akan segera menghubungi Anda melalui channel yang sama."
                )
            else:
                return f"Maaf, terjadi kesalahan saat memproses permintaan: {result.message}"
                
        except Exception as e:
            logger.error(f"Error escalating to human: {e}")
            return ToolException(f"Error escalating to human: {e}")

    @tool()
    async def check_escalation_status(config: RunnableConfig) -> str:
        """
            Check Escalation Status
            
            Checks if the user has any pending escalations and their status.
            
            Args:
                config (RunnableConfig): Contains user_id metadata.
                
            Returns:
                str: Status of user's escalations or message if none found.
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            
            escalations = await service.get_user_escalations(user_id)
            
            if not escalations:
                return "Anda tidak memiliki permintaan eskalasi yang aktif."
            
            # Format response
            status_list = []
            for esc in escalations:
                status_list.append(
                    f"- ID: {esc.id[:8]}... | Status: {esc.status} | Priority: {esc.priority.value}"
                )
            
            return f"Daftar eskalasi Anda:\n" + "\n".join(status_list)
            
        except Exception as e:
            logger.error(f"Error checking escalation status: {e}")
            return ToolException(f"Error checking escalation status: {e}")

    return [escalate_to_human, check_escalation_status]