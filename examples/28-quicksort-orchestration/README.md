# Multi-Agent Quicksort Orchestration

Demonstrates parallel algorithm execution using agent delegation and cost tracking.

## Key Concepts

1. **Parallel Partitioning** - Split sorting tasks across agents
2. **Cost Tracking** - Calculate overhead of parallel execution
3. **Performance Benchmarking** - Compare sequential vs parallel
4. **Decision Making** - When to use parallel patterns

## Run It

```bash
python main.py
```

## What You'll See

- Sequential quicksort execution
- Parallel quicksort using agent delegation
- Performance comparison (speedup factor)
- Cost analysis (overhead calculation)
- Recommendations for when to parallelize

## Key Insights

**When to Parallelize:**
- Task > 10-20ms (overhead amortization)
- Multiple independent subtasks
- Agent cost < speedup benefit

**When NOT to Parallelize:**
- Coordination overhead > speedup
- Sequential faster on small inputs
- Tight latency budgets

## Expected Output

```
Array Size: 1000
Sequential: 0.0042s ($0.0042)
Parallel: 0.0025s ($0.0100)
Speedup: 1.68x
Cost Overhead: +138% (4 agents)
Recommendation: ⚠️ Use for critical tasks only
```

## Learn More

See `docs/user-guide/parallel-agents.md` for detailed patterns.
