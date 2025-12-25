import logging
import httpx
from typing import Any, Dict
from app.channels.core.base_adapter import BaseChannelAdapter
from app.channels.core.models import InternalMessage, InternalResponse, ChannelType
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TelegramAdapter(BaseChannelAdapter):
    def from_request(self, raw_request: Dict[str, Any]) -> InternalMessage:
        # Placeholder for Telegram webhook payload
        message = raw_request.get("message", {})
        user_id = str(message.get("from", {}).get("id", "unknown_tg"))
        text = message.get("text", "")
        
        return InternalMessage(
            user_id=user_id,
            channel=ChannelType.TELEGRAM,
            text=text,
            metadata=raw_request
        )

    def to_response(self, internal_response: InternalResponse) -> Dict[str, Any]:
        # Since we sent the message via API, return simple OK to acknowledge webhook
        return {"status": "ok"}

    async def send_message(self, internal_response: InternalResponse) -> Any:
        """
        Send message via Telegram Bot API.
        """
        meta = internal_response.metadata or {}
        ingress = meta.get("ingress_metadata", {}) or {}

        if not settings.TELEGRAM_BOT_TOKEN:
             logger.info(f"[MOCK SEND] Telegram: {internal_response.text}")
             return {"status": "mock_sent"}

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        # Determine chat_id
        chat_id = (
            meta.get("chat_id")
            or meta.get("user_id")
            or ingress.get("message", {}).get("chat", {}).get("id")
            or "unknown_chat_id"
        )
        
        payload = {
            "chat_id": chat_id,
            "text": internal_response.text,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error sending Telegram message: {e}")
                return {"error": str(e)}
