"""
Example 25: Parallel Agents with asyncio

Demonstrates:
- Parallel task execution  
- Resource limits and quotas
- Result ranking and scoring
- Multi-task orchestration

Use Case:
Execute multiple tasks in parallel with controlled resource usage
"""

import asyncio
from typing import List, Dict, Any


# Simulated agent task
async def execute_task(task_id: str, priority: int, delay: float = 0.1) -> dict:
    """Simulate an agent executing a task."""
    await asyncio.sleep(delay)
    
    # Mock score based on priority
    score = priority / 10.0
    
    return {
        "task_id": task_id,
        "priority": priority,
        "output": f"Completed task {task_id}",
        "score": score,
        "cost": 0.01
    }


async def parallel_execute(tasks: List[Dict[str, Any]], max_concurrent: int = 3) -> List[dict]:
    """Execute tasks in parallel with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_execute(task):
        async with semaphore:
            return await execute_task(**task)
    
    return await asyncio.gather(*[bounded_execute(task) for task in tasks])


def rank_by_metric(results: List[dict], metric: str, descending: bool = True) -> List[dict]:
    """Rank results by a metric."""
    return sorted(
        results,
        key=lambda x: x.get(metric, 0),
        reverse=descending
    )


async def main():
    """Run parallel agent demonstration."""
    print("=" * 70)
    print("EXAMPLE 25: Parallel Agents")
    print("=" * 70)
    print()
    
    # Prepare tasks
    print("Step 1: Preparing parallel tasks...")
    tasks = [
        {"task_id": f"task-{i:02d}", "priority": (i % 3) + 1}
        for i in range(5)
    ]
    print(f"  Created {len(tasks)} tasks")
    for task in tasks:
        print(f"    • {task['task_id']} (priority: {task['priority']})")
    print()
    
    # Configure resource limits
    print("Step 2: Configuring resource limits...")
    max_concurrent = 3
    max_total_cost = 1.0
    min_success_count = 3
    max_failure_rate = 0.5
    
    print(f"  Max concurrent: {max_concurrent}")
    print(f"  Max total cost: ${max_total_cost}")
    print(f"  Min success count: {min_success_count}")
    print()
    
    # Execute parallel dispatch
    print("Step 3: Executing tasks in parallel...")
    print("-" * 70)
    
    try:
        results = await parallel_execute(tasks, max_concurrent=max_concurrent)
        
        print(f"  Completed {len(results)} tasks")
        print()
        
        # Rank results
        print("Step 4: Ranking results by score...")
        print("-" * 70)
        
        ranked = rank_by_metric(results, "score", descending=True)
        
        print(f"  Top {min(3, len(ranked))} results:")
        for i, result in enumerate(ranked[:3], 1):
            print(f"    {i}. {result['output']} (score: {result['score']:.3f})")
        print()
        
        # Statistics
        print("Step 5: Dispatch Statistics")
        print("-" * 70)
        total_cost = sum(r['cost'] for r in results)
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0
        
        print(f"  Total results: {len(results)}")
        print(f"  Total cost: ${total_cost:.3f}")
        print(f"  Average score: {avg_score:.3f}")
        print(f"  Success rate: {len(results)}/{len(tasks)} ({100*len(results)//len(tasks)}%)")
        print()
        
    except Exception as e:
        print(f"  Error during execution: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    print("=" * 70)
    print("✓ Parallel execution complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
