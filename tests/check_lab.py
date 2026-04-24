import os
import sys
import json
import inspect
from typing import Dict, Any

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_section(title: str):
    print(f"\n{'='*50}")
    print(f" {title} ")
    print(f"{'='*50}")

def check_full_memory_stack() -> int:
    """Check for 4 memory backends/interfaces."""
    print_section("1. Full Memory Stack (Max: 25)")
    score = 0
    
    memory_files = [
        ("short_term.py", "ShortTermMemory"),
        ("long_term_redis.py", "LongTermMemoryRedis"),
        ("episodic_json.py", "EpisodicMemoryJSON"),
        ("semantic_chroma.py", "SemanticMemoryChroma")
    ]
    
    found = 0
    for file, cls in memory_files:
        path = os.path.join("src", "memory", file)
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                if f"class {cls}" in content:
                    found += 1
                    print(f"✅ Found {cls} in {file}")
                else:
                    print(f"❌ Found {file} but class {cls} is missing.")
        else:
            print(f"❌ Missing file: {path}")
            
    if found == 4:
        score = 25
    elif found >= 3:
        score = 15
    elif found > 0:
        score = 5
        
    print(f"Score for Section 1: {score}/25")
    return score

def check_langgraph_router_state() -> int:
    """Check LangGraph state, router, and prompt injection."""
    print_section("2. LangGraph state/router + prompt injection (Max: 30)")
    score = 0
    
    path = os.path.join("src", "agent", "graph.py")
    if not os.path.exists(path):
        print("❌ Could not find src/agent/graph.py")
        return 0
        
    with open(path, 'r') as f:
        content = f.read()
        
    if "class AgentState" in content or "AgentState(" in content:
        print("✅ Found AgentState")
        if "messages" in content and ("budget_breakdown" in content or "memory_hit_rate" in content):
            print("✅ AgentState contains messages and memory tracking")
            score += 10
        else:
            print("❌ AgentState is missing core tracking fields")
    else:
        print("❌ AgentState not found")
        
    if "route_memory" in content and "retrieve_memory" in content:
        print("✅ Found route_memory and retrieve_memory nodes in graph")
        score += 10
    else:
        print("❌ Graph missing routing/retrieval nodes")
        
    # Check prompt injection in context manager
    cm_path = os.path.join("src", "agent", "context_manager.py")
    if os.path.exists(cm_path):
        with open(cm_path, 'r') as f:
            cm_content = f.read()
            if "RETRIEVED MEMORY CONTEXT" in cm_content and "budget_breakdown" in cm_content:
                print("✅ Context window manager handles prompt injection and budget")
                score += 10
            else:
                print("❌ Context manager missing explicit injection or budgeting")
    
    print(f"Score for Section 2: {score}/30")
    return score

def check_save_conflict_handling() -> int:
    """Check if memory saves handle conflict correctly."""
    print_section("3. Save/update memory + conflict handling (Max: 15)")
    score = 0
    
    # We will try to simulate a conflict update
    try:
        # Check if the code has LLM extraction logic or hardcoded
        path = os.path.join("src", "agent", "graph.py")
        has_llm_extract = False
        with open(path, 'r') as f:
            content = f.read()
            if "with_structured_output" in content and "save_memory" in content:
                has_llm_extract = True
                
        if has_llm_extract:
            print("✅ Detected advanced LLM extraction logic for conflict handling")
            score = 15
        else:
            print("⚠️ Detected heuristic/basic save_memory without LLM conflict resolution.")
            print("⚠️ The test: 'Tôi dị ứng sữa bò. À nhầm, đậu nành' will likely fail.")
            score = 5 # Minimum points for at least having a save_memory node
            
    except Exception as e:
        print(f"❌ Error during conflict check: {e}")
        
    print(f"Score for Section 3: {score}/15")
    return score

def check_benchmark() -> int:
    """Check benchmark of 10 multi-turn conversations."""
    print_section("4. Benchmark 10 multi-turn conversations (Max: 20)")
    score = 0
    
    # Check data file
    if os.path.exists("data/conversations.json"):
        with open("data/conversations.json", "r") as f:
            data = json.load(f)
            if len(data) == 10:
                print("✅ Found exactly 10 conversations in data/conversations.json")
                score += 10
            else:
                print(f"❌ Found {len(data)} conversations instead of 10.")
    else:
        print("❌ data/conversations.json not found")
        
    # Check report
    if os.path.exists("benchmark_report.md"):
        with open("benchmark_report.md", "r") as f:
            content = f.read()
            if "Baseline (No Memory)" in content and "Multi-Memory Agent" in content:
                print("✅ Found benchmark_report.md with baseline comparison")
                score += 10
            else:
                print("❌ benchmark_report.md missing 'no-memory vs with-memory' comparison")
    else:
        print("❌ benchmark_report.md not found")
        
    print(f"Score for Section 4: {score}/20")
    return score

def check_reflection() -> int:
    """Check for reflection on privacy and limitations."""
    print_section("5. Reflection privacy/limitations (Max: 10)")
    score = 0
    
    # Usually in README.md or a separate REFLECTION.md
    files_to_check = ["README.md", "REFLECTION.md", "benchmark_report.md"]
    found_reflection = False
    
    for file in files_to_check:
        if os.path.exists(file):
            with open(file, "r") as f:
                content = f.read().lower()
                if "privacy" in content or "rủi ro" in content or "risk" in content or "pii" in content:
                    if "limitation" in content or "hạn chế" in content or "fail" in content:
                        found_reflection = True
                        print(f"✅ Found privacy and limitation reflection in {file}")
                        score = 10
                        break
                        
    if not found_reflection:
        print("❌ Reflection on privacy/limitations not found in README.md, REFLECTION.md or benchmark_report.md")
        
    print(f"Score for Section 5: {score}/10")
    return score

def run_tests():
    total_score = 0
    total_score += check_full_memory_stack()
    total_score += check_langgraph_router_state()
    total_score += check_save_conflict_handling()
    total_score += check_benchmark()
    total_score += check_reflection()
    
    print_section("FINAL GRADING SUMMARY")
    print(f"Total Points: {total_score}/100")
    
    if total_score >= 80:
        print("Band: TỐT (Good) - Meets all core requirements.")
    elif total_score >= 50:
        print("Band: TRUNG BÌNH (Average) - Has architecture but weak on benchmark/saves.")
    else:
        print("Band: KÉM (Poor) - Missing full stack, router, or major requirements.")

if __name__ == "__main__":
    run_tests()
