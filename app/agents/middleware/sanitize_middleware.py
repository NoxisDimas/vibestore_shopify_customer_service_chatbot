from langchain.agents.middleware import AgentMiddleware, hook_config
import re

class ThinkSanitizerMiddleware(AgentMiddleware):

    THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)

    @hook_config()
    def after_agent(self, state, runtime):
        messages = state.get("messages", [])
        if not messages:
            return None

        last = messages[-1]
        if hasattr(last, "content"):
            cleaned = self.THINK_PATTERN.sub("", last.content).strip()
            last.content = cleaned

        return None
