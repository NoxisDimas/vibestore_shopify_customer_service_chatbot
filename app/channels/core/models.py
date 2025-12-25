from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel

class ChannelType(str, Enum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

class Attachment(BaseModel):
    type: str  # "image", "file", etc.
    url: str
    metadata: dict = {}

class InternalMessage(BaseModel):
    user_id: str
    channel: ChannelType
    text: str
    attachments: List[Attachment] = []
    metadata: dict = {}

class InternalResponse(BaseModel):
    text: str
    rich_content: Optional[dict] = None
    metadata: dict = {}
