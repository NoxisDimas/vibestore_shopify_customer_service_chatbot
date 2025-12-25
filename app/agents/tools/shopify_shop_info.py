import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain.tools import tool
from app.services.shopify.controllers import ShopifyController

logger = logging.getLogger(__name__)

def create_shopify_shop_info_tools(controller: ShopifyController) -> List[BaseTool]:
    """Create tools for retrieving Shopify store information."""
    
    @tool()
    def get_shop_info() -> str:
        """
            Get Shopify Store Information

            Retrieves the store information from the Shopify database, including
            store name, email, domain, and address.

            Returns:
                str: JSON string containing the store information.

            Example:
                Agent calls: get_shop_info()
        """
        try:
            logger.info("Tool get_shop_info called")
            response = controller.get_shop_info()
            logger.info(f"Tool get_shop_info returning shop info: {response}")
            res_json = response.model_dump_json()
            logger.info(f"Tool get_shop_info returning shop info: {res_json}")
            return res_json
        
        except Exception as e:
            logger.exception("Error retrieving store information from Shopify", exc_info=e)
            raise ToolException(f"Error retrieving store information: {str(e)}")
    
    return [get_shop_info]