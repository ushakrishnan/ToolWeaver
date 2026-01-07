# SmallModelWorker

## Simple Explanation
Execute tools using small, cost-efficient models like GPT-4o-mini or Phi-3 instead of large expensive models for routine tasks.

## Technical Explanation
`SmallModelWorker` is a lightweight execution engine optimized for tool-calling tasks that don't require advanced reasoning. It uses smaller models (1-10B parameters) to reduce latency and cost while maintaining high accuracy for structured tasks like data extraction, formatting, and simple transformations.

**Import Path**
```python
from orchestrator import SmallModelWorker
```

**Signature**
```python
class SmallModelWorker:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        provider: str = "azure-openai",
        max_tokens: int = 1000,
        temperature: float = 0.0
    ):
        ...
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any]
    ) -> Any:
        ...
```

## When to Use
- **Cost Optimization**: Use small models for 80% of tool calls, save large models for planning
- **Two-Model Architecture**: Combine LargePlanner (GPT-4) + SmallModelWorker (GPT-4o-mini)
- **High-Volume Processing**: Process thousands of receipts, emails, or records cheaply
- **Simple Extraction**: Extract structured data without complex reasoning

## Key Methods
- `execute_tool(tool_name, parameters)`: Execute a single tool call with the small model
- `batch_execute(tool_calls)`: Execute multiple tool calls in parallel
- `get_capabilities()`: Return model capabilities and limitations

## Examples

### Basic Tool Execution
```python
from orchestrator import SmallModelWorker

# Create worker with cost-efficient model
worker = SmallModelWorker(
    model="gpt-4o-mini",
    provider="azure-openai",
    temperature=0.0  # Deterministic output
)

# Execute simple extraction task
result = await worker.execute_tool(
    tool_name="extract_receipt_total",
    parameters={"text": receipt_text}
)
print(f"Total: ${result['total']}")
```

### Two-Model Architecture
```python
from orchestrator import LargePlanner, SmallModelWorker, execute_plan

# Step 1: Large model creates plan
planner = LargePlanner(model="gpt-4o")
plan = await planner.create_plan(
    task="Process 100 receipts: extract totals, categorize, summarize",
    tools=tool_catalog
)

# Step 2: Small model executes plan steps
worker = SmallModelWorker(model="gpt-4o-mini")
results = await execute_plan(plan, worker=worker)

# Cost savings: ~90% cheaper than using GPT-4 for everything
print(f"Processed 100 receipts for ${results['cost']:.2f}")
```

### Batch Processing
```python
from orchestrator import SmallModelWorker

worker = SmallModelWorker(model="gpt-4o-mini")

# Process many items in parallel
tool_calls = [
    {"tool": "categorize", "params": {"text": f"receipt_{i}"}}
    for i in range(1000)
]

results = await worker.batch_execute(tool_calls)
print(f"Processed {len(results)} receipts at $0.0002 each")
```

### Cost Comparison
```python
from orchestrator import SmallModelWorker

# Scenario: Process 1000 receipts
# Option 1: All GPT-4 = 1000 calls × $0.03 = $30.00
# Option 2: SmallModelWorker = 1000 calls × $0.0002 = $0.20

worker = SmallModelWorker(model="gpt-4o-mini")
total_cost = 0.0

for receipt in receipts:
    result = await worker.execute_tool("extract_fields", {"text": receipt})
    total_cost += result.get("cost", 0.0002)

print(f"Total cost: ${total_cost:.2f} (150x cheaper than GPT-4)")
```

## See Also
- [LargePlanner](../orchestration/LargePlanner.md) — Planning with large models
- [execute_plan](../orchestration/execute_plan.md) — Execute planned workflows
- [Sample 02: Receipt Categorization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/02-receipt-with-categorization) — Two-model architecture demo
- [How to Orchestrate with Code](../../../how-to/orchestrate-with-code.md) — Orchestration patterns

## Notes
- Small models excel at structured tasks but may struggle with complex reasoning
- Use temperature=0.0 for deterministic extraction and classification
- Supports models: GPT-4o-mini, Claude Haiku, Phi-3, Llama-3.1-8B
- Typical latency: 100-300ms per call (3-5x faster than large models)
- Typical cost: $0.0002-0.0005 per call (100-200x cheaper than GPT-4)
