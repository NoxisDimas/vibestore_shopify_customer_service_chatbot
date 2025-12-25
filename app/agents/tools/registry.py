import logging
from typing import List
from langchain_core.tools import BaseTool
from app.services.datastore.datastore import LightRAGClient
from app.services.shopify.controllers import ShopifyController
from app.services.memory.controller import MemoryController
from app.services.escalations.controller import escalation_service
from app.agents.tools.escalate_to_human import create_escalation_tools
from app.agents.tools.knowledge_base_tools import create_search_tool
from app.agents.tools.memory_tools import create_memory_tools
from app.agents.tools.search_product import create_search_product_tools
from app.agents.tools.order_lookup import create_order_lookup_tools
from app.agents.tools.shopify_shop_info import create_shopify_shop_info_tools

logger = logging.getLogger(__name__)

def get_tools(rag_client: LightRAGClient, memory_ctrl: MemoryController, shopify_ctrl: ShopifyController) -> List[BaseTool]:
    """
    Get all available tools for the agent.
    
    Returns:
        List of tools:
        - search_knowledge_base: Search FAQ/docs/policies
        - escalate_to_human: Transfer to human agent
        - check_escalation_status: Check pending escalations
        - read_profile: Read user context
        - save_preference: Save user preference
        - save_memory: Save general memory
        - delete_memory: Delete specific memory
        - get_memory: Get memory item
        - clear_memory: Clear all memories
        - search_product: Search for products (Airtable)
    """
    search_tool = create_search_tool(rag_client)
    mem_tools = create_memory_tools(memory_ctrl)
    escalation_tools = create_escalation_tools(escalation_service)
    order_lookup_tools = create_order_lookup_tools(shopify_ctrl)
    search_product_tools = create_search_product_tools(shopify_ctrl)
    shop_info_tools = create_shopify_shop_info_tools(shopify_ctrl)
    
    tools = [
        *search_tool,
        *mem_tools,
        *escalation_tools,
        *search_product_tools,
        *order_lookup_tools,
        *shop_info_tools,
    ]

    return tools

