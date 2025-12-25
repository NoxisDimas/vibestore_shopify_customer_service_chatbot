import logging
from typing import List
from langchain.agents.middleware import (
    AgentMiddleware,
    hook_config
)

logger = logging.getLogger(__name__)

class ContentFilterMiddleware(AgentMiddleware):
    
    def __init__(self, banned_keywords:List[str]):
        super().__init__()
        self.banned_keywords = [kw.lower() for kw in banned_keywords]

    @hook_config(can_jump_to="end")
    def before_agent(self, state, runtime):
        if not state["messages"]:
            return None
        
        first_messages = state["messages"][0]
        if first_messages.type != "human":
            return None
        
        content = first_messages.content.lower()

        for keyword in self.banned_keywords:
            if keyword in content:
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I cannot process requests containing inappropriate content. Please rephrase your request."
                    }],
                    "jump_to": "end"
                }
            
        return None