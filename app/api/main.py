import logging
from typing import Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request
from slowapi import  _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config.settings import get_settings
from app.api import deps
from app.api.rate_limit import limiter
from app.channels.core.models import ChannelType
from app.channels.web.adapter import WebAdapter
from app.channels.telegram.adapter import TelegramAdapter
from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.agents.runner import run_agent
from pythonjsonlogger import json

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = json.JsonFormatter(
     "%(asctime)s %(levelname)s %(name)s %(message)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()
    logger.addHandler(logHandler)

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="Urban Vibe Store AI Assistant API",
    description="API for the Urban Vibe Store AI Assistant powered by LangGraph.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

adapters = {
    ChannelType.WEB: WebAdapter(),
    ChannelType.TELEGRAM: TelegramAdapter(),
    ChannelType.WHATSAPP: WhatsAppAdapter(),
}

@app.get("/health", response_model=Dict[str, str])
def health_check():
    return {"status": "healthy"}  
  
@app.post("/v1/chat/{channel_name}")
@limiter.limit("10/minute")
async def chat_endpoint(
    request: Request,
    channel_name: ChannelType,
    payload: Dict[str, Any],
    graph = Depends(deps.get_agent_graph),
) -> Dict[str, Any]:
    if channel_name not in adapters:
        raise HTTPException(status_code=400, detail="Unsupported channel")
    
    adapter = adapters[channel_name]

    try:
        internal_message = adapter.from_request(payload)
    except Exception as e:
        logger.error(f"Error parsing request for channel {channel_name}: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    try:
        internal_response = await run_agent(graph, internal_message)
        logger.info(f"Agent response: {internal_response}")
    except Exception as e:
        logger.error(f"Error processing message for channel {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    try:
        await adapter.send_message(internal_response)
    except Exception as e:
        logger.error(f"Error sending response for channel {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send response")
    
    return adapter.to_response(internal_response)
