import sys
import os

# Add project root to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import HumanMessage
from src.agent.graph import MultiMemoryAgent, AgentState

def main():
    print("Initializing Multi-Memory Agent...")
    user_id = "test_user_interactive"
    agent = MultiMemoryAgent(user_id=user_id)
    
    print("\n--- Agent Ready! ---")
    print("Type your message below. Type 'quit' or 'exit' to stop.")
    print("Type '/clear' to clear all memory for this user.\n")
    
    state: AgentState = {
        "user_id": user_id,
        "messages": [],
        "route_options": None,
        "retrieved_context": "",
        "budget_breakdown": {},
        "memory_hit_rate": {}
    }
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
            if user_input.lower() == '/clear':
                agent.long_term.clear()
                agent.episodic.clear(user_id)
                agent.semantic.clear()
                print("--- Memory Cleared ---")
                state["messages"] = []
                continue
                
            if not user_input.strip():
                continue
                
            state["messages"].append(HumanMessage(content=user_input))
            
            # Run graph
            state = agent.graph.invoke(state)
            
            # Print response
            ai_response = state["messages"][-1].content
            print(f"\nAI: {ai_response}")
            
            # Print behind-the-scenes info
            hits = state.get("memory_hit_rate", {})
            active_hits = [k for k, v in hits.items() if v]
            if active_hits:
                print(f"[Memory Hits: {', '.join(active_hits)}]")
            else:
                print(f"[Memory Hits: None]")
                
            print("-" * 30)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")
            break

if __name__ == "__main__":
    main()
