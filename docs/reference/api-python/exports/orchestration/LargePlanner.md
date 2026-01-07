# LargePlanner

## Simple Explanation
Create execution plans using large language models (GPT-4, Claude Opus) that break down complex tasks into DAG workflows.

## Technical Explanation
`LargePlanner` uses frontier LLMs to analyze tasks and generate directed acyclic graphs (DAGs) of tool calls. It performs Phase 1.9 planning: decompose the task, identify tool dependencies, and create an execution plan that can be executed by smaller, cheaper models.

**Import Path**
```python
from orchestrator import LargePlanner
```

**Signature**
```python
class LargePlanner:
    def __init__(
        self,
        model: str = "gpt-4o",
        provider: str = "azure-openai",
        temperature: float = 0.2
    ):
        ...
    
    async def create_plan(
        self,
        task: str,
        tools: ToolCatalog,
        context: dict[str, Any] | None = None
    ) -> ExecutionPlan:
        ...
```

## When to Use
- **Complex Workflows**: Multi-step tasks requiring reasoning about dependencies
- **Cost Optimization**: Plan once with GPT-4, execute many times with GPT-4o-mini
- **Two-Model Architecture**: Large model plans, small model executes
- **Workflow Automation**: Generate reusable execution plans

## Key Methods
- `create_plan(task, tools, context)`: Generate execution plan as DAG
- `optimize_plan(plan)`: Optimize plan for parallelism and cost
- `validate_plan(plan)`: Check plan for errors before execution

## Examples

### Basic Planning
```python
from orchestrator import LargePlanner

# Create planner with GPT-4
planner = LargePlanner(
    model="gpt-4o",
    provider="azure-openai",
    temperature=0.2  # Low temperature for consistent plans
)

# Plan a complex task
plan = await planner.create_plan(
    task="Process receipt: extract fields, categorize merchant, calculate tax",
    tools=tool_catalog
)

# Plan structure:
# {
#   "steps": [
#     {"id": 1, "tool": "extract_receipt_fields", "depends_on": []},
#     {"id": 2, "tool": "categorize_merchant", "depends_on": [1]},
#     {"id": 3, "tool": "calculate_tax", "depends_on": [1]}
#   ]
# }
```

### Two-Model Architecture
```python
from orchestrator import LargePlanner, SmallModelWorker, execute_plan

# Step 1: Large model creates plan (expensive, once)
planner = LargePlanner(model="gpt-4o")
plan = await planner.create_plan(
    task="Analyze 100 receipts and generate summary report",
    tools=tool_catalog
)
print(f"Planning cost: ${plan.cost:.3f}")  # ~$0.05

# Step 2: Small model executes plan (cheap, 100 times)
worker = SmallModelWorker(model="gpt-4o-mini")
results = []
for receipt in receipts:
    result = await execute_plan(plan, worker=worker, context={"receipt": receipt})
    results.append(result)

execution_cost = sum(r.get("cost", 0.0002) for r in results)
print(f"Execution cost: ${execution_cost:.3f}")  # ~$0.02

# Total: $0.07 (vs $5.00 if using GPT-4 for everything)
```

### Parallel Execution
```python
from orchestrator import LargePlanner, execute_plan

planner = LargePlanner(model="gpt-4o")

# LLM generates plan with parallel steps
plan = await planner.create_plan(
    task="""
    Process receipt:
    1. Extract fields (merchant, total, date)
    2. In parallel:
       - Categorize merchant
       - Validate total format
       - Check date is recent
    3. Save results
    """,
    tools=tool_catalog
)

# Plan identifies steps 2a, 2b, 2c can run in parallel
# Execution time: ~1/3 of sequential
result = await execute_plan(plan, worker=worker)
```

### Plan Reuse
```python
from orchestrator import LargePlanner
import json

planner = LargePlanner(model="gpt-4o")

# Create plan once
plan = await planner.create_plan(
    task="Extract receipt fields and categorize",
    tools=tool_catalog
)

# Save plan for reuse
with open("receipt_plan.json", "w") as f:
    json.dump(plan.to_dict(), f)

# Later: Load and execute many times
with open("receipt_plan.json", "r") as f:
    plan = ExecutionPlan.from_dict(json.load(f))

for receipt in receipts:
    result = await execute_plan(plan, worker=worker, context={"receipt": receipt})
```

### Context-Aware Planning
```python
from orchestrator import LargePlanner

planner = LargePlanner(model="gpt-4o")

# Provide context to influence planning
plan = await planner.create_plan(
    task="Process receipt",
    tools=tool_catalog,
    context={
        "user_preferences": {"detailed_categorization": True},
        "available_budget": 0.50,
        "max_latency_ms": 2000
    }
)

# LLM adjusts plan based on context:
# - Uses detailed categorization tool (user preference)
# - Limits plan complexity to stay within budget
# - Prefers faster tools to meet latency requirement
```

## Plan Structure

A plan contains:
- **Steps**: List of tool calls with IDs
- **Dependencies**: Which steps depend on others (DAG)
- **Parallelism**: Which steps can run concurrently
- **Cost Estimate**: Expected execution cost
- **Metadata**: Task description, creation time, model used

```python
{
    "task": "Process receipt",
    "steps": [
        {
            "id": 1,
            "tool": "extract_receipt_fields",
            "parameters": {"receipt_text": "{{receipt}}"},
            "depends_on": []
        },
        {
            "id": 2,
            "tool": "categorize_merchant",
            "parameters": {"merchant": "{{steps[1].output.merchant}}"},
            "depends_on": [1]
        }
    ],
    "estimated_cost": 0.0024,
    "estimated_latency_ms": 450
}
```

## Cost Comparison

**Scenario**: Process 1000 receipts with 3-step workflow

### All Large Model (GPT-4)
- Planning: 1000 × $0.03 = $30.00
- Execution: 1000 × 3 × $0.03 = $90.00
- **Total: $120.00**

### Two-Model Architecture
- Planning: 1 × $0.05 = $0.05
- Execution: 1000 × 3 × $0.0002 = $0.60
- **Total: $0.65 (185x cheaper)**

## See Also
- [execute_plan](execute_plan.md) — Execute generated plans
- [SmallModelWorker](../execution/SmallModelWorker.md) — Execute plans with small models
- [Sample 02: Receipt Categorization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/02-receipt-with-categorization) — Two-model architecture example
- [How to Orchestrate with Code](../../../how-to/orchestrate-with-code.md) — Orchestration patterns

## Notes
- Use temperature 0.1-0.3 for consistent, reliable plans
- Plans are JSON-serializable for caching and reuse
- Large models better at complex dependency reasoning
- Typical planning latency: 2-5 seconds
- Typical planning cost: $0.02-0.10 per plan
- Cache plans when possible to amortize planning cost
