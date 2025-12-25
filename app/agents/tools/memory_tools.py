import logging
from typing import List
from langchain_core.tools import BaseTool, ToolException
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from app.services.memory.controller import MemoryController

logger = logging.getLogger(__name__)

def create_memory_tools(controller:MemoryController) -> List[BaseTool]:

    @tool()
    async def read_profile(config: RunnableConfig) -> str:
        """
            Read User Profile Context

            Retrieves summarized context for the user, such as past interactions,
            preferences, and other data stored in memory.

            Args:
                config (RunnableConfig): Contains metadata including user_id.

            Returns:
                str: Summary of user context, or an error if no user_id found.

            Example:
                Called when agent needs user history before responding.
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            return await controller.summarize_user_context(user_id)
        except Exception as e:
            logger.error(f"Error reading profile: {e}")
            return ToolException(f"Error reading profile: {e}")

    @tool()
    async def save_preference(preference: str, config: RunnableConfig) -> str:
        """
            Save User Preference

            Saves a user preference (e.g., favorite product type, communication style).
            This helps personalize future responses.

            Args:
                preference (str): A user preference to save.
                config (RunnableConfig): Contains user_id metadata.

            Returns:
                str: Confirmation message or error.

            Example:
                "Simpan metode pembayaran favorit user"
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            await controller.add_memory(user_id, preference, type="preference")
            return "Preference saved successfully."
        except Exception as e:
            logger.error(f"Error saving preference: {e}")
            return ToolException(f"Error saving preference: {e}")

    @tool()
    async def save_memory(memory: str, config: RunnableConfig) -> str:
        """
            Save General Memory

            Stores an arbitrary memory item for the user, such as facts,
            a note, or any user-specific information.

            Args:
                memory (str): The memory or fact to store.
                config (RunnableConfig): Contains user_id metadata.

            Returns:
                str: Confirmation message or error.

            Example:
                "User tinggal di Bali"
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            await controller.add_memory(user_id, memory, type="memory")
            return "Memory saved successfully."
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return ToolException(f"Error saving memory: {e}")
    
    @tool()
    async def delete_memory(memory_id: str, config: RunnableConfig) -> str:
        """
        Delete General Memory

        Deletes a specific memory item from the user's context.

        Args:
            memory_id (str): The ID of the memory to delete.
            config (RunnableConfig): Contains user_id metadata.

        Returns:
            str: Confirmation message or error.

        Example:
            "Delete memory with ID 123"
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            await controller.delete_memory(user_id, memory_id)
            return "Memory deleted successfully."
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return ToolException(f"Error deleting memory: {e}")

    @tool()
    async def get_memory( config: RunnableConfig) -> str:
        """
            Get One Memory Item

            Fetches one of the stored memory items associated with the user.

            Args:
                config (RunnableConfig): Contains user_id metadata.

            Returns:
                str: A memory item's text or a "not found" message if none exists.

            Example:
                Used by agent to pull a relevant detail before responding.
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            
            items = await controller.get_memory(user_id)
            found = next((m for m in items), None)
            return str(found) if found else "Memory not found."
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return ToolException(f"Error getting memory: {e}")

    @tool()
    async def clear_memory(config: RunnableConfig) -> str:
        """
            Clear All User Memories

            Deletes all memory items tied to the user. Useful for reset
            or privacy/purge requests.

            Args:
                config (RunnableConfig): Contains user_id metadata.

            Returns:
                str: Confirmation or error.

            Example:
                Called when user requests to wipe their stored context.
        """
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return ToolException("Error: No user_id found in context.")
            await controller.clear_memory(user_id)
            return "Memory cleared successfully."
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return ToolException(f"Error clearing memory: {e}")

    return [read_profile, save_preference, save_memory, delete_memory, get_memory, clear_memory]