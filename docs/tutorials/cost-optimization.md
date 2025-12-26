# Cost Optimization Tutorial

Learn how to build cost-effective AI workflows by selecting the right tools based on budget constraints and performance tradeoffs.

## What You'll Learn

By the end of this tutorial, you'll understand:

- When to optimize for cost vs speed vs reliability
- How to configure budget constraints for tool selection
- Tradeoffs between expensive premium tools and cheap alternatives
- Real-world cost optimization strategies

## Prerequisites

- Basic understanding of ToolWeaver [tool discovery](../get-started/quickstart.md)
- Familiarity with [tool registration](../how-to/add-a-tool.md)

## The Cost Problem

Imagine you're processing 1,000 receipts per day:

| Tool | Cost per Call | Total Daily Cost |
|------|--------------|------------------|
| **GPT-4 Vision** | $0.10 | $100/day ($3,000/month) |
| **Claude Vision** | $0.05 | $50/day ($1,500/month) |
| **Local OCR** | $0.01 | $10/day ($300/month) |

**Question:** Which tool should you use?

**Answer:** It depends on your constraints:
- **Tight budget?** Use local OCR (10x cheaper)
- **Need accuracy?** Use GPT-4 (but expensive)
- **Balance both?** Use Claude (2x cheaper than GPT-4, still accurate)

ToolWeaver's **CostOptimizer** helps you make this decision automatically based on configurable weights.

---

## Core Concepts

### 1. Cost-Quality Tradeoff

Every tool has three dimensions:

1. **Cost** - How much per API call ($0.01 to $0.50+)
2. **Latency** - How long it takes (100ms to 30s)
3. **Reliability** - Success rate (70% to 99.9%)

You can't optimize all three simultaneously—you must choose priorities.

### 2. Selection Weights

Configure how much each dimension matters:

```python
SelectionConfig(
    cost_weight=0.7,        # 70% priority on cost
    latency_weight=0.2,     # 20% priority on speed
    reliability_weight=0.1, # 10% priority on accuracy
)
```

**Total must equal 1.0**

### 3. Budget Constraints

Set hard limits:

```python
SelectionConfig(
    cost_budget=0.02,         # Never spend more than $0.02/call
    latency_budget=2000,      # Never wait more than 2s
    reliability_threshold=0.9, # Require 90%+ success rate
)
```

---

## When to Use Cost Optimization

### ✅ **Use Cost Optimization When:**

1. **High-volume processing** (100+ operations/day)
   - Batch document processing
   - Receipt scanning at scale
   - Log analysis pipelines

2. **Predictable workloads** (similar tasks repeated)
   - Daily report generation
   - Scheduled data extraction
   - Recurring classification

3. **Budget constraints** (fixed monthly spend)
   - Startup prototyping
   - Free-tier development
   - Cost-sensitive production

### ❌ **Don't Optimize Cost When:**

1. **Accuracy is critical** (medical, financial, legal)
   - Always use best model available
   - Cost is secondary to correctness

2. **One-off tasks** (manual analysis)
   - Optimization overhead not worth it
   - Just use your default model

3. **Real-time requirements** (latency < 500ms)
   - Speed matters more than cost
   - Use fastest available tool

---

## Practical Example: Receipt Processing

Let's build a cost-optimized receipt processor that adapts to workload.

### Step 1: Define Tool Options

Register three vision tools with different cost profiles:

```python
from orchestrator.selection.registry import ToolRegistry
from orchestrator.shared.models import ToolDefinition

registry = ToolRegistry()

# Premium: Fast and accurate, but expensive
gpt4_vision = ToolDefinition(
    name="gpt4_vision",
    description="Premium vision analysis with GPT-4",
    metadata={
        "cost_per_call": 0.10,
        "expected_latency_ms": 500,
        "success_rate": 0.99,
    },
)

# Balanced: Good performance at medium cost
claude_vision = ToolDefinition(
    name="claude_vision",
    description="Balanced vision analysis with Claude",
    metadata={
        "cost_per_call": 0.05,
        "expected_latency_ms": 1500,
        "success_rate": 0.95,
    },
)

# Budget: Slow and less accurate, but cheap
local_ocr = ToolDefinition(
    name="local_ocr",
    description="Local OCR with Tesseract",
    metadata={
        "cost_per_call": 0.01,
        "expected_latency_ms": 3000,
        "success_rate": 0.85,
    },
)

registry.register(gpt4_vision)
registry.register(claude_vision)
registry.register(local_ocr)
```

