import logging
import httpx
from typing import Any, Dict
from app.channels.core.base_adapter import BaseChannelAdapter
from app.channels.core.models import InternalMessage, InternalResponse, ChannelType
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class WhatsAppAdapter(BaseChannelAdapter):
    def from_request(self, raw_request: Dict[str, Any]) -> InternalMessage:
        # Placeholder for WhatsApp payload structure parsing
        # Simplification: Assume some standard webhook format
        # e.g. a Twilio or Meta Graph API payload
        # Meta Business API structure is deeply nested usually
        
        # Checking for standard Meta structure (entry -> changes -> value -> messages)
        # Or simple flat structure for testing
        
        user_id = raw_request.get("From", "unknown_wa_user")
        text = raw_request.get("Body", "")
        
        # Try finding in nested if flat not found
        if not text and "entry" in raw_request:
            try:
                msg = raw_request["entry"][0]["changes"][0]["value"]["messages"][0]
                user_id = msg.get("from", user_id)
                text = msg.get("text", {}).get("body", "")
            except (IndexError, KeyError):
                pass

        return InternalMessage(
            user_id=user_id,
            channel=ChannelType.WHATSAPP,
            text=text,
            metadata=raw_request
        )

    def to_response(self, internal_response: InternalResponse) -> Dict[str, Any]:
        # Since we are sending message via API (async), we just return 200 OK status to the webhook.
        return {"status": "success"}

    async def send_message(self, internal_response: InternalResponse) -> Any:
        """
        Send message via WhatsApp API (Meta or Twilio).
        """
        meta = internal_response.metadata or {}
        ingress = meta.get("ingress_metadata", {}) or {}

        # Example using Meta Graph API structure
        url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        to_number = (
            meta.get("to_phone_number")
            or meta.get("user_id")
            or ingress.get("From")
            or ingress.get("from")
            or "recipient_number"
        )

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,  # Should be in metadata or tracked context
            "type": "text",
            "text": {"body": internal_response.text}
        }
        
        # If simulation / no token
        if not settings.WHATSAPP_ACCESS_TOKEN:
            logger.info(f"[MOCK SEND] WhatsApp to {payload['to']}: {internal_response.text}")
            return {"status": "mock_sent", "payload": payload}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error sending WhatsApp message: {e}")
                # Don't raise, just log, so we don't crash the agent loop
                return {"error": str(e)}
