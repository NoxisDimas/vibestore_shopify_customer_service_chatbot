import logging
from functools import lru_cache
from typing import List
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config.settings import get_settings, Settings
from app.services.llms.manager import LLMManager
from app.services.datastore.datastore import lightrag_client, LightRAGClient
from app.services.memory.controller import MemoryController
from app.services.shopify.controllers import ShopifyController
from app.agents.tools import get_tools
from app.agents.config import AgentConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from app.agents.builder import build_graph_agent

logger = logging.getLogger(__name__)
settings = get_settings()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key:str = Security(api_key_header)):
    if not settings.API_KEY:
        return True
    
    if api_key == settings.API_KEY:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )

@lru_cache()
def get_settings() -> Settings:
    return settings

_pg_pool = None
async def get_pg_pool() -> AsyncPostgresSaver:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = AsyncConnectionPool(
            conninfo=settings.POSTGRES_URI, 
            max_size=20,
            kwargs={"autocommit": True},
            open=False
        )
        await _pg_pool.open()
    return _pg_pool

_checkpointer : AsyncPostgresSaver | None = None

async def get_checkpointer() -> AsyncPostgresSaver:
    global _checkpointer
    if _checkpointer is None:
        pool = await get_pg_pool()
        _checkpointer = AsyncPostgresSaver(pool)
        await _checkpointer.setup()
    return _checkpointer

@lru_cache()
def get_llm_manager() -> LLMManager:
    return LLMManager()

_memory_controller : MemoryController | None = None

async def get_memory_controller() -> MemoryController:
    global _memory_controller
    if _memory_controller is None:
        _memory_controller = await MemoryController.create()

    return _memory_controller

@lru_cache()
def get_lightrag_client() -> LightRAGClient:
    return lightrag_client

@lru_cache()
def get_shopify_controller() -> ShopifyController:
    return ShopifyController()

async def get_agent_graph():
    """
    Builds the agent graph. 
    Note: We don't cache the graph WITH the checkpointer if checkingpointer relies on open cursors.
    But PostgresSaver(pool) should be thread safe and reusable.
    """

    llm_mgr = get_llm_manager()
    rag_client = get_lightrag_client()
    memory_ctrl = await get_memory_controller()

    shopify_ctrl = get_shopify_controller()

    tools = get_tools(rag_client, memory_ctrl, shopify_ctrl)
    logger.info(f"Registering tools: {[t.name for t in tools]}")
    config = AgentConfig()
    
    checkpointer = await get_checkpointer()
    
    return build_graph_agent(llm_mgr, tools, config, checkpointer=checkpointer)