### Step 2: Configure Selection Criteria

**Scenario A: Tight Budget (Startup)**

```python
from orchestrator.selection.registry import SelectionConfig

# Minimize cost, tolerate slower/less accurate results
startup_config = SelectionConfig(
    cost_weight=0.8,
    latency_weight=0.1,
    reliability_weight=0.1,
    cost_budget=0.02,  # Never exceed $0.02/call
)

tool = registry.get_best_tool(startup_config)
print(f"Selected: {tool.name}")  # → local_ocr
print(f"Cost: ${tool.metadata['cost_per_call']}")  # → $0.01
```

**Scenario B: Production (Balanced)**

```python
# Balance cost and accuracy
production_config = SelectionConfig(
    cost_weight=0.4,
    latency_weight=0.2,
    reliability_weight=0.4,
    cost_budget=0.08,  # Can spend up to $0.08/call
)

tool = registry.get_best_tool(production_config)
print(f"Selected: {tool.name}")  # → claude_vision
print(f"Cost: ${tool.metadata['cost_per_call']}")  # → $0.05
```

**Scenario C: Critical Accuracy (Enterprise)**

```python
# Prioritize accuracy over cost
enterprise_config = SelectionConfig(
    cost_weight=0.1,
    latency_weight=0.2,
    reliability_weight=0.7,
    reliability_threshold=0.95,  # Require 95%+ success rate
)

tool = registry.get_best_tool(enterprise_config)
print(f"Selected: {tool.name}")  # → gpt4_vision
print(f"Accuracy: {tool.metadata['success_rate']}")  # → 0.99
```

### Step 3: Adaptive Selection

Change selection dynamically based on workload:

```python
def select_tool_for_batch(batch_size: int) -> ToolDefinition:
    """Select tool based on batch size."""
    
    if batch_size > 1000:
        # High volume → use cheapest
        config = SelectionConfig(cost_weight=0.9, cost_budget=0.02)
    elif batch_size > 100:
        # Medium volume → balance cost and accuracy
        config = SelectionConfig(cost_weight=0.5, reliability_weight=0.5)
    else:
        # Low volume → prioritize accuracy
        config = SelectionConfig(reliability_weight=0.8)
    
    return registry.get_best_tool(config)

# Process 500 receipts
tool = select_tool_for_batch(500)
print(f"Processing 500 items with: {tool.name}")  # → claude_vision
```

---

## Cost-Saving Strategies

### Strategy 1: Tiered Fallback Chain

Use expensive tools only when cheap ones fail:

```python
# Try cheap tool first, fallback to expensive on failure
cheap_result = await execute_tool(local_ocr, receipt)

if cheap_result.confidence < 0.8:
    # Low confidence → retry with premium tool
    expensive_result = await execute_tool(gpt4_vision, receipt)
    return expensive_result

return cheap_result  # Saved $0.09!
```

### Strategy 2: Batch Processing

Aggregate multiple requests to reduce per-call overhead:

```python
# Instead of 100 individual calls ($10):
for receipt in receipts:
    process(receipt)  # $0.10 × 100 = $10

# Use batch processing ($3):
batch_results = await process_batch(receipts)  # $0.03 × 100 = $3
```

### Strategy 3: Caching

Cache expensive operations:

```python
from orchestrator.infra.redis_cache import RedisCache

cache = RedisCache(ttl=3600)  # 1 hour

@cache.cached("receipt-{receipt_id}")
async def process_receipt(receipt_id: str):
    # First call: $0.10
    # Subsequent calls in 1 hour: $0 (cached)
    return await gpt4_vision.execute(receipt_id)
```

**Savings:** 90% if 10 cache hits per unique receipt

---

## Measuring Cost Savings

Track actual vs potential costs:

