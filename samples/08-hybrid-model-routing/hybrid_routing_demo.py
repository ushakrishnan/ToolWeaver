"""
Example 08: Hybrid Model Routing

Demonstrates:
- Routing tasks to appropriate models
- Large models for planning
- Small models for execution
- Cost optimization through routing

Use Case:
Optimize cost and performance by routing tasks to appropriate models
"""

import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass

from orchestrator import mcp_tool, search_tools


# ============================================================
# Model Routing Infrastructure
# ============================================================

@dataclass
class ModelRoute:
    """Describes routing for a task."""
    task: str
    model: str
    reason: str
    cost: float
    tokens: int


class HybridRouter:
    """Route tasks to appropriate models."""
    
    @staticmethod
    def analyze_task(task: str) -> ModelRoute:
        """Determine best model for a task."""
        
        # Routing rules
        if any(x in task.lower() for x in ["plan", "strategy", "complex", "reasoning"]):
            return ModelRoute(
                task=task,
                model="GPT-4o",
                reason="Complex reasoning required",
                cost=0.03,
                tokens=5000
            )
        elif any(x in task.lower() for x in ["extract", "parse", "categorize", "validate"]):
            return ModelRoute(
                task=task,
                model="Phi-3",
                reason="Deterministic processing",
                cost=0.0001,
                tokens=500
            )
        else:
            return ModelRoute(
                task=task,
                model="Phi-3",
                reason="Default to fast model",
                cost=0.0001,
                tokens=500
            )


# ============================================================
# Routed Tools
# ============================================================

@mcp_tool(domain="planning", description="Create execution plan")
async def create_plan(problem: str) -> dict:
    """Create high-level plan (uses GPT-4o)."""
    await asyncio.sleep(2.0)
    return {
        "steps": [
            "Step 1: Extract receipt text",
            "Step 2: Parse line items",
            "Step 3: Categorize items",
            "Step 4: Calculate totals"
        ],
        "model": "GPT-4o",
        "cost": 0.03
    }


@mcp_tool(domain="execution", description="Extract text from receipt")
async def extract_text(image_uri: str) -> dict:
    """Extract text (uses Phi-3)."""
    await asyncio.sleep(0.1)
    return {
        "text": "Receipt data",
        "model": "Phi-3",
        "cost": 0.0001
    }


@mcp_tool(domain="execution", description="Parse items from text")
async def parse_items(text: str) -> dict:
    """Parse items (uses Phi-3)."""
    await asyncio.sleep(0.1)
    return {
        "items": [{"name": "Burger", "price": 12.99}],
        "model": "Phi-3",
        "cost": 0.0001
    }


@mcp_tool(domain="execution", description="Categorize items")
async def categorize(items: list) -> dict:
    """Categorize items (uses Phi-3)."""
    await asyncio.sleep(0.1)
    return {
        "categories": {"food": items},
        "model": "Phi-3",
        "cost": 0.0001
    }


# ============================================================
# Main Demo
# ============================================================

async def main():
    print("="*70)
    print("EXAMPLE 08: Hybrid Model Routing")
    print("="*70)
    print()
    
    print("Scenario: Process 100 Receipts")
    print("-" * 70)
    print()
    
    # Approach 1: Large model for everything
    print("Approach 1: Large Model (GPT-4o) for Everything")
    print("  Requests: 100")
    large_cost = 100 * 0.03
    large_time = 100 * 1.2
    print(f"  Cost: ${large_cost:.2f}")
    print(f"  Time: {large_time:.1f}s")
    print()
    
    # Approach 2: Hybrid routing
    print("Approach 2: Hybrid Routing (GPT-4o Planner + Phi-3 Workers)")
    plan_cost = 0.03
    worker_cost = 100 * 4 * 0.0001  # 4 steps per receipt
    total_cost = plan_cost + worker_cost
    hybrid_time = 2.0 + (100 * 4 * 0.05)  # Plan + parallel steps
    
    print(f"  Planning: 1 × GPT-4o = ${plan_cost:.2f}")
    print(f"  Execution: 400 × Phi-3 = ${worker_cost:.2f}")
    print(f"  Total cost: ${total_cost:.2f}")
    print(f"  Time: {hybrid_time:.1f}s")
    print()
    
    # Comparison
    savings = large_cost - total_cost
    savings_pct = (savings / large_cost) * 100
    speedup = large_time / hybrid_time
    
    print("Comparison:")
    print(f"  Cost savings: ${savings:.2f} ({savings_pct:.1f}%)")
    print(f"  Time speedup: {speedup:.1f}x faster")
    print()
    
    # Routing decisions
    print("Routing Decisions:")
    print("-" * 70)
    
    router = HybridRouter()
    
    tasks = [
        "Create execution plan for processing",
        "Extract text from receipt image",
        "Parse line items from text",
        "Categorize items into groups",
        "Validate totals and amounts",
        "Handle complex edge case",
    ]
    
    total_route_cost = 0.0
    large_model_count = 0
    small_model_count = 0
    
    for task in tasks:
        route = router.analyze_task(task)
        total_route_cost += route.cost
        
        if route.model == "GPT-4o":
            large_model_count += 1
        else:
            small_model_count += 1
        
        print(f"\n  Task: {task}")
        print(f"    → Model: {route.model}")
        print(f"    → Reason: {route.reason}")
        print(f"    → Cost: ${route.cost:.4f}")
    
    print()
    print()
    print("="*70)
    print("ROUTING SUMMARY")
    print("="*70)
    print()
    print(f"  Large Models (GPT-4o):   {large_model_count} tasks")
    print(f"  Small Models (Phi-3):    {small_model_count} tasks")
    print(f"  Cost per workflow:       ${total_route_cost:.4f}")
    print()
    
    # Show tool discovery
    print("Available Tools:")
    print("-" * 70)
    tools = search_tools()
    by_domain = {}
    for tool in tools:
        domain = tool.domain or "uncategorized"
        if domain not in by_domain:
            by_domain[domain] = 0
        by_domain[domain] += 1
    
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain:15} - {count} tools")
    print()
    
    print("="*70)
    print("✓ Hybrid routing demonstration complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
