import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain.tools import tool
from app.services.datastore.datastore import LightRAGClient

logger = logging.getLogger(__name__)

def create_search_tool(controller:LightRAGClient) -> List[BaseTool]:

    @tool()
    async def search_knowledge_base(query: str) -> str:
        """
            Search Knowledge Base

            Uses the LightRAGClient to perform a hybrid search on the
            comprehensive knowledge base, including FAQs, Shop policies, and company profiles. this tools not contain about shopify store info.

            Args:
                query (str): The user's question or search text.

            Returns:
                str: A text summary of the search results, or an error
                message if the search fails.

            Example:
                User: "Apa kebijakan retur barang?"
                Agent calls: search_knowledge_base("kebijakan retur barang")
        """
        try:
            if not query:
                logger.error("query not provider")
                return ToolException("query not given make sure to give query when calling this tool")
            
            return await controller.query(query=query, mode="hybrid")
        
        except Exception as e:
            logger.error(f"Error searching Knowledge Base: {e}")
            return ToolException("Tools Error when searching Knowledge Base, Tell the user that the chatbot system is having problems, and apologize to the user")
        
    return [search_knowledge_base]