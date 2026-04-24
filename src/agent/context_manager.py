import tiktoken
from typing import List, Dict, Any, Tuple
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

class ContextManager:
    """
    Manages the context window to stay within the token budget.
    Implements a 4-level hierarchy for auto-trimming:
    1. Core System Prompt (Never trim)
    2. Recent short-term messages (High priority)
    3. Retrieved memory context (Medium priority)
    4. Older short-term messages (Lowest priority - trim first)
    """
    
    def __init__(self, max_tokens: int = 4000, model_name: str = "gpt-4o-mini"):
        self.max_tokens = max_tokens
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
        
    def count_message_tokens(self, messages: List[BaseMessage]) -> int:
        # Simplified token counting for messages
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.content)
            total += 4  # overhead per message
        return total
        
    def format_retrieved_context(self, redis_data: Dict, chroma_data: List[Dict], episodic_data: List[Dict]) -> str:
        """Format retrieved memories into a single context string."""
        context_parts = []
        
        if redis_data:
            context_parts.append("User Profile/Preferences:\n" + str(redis_data))
            
        if chroma_data:
            context_parts.append("Relevant Facts:\n" + "\n".join([item["text"] for item in chroma_data]))
            
        if episodic_data:
            context_parts.append("Past Interactions:\n" + "\n".join([item["episode"] for item in episodic_data]))
            
        return "\n\n".join(context_parts)

    def assemble_context(
        self, 
        system_prompt: SystemMessage, 
        messages: List[BaseMessage], 
        retrieved_context_str: str,
        recent_k: int = 4
    ) -> Tuple[List[BaseMessage], Dict[str, int]]:
        """
        Assembles final messages list and trims based on priority.
        Returns the trimmed messages and a budget breakdown.
        """
        # Level 1: System Prompt
        sys_tokens = self.count_message_tokens([system_prompt])
        
        # Level 2: Recent messages (keep up to `recent_k` messages if possible)
        # Note: messages should ideally not contain the system prompt here.
        recent_msgs = messages[-recent_k:] if len(messages) > recent_k else messages
        recent_tokens = self.count_message_tokens(recent_msgs)
        
        # Level 3: Retrieved Context
        context_msg = SystemMessage(content=f"--- RETRIEVED MEMORY CONTEXT ---\n{retrieved_context_str}")
        context_tokens = self.count_message_tokens([context_msg]) if retrieved_context_str else 0
        
        # Level 4: Older messages
        older_msgs = messages[:-recent_k] if len(messages) > recent_k else []
        
        available_budget = self.max_tokens - sys_tokens - recent_tokens - context_tokens
        
        # Trimming logic for Level 4 (older messages)
        trimmed_older_msgs = []
        older_tokens = 0
        
        # Iterate from the end of older messages (most recent among the older ones)
        for msg in reversed(older_msgs):
            msg_tokens = self.count_message_tokens([msg])
            if available_budget - msg_tokens > 0:
                trimmed_older_msgs.insert(0, msg)
                available_budget -= msg_tokens
                older_tokens += msg_tokens
            else:
                break
                
        # If we still exceed budget (which means system + recent + context > max_tokens),
        # we would theoretically need to trim retrieved context next, then recent messages.
        # For simplicity in this lab, we assume system + recent + context fits within the budget.
        
        final_messages = [system_prompt]
        if context_msg.content.strip() and retrieved_context_str:
            final_messages.append(context_msg)
        final_messages.extend(trimmed_older_msgs)
        final_messages.extend(recent_msgs)
        
        budget_breakdown = {
            "system_prompt_tokens": sys_tokens,
            "retrieved_context_tokens": context_tokens,
            "older_messages_tokens": older_tokens,
            "recent_messages_tokens": recent_tokens,
            "total_tokens": sys_tokens + context_tokens + older_tokens + recent_tokens,
            "max_tokens": self.max_tokens
        }
        
        return final_messages, budget_breakdown
