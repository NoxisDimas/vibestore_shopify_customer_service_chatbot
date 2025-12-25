import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from app.services.shopify.controllers import ShopifyController

logger = logging.getLogger(__name__)
def create_order_lookup_tools(controller: ShopifyController) -> List[BaseTool]:
    """Create tools for looking up orders in Shopify."""
    
    @tool()
    def order_lookup(
        order_id: str,
    ) -> str:
        """
            Order Lookup

            Searches for orders in the Shopify database by ID or order number.
            Retrieves details such as customer information, items purchased, total amount,
            and order status.
            To use this tool, you must first request the order ID from the user. After obtaining the order ID, use the order ID as an argument when calling this tool.

            Arguments:
            order_id (string): Unique identifier or order number.

            Returns:
            string: JSON string containing the order details.

            Example:
            Agent call: order_lookup(order_id="#1001")
        """
        try:
            logger.info(f"Tool order_lookup called with order_id: {order_id}")
            response = controller.order_lookup(order_id)
            logger.info(f"Tool order_lookup returning order: {response}")
            results = []
            for r in response:
                logger.info(f"Product found: {r}")
                res = r.model_dump_json()
                results.append(res)
            return "[" + ",".join(results) + "]"
        
        except Exception as e:
            logger.exception("Error looking up order in Shopify", exc_info=e)
            raise ToolException(f"Error looking up order: {str(e)}")
    
    return [order_lookup]