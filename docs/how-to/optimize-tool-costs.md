# How to Optimize Tool Costs

Step-by-step guide to reduce tool execution costs using cost-aware selection, caching, and batching.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [Cost Optimization](../tutorials/cost-optimization.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Configured `SelectionConfig` with cost weights  
✅ Set up tool metadata with cost estimates  
✅ Implemented cost-aware tool selection  
✅ Added caching to reduce redundant calls  
✅ Optimized batch operations for cost savings  

**Estimated time:** 30 minutes

---

## Step 1: Configure Tool Metadata with Costs

Add cost estimates to your tool registry.

### 1.1 Create Tool Metadata

**File:** `tools/metadata.py`

```python
from orchestrator.selection.registry import ToolMetadata

# Define tool metadata with costs
gpt4_metadata = ToolMetadata(
    name="gpt4_vision",
    description="GPT-4 Vision for image analysis",
    cost_estimate=0.10,  # $0.10 per call
    latency_estimate=3.5,  # 3.5 seconds
    reliability=0.99
)

claude_metadata = ToolMetadata(
    name="claude_vision",
    description="Claude 3 Vision",
    cost_estimate=0.05,  # $0.05 per call
    latency_estimate=2.8,
    reliability=0.98
)

local_ocr_metadata = ToolMetadata(
    name="tesseract_ocr",
    description="Local Tesseract OCR",
    cost_estimate=0.01,  # $0.01 per call (compute only)
    latency_estimate=1.2,
    reliability=0.85
)
```

### 1.2 Register Tools with Metadata

```python
from orchestrator.selection.registry import ToolRegistry

registry = ToolRegistry()

# Register tools with metadata
registry.register(gpt4_vision, metadata=gpt4_metadata)
registry.register(claude_vision, metadata=claude_metadata)
registry.register(tesseract_ocr, metadata=local_ocr_metadata)
```

---

## Step 2: Configure Cost-Aware Selection

Set up `SelectionConfig` to prioritize cost.

### 2.1 Create SelectionConfig

**File:** `config/selection.py`

```python
from orchestrator.selection.config import SelectionConfig

# High cost sensitivity (minimize cost)
budget_config = SelectionConfig(
    cost_weight=0.7,        # 70% weight on cost
    latency_weight=0.2,     # 20% weight on speed
    reliability_weight=0.1  # 10% weight on reliability
)

# Balanced (moderate cost sensitivity)
balanced_config = SelectionConfig(
    cost_weight=0.4,
    latency_weight=0.3,
    reliability_weight=0.3
)

# Performance-focused (minimize latency)
fast_config = SelectionConfig(
    cost_weight=0.1,
    latency_weight=0.7,
    reliability_weight=0.2
)
```

### 2.2 Apply SelectionConfig to Orchestrator

```python
from orchestrator.core.orchestrator import Orchestrator

orchestrator = Orchestrator(
    tools=registry.get_all_tools(),
    selection_config=budget_config  # Use budget-conscious config
)
```

---

## Step 3: Implement Cost-Aware Tool Selection

Use `CostOptimizer` to select cheapest suitable tool.

### 3.1 Basic Cost Optimization

```python
from orchestrator.selection.optimizer import CostOptimizer

optimizer = CostOptimizer(registry=registry, config=budget_config)

# Select cheapest tool for image analysis
selected_tool = optimizer.select_tool(
    capability="image_analysis",
    constraints={
        "max_cost": 0.05,      # Don't exceed $0.05
        "min_reliability": 0.90  # At least 90% reliable
    }
)

print(f"Selected: {selected_tool.name} (${selected_tool.cost_estimate})")
# Output: Selected: claude_vision ($0.05)
```

### 3.2 Adaptive Selection Based on Task Size

```python
def select_tool_by_batch_size(batch_size: int):
    """Choose tool based on batch economics."""
    
    if batch_size < 10:
        # Small batch: use expensive, accurate tool
        return optimizer.select_tool(
            capability="image_analysis",
            constraints={"min_reliability": 0.99}
        )
    elif batch_size < 100:
        # Medium batch: balanced cost/quality
        return optimizer.select_tool(
            capability="image_analysis",
            constraints={"max_cost": 0.05, "min_reliability": 0.95}
        )
    else:
        # Large batch: minimize cost
        return optimizer.select_tool(
            capability="image_analysis",
            constraints={"max_cost": 0.02}
        )

# Usage
tool = select_tool_by_batch_size(batch_size=150)
print(f"For batch of 150: {tool.name} (${tool.cost_estimate})")
# Output: For batch of 150: tesseract_ocr ($0.01)
```

---

## Step 4: Add Caching to Reduce Redundant Calls

Cache expensive tool results.

### 4.1 Set Up Redis Cache

```bash
# Install Redis
pip install redis

# Start Redis server (Docker)
docker run -d -p 6379:6379 redis:latest
```

### 4.2 Implement Caching Layer

**File:** `tools/cache.py`

```python
import redis
import hashlib
import json

class ToolCache:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.ttl = 3600  # 1 hour TTL
    
    def _make_key(self, tool_name: str, params: dict) -> str:
        """Generate cache key from tool name and params."""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()
        return f"tool:{tool_name}:{params_hash}"
    
    async def get(self, tool_name: str, params: dict):
        """Get cached result."""
        key = self._make_key(tool_name, params)
        cached = self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def set(self, tool_name: str, params: dict, result):
        """Cache result."""
        key = self._make_key(tool_name, params)
        self.redis.setex(
            key,
            self.ttl,
            json.dumps(result)
        )

# Usage
cache = ToolCache()

async def execute_with_cache(tool_name: str, params: dict):
    """Execute tool with caching."""
    
    # Check cache first
    cached_result = await cache.get(tool_name, params)
    if cached_result:
        print(f"✓ Cache hit for {tool_name}")
        return cached_result
    
    # Execute tool
    print(f"✗ Cache miss for {tool_name}, executing...")
    result = await orchestrator.execute_tool(tool_name, params)
    
    # Cache result
    await cache.set(tool_name, params, result)
    
    return result
```

### 4.3 Measure Cache Effectiveness

```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    @property
    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0
    
    @property
    def cost_savings(self):
        # Assume average tool cost of $0.05
        return self.hits * 0.05

metrics = CacheMetrics()

async def execute_with_metrics(tool_name: str, params: dict):
    cached = await cache.get(tool_name, params)
    
    if cached:
        metrics.hits += 1
        return cached
    
    metrics.misses += 1
    result = await orchestrator.execute_tool(tool_name, params)
    await cache.set(tool_name, params, result)
    return result

# After processing 1000 receipts
print(f"Cache hit rate: {metrics.hit_rate:.1%}")
print(f"Cost savings: ${metrics.cost_savings:.2f}")
# Output:
# Cache hit rate: 87.5%
# Cost savings: $43.75
```

---

## Step 5: Optimize Batch Operations

Process multiple items efficiently.

### 5.1 Batch Similar Items Together

```python
from collections import defaultdict

async def process_receipts_optimized(receipts: list):
    """Batch receipts by type for cost optimization."""
    
    # Group by type (similar receipts can use same cheap tool)
    by_type = defaultdict(list)
    for receipt in receipts:
        by_type[receipt.type].append(receipt)
    
    results = []
    
    for receipt_type, batch in by_type.items():
        # Select tool based on batch size
        tool = select_tool_by_batch_size(len(batch))
        
        print(f"Processing {len(batch)} {receipt_type} receipts with {tool.name}")
        
        # Process batch
        batch_results = []
        for receipt in batch:
            result = await execute_with_cache(tool.name, {"receipt_id": receipt.id})
            batch_results.append(result)
        
        results.extend(batch_results)
    
    return results
```

### 5.2 Parallel Execution with Rate Limiting

```python
import asyncio
from asyncio import Semaphore

async def process_batch_parallel(items: list, max_concurrent: int = 10):
    """Process batch with concurrency limit to avoid rate limits."""
    
    semaphore = Semaphore(max_concurrent)
    
    async def process_one(item):
        async with semaphore:
            # Select cheapest tool for each item
            tool = optimizer.select_tool(
                capability="image_analysis",
                constraints={"max_cost": 0.05}
            )
            return await execute_with_cache(tool.name, {"item_id": item.id})
    
    results = await asyncio.gather(*[process_one(item) for item in items])
    return results
```

---

## Step 6: Monitor and Optimize Costs

Track spending and adjust configuration.

### 6.1 Cost Tracking

```python
class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.tool_costs = defaultdict(float)
        self.call_counts = defaultdict(int)
    
    def record_call(self, tool_name: str, cost: float):
        self.total_cost += cost
        self.tool_costs[tool_name] += cost
        self.call_counts[tool_name] += 1
    
    def report(self):
        print(f"\n=== Cost Report ===")
        print(f"Total cost: ${self.total_cost:.2f}\n")
        
        for tool_name in self.tool_costs:
            cost = self.tool_costs[tool_name]
            count = self.call_counts[tool_name]
            avg = cost / count
            print(f"{tool_name}:")
            print(f"  Total: ${cost:.2f}")
            print(f"  Calls: {count}")
            print(f"  Avg: ${avg:.4f}")

tracker = CostTracker()

async def execute_with_tracking(tool_name: str, params: dict):
    """Execute tool with cost tracking."""
    
    # Get tool metadata
    tool_metadata = registry.get_metadata(tool_name)
    
    # Execute
    result = await execute_with_cache(tool_name, params)
    
    # Track cost
    tracker.record_call(tool_name, tool_metadata.cost_estimate)
    
    return result
```

### 6.2 Budget Alerts

```python
class BudgetAlert:
    def __init__(self, budget_limit: float):
        self.budget_limit = budget_limit
        self.spent = 0.0
    
    def check(self, cost: float):
        self.spent += cost
        
        if self.spent > self.budget_limit:
            raise RuntimeError(
                f"Budget exceeded: ${self.spent:.2f} / ${self.budget_limit:.2f}"
            )
        
        if self.spent > self.budget_limit * 0.9:
            print(f"⚠️  Warning: 90% of budget used (${self.spent:.2f} / ${self.budget_limit:.2f})")

# Usage
budget = BudgetAlert(budget_limit=100.00)  # $100 budget

async def execute_with_budget(tool_name: str, params: dict):
    tool_metadata = registry.get_metadata(tool_name)
    budget.check(tool_metadata.cost_estimate)
    return await execute_with_cache(tool_name, params)
```

---

## Step 7: Real-World Example

Complete cost-optimized pipeline.

```python
from orchestrator.selection.optimizer import CostOptimizer
from orchestrator.selection.config import SelectionConfig

async def process_receipts_cost_optimized(receipts: list, budget: float):
    """Process receipts with cost optimization."""
    
    # Setup
    registry = ToolRegistry()
    registry.register(gpt4_vision, metadata=gpt4_metadata)
    registry.register(claude_vision, metadata=claude_metadata)
    registry.register(tesseract_ocr, metadata=local_ocr_metadata)
    
    config = SelectionConfig(cost_weight=0.7, latency_weight=0.2, reliability_weight=0.1)
    optimizer = CostOptimizer(registry=registry, config=config)
    cache = ToolCache()
    tracker = CostTracker()
    budget_alert = BudgetAlert(budget_limit=budget)
    
    # Process
    results = []
    
    for receipt in receipts:
        # Check cache
        cached = await cache.get("image_analysis", {"receipt_id": receipt.id})
        if cached:
            results.append(cached)
            continue
        
        # Select cheapest suitable tool
        tool = optimizer.select_tool(
            capability="image_analysis",
            constraints={"min_reliability": 0.90}
        )
        
        # Check budget
        tool_metadata = registry.get_metadata(tool.name)
        budget_alert.check(tool_metadata.cost_estimate)
        
        # Execute
        result = await orchestrator.execute_tool(tool.name, {"receipt_id": receipt.id})
        
        # Track and cache
        tracker.record_call(tool.name, tool_metadata.cost_estimate)
        await cache.set("image_analysis", {"receipt_id": receipt.id}, result)
        
        results.append(result)
    
    # Report
    tracker.report()
    print(f"\nCache hit rate: {cache.hit_rate:.1%}")
    print(f"Total cost: ${tracker.total_cost:.2f} / ${budget:.2f}")
    
    return results
```

---

## Verification

Run this to verify your setup:

```python
async def verify_cost_optimization():
    """Verify cost optimization is working."""
    
    print("Testing cost optimization...")
    
    # Test 1: Tool selection
    tool = optimizer.select_tool(
        capability="image_analysis",
        constraints={"max_cost": 0.05}
    )
    assert tool.cost_estimate <= 0.05, "Tool cost exceeds limit"
    print("✓ Tool selection working")
    
    # Test 2: Caching
    params = {"test": "data"}
    await cache.set("test_tool", params, {"result": "success"})
    cached = await cache.get("test_tool", params)
    assert cached == {"result": "success"}, "Caching not working"
    print("✓ Caching working")
    
    # Test 3: Budget alerts
    try:
        budget = BudgetAlert(budget_limit=0.10)
        budget.check(0.20)  # Should raise
        assert False, "Budget alert not working"
    except RuntimeError:
        print("✓ Budget alerts working")
    
    print("\n✅ All checks passed!")

# Run verification
await verify_cost_optimization()
```

---

## Common Issues

### Issue 1: Cache Not Hitting

**Symptom:** Cache hit rate is 0%

**Solution:** Check Redis connection and key generation

```python
# Test Redis connection
import redis
r = redis.from_url("redis://localhost:6379")
r.ping()  # Should return True

# Debug cache keys
key = cache._make_key("tool_name", {"param": "value"})
print(f"Cache key: {key}")
```

### Issue 2: Tool Selection Ignoring Cost

**Symptom:** Expensive tools selected despite high `cost_weight`

**Solution:** Verify tool metadata and constraints

```python
# Check tool metadata
for tool in registry.get_all_tools():
    metadata = registry.get_metadata(tool.name)
    print(f"{tool.name}: ${metadata.cost_estimate}")

# Check selection config
print(f"Cost weight: {config.cost_weight}")
```

### Issue 3: Budget Exceeded Without Warning

**Symptom:** Costs exceed budget before alert

**Solution:** Lower alert threshold

```python
# Alert at 80% instead of 90%
if self.spent > self.budget_limit * 0.8:
    print(f"⚠️  Warning: 80% of budget used")
```

---

## Next Steps

- **Tutorial:** [Cost Optimization](../tutorials/cost-optimization.md) - Learn core concepts
- **Deep Dive:** [Hybrid Model Routing](../reference/deep-dives/two-model-architecture.md) - Advanced cost techniques
- **Sample:** [27-cost-optimization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/27-cost-optimization) - Complete example

## Related Guides

- [Use Caching](caching.md) - Cache setup details
- [Monitor Performance](monitor-performance.md) - Track cost metrics
- [Implement Retry Logic](implement-retry-logic.md) - Avoid wasted retries
- [Configure A2A Agents](configure-a2a-agents.md) - Minimize delegation costs

