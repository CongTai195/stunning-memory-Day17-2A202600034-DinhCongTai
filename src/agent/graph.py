from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

from src.memory.short_term import ShortTermMemory
from src.memory.long_term_redis import LongTermMemoryRedis
from src.memory.episodic_json import EpisodicMemoryJSON
from src.memory.semantic_chroma import SemanticMemoryChroma
from src.agent.router import MemoryRouter, MemoryRouteOptions
from src.agent.context_manager import ContextManager
from src.agent.utils import get_llm

class Fact(BaseModel):
    key: str = Field(description="The category of the fact, e.g., 'allergy', 'name', 'profession'")
    value: str = Field(description="The value of the fact")

class ProfileUpdate(BaseModel):
    """Extracted facts to update the user's long-term profile."""
    extracted_facts: List[Fact] = Field(
        description="A list of updated or new facts about the user. If the user contradicts an old fact, output the NEW updated value. If there are no facts to extract, output an empty list."
    )

class AgentState(TypedDict):
    user_id: str
    messages: List[BaseMessage]
    route_options: MemoryRouteOptions
    retrieved_context: str
    budget_breakdown: Dict[str, int]
    memory_hit_rate: Dict[str, bool] # To track which memories actually returned data
    
class MultiMemoryAgent:
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        
        # Initialize memory backends
        self.short_term = ShortTermMemory(k=5)
        self.long_term = LongTermMemoryRedis(user_id=user_id)
        self.episodic = EpisodicMemoryJSON()
        self.semantic = SemanticMemoryChroma()
        
        # Components
        self.router = MemoryRouter()
        self.context_manager = ContextManager(max_tokens=4000)
        self.llm = get_llm(temperature=0.7)
        
        # Build Graph
        builder = StateGraph(AgentState)
        builder.add_node("route_memory", self.route_memory)
        builder.add_node("retrieve_memory", self.retrieve_memory)
        builder.add_node("generate_response", self.generate_response)
        builder.add_node("save_memory", self.save_memory)
        
        builder.add_edge(START, "route_memory")
        builder.add_edge("route_memory", "retrieve_memory")
        builder.add_edge("retrieve_memory", "generate_response")
        builder.add_edge("generate_response", "save_memory")
        builder.add_edge("save_memory", END)
        
        self.graph = builder.compile()
        self.system_prompt = SystemMessage(content="You are a helpful AI assistant with a multi-layered memory system. Use the provided context to answer the user's queries.")
        
    def route_memory(self, state: AgentState):
        """Analyze input to decide which memories to query."""
        last_message = state["messages"][-1].content if state["messages"] else ""
        route_opts = self.router.route(last_message)
        return {"route_options": route_opts}
        
    def retrieve_memory(self, state: AgentState):
        """Fetch from selected backends."""
        route_opts = state.get("route_options", MemoryRouteOptions(use_redis=True, use_chroma=True, use_episodic=True))
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        redis_data = {}
        chroma_data = []
        episodic_data = []
        hits = {"redis": False, "chroma": False, "episodic": False}
        
        if route_opts.use_redis:
            redis_data = self.long_term.get_all()
            if redis_data: hits["redis"] = True
            
        if route_opts.use_chroma:
            chroma_data = self.semantic.search(last_message, n_results=3)
            if chroma_data: hits["chroma"] = True
            
        if route_opts.use_episodic:
            episodic_data = self.episodic.get_episodes(self.user_id, limit=3)
            if episodic_data: hits["episodic"] = True
            
        context_str = self.context_manager.format_retrieved_context(redis_data, chroma_data, episodic_data)
        
        return {
            "retrieved_context": context_str,
            "memory_hit_rate": hits
        }
        
    def generate_response(self, state: AgentState):
        """Trim context, assemble messages, and call LLM."""
        context_str = state.get("retrieved_context", "")
        
        final_messages, breakdown = self.context_manager.assemble_context(
            self.system_prompt,
            state["messages"],
            context_str,
            recent_k=self.short_term.k * 2
        )
        
        response = self.llm.invoke(final_messages)
        
        # Append the new AI message to the original message list
        new_messages = state["messages"] + [response]
        
        return {
            "messages": new_messages,
            "budget_breakdown": breakdown
        }
        
    def save_memory(self, state: AgentState):
        """Extract and save new information to backends."""
        messages = state["messages"]
        if len(messages) >= 2:
            last_human = messages[-2].content
            last_ai = messages[-1].content
            
            # LLM-based profile extraction for conflict resolution
            extractor_llm = self.llm.with_structured_output(ProfileUpdate)
            existing_profile = self.long_term.get_all()
            
            prompt = f"""
            Analyze the user's latest message and extract any new or updated personal facts or preferences.
            Existing profile: {existing_profile}
            User message: {last_human}
            
            If the user corrects or updates a fact (e.g., 'Ah actually I am allergic to soy, not cow milk'), ensure the new value overrides the old one.
            Return the dictionary of updated facts. If nothing to update, return an empty dict.
            """
            
            try:
                update_result = extractor_llm.invoke([HumanMessage(content=prompt)])
                if update_result and update_result.extracted_facts:
                    for fact in update_result.extracted_facts:
                        self.long_term.set(fact.key, fact.value)
            except Exception as e:
                print(f"Memory extraction failed: {e}")
                
            # Always save to episodic log
            episode_text = f"User: {last_human}\nAI: {last_ai}"
            self.episodic.add_episode(self.user_id, episode_text)
            
            # Save to semantic memory
            self.semantic.add_memory(episode_text, metadata={"user_id": self.user_id})
            
        return {}
