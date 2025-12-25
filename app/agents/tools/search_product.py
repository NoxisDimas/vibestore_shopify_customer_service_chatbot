import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain.tools import tool
from app.services.shopify.controllers import ShopifyController

logger = logging.getLogger(__name__)

def create_search_product_tools(controller: ShopifyController) -> List[BaseTool]:
    """Create tools for searching products in Shopify."""
    
    @tool()
    def search_product(
        query: str,
    ) -> str:
        """
            Search Product

            Searches for products in the Shopify database matching the query.
            The search looks for matches in product name, category, description,
            materials, and available colors. Only active
            products are returned.

            Args:
                query (str): The search query must be a string with english language only.

            Returns:
                str: JSON string containing a list of matching products with details.

            Example:
                Agent calls: search_product(query="red cotton t-shirt")
        """
        try:
            logger.info(f"Tool search_product called with query: {query}")
            response = controller.search_products(query)
            logger.info(f"Tool search_product returning {len(response) if response else 0} results")
            results = []
            for r in response:
                logger.info(f"Product found: {r}")
                res = r.model_dump_json()
                results.append(res)
            return "[" + ",".join(results) + "]"

        
        except Exception as e:
            logger.exception("Error searching products in Shopify", exc_info=e)
            raise ToolException(f"Error searching products: {str(e)}")
    
    return [search_product]