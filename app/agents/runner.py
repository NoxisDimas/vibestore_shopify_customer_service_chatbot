import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.channels.core.models import InternalMessage, InternalResponse, ChannelType

logger = logging.getLogger(__name__)

async def run_agent(
        graph,
        message : InternalMessage,
        session_context: Optional[Dict[str, Any]] = None,

) -> InternalResponse:
    try:
        human_messages = HumanMessage(content=message.text)
        inputs = {"messages": [human_messages]}

        user_id = message.user_id
        thread_id = session_context.get("thread_id", user_id) if session_context else user_id

        config = {
            "configurable": {
                "thread_id" : thread_id,
                "user_id" : user_id,
                "channel_id" : message.channel.value if isinstance(message.channel, ChannelType) else str(message.channel)
            }
        }

        result = await graph.ainvoke(inputs, config)

        ai_messages = result.get("messages", [])
        last_messages = ai_messages[-1] if ai_messages else None
        output_text = last_messages.text if last_messages and hasattr(last_messages, "text") else(
            last_messages.content if last_messages else "No response generated."
        )

        return InternalResponse(
            text=str(output_text),
            metadata={
                "agent_name": "CustomerServiceAgent (LangGraph)",
                "thread_id": thread_id,
                "user_id": user_id,
                "channel": message.channel.value if isinstance(message.channel, ChannelType) else str(message.channel),
                "ingress_metadata": message.metadata,
            }
        )

    except Exception as e:
        logger.exception(
            "Error running agent",
            extra={
                "user_id": message.user_id,
                "channel": getattr(message.channel, "value", str(message.channel)),
                "text": message.text,
            },
        )
        return InternalResponse(
            text="I apologize, but I encountered an internal error. Please try again later.",
            metadata={"error": str(e)}
        )    