from abc import ABC, abstractmethod
from typing import Any
from app.channels.core.models import InternalMessage, InternalResponse

class BaseChannelAdapter(ABC):
    @abstractmethod
    def from_request(self, raw_request: Any) -> InternalMessage:
        """Convert a channel-specific request to an InternalMessage."""
        pass

    @abstractmethod
    def to_response(self, internal_response: InternalResponse) -> Any:
        """Convert an InternalResponse to a channel-specific response format (for synchronous replies)."""
        pass

    @abstractmethod
    async def send_message(self, internal_response: InternalResponse) -> Any:
        """Actively send a message to the channel API (for asynchronous replies)."""
        pass
