import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def generate_report(results_path: str = "data/benchmark_results.json", output_path: str = "benchmark_report.md"):
    if not os.path.exists(results_path):
        print(f"Results file {results_path} not found. Please run evaluator.py first.")
        return
        
    with open(results_path, 'r') as f:
        results = json.load(f)
        
    baseline = results.get("baseline", {})
    multi_memory = results.get("multi_memory", {})
    
    # Calculate Memory Hit Rate
    hits = multi_memory.get("memory_hits", {})
    total_hits = sum(hits.values())
    
    # Generate Markdown
    md = [
        "# Multi-Memory Agent Benchmark Report\n",
        "## 1. Metrics Comparison\n",
        "| Metric | Baseline (No Memory) | Multi-Memory Agent |",
        "|--------|----------------------|--------------------|",
        f"| Average Relevance Score (1-5) | **{baseline.get('average_score', 0):.2f}** | **{multi_memory.get('average_score', 0):.2f}** |",
        "\n*Note: Relevance score is determined by an LLM-as-a-judge evaluating the response against the expected fact.*",
        "\n## 2. Memory Hit Rate Analysis\n",
        "This shows how often each memory backend successfully retrieved relevant context during the recall phase.\n",
        f"- **Redis (Long-term profile):** {hits.get('redis', 0)} hits",
        f"- **Chroma (Semantic facts):** {hits.get('chroma', 0)} hits",
        f"- **JSON (Episodic log):** {hits.get('episodic', 0)} hits\n",
        f"**Total successful memory retrievals:** {total_hits}\n",
        "## 3. Token Budget Breakdown\n",
        "Average token distribution per response generation step when using the Context Window Manager (4-level hierarchy).\n",
        "| Component | Average Tokens | Priority Level |",
        "|-----------|----------------|----------------|",
    ]
    
    budget = multi_memory.get("token_budget_avg", {})
    md.extend([
        f"| System Prompt | {budget.get('system_prompt', 0):.1f} | 1 (Highest) |",
        f"| Recent Messages | {budget.get('recent_messages', 0):.1f} | 2 |",
        f"| Retrieved Context | {budget.get('retrieved_context', 0):.1f} | 3 |",
        f"| Older Messages | {budget.get('older_messages', 0):.1f} | 4 (Trimmed First) |",
        f"| **Total Average Usage** | **{budget.get('total', 0):.1f}** | - |"
    ])
    
    md.append("\n## Conclusion")
    improvement = multi_memory.get('average_score', 0) - baseline.get('average_score', 0)
    md.append(f"The Multi-Memory Agent demonstrated a **{improvement:.2f} point improvement** in relevance scoring compared to the baseline.")
    md.append("This validates the effectiveness of the routing and multi-backend memory strategy.")

    with open(output_path, 'w') as f:
        f.write("\n".join(md))
        
    print(f"Report generated successfully at {output_path}")

if __name__ == "__main__":
    generate_report()
