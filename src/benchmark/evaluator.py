import json
import time
import sys
import os
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import HumanMessage
from src.agent.graph import MultiMemoryAgent, AgentState
from src.agent.utils import get_llm
from pydantic import BaseModel, Field

class EvaluationScore(BaseModel):
    score: int = Field(description="Score from 1 to 5 on how relevant and correct the response is based on the expected recall.")
    reasoning: str = Field(description="Reasoning for the score.")

def evaluate_relevance(llm, expected: str, actual: str) -> int:
    """Use LLM as a judge to score response relevance (1-5)."""
    eval_llm = llm.with_structured_output(EvaluationScore)
    prompt = f"Expected answer: {expected}\nActual answer: {actual}\nScore the actual answer from 1 to 5 based on how well it matches the expected answer."
    try:
        result = eval_llm.invoke([HumanMessage(content=prompt)])
        return result.score
    except Exception as e:
        print(f"Evaluation error: {e}")
        return 1

def run_benchmark(data_path: str = "data/conversations.json"):
    with open(data_path, 'r') as f:
        conversations = json.load(f)
        
    llm = get_llm(temperature=0)
    results = {
        "baseline": {"relevance_scores": [], "average_score": 0},
        "multi_memory": {
            "relevance_scores": [], 
            "average_score": 0, 
            "memory_hits": {"redis": 0, "chroma": 0, "episodic": 0},
            "token_budget_avg": {
                "system_prompt": 0,
                "retrieved_context": 0,
                "older_messages": 0,
                "recent_messages": 0,
                "total": 0
            }
        }
    }
    
    total_recall_questions = 0
    token_stats_count = 0
    
    for idx, conv in enumerate(conversations):
        print(f"Running conversation {idx+1}/{len(conversations)}: {conv['description']}")
        
        user_id = f"user_{idx}"
        agent = MultiMemoryAgent(user_id=user_id)
        
        # Phase 1: Ingestion
        # We run the first few turns to populate memory
        state: AgentState = {
            "user_id": user_id,
            "messages": [],
            "route_options": None,
            "retrieved_context": "",
            "budget_breakdown": {},
            "memory_hit_rate": {}
        }
        
        for turn in conv["turns"]:
            if "expected_facts" in turn:
                # Ingestion turn
                state["messages"].append(HumanMessage(content=turn["user"]))
                state = agent.graph.invoke(state)
                # Ensure we have the AI message in state
                
        # Phase 2: Recall (New Session to simulate time passing and short-term memory clearing)
        # Baseline agent (No external memory, just empty state)
        for turn in conv["turns"]:
            if "expected_recall" in turn:
                total_recall_questions += 1
                query = turn["user"]
                expected = turn["expected_recall"]
                
                # --- Baseline ---
                baseline_messages = [HumanMessage(content=query)]
                baseline_response = llm.invoke([agent.system_prompt] + baseline_messages)
                baseline_score = evaluate_relevance(llm, expected, baseline_response.content)
                results["baseline"]["relevance_scores"].append(baseline_score)
                
                # --- Multi-Memory Agent ---
                # We start a new state to simulate a new session, relying entirely on external memory
                recall_state: AgentState = {
                    "user_id": user_id,
                    "messages": [HumanMessage(content=query)],
                    "route_options": None,
                    "retrieved_context": "",
                    "budget_breakdown": {},
                    "memory_hit_rate": {}
                }
                
                final_state = agent.graph.invoke(recall_state)
                actual_response = final_state["messages"][-1].content
                memory_score = evaluate_relevance(llm, expected, actual_response)
                results["multi_memory"]["relevance_scores"].append(memory_score)
                
                # Record metrics
                hits = final_state.get("memory_hit_rate", {})
                for k, v in hits.items():
                    if v: results["multi_memory"]["memory_hits"][k] += 1
                    
                budget = final_state.get("budget_breakdown", {})
                if budget:
                    token_stats_count += 1
                    results["multi_memory"]["token_budget_avg"]["system_prompt"] += budget.get("system_prompt_tokens", 0)
                    results["multi_memory"]["token_budget_avg"]["retrieved_context"] += budget.get("retrieved_context_tokens", 0)
                    results["multi_memory"]["token_budget_avg"]["older_messages"] += budget.get("older_messages_tokens", 0)
                    results["multi_memory"]["token_budget_avg"]["recent_messages"] += budget.get("recent_messages_tokens", 0)
                    results["multi_memory"]["token_budget_avg"]["total"] += budget.get("total_tokens", 0)
                    
        # Clean up memory for the next conversation just in case, though user_ids differ
        agent.long_term.clear()
        agent.semantic.clear()
        agent.episodic.clear(user_id)
        
    # Average scores
    if total_recall_questions > 0:
        results["baseline"]["average_score"] = sum(results["baseline"]["relevance_scores"]) / total_recall_questions
        results["multi_memory"]["average_score"] = sum(results["multi_memory"]["relevance_scores"]) / total_recall_questions
        
    if token_stats_count > 0:
        for k in results["multi_memory"]["token_budget_avg"]:
            results["multi_memory"]["token_budget_avg"][k] /= token_stats_count
            
    with open("data/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Benchmarking complete. Results saved to data/benchmark_results.json")
    return results

if __name__ == "__main__":
    run_benchmark()
