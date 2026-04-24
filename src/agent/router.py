from pydantic import BaseModel, Field
from typing import List
from src.agent.utils import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

class MemoryRouteOptions(BaseModel):
    """Routing decisions for memory."""
    use_redis: bool = Field(description="True if the user is asking about or sharing personal preferences, profile info, or long-term facts.")
    use_chroma: bool = Field(description="True if the user is asking about specific facts or knowledge discussed previously.")
    use_episodic: bool = Field(description="True if the user is asking about past experiences, specific past interactions, or episodes.")
    
class MemoryRouter:
    """Routes the user's input to determine which memory backends to query."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0).with_structured_output(MemoryRouteOptions)
        self.system_prompt = SystemMessage(content=(
            "You are a routing agent for a multi-memory system. Analyze the user's latest input "
            "and determine which memory systems need to be accessed to generate a good response.\n"
            "- Redis (long-term): user preferences, personal profile, generic user-centric facts.\n"
            "- Chroma (semantic): facts, knowledge, or specific details from past conversations.\n"
            "- Episodic (JSON): past events, what happened in previous conversations, summaries of interactions.\n"
            "You can select more than one memory type if needed."
        ))
        
    def route(self, user_input: str) -> MemoryRouteOptions:
        """Analyze the input and return routing decisions."""
        messages = [
            self.system_prompt,
            HumanMessage(content=user_input)
        ]
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            print(f"Router error: {e}. Defaulting to all memories.")
            return MemoryRouteOptions(use_redis=True, use_chroma=True, use_episodic=True)
