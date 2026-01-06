# Tutorial: Parallel Agents

## Simple Explanation
Run many tools/agents at once with limits on cost and concurrency; combine results for a robust decision.

## Technical Explanation
Fan-out dispatcher batches work under a semaphore (`max_parallel`), enforces budgets and failure-rate thresholds, applies idempotency for instant retries, and aggregates results via vote/rank/best.

Fan out work with guardrails for cost, concurrency, and safety.

Run:
```bash
python samples/25-parallel-agents/parallel_agents_main.py
```

Prerequisites:
- Install from PyPI: `pip install toolweaver`

What you will see:
- Batch processing: 20 receipts in ~0.2s
- Multi-model consensus with majority vote
- Semaphore control batches work (max_parallel)
- Quota protection stops cost bombs
- Idempotency cache makes retries instant

Files:
- [samples/25-parallel-agents/parallel_agents_main.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/parallel_agents_main.py)
- [samples/25-parallel-agents/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/README.md)

---

## Multi-Agent Coordination

When running multiple agents in parallel, you often need to coordinate their results. ToolWeaver provides patterns for combining agent outputs.

### When to Use Parallel Agents

**Use parallel agents when:**
- Multiple agents can work independently (no dependencies)
- You need consensus from multiple models (hedge against errors)
- Speed matters (reduce latency via concurrency)
- You want diverse perspectives (different models/prompts)

**Use sequential agents when:**
- Agents depend on previous results (data pipeline)
- Order matters (validation → execution)
- You need deterministic flow

### Coordination Patterns

**1. Consensus Voting**

Run multiple agents, combine via majority vote:

```python
from collections import Counter

# Execute agents in parallel
results = await execute_agents_parallel([agent1, agent2, agent3])

# Majority vote
votes = Counter([r["category"] for r in results])
winner = votes.most_common(1)[0][0]
```

**2. Best-of-N Selection**

Execute N agents, select highest-quality result:

```python
# Score each result
scored = [(score_quality(r), r) for r in results]

# Select best
best_result = max(scored, key=lambda x: x[0])[1]
```

**3. Ensemble Aggregation**

Combine numerical outputs statistically:

```python
import statistics

# Average predictions
predictions = [r["amount"] for r in results]
final_amount = statistics.mean(predictions)
```

### Advanced Aggregation

For comprehensive aggregation strategies including conflict resolution, weighted voting, and tiebreaker agents, see:

- **How-to Guide:** [Aggregate Agent Results](../how-to/aggregate-agent-results.md) - Voting, best-of-N, ensembles
- **Sample Code:** [17-multi-agent-coordination](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/17-multi-agent-coordination) - Complete coordination patterns
