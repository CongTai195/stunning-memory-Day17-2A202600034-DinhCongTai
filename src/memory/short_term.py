from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

class ShortTermMemory:
    """
    Manages the short-term conversation buffer.
    In LangGraph, the state already holds the message history.
    This class provides utility functions to interact with the recent conversation buffer.
    """
    
    def __init__(self, k: int = 5):
        """
        Args:
            k: The number of recent turns (Human + AI) to keep in explicit short-term focus.
        """
        self.k = k
        
    def get_recent_messages(self, all_messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        Extracts the `k` most recent turns from the message history.
        Assumes the first message might be a SystemMessage, which should be handled by the context manager.
        """
        # Filter out system messages for this specific calculation if needed, 
        # or just take the last 2*k messages.
        recent = all_messages[-(self.k * 2):] if len(all_messages) > (self.k * 2) else all_messages
        return recent
