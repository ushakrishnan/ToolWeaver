"""Example 08: Hybrid Model Routing (Two-Model Architecture)"""
import asyncio
from pathlib import Path
import sys

from orchestrator.hybrid_dispatcher import HybridDispatcher
from orchestrator.small_model_worker import SmallModelWorker
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

async def main():
    print("="*70)
    print(" "*15 + "HYBRID MODEL ROUTING EXAMPLE")
    print("="*70)
    
    print("\nScenario: Process 100 receipts")
    print("-" * 40)
    
    # Approach 1: Large model for everything
    print("\nApproach 1: GPT-4 for Everything")
    large_model_cost = 100 * 0.03
    large_model_time = 100 * 1.2
    print(f"  Requests: 100 × GPT-4")
    print(f"  Cost: ${large_model_cost:.2f}")
    print(f"  Time: {large_model_time:.1f}s")
    
    # Approach 2: Hybrid (1 plan + 100 worker tasks)
    print("\nApproach 2: Hybrid (GPT-4 Planner + Phi-3 Workers)")
    plan_cost = 0.03
    worker_cost = 100 * 0.0001
    total_cost = plan_cost + worker_cost
    hybrid_time = 2.0 + (100 * 0.05)  # Plan + parallel worker execution
    
    print(f"  Planning: 1 × GPT-4 = ${plan_cost:.2f}")
    print(f"  Execution: 100 × Phi-3 = ${worker_cost:.2f}")
    print(f"  Total cost: ${total_cost:.2f}")
    print(f"  Time: {hybrid_time:.1f}s (parallel)")
    
    # Savings
    savings = large_model_cost - total_cost
    savings_pct = (savings / large_model_cost) * 100
    speedup = large_model_time / hybrid_time
    
    print(f"\nSavings:")
    print(f"  Cost: ${savings:.2f} ({savings_pct:.1f}% reduction)")
    print(f"  Time: {speedup:.1f}x faster")
    
    # Routing decisions
    print("\nRouting Decisions:")
    print("-" * 40)
    tasks = [
        ("Create execution plan", "GPT-4", "Complex reasoning required"),
        ("Extract text from receipt", "Phi-3", "Simple OCR parsing"),
        ("Parse line items", "Phi-3", "Pattern matching"),
        ("Categorize items", "Phi-3", "Classification task"),
        ("Validate totals", "Phi-3", "Arithmetic validation"),
        ("Handle edge case", "GPT-4", "Requires complex reasoning"),
    ]
    
    for task, model, reason in tasks:
        symbol = "🧠" if model == "GPT-4" else "⚡"
        print(f"  {symbol} {task:30s} → {model:6s} ({reason})")
    
    print("\n✓ Example completed!")
    print("\nKey Insight:")
    print("  Use expensive models for planning, cheap models for execution")

if __name__ == "__main__":
    asyncio.run(main())
