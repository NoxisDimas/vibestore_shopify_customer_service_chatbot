import logging
from typing import List, Optional
from langchain_core.tools import BaseTool
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    PIIMiddleware
)
from app.agents.middleware.content_filter_middleware import ContentFilterMiddleware
from app.agents.middleware.sanitize_middleware import ThinkSanitizerMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.services.llms.manager import LLMManager
from app.agents.config import AgentConfig

logger = logging.getLogger(__name__)
        
def build_graph_agent(
    llm_manager : LLMManager,
    tools : Optional[List[BaseTool]],
    config : AgentConfig,
    checkpointer: Optional[AsyncPostgresSaver] = None
) :
    llm = llm_manager.get_llm(temperature = 0.3)
    lc_tools : List[BaseTool] = tools if isinstance(tools, list) else [tools]
    logger.info(f"Building agent with {len(lc_tools)} tools")

    graph = create_agent(
        name=config.agent_name,
        model=llm,
        tools=lc_tools if lc_tools else [],
        system_prompt=config.system_prompt,
        middleware=[
            ContentFilterMiddleware(
                banned_keywords=["hack", "exploit", "malware"]
            ),
            PIIMiddleware(
                "credit_card", strategy="mask"
            ),
            PIIMiddleware(
                "email", strategy="hash"
            ),
            PIIMiddleware(
                "url", strategy="redact"
            ),
            PIIMiddleware(
                "ip", strategy="hash"
            ),
            ThinkSanitizerMiddleware(),
            ModelRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
            )
        ],

        state_schema=AgentState,
        checkpointer=checkpointer
    )
    
    return graph