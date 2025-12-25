# Cost-Aware Tool Selection

Choose the right tool for the job based on cost, latency, and reliability constraints.

## What it does
- Scores tools by efficiency (cost × latency × reliability).
- Enforces hard constraints (budget, latency, required capabilities).
- Ranks tools for ranked selection or filtering.
- Integrates with tool registry for seamless selection.

## API

### CostOptimizer
```python
from orchestrator.selection.cost_optimizer import CostOptimizer

optimizer = CostOptimizer(
    cost_weight=0.5,        # 50% importance to cost
    latency_weight=0.3,     # 30% importance to latency
    reliability_weight=0.2, # 20% importance to reliability
)

# Find best tool within budget and time constraints
best = optimizer.select_best_tool(
    tools=[...],
    cost_budget=0.05,           # Max $0.05 per call
    latency_budget=1000,        # Max 1 second
    capability_filter="vision", # Only tools with vision
)

# Rank all qualifying tools
ranked = optimizer.rank_tools(tools, cost_budget=0.05)
for tool, score in ranked:
    print(f"{tool.name}: {score.score:.2f}")
```

### Tool metadata
Add these to `ToolDefinition.metadata`:
```python
tool_def.metadata = {
    "cost_per_call": 0.01,        # USD
    "expected_latency_ms": 500,   # milliseconds
    "success_rate": 0.95,         # 0-1
    "capabilities": ["text", "vision", "code"],
}
```

## Example: Select cheapest text analyzer
```python
from orchestrator.selection.cost_optimizer import CostOptimizer

optimizer = CostOptimizer(cost_weight=0.8, latency_weight=0.1, reliability_weight=0.1)
best = optimizer.select_best_tool(
    tools=text_analyzers,
    capability_filter="text",
)
```

## Weights

Default: `cost:0.5, latency:0.3, reliability:0.2`

Common presets:
- **Cost-optimized:** `cost:0.8, latency:0.1, reliability:0.1`
- **Speed-optimized:** `cost:0.2, latency:0.7, reliability:0.1`
- **Reliability-optimized:** `cost:0.2, latency:0.1, reliability:0.7`
- **Balanced:** `cost:0.33, latency:0.33, reliability:0.34`

## Scoring formula

```
efficiency_score = 
  cost_weight × (1 - normalized_cost) +
  latency_weight × (1 - normalized_latency) +
  reliability_weight × success_rate
```

All components normalized to 0-1 range for fair comparison.

## When to use
- Divide-and-conquer when multiple tools can do the job; pick the most efficient.
- Cost-sensitive applications with strict budgets.
- Latency-critical flows where response time matters.
- Fallback strategy: if primary tool too slow, pick faster alternative.