```python
from orchestrator.monitoring.cost_tracker import CostTracker

tracker = CostTracker()

# Track actual selection
actual_tool = registry.get_best_tool(startup_config)
actual_cost = actual_tool.metadata["cost_per_call"]
tracker.log_selection(actual_tool, actual_cost)

# Compare to baseline (if we always used premium)
baseline_tool = registry.get_tool("gpt4_vision")
baseline_cost = baseline_tool.metadata["cost_per_call"]

savings = baseline_cost - actual_cost
savings_pct = (savings / baseline_cost) * 100

print(f"Actual cost: ${actual_cost:.2f}")
print(f"Baseline cost: ${baseline_cost:.2f}")
print(f"Savings: ${savings:.2f} ({savings_pct:.0f}%)")
```

**Example Output:**
```
Actual cost: $0.01
Baseline cost: $0.10
Savings: $0.09 (90%)
```

---

## Real-World Scenarios

### Scenario 1: Startup with $100/month Budget

**Goal:** Process as many receipts as possible within budget.

```python
monthly_budget = 100.00
receipts_per_month = 5000

max_cost_per_call = monthly_budget / receipts_per_month  # $0.02

config = SelectionConfig(
    cost_weight=0.95,
    cost_budget=max_cost_per_call,
)

tool = registry.get_best_tool(config)  # → local_ocr ($0.01)

# Can process 10,000 receipts instead of 5,000!
actual_capacity = monthly_budget / tool.metadata["cost_per_call"]
print(f"Monthly capacity: {actual_capacity:.0f} receipts")  # 10,000
```

### Scenario 2: Enterprise with SLA Requirements

**Goal:** 99% accuracy, process within 2 seconds.

```python
config = SelectionConfig(
    reliability_weight=0.7,
    latency_weight=0.3,
    reliability_threshold=0.99,
    latency_budget=2000,  # 2 seconds
)

tool = registry.get_best_tool(config)  # → gpt4_vision
# Costs more, but meets SLA
```

### Scenario 3: Hybrid Workload

**Goal:** Mix of simple (cheap) and complex (expensive) receipts.

```python
def classify_complexity(receipt) -> str:
    # Simple: Only a few line items
    if len(receipt.items) < 5:
        return "simple"
    # Complex: Many items or poor image quality
    return "complex"

async def process_adaptive(receipt):
    complexity = classify_complexity(receipt)
    
    if complexity == "simple":
        # Use cheap tool for simple cases
        config = SelectionConfig(cost_weight=0.9)
    else:
        # Use accurate tool for complex cases
        config = SelectionConfig(reliability_weight=0.9)
    
    tool = registry.get_best_tool(config)
    return await tool.execute(receipt)

# Average cost: $0.03 instead of $0.10 (70% savings)
```

---

## Best Practices

### ✅ Do's

1. **Profile your tools** - Measure actual cost/latency/accuracy
2. **Set realistic budgets** - Don't optimize to unusable quality
3. **Cache aggressively** - 80%+ cache hit rate = 80% cost savings
4. **Use fallbacks** - Try cheap first, fallback to expensive
5. **Monitor actual costs** - Track daily/monthly spend

### ❌ Don'ts

1. **Don't sacrifice accuracy for pennies** - Incorrect results cost more to fix
2. **Don't over-optimize** - Diminishing returns below $0.01/call
3. **Don't ignore latency** - Slow tools frustrate users
4. **Don't hardcode tool names** - Use selection config for flexibility
5. **Don't skip error handling** - Failed calls still cost money

---

## Next Steps

- **How-To Guide:** [Optimize Tool Costs](../how-to/optimize-tool-costs.md) - Step-by-step implementation
- **Deep Dive:** [Hybrid Model Routing](../reference/deep-dives/hybrid-model-routing.md) - Two-model architecture
- **Sample:** [27-cost-optimization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/27-cost-optimization) - Working example

## Related Topics

- [Error Recovery](error-recovery.md) - Handle failures without wasting money
- [Caching Deep Dive](caching-deep-dive.md) - Reduce costs with caching
- [Two-Model Architecture](../reference/deep-dives/two-model-architecture.md) - GPT-4 for planning, Phi-3 for execution

