# execute_plan

## Simple Explanation
Execute a workflow plan (DAG) created by LargePlanner using configured workers and track results.

## Technical Explanation
`execute_plan` is the Phase 1.10 runtime orchestrator that takes an `ExecutionPlan` (created by `LargePlanner`) and executes it step-by-step, respecting dependencies, managing parallelism, and collecting results. It's designed to work with `SmallModelWorker` for cost-efficient execution.

**Import Path**
```python
from orchestrator import execute_plan
```

**Signature**
```python
async def execute_plan(
    plan: ExecutionPlan,
    worker: SmallModelWorker | None = None,
    context: dict[str, Any] | None = None,
    limits: ResourceLimits | None = None,
    track_cost: bool = True
) -> dict[str, Any]:
    ...
```

## When to Use
- **Two-Model Architecture**: Execute plans from LargePlanner with small models
- **Workflow Execution**: Run multi-step workflows with dependency management
- **Parallel Processing**: Automatically execute independent steps in parallel
- **Cost Tracking**: Monitor execution cost and resource usage

## Parameters
- `plan`: ExecutionPlan from LargePlanner
- `worker`: SmallModelWorker for tool execution (defaults to GPT-4o-mini)
- `context`: Input data available to all steps (e.g., `{"receipt": text}`)
- `limits`: ResourceLimits for execution (memory, timeout, cost)
- `track_cost`: Whether to track and return cost metrics

## Return Value
```python
{
    "result": <final output>,
    "steps": [<step results>],
    "cost": 0.024,
    "latency_ms": 450,
    "steps_completed": 5,
    "parallel_efficiency": 0.78
}
```

## Examples

### Basic Execution
```python
from orchestrator import LargePlanner, SmallModelWorker, execute_plan

# Step 1: Create plan
planner = LargePlanner(model="gpt-4o")
plan = await planner.create_plan(
    task="Extract receipt fields and categorize",
    tools=tool_catalog
)

# Step 2: Execute plan
worker = SmallModelWorker(model="gpt-4o-mini")
result = await execute_plan(
    plan=plan,
    worker=worker,
    context={"receipt_text": text}
)

print(f"Result: {result['result']}")
print(f"Cost: ${result['cost']:.4f}")
print(f"Latency: {result['latency_ms']}ms")
```

### With Resource Limits
```python
from orchestrator import execute_plan, ResourceLimits

# Enforce strict limits
limits = ResourceLimits(
    timeout_seconds=30,
    max_tool_calls=20,
    max_total_cost_usd=0.10
)

result = await execute_plan(
    plan=plan,
    worker=worker,
    context=context,
    limits=limits
)

# Execution stops if limits exceeded
if result.get("exceeded_limits"):
    print(f"Stopped: {result['exceeded_limits']}")
```

### Batch Processing
```python
from orchestrator import LargePlanner, SmallModelWorker, execute_plan

# Create plan once
planner = LargePlanner(model="gpt-4o")
plan = await planner.create_plan(
    task="Process receipt: extract + categorize + validate",
    tools=tool_catalog
)

# Execute plan for many receipts
worker = SmallModelWorker(model="gpt-4o-mini")
results = []

for receipt_text in receipts:
    result = await execute_plan(
        plan=plan,
        worker=worker,
        context={"receipt": receipt_text}
    )
    results.append(result)

# Cost efficiency: 1 plan × $0.05 + 100 executions × $0.0006 = $0.11
# vs all GPT-4: 100 × $0.09 = $9.00
print(f"Total cost: ${sum(r['cost'] for r in results):.2f}")
```

### Parallel Execution
```python
from orchestrator import execute_plan
import asyncio

# Plan with parallel steps
# Step 1: extract (sequential)
# Step 2a, 2b, 2c: validate, categorize, check (parallel)
# Step 3: save (sequential)

result = await execute_plan(plan=plan, worker=worker, context=context)

# Execution automatically parallelizes steps 2a, 2b, 2c
# Latency: ~400ms (vs ~1200ms if sequential)
print(f"Parallel efficiency: {result['parallel_efficiency']:.1%}")
```

### Error Handling
```python
from orchestrator import execute_plan

try:
    result = await execute_plan(plan=plan, worker=worker, context=context)
except TimeoutError:
    print("Execution exceeded timeout")
except ResourceLimitError as e:
    print(f"Resource limit exceeded: {e}")
except ToolExecutionError as e:
    print(f"Tool failed: {e.tool_name} - {e.error}")
```

### Cost Tracking
```python
from orchestrator import execute_plan

result = await execute_plan(
    plan=plan,
    worker=worker,
    context=context,
    track_cost=True
)

# Detailed cost breakdown
print(f"Total cost: ${result['cost']:.4f}")
print(f"Cost per step:")
for step in result['steps']:
    print(f"  {step['tool']}: ${step['cost']:.4f}")
```

## Execution Flow

```
Input Context → Step 1 (extract) → Step 2 (categorize) → Step 3 (save) → Result
                                 ↘ Step 2b (validate) ↗
                                   (parallel)
```

1. **Parse Plan**: Load plan and identify dependencies
2. **Topological Sort**: Order steps respecting dependencies
3. **Execute Steps**: Run each step with worker
4. **Manage Parallelism**: Execute independent steps concurrently
5. **Propagate Results**: Pass step outputs to dependent steps
6. **Return Results**: Collect final output and metrics

## Performance

### Sequential (No Parallelism)
```
Step 1 (200ms) → Step 2 (150ms) → Step 3 (100ms) = 450ms total
```

### Parallel (Automatic)
```
Step 1 (200ms) → [Step 2a (150ms), Step 2b (100ms)] → Step 3 (100ms) = 350ms total
                  (parallel)
```

**Parallel Efficiency**: 450ms / 350ms = 1.29x speedup

## Cost Comparison

### Traditional Multi-Round (All GPT-4)
```
LLM call 1 → Tool → LLM call 2 → Tool → LLM call 3 → Tool → Result
Cost: 3 × $0.03 = $0.09 per workflow
```

### Two-Model with execute_plan
```
LargePlanner → execute_plan (SmallModelWorker) → Result
Cost: 1 × $0.05 (planning) + 3 × $0.0002 (execution) = $0.0506 per workflow
```

**Savings**: 78% cheaper (plus 3-5x faster due to no LLM round-trips)

## See Also
- [LargePlanner](LargePlanner.md) — Create execution plans
- [SmallModelWorker](../execution/SmallModelWorker.md) — Execute with small models
- [ResourceLimits](../execution/ResourceLimits.md) — Configure execution limits
- [Sample 02: Receipt Categorization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/02-receipt-with-categorization) — Complete two-model example
- [How to Orchestrate with Code](../../../how-to/orchestrate-with-code.md) — Orchestration guide

## Notes
- Automatically parallelizes independent steps
- Tracks cost per step when `track_cost=True`
- Enforces resource limits during execution
- Caches step results for retry/debugging
- Returns partial results on failure (up to failed step)
- Typical execution: 100-500ms for 3-5 step plans
- Typical cost: $0.0002-0.001 per step with small models
