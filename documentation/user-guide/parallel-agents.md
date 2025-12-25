# Parallel Agent Patterns

Guide to implementing parallel agent orchestration patterns with ToolWeaver.

## Overview

ToolWeaver supports multiple patterns for parallel agent execution:
- **Fan-Out**: Dispatch to many agents in parallel
- **Tree-Based**: Recursive tree of agent delegations
- **Pipeline**: Sequential agent chain with parallel branches
- **Fan-In**: Gather results from parallel agents

## Pattern 1: Fan-Out (Map-Reduce)

Distribute work across many agents, collect results.

```python
from orchestrator import A2AClient, AgentDelegationRequest
import asyncio

async def fan_out_processing(items: list, agent_ids: list):
    """Process items in parallel using multiple agents."""
    client = A2AClient()
    
    # Create delegation requests
    tasks = []
    for i, item in enumerate(items):
        agent_id = agent_ids[i % len(agent_ids)]
        request = AgentDelegationRequest(
            agent_id=agent_id,
            task="process_item",
            context={"item": item},
            timeout=30,
        )
        tasks.append(client.delegate(request))
    
    # Execute in parallel
    results = await asyncio.gather(*tasks)
    return results
```

**Use Cases:**
- Batch processing
- Map-reduce algorithms
- Parallel data transformation

**Cost Calculation:**
- Sequential: N × T (time × agents)
- Parallel: T × log(N) (constant + communication)
- Breakeven: ~10-20ms per task

## Pattern 2: Tree-Based Recursion

Recursive tree of agents for divide-and-conquer algorithms.

```python
async def tree_sort(array: list, depth: int = 0, max_depth: int = 2):
    """Sort using recursive agent tree."""
    if len(array) <= 1 or depth >= max_depth:
        return sorted(array)  # Base case: sequential sort
    
    # Partition
    pivot = array[len(array) // 2]
    left = [x for x in array if x < pivot]
    right = [x for x in array if x >= pivot]
    
    # Delegate subtasks to agents in parallel
    left_task = delegate_sort(left, depth + 1)
    right_task = delegate_sort(right, depth + 1)
    
    left_result, right_result = await asyncio.gather(left_task, right_task)
    return left_result + right_result
```

**Use Cases:**
- Quicksort, merge sort
- Binary search
- Tree algorithms (DFS, BFS)

**Cost Analysis:**
- Time: O(log N) depth × parallelism factor
- Cost: O(N) agent calls (one per leaf)

## Pattern 3: Pipeline with Branches

Sequential pipeline with parallel branches at key points.

```python
async def pipeline_with_branches(item):
    """Process through pipeline with parallel enrichment."""
    client = A2AClient()
    
    # Step 1: Sequential (validation)
    validated = await client.delegate(AgentDelegationRequest(
        agent_id="validator",
        task="validate",
        context={"item": item}
    ))
    
    # Step 2: Parallel branches (enrichment)
    enrichment_tasks = [
        client.delegate(AgentDelegationRequest(
            agent_id=agent_id,
            task="enrich",
            context={"item": validated}
        ))
        for agent_id in ["enricher_1", "enricher_2", "enricher_3"]
    ]
    enrichments = await asyncio.gather(*enrichment_tasks)
    
    # Step 3: Sequential (aggregation)
    final = await client.delegate(AgentDelegationRequest(
        agent_id="aggregator",
        task="combine",
        context={"enrichments": enrichments}
    ))
    
    return final
```

**Use Cases:**
- Data enrichment pipelines
- Multi-stage processing
- Parallel validation chains

## Pattern 4: Fan-In (Reduce)

Gather results from parallel agents into single result.

```python
async def fan_in_aggregation(sources: list):
    """Collect from parallel sources and aggregate."""
    client = A2AClient()
    
    # Parallel collection
    results = await asyncio.gather(
        *[
            client.delegate(AgentDelegationRequest(
                agent_id="collector",
                task="fetch",
                context={"source": src}
            ))
            for src in sources
        ]
    )
    
    # Aggregate (can also be parallel)
    aggregation = await client.delegate(AgentDelegationRequest(
        agent_id="aggregator",
        task="combine",
        context={"results": results}
    ))
    
    return aggregation
```

**Use Cases:**
- Data aggregation
- Consensus collection
- Report generation

## Cost Calculation Best Practices

### Sequential Cost
```
cost_seq = agent_cost × num_tasks
```

### Parallel Cost
```
cost_par = agent_cost × num_agents × (1 + overhead_factor)
```

Where `overhead_factor` accounts for:
- Coordination (5-10%)
- Network (2-5%)
- Duplicate work (varies)

### Break-Even Analysis

Parallel is worthwhile when:
```
speedup_factor > cost_multiplier
```

Example:
- Sequential: 4 agents × 100ms = $0.40
- Parallel: 4 agents × 30ms = $0.12 (assuming parallel overhead)
- Speedup: 3.3x
- Cost: 0.3x (70% savings!)

## Error Handling in Parallel Patterns

### Partial Failure Recovery

```python
from orchestrator.selection.registry import ErrorRecoveryPolicy, ErrorStrategy

policy = ErrorRecoveryPolicy(
    strategy=ErrorStrategy.FALLBACK,
    fallback_tools=["backup_agent"],
    max_retries=2,
)

# Will retry or fallback on failure
result = await executor.execute_with_recovery(
    delegation_request,
    policy=policy
)
```

### All-or-Nothing Pattern

```python
async def all_or_nothing(requests: list):
    """Fail if any agent fails."""
    try:
        results = await asyncio.gather(
            *[process_request(r) for r in requests],
            return_exceptions=False  # Raise on any failure
        )
    except Exception as e:
        # Rollback or cleanup
        await cleanup()
        raise
    
    return results
```

### Partial Success Pattern

```python
async def partial_success(requests: list):
    """Accept partial results."""
    results = await asyncio.gather(
        *[process_request(r) for r in requests],
        return_exceptions=True  # Capture exceptions as results
    )
    
    # Process successes and failures
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    
    return {
        "results": successes,
        "errors": failures,
        "success_rate": len(successes) / len(results)
    }
```

## Performance Tips

### 1. Batch Size Tuning
- Small batches: More parallelism, higher coordination overhead
- Large batches: Better amortization, less parallelism
- Optimal: 10-100 items per agent

### 2. Agent Pool Sizing
```python
# Rule of thumb
num_agents = min(cpu_cores * 2, num_tasks / 10)
```

### 3. Timeout Strategy
```python
# Sequential timeout
timeout_seq = task_time × num_tasks + buffer

# Parallel timeout
timeout_par = max(task_time × log(num_tasks), min_timeout) + buffer
```

### 4. Monitoring
```python
# Track metrics
metrics = {
    "total_time": end - start,
    "agent_count": len(agent_ids),
    "parallelism_factor": tasks / agents,
    "cost": total_cost,
    "success_rate": successes / total
}
```

## When NOT to Parallelize

- Small tasks (<10ms)
- Sequential dependencies
- Tight latency budgets (<100ms)
- High coordination overhead
- Memory-constrained environments

## When to Parallelize

- Large batch processing
- Independent tasks
- High-latency tasks (>100ms)
- Cost savings > overhead
- Distributed infrastructure  

## Examples

See `examples/28-quicksort-orchestration/` for complete working example.

## References

- [A2A Client API](../../docs/reference/a2a-client.md)
- [Cost Optimization Guide](./cost_aware_selection.md)
- [Error Recovery Guide](./error_recovery.md)
